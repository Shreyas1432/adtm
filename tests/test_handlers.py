"""Worker handler wiring (Phase 1 engines): dq/mapping/simulate/reconcile over
tmp Parquet, no DB. Confirms the thin job handlers call the right engines."""
import sys
import pathlib

import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "workers"))

from handlers import dq, mapping, reconcile, simulate  # noqa: E402


def _bronze(tmp_path):
    path = str(tmp_path / "bronze.parquet")
    pq.write_table(pa.table({"VENDOR_NAME": ["Acme", "Globex"], "TAX_ID": ["IE1", "IE2"]}), path)
    return path


def test_mapping_handler_writes_transformed_gold(tmp_path):
    gold = str(tmp_path / "gold.parquet")
    mapping.run("j", "v", {
        "bronze_path": _bronze(tmp_path),
        "mappings": [{"source_field": "VENDOR_NAME", "target_field": "SupplierName"}],
        "gold_path": gold,
    }, {})
    rows = pq.read_table(gold).to_pylist()
    assert rows == [{"SupplierName": "Acme"}, {"SupplierName": "Globex"}]


def test_dq_handler_runs_over_bronze(tmp_path):
    dq.run("j", "v", {
        "bronze_path": _bronze(tmp_path),
        "rules": [{"type": "null", "params": {"column": "TAX_ID"}}],
    }, {})  # thin wiring: must not raise


def test_simulate_handler_runs_over_gold(tmp_path):
    simulate.run("j", "v", {"gold_path": _bronze(tmp_path), "required": ["VENDOR_NAME"]}, {})


def test_reconcile_handler_runs():
    reconcile.run("j", "v", {"source_keys": ["a", "b"], "actual_keys": ["a", "b"]}, {})
