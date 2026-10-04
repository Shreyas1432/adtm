# ADTM — Product Requirements Document (PRD)

> **Status:** Phase 0 (walking skeleton) complete; Phase 1 in planning.
> **Owner:** Shreyas Sudarshanam · **Last updated:** 2026-10-04
> This PRD is bound by the locked architecture in [`docs/adr/`](adr/) and the
> non-negotiable invariants in [`CLAUDE.md`](../CLAUDE.md). Where this document
> and an ADR disagree, the ADR wins — change the ADR first.

---

## 1. Summary

**ADTM** is a **sovereign, client-deployed ERP migration & diagnostics accelerator**.
It runs entirely **inside the client's environment** (no data leaves the client
boundary) and shortens the most expensive, error-prone parts of an ERP migration:
extraction, data-quality assessment, mapping, load, and reconciliation.

- **Initial wedge:** Oracle **EBS → Oracle Fusion**.
- **Delivery model:** an IP-led delivery accelerator used by a migration team —
  **not** a licensed SaaS product for the initial wedge.
- **Differentiator:** source-preserving (immutable Bronze), security-first
  (field-level AEAD + envelope keys), and **AI as design-time assistance only** —
  every AI suggestion becomes human-approved, versioned, deterministic config.

## 2. Problem & goals

ERP migrations fail or overrun on three things: (1) opaque source data quality,
(2) mapping effort and rework, and (3) reconciliation — proving the target
actually matches the source. Teams also cannot safely use cloud AI on client ERP
data for sovereignty/compliance reasons.

**Goals**
- Cut mapping / DQ / reconciliation effort measurably versus a manual baseline.
- Make every run **reproducible** and **auditable** (hash-chained audit).
- Keep all data and keys **inside the client boundary**.
- Prove safe **partial-failure replay** and **actual-state read-back** reconciliation.

**Non-goals (now)** — see [`CLAUDE.md`](../CLAUDE.md) "Do NOT build yet":
SAP/PeopleSoft/JDE/NetSuite adapters, Spark, Temporal, Kubernetes, autonomous or
runtime AI, multi-client SaaS, DRM/licence tamper-resistance.

## 3. Scope

### In scope (Phase 0 → Phase 1)
| Area | Phase 0 (done) | Phase 1 (MVP, one object end-to-end) |
|---|---|---|
| Control plane | Postgres schema + FastAPI health/read endpoints | Routers for connections, extraction, DQ, mapping, load, readback, reconcile, audit |
| Jobs | Durable-jobs worker (`FOR UPDATE SKIP LOCKED`) + handler stubs | Idempotent, checkpointed handlers implemented |
| Data plane | Immutable Bronze (Parquet + manifest + sha256), DuckDB helper | Extraction → Bronze → DQ/profiling → mapping transforms |
| Security | AES-256-GCM + envelope wrap + HMAC blind index (tested) | Encryption-choice UI, key-version tracking per dataset |
| Adapters | Contracts for EBS source / Fusion load / Fusion read-back | Real implementations validated at pilot |
| AI | Gateway interface (disabled) | Design-time suggestions (table/SQL/mapping/DQ/error) + instrumentation |
| UI | React+TS shell showing API health | Phase-1 screens (see journeys) |

### MVP migration object
Default **Suppliers** (self-contained) → then **AP Invoice** (financial
reconciliation). Finalised against the pilot client's scope. *(Open item — does
not block Phase 0.)*

### Out of scope
Everything in the "Do NOT build yet" list, and any feature that would require AI
at execution time or writing back to a source ERP.

## 4. Users & personas

| Persona | Role | Primary needs | Key screens |
|---|---|---|---|
| **Migration Engineer** | Builds & runs the migration | Connect source, write/version extraction SQL, review DQ, build mappings, run load, reconcile | Extraction, DQ, Mapping, Load, Reconciliation |
| **Data / DQ Analyst** | Assesses source readiness | Profiling, DQ rule results, readiness diagnostic report | DQ, Profiling |
| **Migration Lead / Approver** | Owns correctness & sign-off | Approve AI suggestions & mappings, review reconciliation evidence, verify audit chain | Mapping approval, Reconciliation, Audit |
| **Security / Compliance Officer** | Owns sovereignty & controls | Confirm keys never leave KMS, verify audit integrity, confirm source read-only | Audit, Connections (secret refs) |
| **Workspace Admin** | Tenancy & access | Manage workspace, members, connections | Admin, Connections |

All users operate within a single **workspace** (tenant isolation boundary).
RBAC is thin in Phase 0 (`workspace_member.role`) and hardened in Phase 2.

## 5. User journeys

### J1 — Connect & discover (source, read-only)
1. Admin registers an **EBS connection** (`kind='source_ebs'`); the secret is a
   `secret_ref` handle — the actual credential lives in the client secrets
   manager, never in the DB.
2. Engineer tests the connection (read-only account), lists tables, and inspects
   column metadata (name/type/length/PK/description).

### J2 — Extract to immutable Bronze
1. Engineer writes extraction SQL (optionally AI-assisted), reviews it, and runs it.
2. An `extract` job is enqueued; the worker claims it and streams rows to a
   **write-once** Bronze Parquet dataset with a manifest + sha256.
3. A new run **never overwrites** Bronze — it creates a new dataset/version.

### J3 — Data quality & readiness diagnostic
1. Engineer/Analyst defines DQ rules (null/datatype/length/duplicate/RI/date/business).
2. A `dq` job runs them over Bronze via DuckDB; results (passed/failed/sample) are
   stored and shown. Profiling + DQ can be packaged as a standalone **readiness diagnostic**.

### J4 — Mapping (human-approved, versioned)
1. Engineer builds field mappings (1:1 / 1:many / static / XREF / lookup).
2. AI may **suggest** mappings; a human **approves** (`approved_by/approved_at`).
3. Approved config is frozen into a **workflow version** — a rerun reproduces
   results with **no model available**.

### J5 — Load → read-back → reconcile
1. A `load` job validates and submits payloads to Fusion with an **idempotency key**;
   async + **partial success** is treated as normal; failed subsets are replayable.
2. A `readback` job re-reads **actual** target state (never infers success from
   the load response).
3. A `reconcile` job computes counts (source/expected/actual/loaded/failed/unmatched)
   and control/financial totals, and writes a reconciliation **evidence artifact**.

### J6 — Audit & sign-off
1. Every security-relevant action appends to a **hash-chained** audit log.
2. Approver reviews reconciliation evidence and **verifies the audit chain** before sign-off.

## 6. Feature specifications

Each feature maps to control-plane tables in
[`db/migrations/0001_init.sql`](../db/migrations/0001_init.sql) and job handlers in
[`workers/handlers/`](../workers/handlers/).

### F1 — Connections
- **Tables:** `connection` (`kind`, `name`, `secret_ref`, `config` JSONB).
- **Rules:** secrets are references only; source connections use a **read-only**
  account; test-connection is non-mutating.
- **API (Phase 1):** `POST /connections`, `POST /connections/{id}/test`, `GET /connections`.

### F2 — Schema discovery
- **Adapter:** `SourceAdapter.list_tables()`, `column_metadata(table)`.
- **Output:** table list + column metadata (type/length/PK/description) to drive
  extraction and the per-field encryption choice.

### F3 — Extraction → Bronze
- **Tables:** `extraction` (sql_text, tables), `bronze_manifest` (file_path,
  file_sha256, row_count, schema_fingerprint, key_version).
- **Handler:** `extract.run` — idempotent, checkpointed; writes via
  [`dataplane/bronze.write_bronze`](../dataplane/bronze.py).
- **Invariant:** Bronze is **immutable**; sensitive columns encrypted with a
  DEK; `key_version` stamped on the manifest.

### F4 — Data quality engine
- **Tables:** `dq_rule` (rule_type, params), `dq_result` (passed/failed/sample/run_id).
- **Rule types:** null · datatype · length · duplicate · RI · date · business.
- **Engine:** DuckDB over Bronze Parquet ([`dataplane/duck.py`](../dataplane/duck.py)).
- **Deliverable:** packaged **readiness diagnostic** (profiling + DQ).

### F5 — Mapping
- **Tables:** `mapping` (source_field, target_field, kind, transform,
  approved_by/at), `xref` (source_value → target_value).
- **Kinds:** one_to_one · one_to_many · static · xref · lookup.
- **Rule:** **human approval required** before a mapping enters a version.

### F6 — Versioning & reproducibility
- **Tables:** `workflow`, `workflow_version` (frozen `config` snapshot, `version_no`).
- **Rule:** a version rerun must reproduce results **deterministically with no AI**.

### F7 — Load (Fusion)
- **Tables:** `load_run` (manifest, target_job_id, target_file_id, status,
  response_artifact).
- **Adapter:** `TargetLoadAdapter` — `validate/submit/poll/errors/replay_failed`.
- **Rules:** idempotent submit; partial success normal; failed-subset replay.

### F8 — Read-back & reconciliation
- **Adapter:** `TargetReadBackAdapter.read_back/coverage` — re-reads **actual** state.
- **Tables:** `reconciliation` (source/expected/actual/loaded/failed/unmatched
  counts, control_totals, evidence_path).
- **Invariant:** success is proven by read-back, never inferred from the load response.

### F9 — AI design-time assistance
- **Tables:** `ai_suggestion` (kind, suggestion, confidence, decision,
  t_generated_ms, t_review_ms).
- **Gateway:** [`ai_gateway/gateway.py`](../ai_gateway/gateway.py) — disabled by
  default (`ADTM_AI_ENABLED=false`). See [AI Agents Guide](AI_AGENTS_GUIDE.md).
- **Rules:** suggestions only → human approval → versioned config; model sees
  metadata/masked samples, never raw PII.

### F10 — Audit
- **Table:** `audit_log` (prev_hash, hash) — append-only, **hash-chained**.
- **Feature:** chain-verification endpoint/report for sign-off.

### F11 — Durable jobs
- **Table:** `job` (job_type, status, attempt/max_attempts, idempotency_key,
  checkpoint, payload). Claim via `FOR UPDATE SKIP LOCKED`.
- **Types:** extract · dq · map · simulate · load · readback · reconcile.

### F12 — Simulation (built last in Phase 1)
- **Handler:** `simulate.run` — predicts load failures; implemented **after** real
  load errors are observed (per backlog build order).

## 7. Success metrics (gate-mapped)

| Gate | Evidence |
|---|---|
| Gate 1 | Architecture + benchmark feasibility (extraction, DuckDB, encryption, isolation, read-back) |
| Gate 2 | Measurable mapping/DQ/reconciliation effort reduction vs baseline (`t_generated_ms` vs `t_review_ms`; AI acceptance/correction rate) |
| Gate 3 | Safe partial-failure replay + actual-state read-back reconciliation |
| Gate 4 | A credible delivery engagement shows real economics |
| Gate 5 | Scale / pivot / stop decision |

**Open item (do not block Phase 0):** baseline measurement method — parallel manual
run vs comparable engagement vs structured estimation. Decide before measuring
(Gate 2/Gate 4 depend on it).

## 8. Constraints & invariants (summary)

Source read-only · Bronze immutable · AI design-time only · AI sees metadata not
raw PII · reconciliation re-reads actual target state · control plane ≠ data plane
· AES-256-GCM + blind index on high-cardinality keys only · keys via envelope
encryption in client KMS/HSM (never in DB/source/logs) · audit hash-chained ·
every handler idempotent. Full text in [`CLAUDE.md`](../CLAUDE.md).

## 9. Release phases

Phase 0 foundation (this skeleton) → Phase 1 one object end-to-end + MVP AI +
instrumentation → Phase 2 hardening → Phase 3 scale → Phase 4 AI intelligence →
Phase 5 expansion. **Every phase ships a usable increment.**
See [`docs/BACKLOG_Phase0_Phase1.md`](BACKLOG_Phase0_Phase1.md).
