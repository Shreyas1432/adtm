"""Slice 2: DQ engine — one case per rule type."""
from dataplane.dq import evaluate

ROWS = [
    {"vendor_id": 1, "vendor_name": "Acme", "tax_id": "IE1", "country": "IE", "created": "2020-01-01"},
    {"vendor_id": 2, "vendor_name": "", "tax_id": "IE1", "country": "ZZ", "created": "nope"},
    {"vendor_id": "x", "vendor_name": "Globex", "tax_id": "IE3", "country": "US", "created": "2021-05-05"},
]


def _r(results, i):
    return results[i]


def test_null_rule():
    assert evaluate(ROWS, [{"type": "null", "params": {"column": "vendor_name"}}])[0]["failed"] == 1


def test_datatype_rule_int():
    assert evaluate(ROWS, [{"type": "datatype", "params": {"column": "vendor_id", "datatype": "int"}}])[0]["failed"] == 1


def test_length_rule():
    assert evaluate(ROWS, [{"type": "length", "params": {"column": "country", "max": 2}}])[0]["failed"] == 0
    assert evaluate(ROWS, [{"type": "length", "params": {"column": "vendor_name", "max": 5}}])[0]["failed"] == 1  # "Globex" (6)


def test_duplicate_rule():
    res = evaluate(ROWS, [{"type": "duplicate", "params": {"columns": ["tax_id"]}}])[0]
    assert res["failed"] == 2  # the two IE1 rows


def test_ri_rule():
    res = evaluate(ROWS, [{"type": "ri", "params": {"column": "country", "reference": ["IE", "US"]}}])[0]
    assert res["failed"] == 1  # ZZ


def test_date_rule():
    assert evaluate(ROWS, [{"type": "date", "params": {"column": "created"}}])[0]["failed"] == 1  # "nope"


def test_business_rule():
    res = evaluate(ROWS, [{"type": "business", "params": {"column": "vendor_id", "op": "gt", "value": 0}}])[0]
    assert res["failed"] == 1  # vendor_id "x" not > 0


def test_sample_capped():
    res = evaluate(ROWS, [{"type": "null", "params": {"column": "nonexistent"}}])[0]
    assert res["failed"] == 3 and len(res["sample"]) <= 5
