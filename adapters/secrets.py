"""Secret resolution for adapters.

Invariant #7: keys/secrets never live in the DB, source, logs or config files.
A `connection.secret_ref` is only a *handle*; the real credential is fetched at
call time from the client's secrets manager and never persisted or logged.

Phase 0/1 ships a dev resolver that reads the handle from an environment
variable (the same pattern the crypto module uses for dev key material). In
production, inject a resolver backed by the client KMS/Vault/secrets manager.
"""
from __future__ import annotations
import json
import os
from typing import Callable

# A resolver maps a secret handle -> a credential dict (e.g. {"user", "password"}).
SecretResolver = Callable[[str], dict]


def dev_env_resolver(secret_ref: str) -> dict:
    """DEV ONLY. Resolve a handle from an env var holding a JSON credential.

    e.g. export EBS_SUPPLIERS_RO='{"user":"adtm_ro","password":"..."}'
         secret_ref = "EBS_SUPPLIERS_RO"

    Production must replace this with a client-secrets-manager-backed resolver;
    credentials are never stored in the control-plane DB or any config file.
    """
    raw = os.environ.get(secret_ref)
    if not raw:
        raise RuntimeError(
            f"secret_ref {secret_ref!r} is not resolvable in the dev environment. "
            "Set the env var to a JSON credential, or inject a production "
            "secret_resolver backed by the client secrets manager."
        )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"secret_ref {secret_ref!r} must contain JSON: {e}") from None
    if not isinstance(data, dict) or "user" not in data or "password" not in data:
        raise RuntimeError("resolved secret must be a JSON object with 'user' and 'password'")
    return data
