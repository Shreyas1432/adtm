"""Envelope key recovery (ADR-0007): a KEK rotation/restore never renders
immutable Bronze unrecoverable, because only the DEK's wrapping changes."""
import os

import pytest
from cryptography.exceptions import InvalidTag

from security import crypto


def _kek():
    return os.urandom(32)


def test_data_still_decrypts_after_kek_rotation():
    kek_v1, kek_v2 = _kek(), _kek()
    dek = crypto.generate_dek()
    ciphertext = crypto.encrypt_field("IE1234567T", dek, aad=b"TAX_ID")  # written to Bronze
    wrapped = crypto.wrap_dek(dek, kek_v1)

    # Rotate the KEK: re-wrap the DEK, leave the Bronze ciphertext untouched.
    rewrapped = crypto.rewrap_dek(wrapped, kek_v1, kek_v2)

    dek_after = crypto.unwrap_dek(rewrapped, kek_v2)
    assert dek_after == dek
    assert crypto.decrypt_field(ciphertext, dek_after, aad=b"TAX_ID") == "IE1234567T"


def test_rewrap_keeps_dek_identity():
    kek_v1, kek_v2 = _kek(), _kek()
    dek = crypto.generate_dek()
    rewrapped = crypto.rewrap_dek(crypto.wrap_dek(dek, kek_v1), kek_v1, kek_v2)
    assert crypto.unwrap_dek(rewrapped, kek_v2) == dek


def test_restore_old_kek_still_unwraps_original_blob():
    # Escrow/break-glass: the original wrapped blob recovers once KEK_v1 is restored.
    kek_v1 = _kek()
    dek = crypto.generate_dek()
    wrapped = crypto.wrap_dek(dek, kek_v1)
    restored_kek_v1 = kek_v1  # restored from escrow after loss
    assert crypto.unwrap_dek(wrapped, restored_kek_v1) == dek


def test_data_from_before_and_after_rotation_share_one_dek():
    kek_v1, kek_v2 = _kek(), _kek()
    dek = crypto.generate_dek()
    before = crypto.encrypt_field("before", dek, aad=b"c")
    rewrapped = crypto.rewrap_dek(crypto.wrap_dek(dek, kek_v1), kek_v1, kek_v2)
    dek2 = crypto.unwrap_dek(rewrapped, kek_v2)
    after = crypto.encrypt_field("after", dek2, aad=b"c")
    assert crypto.decrypt_field(before, dek2, aad=b"c") == "before"
    assert crypto.decrypt_field(after, dek2, aad=b"c") == "after"


def test_unwrap_with_wrong_kek_fails():
    dek = crypto.generate_dek()
    wrapped = crypto.wrap_dek(dek, _kek())
    with pytest.raises(InvalidTag):
        crypto.unwrap_dek(wrapped, _kek())  # a different KEK cannot unwrap


def test_tampered_wrapped_blob_fails_integrity():
    import base64
    kek = _kek()
    wrapped = crypto.wrap_dek(crypto.generate_dek(), kek)
    blob = bytearray(base64.b64decode(wrapped))
    blob[-1] ^= 0x01  # flip a ciphertext bit
    with pytest.raises(InvalidTag):
        crypto.unwrap_dek(base64.b64encode(bytes(blob)).decode(), kek)


def test_rewrap_with_wrong_old_kek_fails():
    kek_v1, kek_v2 = _kek(), _kek()
    wrapped = crypto.wrap_dek(crypto.generate_dek(), kek_v1)
    with pytest.raises(InvalidTag):
        crypto.rewrap_dek(wrapped, _kek(), kek_v2)  # wrong old KEK -> cannot unwrap
