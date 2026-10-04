"""Data quality: evaluate rules over a Bronze dataset -> dq_result.

Thin wiring: read the Bronze Parquet and run dataplane.dq. Idempotent — a rerun
over the same immutable Bronze yields the same results.
"""
import pyarrow.parquet as pq

from dataplane.dq import evaluate


def run(job_id, version_id, payload: dict, checkpoint: dict) -> None:
    rows = pq.read_table(payload["bronze_path"]).to_pylist()
    evaluate(rows, payload.get("rules", []))
