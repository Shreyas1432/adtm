"""Simulation: predict target load failures before submission.

Built after real load errors are known (per backlog). Reuses the DQ engine to
flag Gold rows missing fields the target requires — no separate rules engine.
"""
import pyarrow.parquet as pq

from dataplane.dq import evaluate


def run(job_id, version_id, payload: dict, checkpoint: dict) -> None:
    gold = pq.read_table(payload["gold_path"]).to_pylist()
    rules = [{"type": "null", "params": {"column": c}} for c in payload["required"]]
    evaluate(gold, rules)  # failed rows == predicted rejects
