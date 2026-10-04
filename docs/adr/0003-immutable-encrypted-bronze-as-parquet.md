# ADR-0003: Immutable encrypted Bronze as Parquet

**Status:** Accepted

## Context
Keeping Bronze + Silver + Gold + retained versions as live relational tables multiplies storage and causes bloat/backup pressure.

## Decision
Bronze is write-once, compressed, columnar Parquet on client-controlled storage, with sha256 + manifest metadata; Postgres stores manifests only.

## Consequences
Cheap immutability, replayability and audit-defensibility; new extraction => new dataset/version.
