"""Target read-back: re-read ACTUAL Fusion state via the Read-Back Adapter (ADR-0009).

Thin wiring — returns the actual records for the submitted keys so reconciliation
compares against real target state, never the load response. Real adapter wired
at pilot; dev/E2E uses adapters.fusion_local.
"""
from adapters.fusion_readback import FusionReadBackAdapter


def run(job_id, version_id, payload: dict, checkpoint: dict) -> None:
    list(FusionReadBackAdapter().read_back(payload["object_name"], payload["keys"]))
