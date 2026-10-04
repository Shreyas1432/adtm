# ADR-0010: Appliance packaging via Docker Compose

**Status:** Accepted

## Context
Client-deployed, often air-gapped installs need repeatable, offline-capable packaging without cluster ops.

## Decision
Ship a signed, versioned Compose bundle (images + migrations + install verifier). Kubernetes only when a client's platform/scale requires it.

## Consequences
Predictable cost-to-serve; Compose for MVP, K8s is a later, justified option.
