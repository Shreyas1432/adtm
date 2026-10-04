"""Slice 5: MVP AI suggesters (metadata-only, deterministic, instrumented)."""
from ai_gateway.local import suggest_mappings, suggest_dq_rules

COLS = [
    {"name": "VENDOR_ID", "type": "NUMBER", "pk": True},
    {"name": "VENDOR_NAME", "type": "VARCHAR2"},
    {"name": "CREATION_DATE", "type": "DATE"},
]


def test_mapping_suggestion_pascalcases_and_flags_pk_confidence():
    s = suggest_mappings(COLS)
    items = {i["source_field"]: i for i in s["suggestion"]}
    assert items["VENDOR_ID"]["target_field"] == "VendorId"
    assert items["VENDOR_ID"]["confidence"] > items["VENDOR_NAME"]["confidence"]
    assert "t_generated_ms" in s and s["context_fields"] == [c["name"] for c in COLS]


def test_dq_suggestion_covers_pk_number_date():
    rules = suggest_dq_rules(COLS)["suggestion"]
    kinds = {(r["type"], r["params"].get("column") or tuple(r["params"].get("columns", []))) for r in rules}
    assert ("null", "VENDOR_ID") in kinds
    assert ("duplicate", ("VENDOR_ID",)) in kinds
    assert ("datatype", "VENDOR_ID") in kinds
    assert ("date", "CREATION_DATE") in kinds


def test_context_is_metadata_only_no_values():
    # suggesters receive column metadata, never row values
    s = suggest_mappings(COLS)
    assert all(isinstance(f, str) for f in s["context_fields"])
