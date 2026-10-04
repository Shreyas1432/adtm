"""Hash-chained, tamper-evident audit (ADR-0008).

Pure helpers; the control plane persists the stamped rows into
audit_log(prev_hash, hash). Each row's hash covers the previous hash + a
canonical encoding of the action, so any edit/removal breaks the chain.
"""
from __future__ import annotations

import hashlib
import json

GENESIS = "0" * 64


def _canon(action: str, object_ref, details: dict) -> str:
    return json.dumps(
        {"action": action, "object_ref": object_ref, "details": details or {}},
        sort_keys=True,
        separators=(",", ":"),
    )


def chain_hash(prev_hash: str, action: str, object_ref, details: dict) -> str:
    return hashlib.sha256((prev_hash + "|" + _canon(action, object_ref, details)).encode()).hexdigest()


def append(entries: list[dict], prev_hash: str = GENESIS) -> list[dict]:
    """Stamp entries ({action, object_ref?, details?}) with prev_hash + hash."""
    out = []
    for e in entries:
        h = chain_hash(prev_hash, e["action"], e.get("object_ref"), e.get("details", {}))
        out.append({**e, "prev_hash": prev_hash, "hash": h})
        prev_hash = h
    return out


def verify(rows: list[dict], prev_hash: str = GENESIS) -> bool:
    for r in rows:
        if r.get("prev_hash") != prev_hash:
            return False
        if chain_hash(prev_hash, r["action"], r.get("object_ref"), r.get("details", {})) != r["hash"]:
            return False
        prev_hash = r["hash"]
    return True
