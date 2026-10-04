"""Apply per-column encryption choices to source rows before Bronze write
(ADR-0003/0006).

- 'aead'              -> AES-256-GCM ciphertext replaces the value.
- 'aead_blind_index' -> AEAD + a '<col>_bidx' HMAC for equality/dedupe on the
                        encrypted (high-cardinality) value.
- 'none'             -> left as-is.

Pure: the DEK is passed in (unwrapped from the client KMS upstream, never stored).
"""
from __future__ import annotations

from . import crypto


def encrypt_rows(rows, choices: dict[str, str], dek: bytes) -> list[dict]:
    out = []
    for row in rows:
        r = dict(row)
        for col, choice in (choices or {}).items():
            if choice == "none" or r.get(col) is None:
                continue
            val = str(r[col])
            if choice in ("aead", "aead_blind_index"):
                r[col] = crypto.encrypt_field(val, dek, aad=col.encode())
            if choice == "aead_blind_index":
                r[f"{col}_bidx"] = crypto.blind_index(val, col)
        out.append(r)
    return out
