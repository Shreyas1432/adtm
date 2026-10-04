"""Phase 1 E2E (Suppliers): extract -> encrypted Bronze -> DQ -> mapping -> load
-> read-back -> reconcile -> hash-chained audit, fully offline."""
import pyarrow.parquet as pq

from security import crypto, audit
from dataplane.extract import extract_to_bronze
from dataplane.dq import evaluate
from dataplane.transform import apply_mappings
from dataplane.reconcile import reconcile
from adapters.fusion_local import LocalFusionTarget


def test_suppliers_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr("dataplane.bronze.DATA_ROOT", str(tmp_path))

    # 1) Extract from source -> encrypted, immutable Bronze
    source = [
        {"VENDOR_NAME": "Acme", "TAX_ID": "IE1", "COUNTRY": "IE"},
        {"VENDOR_NAME": "Globex", "TAX_ID": "IE2", "COUNTRY": "US"},
    ]
    dek = crypto.generate_dek()
    choices = {"TAX_ID": "aead_blind_index", "VENDOR_NAME": "aead"}
    manifest = extract_to_bronze(source, workspace_id="ws1", dataset_name="suppliers",
                                 choices=choices, dek=dek)
    bronze = pq.read_table(manifest["file_path"]).to_pylist()
    assert manifest["row_count"] == 2
    assert bronze[0]["VENDOR_NAME"] != "Acme"          # encrypted at rest
    assert bronze[0]["TAX_ID_bidx"]                    # blind index for match key

    # 2) Data quality on Bronze (plaintext structural col)
    assert evaluate(bronze, [{"type": "null", "params": {"column": "COUNTRY"}}])[0]["failed"] == 0

    # 3) Mapping -> Gold (plaintext decrypted inside the boundary; source used here)
    mappings = [
        {"source_field": "VENDOR_NAME", "target_field": "SupplierName"},
        {"source_field": "TAX_ID", "target_field": "TaxId"},
        {"source_field": "COUNTRY", "target_field": "Country", "kind": "xref",
         "transform": {"xref": "country", "default": "??"}},
    ]
    gold = apply_mappings(source, mappings, {"country": {"IE": "IRL", "US": "USA"}})

    # 4) Load -> 5) read-back ACTUAL state -> 6) reconcile
    target = LocalFusionTarget(key_field="SupplierName", required=["SupplierName", "TaxId"])
    res = target.submit(gold, "run-1")
    assert res["accepted"] == 2 and res["rejected"] == 0
    src_keys = [g["SupplierName"] for g in gold]
    actual = [r["SupplierName"] for r in target.read_back("suppliers", src_keys)]
    rec = reconcile(src_keys, actual)
    assert rec["status"] == "reconciled" and rec["loaded_count"] == 2

    # 7) Hash-chained audit over the run
    chain = audit.append([
        {"action": "extract", "object_ref": "suppliers", "details": {"rows": manifest["row_count"]}},
        {"action": "load", "object_ref": "suppliers", "details": {"accepted": res["accepted"]}},
        {"action": "reconcile", "object_ref": "suppliers", "details": {"status": rec["status"]}},
    ])
    assert audit.verify(chain)
