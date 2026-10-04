# ADR-0007: Envelope encryption + tested key recovery

**Status:** Accepted

## Context
An immutable encrypted Bronze store is only as durable as the ability to recover its keys.

## Decision
Per-domain DEKs wrapped by a client KMS/HSM KEK; key-version stamped per object; rotation without re-encrypting history; break-glass/escrow defined and restore-tested before production ingest.

## Consequences
Key loss does not render immutable Bronze unrecoverable; rotation is a lifecycle op, not a prerequisite.
