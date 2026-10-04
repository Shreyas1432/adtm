# ADR-0008: Hash-chained tamper-evident audit

**Status:** Accepted

## Context
Audit-grade sign-off requires tamper evidence, not an append-only UI convention a DBA can bypass.

## Decision
Each audit record stores the prior record's hash and is hashed over canonical content + prior hash; periodic anchoring and independent verification (verification tooling in Phase 2).

## Consequences
Tampering is detectable; reconciliation evidence is defensible to CFO/audit.
