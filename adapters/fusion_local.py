"""Local Fusion target for dev/test/E2E — NOT the pilot adapter.

Implements both TargetLoadAdapter and TargetReadBackAdapter (kept distinct per
ADR-0009) against an in-memory store, so load -> read-back -> reconcile runs
offline. Models async completion, partial success, idempotent replay, and
read-back of ACTUAL target state. The real FusionLoad/ReadBack adapters stay
pilot stubs; swap them in at pilot.
"""
from __future__ import annotations

from typing import Iterable


class LocalFusionTarget:
    def __init__(self, key_field: str = "key", required: list[str] | None = None):
        self.key_field = key_field
        self.required = required or [key_field]
        self.store: dict[str, dict] = {}        # actual target state
        self._submitted: dict[str, dict] = {}   # idempotency_key -> result
        self._errors: dict[str, list] = {}      # job_id -> errors

    # --- TargetLoadAdapter ---
    def validate(self, payload) -> dict:
        ok, bad = [], []
        for rec in payload:
            missing = [c for c in self.required if not rec.get(c)]
            if missing:
                bad.append({"record": rec, "missing": missing})
            else:
                ok.append(rec)
        return {"valid": ok, "invalid": bad}

    def submit(self, payload, idempotency_key) -> dict:
        if idempotency_key in self._submitted:
            return self._submitted[idempotency_key]            # idempotent replay
        v = self.validate(payload)
        job_id = f"job-{idempotency_key}"
        for rec in v["valid"]:
            self.store[str(rec[self.key_field])] = rec         # upsert actual state
        self._errors[job_id] = [
            {"record": b["record"], "error": f"missing {b['missing']}"} for b in v["invalid"]
        ]
        res = {
            "job_id": job_id, "file_id": f"file-{idempotency_key}",
            "accepted": len(v["valid"]), "rejected": len(v["invalid"]),
        }
        self._submitted[idempotency_key] = res
        return res

    def poll(self, job_id) -> dict:
        return {"job_id": job_id, "status": "completed"}

    def errors(self, job_id) -> list[dict]:
        return self._errors.get(job_id, [])

    def replay_failed(self, job_id, failed_subset, idempotency_key) -> dict:
        return self.submit(failed_subset, idempotency_key)

    # --- TargetReadBackAdapter (re-reads ACTUAL state) ---
    def read_back(self, object_name, keys) -> Iterable[dict]:
        for k in keys:
            if str(k) in self.store:
                yield self.store[str(k)]

    def coverage(self) -> dict:
        return {"found": len(self.store)}
