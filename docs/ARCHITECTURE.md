# ADTM — Architecture

> Bound by the Architecture Decision Records in [`docs/adr/`](adr/) and the
> invariants in [`CLAUDE.md`](../CLAUDE.md). New architectural decisions require a
> new ADR **before** coding. **Last updated:** 2026-10-04.

---

## 1. Context

ADTM is a **sovereign appliance**: it is deployed and runs entirely **inside the
client's environment**. No source data, no derived data, and no key material
leaves the client boundary. The initial wedge migrates **Oracle EBS → Oracle
Fusion**.

```
                        ┌────────────────────────── CLIENT BOUNDARY ──────────────────────────┐
                        │                                                                      │
  Oracle EBS  ──(RO)──▶ │  Source Adapter ──▶ Bronze (Parquet, immutable) ──▶ DuckDB transform │
  (read-only acct)      │        │                     │                           │           │
                        │        │              Bronze manifests            DQ / profiling      │
                        │        ▼                     ▼                           ▼            │
                        │  ┌───────────── Control plane (PostgreSQL) ─────────────┐             │
                        │  │ workspaces/projects/connections/workflow/versions    │             │
                        │  │ mappings/dq/jobs/manifests/load/reconciliation/audit │             │
                        │  └───────────┬──────────────────────────┬──────────────┘             │
                        │       FastAPI API                 Durable-jobs worker                 │
                        │      (control only)        (extract/dq/map/load/readback/reconcile)   │
                        │              │                           │                            │
                        │        React+TS UI                 Load Adapter ──▶  Oracle Fusion     │
                        │                                    Read-Back Adapter ◀── (actual state)│
                        │                                                                      │
                        │        AI gateway (design-time only, disabled by default)             │
                        │        KEK in client KMS/HSM ─ wraps per-domain DEKs                   │
                        └──────────────────────────────────────────────────────────────────────┘
```

## 2. Tech stack (locked — see ADRs)

| Layer | Choice | ADR / notes |
|---|---|---|
| Frontend | **React 18 + TypeScript** (Vite), MUI as the component library | shell in [`frontend/`](../frontend/); see [Design System](DESIGN_SYSTEM.md) |
| API | **FastAPI / Python ≥3.11**, SQLAlchemy core over `text()` | control plane only — ADR-0001 |
| Control store | **PostgreSQL 16** | workflow/metadata/audit — ADR-0001 |
| Durable jobs | **PostgreSQL job table** + idempotent workers (`FOR UPDATE SKIP LOCKED`) | **not** Temporal/Celery — ADR-0004 |
| Bronze store | **Parquet** (zstd), write-once + sha256 + manifest | immutable — ADR-0003 |
| Analytics/transform | **DuckDB** over Parquet | Spark deferred — ADR-0002 |
| Security | **AES-256-GCM** AEAD · envelope-wrapped DEKs · HMAC blind index | ADR-0006, ADR-0007 |
| Audit | **Hash-chained** append-only log | ADR-0008 |
| AI | Model-agnostic gateway (vLLM/Ollama), **design-time only** | ADR-0005 |
| Packaging | **Docker Compose** appliance | not K8s — ADR-0010 |

## 3. Components

### 3.1 Control plane — FastAPI (`api/`)
Thin, **control-plane-only** service. Phase 0 exposes `/health`, `/workspaces`,
`/projects`, `/jobs` ([`api/app/main.py`](../api/app/main.py)). DB access is a
pooled SQLAlchemy engine with `pool_pre_ping` ([`api/app/db.py`](../api/app/db.py));
the DSN is built from env ([`api/app/config.py`](../api/app/config.py)). **Bulk
data never flows through the API/ORM** — only control, workflow, metadata, audit.

### 3.2 Durable-jobs worker (`workers/`)
A single-loop worker ([`workers/worker.py`](../workers/worker.py)) claims one
`pending` job via `UPDATE ... WHERE id = (SELECT ... FOR UPDATE SKIP LOCKED)`,
dispatches by `job_type` to a handler, and marks success/failure. Handlers live in
[`workers/handlers/`](../workers/handlers/) (`extract`, `dq`, `mapping`,
`simulate`, `load`, `readback`, `reconcile`) and must be **idempotent and
checkpointed** so partial failures replay without duplicate target creation.

### 3.3 Data plane (`dataplane/`)
- **Bronze writer** ([`dataplane/bronze.py`](../dataplane/bronze.py)): writes
  columnar Parquet under `ADTM_DATA_ROOT/<workspace>/bronze/<dataset>/`, computes
  a sha256, writes a `*.manifest.json`, and returns a manifest dict the caller
  persists into `bronze_manifest`. **Write-once** — a new extraction = a new file.
- **DuckDB helper** ([`dataplane/duck.py`](../dataplane/duck.py)): registers
  Parquet files as views and runs analytical/transform SQL.

### 3.4 Adapters (`adapters/`)
Three **distinct** contracts ([`adapters/base.py`](../adapters/base.py)):
- `SourceAdapter` — `test_connection`, `list_tables`, `column_metadata`,
  `extract` (read-only; never writes source). EBS impl is a Phase-1 stub.
- `TargetLoadAdapter` — `validate/submit/poll/errors/replay_failed` with an
  idempotency key; async + partial success are normal.
- `TargetReadBackAdapter` — `read_back/coverage`; re-reads **actual** target
  state for reconciliation. Load and read-back are intentionally separate (ADR-0009).

### 3.5 Security (`security/`)
[`security/crypto.py`](../security/crypto.py): envelope encryption (`generate_dek`,
`wrap_dek`, `unwrap_dek`), field AEAD (`encrypt_field`/`decrypt_field`,
randomized nonce), and a keyed **`blind_index`** (HMAC-SHA256, domain-salted) for
equality/dedupe on **high-cardinality** keys only. `KEY_VERSION` is stamped on
encrypted objects. Dev keys come from env; **production keys come from the client
KMS/HSM**. Covered by [`tests/test_crypto.py`](../tests/test_crypto.py).

### 3.6 AI gateway (`ai_gateway/`)
[`ai_gateway/gateway.py`](../ai_gateway/gateway.py): model-agnostic interface,
**disabled by default** (`ADTM_AI_ENABLED=false`). Returns instrumented
`Suggestion`s (metadata-only context). Details in [AI Agents Guide](AI_AGENTS_GUIDE.md).

### 3.7 Frontend (`frontend/`)
React+TS Vite shell ([`frontend/src/App.tsx`](../frontend/src/App.tsx)) that polls
API health. Vite proxies `/api` → `http://api:8000`
([`frontend/vite.config.ts`](../frontend/vite.config.ts)).

## 4. Data flow (one object, Phase 1)

```
connect(RO) → discover schema → extraction SQL (versioned)
     → [job: extract]  → Bronze Parquet (immutable) + manifest(sha256,key_version)
     → [job: dq]       → DuckDB over Bronze → dq_result (+ readiness diagnostic)
     → mapping (human-approved) frozen into workflow_version
     → [job: load]     → Fusion submit (idempotency_key); partial success OK
     → [job: readback] → re-read ACTUAL Fusion state
     → [job: reconcile]→ counts + control totals + evidence_path
     → audit_log (hash-chained) across the whole run
```

Two planes, never crossed:
- **Control plane (Postgres):** workflow state, metadata, mappings, DQ config/results,
  job queue, manifests, load/reconciliation records, audit. Transactional, queryable.
- **Data plane (Parquet + DuckDB):** bulk source snapshots and transforms. Bulk
  data is **never** routed through the ORM; control state is **never** put in Parquet.

## 5. System boundaries

- **Client boundary (hard):** everything runs inside the client's environment.
  No external calls for data or AI; the AI runtime (if enabled) is a local model
  (vLLM/Ollama) inside the boundary.
- **Source boundary:** source ERP is **read-only**. ADTM never writes back to a source.
- **Control vs data plane:** enforced by component responsibility (§4).
- **Secrets boundary:** connection secrets are **references** (`connection.secret_ref`);
  real credentials live in the client secrets manager. **Keys/secrets never live in
  the DB, source, logs, or config files.** KEK in client KMS/HSM; DEKs unwrapped on demand.
- **AI boundary:** AI is invoked **only at design time**; no execution path calls a
  model at runtime; the model sees metadata/masked samples, not raw PII.
- **Trust/integrity boundary:** audit log is append-only and hash-chained; Bronze
  is immutable and checksummed.

## 6. Deployment (ADR-0010)

Packaged as a **Docker Compose** appliance
([`docker-compose.yml`](../docker-compose.yml)): `postgres` (auto-applies
`db/migrations/` on first boot) + `api` (`:8000`) + `worker` + `frontend`
(`:5173`). A persistent `datavol` holds the Bronze data plane; `pgdata` holds the
control plane. An optional local `ai-runtime` (Ollama) service is commented out and
enabled per client. **Kubernetes is explicitly deferred.**

### Run locally
```bash
cp .env.example .env            # dev defaults; replace key material via KMS in prod
docker compose up --build
# API   -> http://localhost:8000/health   (+ /docs)
# Front -> http://localhost:5173
```

## 7. Configuration

Env (see [`.env.example`](../.env.example)): `POSTGRES_*`; `ADTM_KEK_DEV` and
`ADTM_BLIND_INDEX_KEY_DEV` (32-byte base64, **dev only** — KMS in prod);
`ADTM_DATA_ROOT` (Bronze root, default `/data`); `ADTM_AI_BASE_URL` and
`ADTM_AI_ENABLED` (default `false`). `.env` is git-ignored and must never be committed.

## 8. ADR index

| ADR | Decision |
|---|---|
| 0001 | Control plane / data plane separation |
| 0002 | DuckDB as default engine; Spark deferred |
| 0003 | Immutable encrypted Bronze as Parquet |
| 0004 | PostgreSQL durable jobs, not Temporal (MVP) |
| 0005 | AI is design-time assistance only |
| 0006 | AEAD + keyed blind index, high-cardinality only |
| 0007 | Envelope encryption + tested key recovery |
| 0008 | Hash-chained, tamper-evident audit |
| 0009 | Reconciliation re-reads actual target state |
| 0010 | Appliance packaging via Docker Compose |
