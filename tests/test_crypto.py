import os, base64
os.environ.setdefault("ADTM_KEK_DEV", base64.b64encode(os.urandom(32)).decode())
os.environ.setdefault("ADTM_BLIND_INDEX_KEY_DEV", base64.b64encode(os.urandom(32)).decode())
from security import crypto

def test_envelope_roundtrip():
    dek = crypto.generate_dek()
    wrapped = crypto.wrap_dek(dek)
    assert crypto.unwrap_dek(wrapped) == dek

def test_field_roundtrip():
    dek = crypto.generate_dek()
    ct = crypto.encrypt_field("IE29ABANK12345", dek, aad=b"bank_account")
    assert ct != "IE29ABANK12345"
    assert crypto.decrypt_field(ct, dek, aad=b"bank_account") == "IE29ABANK12345"

def test_blind_index_matches_equal_values():
    a = crypto.blind_index("Acme Ltd", "supplier_name")
    b = crypto.blind_index("  acme ltd ", "supplier_name")
    c = crypto.blind_index("Other Ltd", "supplier_name")
    assert a == b and a != c

def test_randomized_ciphertext_differs():
    dek = crypto.generate_dek()
    assert crypto.encrypt_field("x", dek) != crypto.encrypt_field("x", dek)
