"""Auth + single-workspace context (ADR-0011): unit tests on `authenticate`
and HTTP-layer tests proving the guard and workspace scoping apply to routes."""
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "api"))

from fastapi.testclient import TestClient  # noqa: E402

from app.auth import AuthError, Principal, authenticate  # noqa: E402
from app.db import get_session  # noqa: E402
from app.main import app  # noqa: E402
from tests.support import FakeSession  # noqa: E402

TOKEN = "s3cr3t-deploy-token"
WS = "00000000-0000-0000-0000-000000000001"


@pytest.fixture(autouse=True)
def _auth_env(monkeypatch):
    monkeypatch.setenv("ADTM_API_TOKEN", TOKEN)
    monkeypatch.setenv("ADTM_WORKSPACE_ID", WS)


# ---- pure authenticate() ----

def test_authenticate_valid_returns_workspace_bound_principal():
    p = authenticate(f"Bearer {TOKEN}")
    assert p == Principal(workspace_id=WS, subject="api-token")


@pytest.mark.parametrize("header", [None, "", "Bearer", "Bearer ", "Basic xyz", TOKEN, "Bearer a b"])
def test_authenticate_rejects_missing_or_malformed(header):
    with pytest.raises(AuthError):
        authenticate(header)


def test_authenticate_rejects_wrong_token():
    with pytest.raises(AuthError):
        authenticate("Bearer not-the-token")


def test_authenticate_fails_closed_when_unconfigured(monkeypatch):
    monkeypatch.delenv("ADTM_API_TOKEN", raising=False)
    with pytest.raises(AuthError):
        authenticate(f"Bearer {TOKEN}")


def test_authenticate_fails_closed_without_workspace(monkeypatch):
    monkeypatch.delenv("ADTM_WORKSPACE_ID", raising=False)
    with pytest.raises(AuthError):
        authenticate(f"Bearer {TOKEN}")


# ---- HTTP wiring ----

def _client(session):
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_health_is_open_no_token():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200  # db degraded (no psycopg) is fine; route is open


@pytest.mark.parametrize("path", ["/workspaces", "/projects", "/jobs"])
def test_protected_routes_401_without_token(path):
    client = _client(FakeSession())
    r = client.get(path)
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate") == "Bearer"


def test_protected_route_401_with_bad_token():
    client = _client(FakeSession())
    r = client.get("/projects", headers={"Authorization": "Bearer wrong"})
    assert r.status_code == 401


def test_projects_scopes_query_to_workspace():
    session = FakeSession([{"id": "p1", "workspace_id": WS, "name": "demo"}])
    client = _client(session)
    r = client.get("/projects", headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 200
    assert r.json() == [{"id": "p1", "workspace_id": WS, "name": "demo"}]
    sql, params = session.calls[-1]
    assert params == {"ws": WS} and "workspace_id=:ws" in sql


def test_jobs_scoped_by_workspace_join():
    session = FakeSession([])
    client = _client(session)
    r = client.get("/jobs", headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 200
    sql, params = session.calls[-1]
    assert params == {"ws": WS} and "p.workspace_id=:ws" in sql


def test_connection_lookup_is_workspace_scoped():
    # No matching connection -> 404, and the lookup is bound to the workspace.
    session = FakeSession([])
    client = _client(session)
    cid = "11111111-1111-1111-1111-111111111111"
    r = client.get(f"/connections/{cid}/tables", headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 404
    sql, params = session.calls[-1]
    assert params["ws"] == WS and params["id"] == cid and "workspace_id=:ws" in sql
