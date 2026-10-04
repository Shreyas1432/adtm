"""Slice 1: encrypted-Bronze extraction + hash-chained audit."""
import pyarrow.parquet as pq

from security import crypto, audit
from security.rowcrypt import encrypt_rows
from dataplane import extract as dpx


def test_rows_to_table_unions_columns():
    t = dpx.rows_to_table([{"a": 1}, {"a": 2, "b": "x"}])
    assert set(t.column_names) == {"a", "b"}
    assert t.num_rows == 2


def test_encrypt_rows_aead_and_blind_index():
    dek = crypto.generate_dek()
    rows = [{"vendor_name": "Acme", "tax_id": "IE123", "status": "A"}]
    choices = {"vendor_name": "aead", "tax_id": "aead_blind_index", "status": "none"}
    enc = encrypt_rows(rows, choices, dek)[0]
    assert enc["status"] == "A"                              # untouched
    assert enc["vendor_name"] != "Acme"                      # encrypted
    assert crypto.decrypt_field(enc["vendor_name"], dek, aad=b"vendor_name") == "Acme"
    assert enc["tax_id_bidx"] == crypto.blind_index("IE123", "tax_id")  # match key indexed


def test_extract_to_bronze_writes_parquet(tmp_path, monkeypatch):
    monkeypatch.setattr("dataplane.bronze.DATA_ROOT", str(tmp_path))
    rows = [{"vendor_id": 1, "vendor_name": "Acme"}, {"vendor_id": 2, "vendor_name": "Globex"}]
    m = dpx.extract_to_bronze(rows, workspace_id="ws1", dataset_name="suppliers")
    assert m["row_count"] == 2 and m["file_sha256"]
    assert pq.read_table(m["file_path"]).num_rows == 2


def test_audit_chain_append_and_verify():
    rows = audit.append([
        {"action": "extract", "object_ref": "suppliers", "details": {"rows": 2}},
        {"action": "dq", "object_ref": "suppliers"},
    ])
    assert audit.verify(rows) is True
    rows[0]["details"] = {"rows": 999}          # tamper
    assert audit.verify(rows) is False
