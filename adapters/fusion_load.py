"""Oracle Fusion LOAD adapter. STUB - Phase 1.
Validate FBDI/ESS/import mechanism per object at pilot. Must treat async +
partial success as normal and support failed-subset replay with idempotency.
"""
class FusionLoadAdapter:  # implements TargetLoadAdapter
    def validate(self, payload): raise NotImplementedError
    def submit(self, payload, idempotency_key): raise NotImplementedError
    def poll(self, job_id): raise NotImplementedError
    def errors(self, job_id): raise NotImplementedError
    def replay_failed(self, job_id, failed_subset, idempotency_key): raise NotImplementedError
