"""Mapping/transform engine — apply approved source->target mappings to produce
the Gold dataset.

Mapping kinds: one_to_one | static | xref | lookup. Pure: mappings are the
human-approved, versioned config (ADR-0005); xref/lookup tables are passed in.
(one_to_many is deferred — not needed for the Suppliers MVP.)
"""
from __future__ import annotations

_OPS = {"upper": str.upper, "lower": str.lower, "trim": str.strip}


def _op(name, v):
    if v is None or not name:
        return v
    fn = _OPS.get(name)
    return fn(str(v)) if fn else v


def _value(m, row, xrefs):
    kind = m.get("kind", "one_to_one")
    tr = m.get("transform", {})
    if kind == "static":
        return tr.get("value")
    src = row.get(m.get("source_field"))
    if kind in ("xref", "lookup"):
        table = xrefs.get(tr.get("xref") or m.get("source_field"), {})
        return table.get(src, tr.get("default"))
    return _op(tr.get("op"), src)


def apply_mappings(rows, mappings, xrefs: dict | None = None) -> list[dict]:
    xrefs = xrefs or {}
    return [{m["target_field"]: _value(m, row, xrefs) for m in mappings} for row in rows]
