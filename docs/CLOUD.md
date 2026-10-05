# Running ADTM Phase 2 in a Claude Code cloud session

This prepares the repo so **Phase 2 (hardening)** can be driven by a Claude Code
**cloud session** (billed to your cloud credits). The ADTM product itself stays a
sovereign, client-deployed appliance — this is about running the *development
work* in the cloud, not hosting the appliance there.

## Prerequisites (ready)
- Repo on GitHub: `Shreyas1432/adtm` ✅
- CI: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs the test suite on every push/PR ✅
- One-command bootstrap: [`scripts/setup.sh`](../scripts/setup.sh) ✅

## Environment setup command
Point the cloud environment's setup at:
```bash
bash scripts/setup.sh
```
It creates `.venv`, installs [`requirements-dev.txt`](../requirements-dev.txt), and runs `pytest -q`.
(Tests inject fakes for Oracle/Fusion, so no database or ERP is needed in the cloud env.)

## How to launch (desktop app)
1. Open this project, then start a **cloud session** on the `adtm` repo (New session → run on cloud),
   or move the current session to cloud.
2. Use the environment setup command above so the session boots green.
3. Give it the Phase 2 brief below.

## Phase 2 brief (hardening) — status
Build order: smallest, highest-leverage safety first. Minimum code, test each slice.
- [x] **Thin auth + single-workspace context** on every API request (ADR-0011).
- [x] **Input validation** on the discovery endpoints (UUID + bounded Oracle identifier; 422 on bad/oversized input).
- [x] **Worker resilience**: retry/backoff honoring `job.max_attempts`, dead-letter on exhaustion, redacted structured logging (ADR-0012).
- [x] **Key-recovery test** (ADR-0007): envelope DEK unwrap proven across KEK rotation/restore.
- [x] **Audit persistence + chain-verification endpoint** (`GET /audit/verify`) over a real run.
- [x] **Secret-handling hardening**: no secret/key in errors, logs, process objects, or `/health`.
- [x] **Coverage gate** in CI (`--cov-fail-under=88`; suite at ~90%).

## Guardrails for the cloud session (do not violate)
- All ADTM invariants in [`CLAUDE.md`](../CLAUDE.md) still apply: source read-only,
  Bronze immutable, **AI design-time only (no runtime model)**, control≠data plane,
  reconciliation re-reads actual state, keys via KMS, audit hash-chained.
- ruflo / any AI tooling is **dev-time only** — never wired into ADTM's runtime.
- New architectural decision → a new ADR in [`docs/adr/`](adr/) before coding.
- Keep changes minimal; a new ADR or test accompanies behavioural changes.
