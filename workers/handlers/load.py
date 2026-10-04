"""Fusion load: submit via Load Adapter; capture file/job ids; partial-failure replay.
STUB - Phase 1. Must be idempotent and checkpoint progress for safe replay."""
def run(job_id, version_id, payload: dict, checkpoint: dict) -> None:
    raise NotImplementedError("Phase 1: implement load handler")
