# ADTM - Sovereign ERP Migration Accelerator

Client-deployed, source-preserving ERP migration & diagnostics platform.
Initial wedge: **Oracle EBS → Oracle Fusion**. IP-led delivery accelerator
(not a licensed product for the initial wedge).

This repository is the **Phase-0 walking skeleton**: the thin spine on which the
first migration object runs. It boots end-to-end; the migration stages are
scaffolded as idempotent job handlers to be filled in Phase 1.

## What runs today (Phase 0)
- PostgreSQL control-plane schema (projects, workspaces, connections, workflows,
  versions, mappings, DQ rules, jobs, manifests, load/reconciliation, audit).
- FastAPI control-plane API (`/health`, `/workspaces`, `/projects`, `/jobs`).
- Durable-jobs worker that claims jobs via `FOR UPDATE SKIP LOCKED`.
- Dataplane: immutable Bronze writer (encrypted-ready Parquet + manifest + sha256), DuckDB helper.
- Security: AES-256-GCM field encryption + envelope wrap + HMAC blind index (tested).
- Adapter contracts: EBS source, Fusion **load**, Fusion **read-back** (distinct).
- AI gateway interface (disabled by default; design-time only).
- React + TypeScript shell showing API health.

## Quick start
```bash
cp .env.example .env            # dev defaults; replace key material via KMS in prod
docker compose up --build
# API    -> http://localhost:8000/health   (+ /docs for OpenAPI)
# Front  -> http://localhost:5173
```

## Run the crypto tests
```bash
pip install -r api/requirements.txt pytest
pytest tests/
```

## Layout
| Path | Responsibility |
|---|---|
| `api/` | FastAPI control-plane service (control plane only) |
| `core/` logic lives in `api/app` | domain models/routers (Phase 1) |
| `workers/` | durable-jobs worker + stage handlers |
| `dataplane/` | Bronze (Parquet) I/O + DuckDB transform/profiling |
| `adapters/` | `source_ebs`, `fusion_load`, `fusion_readback` |
| `ai_gateway/` | model-agnostic AI interface (design-time only) |
| `security/` | AEAD crypto, blind index, envelope keys |
| `db/migrations/` | control-plane schema (auto-applied by Postgres on first boot) |
| `deploy` = `docker-compose.yml` | appliance packaging (Compose, not K8s) |
| `docs/adr/` | Architecture Decision Records (locked decisions) |
| `tests/` | pytest (crypto) + Phase-1 E2E (Playwright) |

## Non-negotiable invariants
See `CLAUDE.md`. In short: source is read-only; Bronze is immutable; AI never
runs at execution time; reconciliation re-reads actual target state; secrets/keys
never live in the DB or source; everything stays inside the client boundary.

## Open items (finalise with pilot client — do not block Phase 0)
- **MVP object**: default **Suppliers** (self-contained) → then **AP Invoice**
  (financial reconciliation). Finalise against the client's migration scope.
- **Baseline measurement method**: parallel manual run vs comparable engagement
  vs structured estimation — decide before measuring (Gate 2/Gate 4 depend on it).
