# ADR-0001: Control-plane / data-plane separation

**Status:** Accepted

## Context
A single Postgres was proposed as the universal substrate. Heavy EBS transformation at cutover concurrency would contend with transactional control functions.

## Decision
Separate control plane (Postgres: metadata, workflow, audit) from data plane (Parquet + DuckDB: Bronze, transforms) as distinct logical tiers from day one.

## Consequences
Prevents coupling of control state to heavy workloads; enables swapping the processing engine without touching workflow semantics.
