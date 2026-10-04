"""Slice 3: mapping/transform engine."""
from dataplane.transform import apply_mappings

ROWS = [{"VENDOR_NAME": " acme ", "COUNTRY": "IE", "SEGMENT": "A"}]


def test_one_to_one_with_op():
    out = apply_mappings(ROWS, [
        {"source_field": "VENDOR_NAME", "target_field": "SupplierName", "transform": {"op": "trim"}},
    ])[0]
    assert out["SupplierName"] == "acme"


def test_static():
    out = apply_mappings(ROWS, [
        {"target_field": "Source", "kind": "static", "transform": {"value": "EBS"}},
    ])[0]
    assert out["Source"] == "EBS"


def test_xref_and_default():
    mappings = [
        {"source_field": "COUNTRY", "target_field": "CountryCode", "kind": "xref",
         "transform": {"xref": "country"}},
        {"source_field": "SEGMENT", "target_field": "Seg", "kind": "lookup",
         "transform": {"xref": "seg", "default": "UNKNOWN"}},
    ]
    xrefs = {"country": {"IE": "IRL"}, "seg": {}}
    out = apply_mappings(ROWS, mappings, xrefs)[0]
    assert out["CountryCode"] == "IRL"
    assert out["Seg"] == "UNKNOWN"
