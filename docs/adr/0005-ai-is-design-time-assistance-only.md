# ADR-0005: AI is design-time assistance only

**Status:** Accepted

## Context
The determinism claim must be structural and auditable, and sensitive data must not leak to models.

## Decision
No runtime model invocation. AI returns suggestions -> human approval -> versioned config -> deterministic execution. Default AI context is metadata/profiles/masked samples, never raw PII. All suggestions instrumented (T_AI vs T_manual).

## Consequences
Reruns are model-independent; security reviewers can confirm no model is in the execution path; Gate 2 has measurement data.
