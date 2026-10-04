"""Local, deterministic, metadata-only suggesters — the MVP AI (ADR-0005).

No network and no model required: suggestions come from column *metadata* only
(never raw PII), are design-time and must be human-approved into versioned config,
and are instrumented (t_generated_ms) so Gate 2 can compare against manual effort.
A hosted model can replace these behind the same gateway later.
"""
from __future__ import annotations

import re
import time


def _pascal(name: str) -> str:
    return "".join(p.capitalize() for p in re.split(r"[_\s]+", name.lower()) if p)


def suggest_mappings(columns: list[dict]) -> dict:
    t0 = time.monotonic()
    items = [
        {
            "source_field": c["name"],
            "target_field": _pascal(c["name"]),
            "kind": "one_to_one",
            "confidence": 0.8 if c.get("pk") else 0.6,
        }
        for c in columns
    ]
    return {
        "kind": "mapping",
        "suggestion": items,
        "t_generated_ms": int((time.monotonic() - t0) * 1000),
        "context_fields": [c["name"] for c in columns],
    }


def suggest_dq_rules(columns: list[dict]) -> dict:
    t0 = time.monotonic()
    rules: list[dict] = []
    for c in columns:
        name, ctype = c["name"], (c.get("type") or "").upper()
        if c.get("pk"):
            rules.append({"type": "null", "params": {"column": name}})
            rules.append({"type": "duplicate", "params": {"columns": [name]}})
        if ctype.startswith("NUMBER"):
            rules.append({"type": "datatype", "params": {"column": name, "datatype": "number"}})
        if "DATE" in ctype:
            rules.append({"type": "date", "params": {"column": name}})
    return {
        "kind": "dq_rule",
        "suggestion": rules,
        "t_generated_ms": int((time.monotonic() - t0) * 1000),
        "context_fields": [c["name"] for c in columns],
    }
