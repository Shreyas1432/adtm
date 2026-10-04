"""Mapping/transform: apply approved mappings over a Bronze dataset -> Gold Parquet.

Thin wiring around dataplane.transform. Only approved, versioned mappings are
executed (ADR-0005); deterministic, so a version rerun reproduces the Gold set.
"""
import pyarrow as pa
import pyarrow.parquet as pq

from dataplane.transform import apply_mappings


def run(job_id, version_id, payload: dict, checkpoint: dict) -> None:
    rows = pq.read_table(payload["bronze_path"]).to_pylist()
    gold = apply_mappings(rows, payload["mappings"], payload.get("xrefs"))
    pq.write_table(pa.Table.from_pylist(gold), payload["gold_path"], compression="zstd")
