# ADR-0002: DuckDB as default engine; Spark deferred

**Status:** Accepted

## Context
Migration object sizes are bounded and the product is client-deployed, often air-gapped. Spark adds cluster/worker/scheduler operational weight.

## Decision
Use DuckDB over Parquet for analytical/transform workloads. Introduce Spark only when a benchmark proves DuckDB cannot meet throughput/memory/concurrency targets.

## Consequences
Minimal operational surface for an appliance; distributed processing added only on evidence, not by default.
