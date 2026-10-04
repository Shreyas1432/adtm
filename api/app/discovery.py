"""Schema discovery + design-time encryption-choice suggestions (Phase 1, step 2).

Control-plane only: returns source METADATA (tables, columns) via the source
adapter — bulk rows never flow here (invariant #6); extraction to Bronze is a
worker job.

Encryption suggestions follow ADR-0006: a keyed blind index is suggested ONLY for
high-cardinality match keys; other sensitive fields get AEAD without a blind
index; the rest get none. These are design-time *suggestions* — a human approves
them into the versioned config (ADR-0005).
"""
from __future__ import annotations

AEAD_BLIND = "aead_blind_index"  # AES-256-GCM + HMAC blind index (equality/dedupe)
AEAD = "aead"                    # AES-256-GCM only
NONE = "none"

# High-cardinality match keys -> AEAD + blind index.
_MATCH_KEYS = (
    "tax_id", "taxid", "vat", "iban", "bank_account", "account_number",
    "email", "duns", "external_ref", "ssn", "pps",
)
# Sensitive but not match keys -> AEAD only (never blind-indexed).
_SENSITIVE = ("name", "address", "addr", "phone", "contact", "dob", "birth")


def suggest_encryption(column: dict) -> str:
    n = (column.get("name") or "").lower()
    if any(k in n for k in _MATCH_KEYS):
        return AEAD_BLIND
    if any(k in n for k in _SENSITIVE):
        return AEAD
    return NONE


def discover_columns(adapter, table: str) -> list[dict]:
    cols = adapter.column_metadata(table)
    for c in cols:
        c["encryption"] = suggest_encryption(c)
    return cols


def build_ebs_adapter(connection: dict):
    from adapters.source_ebs import EbsSourceAdapter

    return EbsSourceAdapter(connection["secret_ref"], connection.get("config") or {})
