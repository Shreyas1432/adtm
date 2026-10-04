# ADR-0004: PostgreSQL durable jobs, not Temporal (MVP)

**Status:** Accepted

## Context
Temporal carries operational weight (its own store, workers, versioning) that conflicts with the appliance / ops-light posture that motivated DuckDB-over-Spark.

## Decision
Implement job/status/retry/dependency/checkpoint/idempotency as a Postgres job table with idempotent workers claiming via FOR UPDATE SKIP LOCKED. Abstract the execution interface.

## Consequences
Introduce Temporal only on benchmarked need; swappable without changing workflow semantics.
