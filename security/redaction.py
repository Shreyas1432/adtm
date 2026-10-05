"""Secret redaction for logs/diagnostics (invariant #7: keys/secrets never in logs).

`redact` masks values whose key hints at a credential, recursively. Over-masking
is intentional: a log line should never carry a secret, even at the cost of a
masked-but-harmless field.
"""
from __future__ import annotations

REDACTED = "***REDACTED***"

# Substrings that mark a key as secret-bearing. Kept specific so routine keys
# (idempotency_key, key_version) are not masked, while credentials always are.
_SECRET_HINTS = (
    "password", "passwd", "pwd", "secret", "token", "credential",
    "api_key", "apikey", "access_key", "private_key", "kek", "dek", "authorization",
)


def is_secret_key(key) -> bool:
    k = str(key).lower()
    return any(h in k for h in _SECRET_HINTS)


def redact(obj):
    """Return a copy of obj with secret-keyed values masked (dicts/lists recursed)."""
    if isinstance(obj, dict):
        return {k: (REDACTED if is_secret_key(k) else redact(v)) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [redact(v) for v in obj]
    return obj
