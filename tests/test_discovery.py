"""Tests for schema discovery + encryption-choice suggestions (pure logic, no DB)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "api"))

from app.discovery import (
    suggest_encryption, discover_columns, is_valid_identifier,
    MAX_IDENTIFIER_LEN, AEAD_BLIND, AEAD, NONE,
)


def test_is_valid_identifier_accepts_oracle_names():
    for name in ["AP_SUPPLIERS", "x", "V$SESSION", "col_1", "a" * MAX_IDENTIFIER_LEN]:
        assert is_valid_identifier(name)


def test_is_valid_identifier_rejects_bad_names():
    for name in ["", "1abc", "ap suppliers", "drop;table", "a" * (MAX_IDENTIFIER_LEN + 1),
                 "tbl-name", "tbl'); --", "tbl\n"]:
        assert not is_valid_identifier(name)


def test_suggest_high_cardinality_match_keys_get_blind_index():
    for name in ["TAX_ID", "bank_account", "EMAIL", "iban", "vendor_vat_number"]:
        assert suggest_encryption({"name": name}) == AEAD_BLIND


def test_suggest_sensitive_non_key_gets_aead_only():
    for name in ["VENDOR_NAME", "address_line1", "contact_phone"]:
        assert suggest_encryption({"name": name}) == AEAD


def test_suggest_low_cardinality_never_encrypted_or_blind_indexed():
    for name in ["STATUS", "COUNTRY_CODE", "account_type", "LAST_UPDATE_DATE"]:
        assert suggest_encryption({"name": name}) == NONE


class _StubAdapter:
    def column_metadata(self, table):
        return [
            {"name": "VENDOR_ID", "type": "NUMBER", "pk": True},
            {"name": "VENDOR_NAME", "type": "VARCHAR2"},
            {"name": "TAX_ID", "type": "VARCHAR2"},
            {"name": "STATUS", "type": "VARCHAR2"},
        ]


def test_discover_columns_enriches_with_encryption():
    cols = {c["name"]: c for c in discover_columns(_StubAdapter(), "ap_suppliers")}
    assert cols["VENDOR_NAME"]["encryption"] == AEAD
    assert cols["TAX_ID"]["encryption"] == AEAD_BLIND
    assert cols["STATUS"]["encryption"] == NONE
