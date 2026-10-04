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
- [ ] EBS source adapter: connect (read-only), list tables, column metadata (type/len/PK/desc)
- [ ] Schema discovery UI + encryption-choice selection
- [ ] Extraction: SQL editor (AI-assisted), execute, immutable Bronze version, inspect
- [ ] DQ engine: null/datatype/length/duplicate/RI/date/business rules + results UI
- [ ]   → package DQ + profiling as the standalone **readiness diagnostic**
- [ ] Mapping: 1:1 / 1:many / static / XREF / lookup; human approval + versioning
- [ ] Fusion **load** adapter: validate → submit → poll → errors → partial-failure replay (idempotent)
- [ ] Fusion **read-back** adapter: re-read actual state; coverage report
- [ ] Reconciliation: counts, loaded/failed/unmatched, control/financial totals, evidence artifact
- [ ] Simulation: predict load failures (built after real errors are known)
- [ ] MVP AI: table/SQL/mapping/DQ suggestions + error explanation (approval-gated)
- [ ] AI instrumentation: acceptance/correction rate, T_AI vs T_manual
- [ ] Hash-chained audit over the full run + chain verification
- [ ] E2E test: one object extract→…→reconcile (Playwright)
- [ ] Benchmark: extraction/transform/read-back/concurrency envelope

## Gate-mapped exit evidence
- Gate 1: architecture + benchmark feasibility (extraction, DuckDB, encryption, isolation, read-back)
- Gate 2: measurable mapping/DQ/reconciliation effort reduction vs baseline
- Gate 3: safe partial-failure replay + actual-state read-back reconciliation
- Gate 4: a credible Deloitte engagement shows real delivery economics
- Gate 5: scale / pivot / stop
