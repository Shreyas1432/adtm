"""Reconciliation (ADR-0009). Compares the source/expected set against the
ACTUAL target state read back from Fusion — never infers success from the load
response. Pure.
"""
from __future__ import annotations


def reconcile(source_keys, actual_keys, *, failed: int = 0, control_totals: dict | None = None) -> dict:
    src = set(map(str, source_keys))
    actual = set(map(str, actual_keys))
    loaded = src & actual
    missing = src - actual
    unexpected = actual - src
    if not missing and not unexpected and failed == 0:
        status = "reconciled"
    elif loaded:
        status = "partial"
    else:
        status = "failed"
    return {
        "source_count": len(src),
        "actual_count": len(actual),
        "loaded_count": len(loaded),
        "failed_count": failed,
        "unmatched_count": len(missing) + len(unexpected),
        "missing_keys": sorted(missing)[:50],
        "unexpected_keys": sorted(unexpected)[:50],
        "control_totals": control_totals or {},
        "status": status,
    }
