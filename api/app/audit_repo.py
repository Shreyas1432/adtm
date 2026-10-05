"""Persistence for the hash-chained audit log (ADR-0008).

Thin repository over `audit_log`: continue the chain from the last stored hash,
append new entries (stamped by the pure `security.audit`), and read a workspace's
chain back for verification. Details are stored as JSONB.
"""
from __future__ import annotations

import json

from sqlalchemy import text

from security import audit


def last_hash(s, workspace_id: str) -> str:
    h = s.execute(text(
        "SELECT hash FROM audit_log WHERE workspace_id=:ws ORDER BY id DESC LIMIT 1"
    ), {"ws": workspace_id}).scalar()
    return h or audit.GENESIS


def persist(s, workspace_id: str, actor, entries: list[dict]) -> list[dict]:
    """Stamp entries onto the workspace's chain and insert them. Returns stamped rows."""
    stamped = audit.append(entries, last_hash(s, workspace_id))
    for r in stamped:
        s.execute(text(
            "INSERT INTO audit_log (workspace_id, actor, action, object_ref, details, prev_hash, hash) "
            "VALUES (:ws, :actor, :action, :object_ref, CAST(:details AS JSONB), :prev_hash, :hash)"
        ), {"ws": workspace_id, "actor": actor, "action": r["action"],
            "object_ref": r.get("object_ref"), "details": json.dumps(r.get("details", {})),
            "prev_hash": r["prev_hash"], "hash": r["hash"]})
    s.commit()
    return stamped


def load_chain(s, workspace_id: str) -> list[dict]:
    rows = s.execute(text(
        "SELECT action, object_ref, details, prev_hash, hash FROM audit_log "
        "WHERE workspace_id=:ws ORDER BY id"
    ), {"ws": workspace_id}).mappings().all()
    return [dict(r) for r in rows]
