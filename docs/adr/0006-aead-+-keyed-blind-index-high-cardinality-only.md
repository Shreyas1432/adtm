# ADR-0006: AEAD + keyed blind index (high-cardinality only)

**Status:** Accepted

## Context
Migration must match/dedupe on the very PII it protects. Deterministic ciphertext leaks equality; blind indexes on low-cardinality fields leak frequency.

## Decision
Randomized AES-256-GCM for confidentiality; keyed HMAC blind index for equality matching, restricted to high-cardinality match keys. Low-cardinality fields are AEAD-only.

## Consequences
Operational matching/dedup without exposing equality through ciphertext; frequency leakage avoided.
