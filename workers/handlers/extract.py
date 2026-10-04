"""Extraction: run versioned SQL against EBS (read-only) -> immutable Bronze (Parquet).
STUB - Phase 1. Must be idempotent and checkpoint progress for safe replay."""
def run(job_id, version_id, payload: dict, checkpoint: dict) -> None:
    raise NotImplementedError("Phase 1: implement extract handler")
