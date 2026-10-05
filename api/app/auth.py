"""Thin API authentication + single-workspace request context (ADR-0011).

Every control-plane route (except /health) requires a bearer token that matches
`ADTM_API_TOKEN`, compared in constant time. Each authenticated request carries a
`Principal` bound to the appliance's single workspace (`ADTM_WORKSPACE_ID`).

The token and workspace id are injected from the client's secrets manager at
deploy time and are never stored or logged (invariant #7). The guard fails closed:
an unset token rejects all requests.
"""
from __future__ import annotations

import hmac
import os
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException


@dataclass(frozen=True)
class Principal:
    workspace_id: str
    subject: str


class AuthError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


def _parse_bearer(authorization: str | None) -> str:
    if not authorization:
        raise AuthError("missing bearer token")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise AuthError("malformed Authorization header; expected 'Bearer <token>'")
    return parts[1].strip()


def authenticate(authorization: str | None) -> Principal:
    """Validate the Authorization header and return the bound Principal.

    Fails closed: raises AuthError if the token is unset, missing, or wrong.
    """
    expected = os.environ.get("ADTM_API_TOKEN", "")
    workspace_id = os.environ.get("ADTM_WORKSPACE_ID", "")
    if not expected or not workspace_id:
        raise AuthError("API auth is not configured")
    token = _parse_bearer(authorization)
    if not hmac.compare_digest(token, expected):
        raise AuthError("invalid token")
    return Principal(workspace_id=workspace_id, subject="api-token")


def require_principal(authorization: str | None = Header(default=None)) -> Principal:
    try:
        return authenticate(authorization)
    except AuthError as e:
        raise HTTPException(401, e.detail, headers={"WWW-Authenticate": "Bearer"})


# Dependency alias for routes that also need the principal value.
CurrentPrincipal = Depends(require_principal)
