# ADTM — AI Agents Guide

> How AI is used in ADTM, the guardrails it operates under, and how AI *coding*
> agents (e.g. Claude Code) should work on this repository. Bound by **ADR-0005**
> (AI is design-time assistance only) and [`CLAUDE.md`](../CLAUDE.md).
> **Last updated:** 2026-10-04.

---

## Part A — AI inside the ADTM product

### A1. The one rule: AI is design-time assistance only (ADR-0005)
AI never runs on the execution path. The lifecycle is always:

```
AI suggestion  →  human approval  →  versioned config  →  deterministic execution
```

A version rerun **must reproduce results with no model available**. If a feature
seems to need a model at runtime, it is wrong — redesign it so the model only
produces design-time suggestions that a human freezes into config.

### A2. Sovereignty & privacy guardrails
- **Local only.** The model runs inside the client boundary (vLLM/Ollama behind
  the gateway). No ERP data is sent to any external/cloud AI service.
- **Metadata, not raw PII (invariant #4).** Default model context = schema, column
  descriptions, profiles, and **masked/synthetic** samples. Raw PII requires an
  explicit, separately audited path — not the default.
- **Disabled by default.** `ADTM_AI_ENABLED=false` in [`.env.example`](../.env.example);
  the gateway raises if called while disabled. Enable per client after model review.
- Every suggestion records *what the model saw* (`Suggestion.context_fields`) so the
  no-raw-PII guarantee is auditable.

### A3. The AI gateway
[`ai_gateway/gateway.py`](../ai_gateway/gateway.py) is a **model-agnostic** interface.

- `AIGateway.suggest(kind, context) -> Suggestion`
- Guard: raises `RuntimeError` unless `ADTM_AI_ENABLED=true`.
- `Suggestion` fields: `kind`, `suggestion` (dict), `confidence`, `model_ref`,
  `t_generated_ms`, `context_fields` (no raw PII).
- Config: `ADTM_AI_BASE_URL` (e.g. local `http://ai-runtime:11434`), `ADTM_AI_ENABLED`.
- The `ai-runtime` service is a commented-out, per-client-supplied local model in
  [`docker-compose.yml`](../docker-compose.yml).

### A4. Suggestion kinds (the "agents")
Each kind is a bounded, reviewable design-time assistant. Persisted to the
`ai_suggestion` table ([`db/migrations/0001_init.sql`](../db/migrations/0001_init.sql)).

| `kind` | Assists with | Human approves into |
|---|---|---|
| `table` | which source tables/columns to extract | extraction scope |
| `sql` | drafting/explaining extraction SQL | `extraction.sql_text` (versioned) |
| `mapping` | source→target field mappings & transforms | `mapping` rows (`approved_by/at`) |
| `dq_rule` | candidate data-quality rules | `dq_rule` rows |
| `error_explanation` | explaining Fusion load errors / DQ failures | operator understanding (no auto-fix) |

### A5. Approval & versioning
- No suggestion takes effect until a human **approves** it (`ai_suggestion.decision`
  = approved/rejected/edited; mappings also stamp `mapping.approved_by/at`).
- Approved output is frozen into a `workflow_version.config` snapshot. Execution
  reads the frozen version — never the model.

### A6. Instrumentation (Gate 2 evidence)
Every suggestion is timed so we can prove effort reduction vs a manual baseline:
- `t_generated_ms` — model time to produce the suggestion.
- `t_review_ms` — human time to review/accept/edit.
- `decision` — approved / rejected / edited → **acceptance & correction rate**.

These feed the Gate 2 metric (T_AI vs T_manual). See [PRD §7](PRD.md#7-success-metrics-gate-mapped).

### A7. Explicitly NOT building (per `CLAUDE.md`)
Autonomous/runtime AI · an advanced AI copilot · any agent that writes to a source
ERP or mutates Bronze · any path that sends ERP data to an external model. Advanced
AI intelligence is **Phase 4**, still within the design-time-only rule.

### A8. Implementation checklist (Phase 1)
- [ ] Implement `AIGateway.suggest` to call the local model via `base_url` with a
      **metadata-only** context builder (schema/descriptions/profiles/masked samples).
- [ ] Populate `Suggestion.context_fields` with exactly what was sent.
- [ ] Persist every suggestion to `ai_suggestion` with timings + `model_ref`.
- [ ] Gate every suggestion behind an explicit approval UI (see [Design System](DESIGN_SYSTEM.md)).
- [ ] Verify a version rerun reproduces results with the model **disabled**.

---

## Part B — AI coding agents working on this repo

> For Claude Code / any AI contributor. The authoritative rules are in
> [`CLAUDE.md`](../CLAUDE.md); this is operational guidance.

### B1. Before you change anything
1. Read [`CLAUDE.md`](../CLAUDE.md) (non-negotiable invariants) and the relevant
   ADR(s) in [`docs/adr/`](adr/).
2. A change that would alter a locked decision requires a **new ADR first** — do
   not just change code.

### B2. Guardrails that block common mistakes
- **Never** add a write path to a source ERP (invariant #1).
- **Never** overwrite/mutate Bronze — new extraction = new dataset/version (invariant #2).
- **Never** call a model on an execution path (invariant #3 / ADR-0005).
- **Never** put bulk data through the ORM, or control state into Parquet (invariant #6).
- **Never** put keys/secrets in the DB, source, logs, or config files; dev keys come
  from env, prod keys from the client KMS/HSM (invariant #7).
- **Never** apply a blind index to low-cardinality fields — high-cardinality match
  keys only (ADR-0006).
- Keep job handlers **idempotent and checkpointed** (invariant #9).

### B3. Conventions
- Python ≥3.11, type hints, small auditable modules; `pytest` for logic
  (crypto is tested in [`tests/test_crypto.py`](../tests/test_crypto.py)).
- API is control-plane only; long-running work goes through the `job` table + workers.
- Respect the Phase order — don't build deferred items (SAP/Spark/Temporal/K8s/etc.).

### B4. Local workflow
```bash
cp .env.example .env
docker compose up --build        # postgres + api + worker + frontend
pip install -r api/requirements.txt pytest && pytest tests/   # run crypto tests
```

### B5. Plugins & local agent config (not committed)
Claude Code marketplaces/plugins and any local agent settings are developer-local
and **git-ignored** (`.claude/`, `*.local.json` in [`.gitignore`](../.gitignore)) —
they are never pushed to GitHub. Install them per developer; do not commit them.
