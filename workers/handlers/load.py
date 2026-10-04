"""Fusion load: submit the Gold dataset via the Load Adapter.

Thin wiring. Uses job.idempotency_key so a retry/replay never double-creates in
the target; partial success + failed-subset replay are handled by the adapter.
The real FusionLoadAdapter is wired at pilot; dev/E2E uses adapters.fusion_local.
"""
import pyarrow.parquet as pq

from adapters.fusion_load import FusionLoadAdapter


def run(job_id, version_id, payload: dict, checkpoint: dict) -> None:
    gold = pq.read_table(payload["gold_path"]).to_pylist()
    FusionLoadAdapter().submit(gold, payload["idempotency_key"])
