# ADR-0012: Worker retry/backoff + dead-letter

**Status:** Accepted

## Context
Phase-0 workers marked a failed job `failed` and stopped — no retry of transient
failures, and no honouring of `job.max_attempts` (ADR-0004). Handlers are already
idempotent + checkpointed (invariant #9), so safe retry is possible.

## Decision
On handler failure the worker consults a pure policy keyed on the (already
incremented) `attempt` and the job's `max_attempts`: while `attempt < max_attempts`
the job is requeued `pending` with a capped exponential backoff (via a new
`available_at` gate the claim query respects); on the final attempt it moves to
the terminal `dead` state (dead-letter). All worker logging is structured JSON
and passes through secret redaction, so no credential is ever printed (invariant
#7). Error text is persisted to `job.error`; logs carry only the exception type.

## Consequences
Transient failures self-heal without duplicate target creation (idempotency);
poison jobs land in `dead` for inspection instead of looping. `available_at` and
`dead` are additive; the claim index is rebuilt to match. No new infrastructure
(still Postgres durable jobs, not Temporal).
