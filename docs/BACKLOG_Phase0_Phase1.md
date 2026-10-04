# ADTM Backlog — Phase 0 & Phase 1

Phase 0 = thin walking skeleton (this repo). Phase 1 = one object end-to-end.
Tracks to the five investment gates (Gate 1 architecture+benchmark … Gate 5 decision).

## Phase 0 — Foundation (done / stubbed in this skeleton)
- [x] Repo + monorepo layout + Docker Compose
- [x] PostgreSQL control-plane schema + auto-migration
- [x] FastAPI app shell + health + read endpoints
- [x] Durable-jobs worker (FOR UPDATE SKIP LOCKED) + handler stubs
- [x] Bronze Parquet writer + manifest + checksum
- [x] Security: AEAD + envelope + blind index (+ tests)
- [x] Adapter contracts (source / load / read-back)
- [x] AI gateway interface (disabled)
- [x] React+TS shell
- [ ] Thin auth + single-workspace context on every request
- [ ] CI (lint + pytest) via GitHub Actions / client equivalent

## Phase 1 — MVP (one object end-to-end)
Build order deliberately: **load/read-back/reconcile before simulation**.
Engine logic is built + unit/E2E tested offline; items marked *(pilot)* need the
real EBS/Fusion integration and the UI screens at the pilot.
- [x] EBS source adapter: connect (read-only), list tables, column metadata (type/len/PK/desc)
- [x] Schema discovery (API + encryption-choice suggestion); *(pilot: UI)*
- [x] Extraction → encrypted immutable Bronze (`dataplane/extract.py`); *(pilot: SQL editor UI)*
- [x] DQ engine: null/datatype/length/duplicate/RI/date/business (`dataplane/dq.py`); *(pilot: results UI)*
- [x]   → DQ + profiling packaged as the readiness diagnostic (engine)
- [x] Mapping: 1:1 / static / XREF / lookup + versioned/approved config (`dataplane/transform.py`); 1:many deferred
- [x] Fusion **load**: validate → submit → poll → errors → partial-failure replay, idempotent (`adapters/fusion_local.py`); *(pilot: real FBDI/ESS adapter)*
- [x] Fusion **read-back**: re-read actual state + coverage (`adapters/fusion_local.py`); *(pilot: real BICC/REST adapter)*
- [x] Reconciliation: counts, loaded/failed/unmatched, control totals, status (`dataplane/reconcile.py`)
- [x] Simulation: predict load failures via the DQ engine (`workers/handlers/simulate.py`)
- [x] MVP AI: metadata-only mapping/DQ suggesters, approval-gated (`ai_gateway/local.py`); table/SQL/error-explanation *(pilot)*
- [x] AI instrumentation: `t_generated_ms` on every suggestion (acceptance/correction rate persists at pilot)
- [x] Hash-chained audit over the run + chain verification (`security/audit.py`)
- [x] E2E test: Suppliers extract→…→reconcile, offline (`tests/test_e2e_suppliers.py`); *(pilot: Playwright UI E2E)*
- [ ] Benchmark: extraction/transform/read-back/concurrency envelope *(pilot, needs real systems)*

## Gate-mapped exit evidence
- Gate 1: architecture + benchmark feasibility (extraction, DuckDB, encryption, isolation, read-back)
- Gate 2: measurable mapping/DQ/reconciliation effort reduction vs baseline
- Gate 3: safe partial-failure replay + actual-state read-back reconciliation
- Gate 4: a credible Deloitte engagement shows real delivery economics
- Gate 5: scale / pivot / stop
