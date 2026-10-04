"""Oracle EBS source adapter (read-only). STUB - Phase 1.
Validate python-oracledb thin/thick mode + Instant Client per EBS version at pilot.
"""
from .base import SourceAdapter

class EbsSourceAdapter:  # implements SourceAdapter
    def __init__(self, secret_ref: str, config: dict):
        self.secret_ref = secret_ref; self.config = config
    def test_connection(self) -> bool:
        raise NotImplementedError("Phase 1: connect via python-oracledb (read-only account)")
    def list_tables(self): raise NotImplementedError
    def column_metadata(self, table): raise NotImplementedError
    def extract(self, sql): raise NotImplementedError
