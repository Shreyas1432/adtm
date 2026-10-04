"""Slice 4: local Fusion target (partial success, idempotent replay, read-back)
and the reconciliation engine."""
from adapters.fusion_local import LocalFusionTarget
from dataplane.reconcile import reconcile


def test_partial_success_and_readback():
    t = LocalFusionTarget(key_field="SupplierName", required=["SupplierName", "TaxId"])
    recs = [
        {"SupplierName": "Acme", "TaxId": "IE1"},
        {"SupplierName": "Globex", "TaxId": None},   # invalid -> rejected
    ]
    res = t.submit(recs, "idem-1")
    assert res["accepted"] == 1 and res["rejected"] == 1
    assert t.errors(res["job_id"])[0]["record"]["SupplierName"] == "Globex"
    assert list(t.read_back("suppliers", ["Acme", "Globex"])) == [{"SupplierName": "Acme", "TaxId": "IE1"}]


def test_idempotent_submit_no_duplicate():
    t = LocalFusionTarget(key_field="SupplierName")
    recs = [{"SupplierName": "Acme"}]
    a = t.submit(recs, "idem-1")
    b = t.submit(recs, "idem-1")   # same key -> same result, no re-store
    assert a == b and len(t.store) == 1


def test_replay_failed_then_reconcile():
    t = LocalFusionTarget(key_field="SupplierName", required=["SupplierName", "TaxId"])
    source = [{"SupplierName": "Acme", "TaxId": "IE1"}, {"SupplierName": "Globex", "TaxId": None}]
    t.submit(source, "idem-1")
    # fix + replay the failed one
    t.replay_failed("job-idem-1", [{"SupplierName": "Globex", "TaxId": "IE2"}], "idem-2")
    source_keys = [r["SupplierName"] for r in source]
    actual = [r["SupplierName"] for r in t.read_back("suppliers", source_keys)]
    rec = reconcile(source_keys, actual)
    assert rec["status"] == "reconciled" and rec["loaded_count"] == 2 and rec["unmatched_count"] == 0


def test_reconcile_detects_missing():
    rec = reconcile(["A", "B", "C"], ["A", "B"], failed=1)
    assert rec["status"] == "partial" and rec["missing_keys"] == ["C"] and rec["failed_count"] == 1
