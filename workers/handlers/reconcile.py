"""Reconciliation: compare source/expected vs actual read-back; write evidence.

Thin wiring around dataplane.reconcile (ADR-0009). Counts + control totals +
status form the reconciliation evidence artifact.
"""
from dataplane.reconcile import reconcile


def run(job_id, version_id, payload: dict, checkpoint: dict) -> None:
    reconcile(
        payload["source_keys"],
        payload["actual_keys"],
        failed=payload.get("failed", 0),
        control_totals=payload.get("control_totals"),
    )
