"""Extraction: run versioned read-only SQL against EBS -> immutable Bronze.

Idempotent via job.idempotency_key + Bronze being write-once. Thin wiring around
dataplane.extract; field encryption uses a DEK unwrapped from the client KMS
(wired at pilot — see adapters/secrets.py), so Phase-1 dev runs leave it unset.
"""
from adapters.source_ebs import EbsSourceAdapter
from dataplane.extract import extract_to_bronze


def run(job_id, version_id, payload: dict, checkpoint: dict) -> None:
    adapter = EbsSourceAdapter(payload["secret_ref"], payload.get("config") or {})
    rows = adapter.extract(payload["sql"])
    extract_to_bronze(
        rows,
        workspace_id=payload["workspace_id"],
        dataset_name=payload["dataset_name"],
        choices=payload.get("encryption"),
        version_id=version_id,
        key_version=payload.get("key_version"),
    )
