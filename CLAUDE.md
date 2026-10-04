# ADTM — working rules for Claude Code / contributors

ADTM is a **sovereign, client-deployed ERP migration accelerator** (Oracle EBS →
Oracle Fusion). Everything runs **inside the client's environment**. These rules
are derived from the locked architecture (`docs/adr/`). Do not violate them; if a
change seems to require it, add/alter an ADR first.

## Non-negotiable invariants
1. **Source is read-only.** Never write back to any source ERP. Extraction uses a
   read-only account.
2. **Bronze is immutable.** Source snapshots are write-once Parquet. A new
   extraction creates a new dataset/version; never overwrite or mutate Bronze.
3. **AI is design-time only.** No execution path may call a model at runtime. AI
   produces *suggestions* → **human approval** → **versioned config** → deterministic
   execution. A version rerun must reproduce results with no model available.
4. **AI sees metadata, not raw PII.** Default context = schema, descriptions,
   profiles, masked/synthetic samples. Raw PII requires an explicit, audited path.
5. **Reconciliation re-reads actual target state** via the Read-Back Adapter — never
   infer success from the load response.
6. **Control plane ≠ data plane.** Control/workflow/metadata/audit in PostgreSQL;
   bulk source/transform data in Parquet + DuckDB. Do not route bulk data through
   the ORM; do not put control state in Parquet.
7. **Encryption**: AES-256-GCM (AEAD) for sensitive values; **blind index only on
   high-cardinality match keys** (tax id, bank account, email) — never low-cardinality
   fields. Keys via envelope encryption; KEK in client KMS/HSM. Keys/secrets never in
   the DB, source, logs or config files.
8. **Audit is hash-chained** and append-only; every security-relevant action logged.
9. **Idempotency**: every job handler is idempotent and checkpointed so partial
   failures replay without duplicate target creation.

## Stack (locked — see ADRs)
React+TS (MUI) · FastAPI/Python · PostgreSQL (control) · Parquet (Bronze) · DuckDB
(analytics/transform) · PostgreSQL durable jobs (not Temporal) · Docker Compose
(not K8s) · vLLM/Ollama behind an AI gateway (model chosen per client).

## Do NOT build yet
SAP/PeopleSoft/JDE/NetSuite adapters · Spark · Temporal · Kubernetes · advanced AI
copilot · autonomous/runtime AI · large object catalog · multi-client SaaS · DRM /
licence tamper-resistance · active HA (unless recovery test fails) · complex scheduling.

## Phase order
Phase 0 foundation (this skeleton) → Phase 1 one object end-to-end + MVP AI +
instrumentation → Phase 2 hardening → Phase 3 scale → Phase 4 AI intelligence →
Phase 5 expansion. Every phase must ship a usable increment.

## Conventions
- Python: type hints, small auditable modules; `pytest` for logic (crypto has tests).
- API is control-plane only; long-running work goes through the `job` table + workers.
- New architectural decisions → a new file in `docs/adr/` before coding.
