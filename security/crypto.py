"""
ADTM field-level encryption (ADR-0006, ADR-0007).

- Confidentiality: AES-256-GCM (AEAD, randomized nonce) for sensitive values.
- Equality matching / dedupe: keyed HMAC-SHA256 blind index, HIGH-CARDINALITY
  match keys ONLY (tax id, bank account, email, external ref). Never apply a
  blind index to low-cardinality fields (status, country) - it leaks frequency.
- Envelope encryption: per-domain Data Encryption Key (DEK) wrapped by a
  Key-Encryption Key (KEK). In production the KEK lives in the client KMS/HSM
  and DEKs are unwrapped on demand; here a dev KEK comes from the environment.

This module is deliberately small and dependency-light so it can be audited.
"""
from __future__ import annotations
import base64, hmac, hashlib, os
from dataclasses import dataclass
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_VERSION = "v1"  # stamp stored per encrypted object (bronze_manifest.key_version)

def _b64d(s: str) -> bytes:
    return base64.b64decode(s)

def _dev_kek() -> bytes:
    raw = _b64d(os.environ.get("ADTM_KEK_DEV", ""))
    if len(raw) != 32:
        raise RuntimeError("ADTM_KEK_DEV must be 32 bytes base64 (dev only; use KMS in prod)")
    return raw

def _blind_key() -> bytes:
    raw = _b64d(os.environ.get("ADTM_BLIND_INDEX_KEY_DEV", ""))
    if len(raw) != 32:
        raise RuntimeError("ADTM_BLIND_INDEX_KEY_DEV must be 32 bytes base64 (dev only)")
    return raw

# --- Envelope: wrap/unwrap a per-domain DEK with the KEK ---
def generate_dek() -> bytes:
    return AESGCM.generate_key(bit_length=256)

def wrap_dek(dek: bytes, kek: bytes | None = None) -> str:
    kek = kek or _dev_kek()
    nonce = os.urandom(12)
    ct = AESGCM(kek).encrypt(nonce, dek, b"adtm-dek")
    return base64.b64encode(nonce + ct).decode()

def unwrap_dek(wrapped: str, kek: bytes | None = None) -> bytes:
    kek = kek or _dev_kek()
    blob = _b64d(wrapped); nonce, ct = blob[:12], blob[12:]
    return AESGCM(kek).decrypt(nonce, ct, b"adtm-dek")

# --- Field encryption with a DEK (randomized AEAD) ---
def encrypt_field(plaintext: str, dek: bytes, aad: bytes = b"") -> str:
    nonce = os.urandom(12)
    ct = AESGCM(dek).encrypt(nonce, plaintext.encode("utf-8"), aad)
    return base64.b64encode(nonce + ct).decode()

def decrypt_field(ciphertext: str, dek: bytes, aad: bytes = b"") -> str:
    blob = _b64d(ciphertext); nonce, ct = blob[:12], blob[12:]
    return AESGCM(dek).decrypt(nonce, ct, aad).decode("utf-8")

# --- Blind index for equality matching (HIGH-CARDINALITY KEYS ONLY) ---
def blind_index(value: str, domain: str) -> str:
    """Deterministic, keyed, salted-by-domain. Enables JOIN/dedupe on encrypted
    high-cardinality values without storing plaintext or deterministic ciphertext."""
    norm = value.strip().lower().encode("utf-8")
    mac = hmac.new(_blind_key(), domain.encode() + b"|" + norm, hashlib.sha256)
    return mac.hexdigest()

@dataclass
class EncryptedCell:
    ciphertext: str
    blind_index: str | None
    key_version: str = KEY_VERSION
