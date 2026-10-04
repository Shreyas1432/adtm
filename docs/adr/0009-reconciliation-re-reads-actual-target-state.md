# ADR-0009: Reconciliation re-reads actual target state

**Status:** Accepted

## Context
Trusting the load response misses target-side defaults, transformations and silent rejections. Read-back is a different integration from load.

## Decision
A first-class Target Read-Back Adapter (BICC/BI Publisher/REST/permitted views) re-reads actual Fusion state; reconciliation compares source/expected vs actual and reports coverage.

## Consequences
Credible, auditable sign-off; read-back cost/latency benchmarked within the reconciliation window.
