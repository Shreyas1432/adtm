"""Data-quality engine (ADR-0002). Evaluated in-memory over Bronze rows.

Rule types: null | datatype | length | duplicate | ri | date | business.
Each rule = {"type", "params"}; returns {type, column, passed, failed, sample}
for persistence into dq_result. Packaged with profiling as the standalone
readiness diagnostic.
"""
from __future__ import annotations

import datetime as dt

_OPS = {
    "gt": lambda a, b: a > b, "ge": lambda a, b: a >= b,
    "lt": lambda a, b: a < b, "le": lambda a, b: a <= b,
    "eq": lambda a, b: a == b, "ne": lambda a, b: a != b,
}


def _is_number(v):
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def _is_int(v):
    try:
        int(str(v))
        return True
    except (TypeError, ValueError):
        return False


def _is_date(v, fmt=None):
    try:
        dt.datetime.strptime(str(v), fmt) if fmt else dt.date.fromisoformat(str(v))
        return True
    except (TypeError, ValueError):
        return False


def _failing(t, p, col, rows):
    for r in rows:
        v = r.get(col) if col else None
        if t == "null":
            bad = v is None or v == ""
        elif t == "datatype":
            check = {"int": _is_int, "number": _is_number, "date": _is_date}.get(p.get("datatype"), lambda x: True)
            bad = v is not None and not check(v)
        elif t == "length":
            bad = v is not None and len(str(v)) > int(p["max"])
        elif t == "date":
            bad = v is not None and not _is_date(v, p.get("format"))
        elif t == "ri":
            bad = v is not None and v not in set(p.get("reference", []))
        elif t == "business":
            op = _OPS.get(p.get("op", ""))
            try:
                bad = op is not None and not op(v, p.get("value"))
            except TypeError:
                bad = True
        else:
            bad = False
        if bad:
            yield r


def _check(rule, rows):
    t, p = rule["type"], rule.get("params", {})
    col = p.get("column")
    if t == "duplicate":
        cols = p.get("columns") or ([col] if col else [])
        groups: dict = {}
        for r in rows:
            groups.setdefault(tuple(r.get(c) for c in cols), []).append(r)
        bad = [r for g in groups.values() if len(g) > 1 for r in g]
    else:
        bad = list(_failing(t, p, col, rows))
    return {"type": t, "column": col, "passed": len(rows) - len(bad), "failed": len(bad), "sample": bad[:5]}


def evaluate(rows, rules) -> list[dict]:
    rows = list(rows)
    return [_check(rule, rows) for rule in rules]
