"""Data quality: null/datatype/length/duplicate/RI/date/business rules -> dq_result.
STUB - Phase 1. Must be idempotent and checkpoint progress for safe replay."""
def run(job_id, version_id, payload: dict, checkpoint: dict) -> None:
    raise NotImplementedError("Phase 1: implement dq handler")
