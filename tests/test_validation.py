"""Input validation on the discovery endpoints (ADR-0011 hardening): malformed
connection ids and illegal/oversized table names are rejected with 422 before
any handler logic runs."""
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "api"))

from fastapi.testclient import TestClient  # noqa: E402

from app.db import get_session  # noqa: E402
from app.main import app  # noqa: E402
from tests.support import FakeSession  # noqa: E402

TOKEN = "s3cr3t-deploy-token"
WS = "00000000-0000-0000-0000-000000000001"
CID = "11111111-1111-1111-1111-111111111111"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("ADTM_API_TOKEN", TOKEN)
    monkeypatch.setenv("ADTM_WORKSPACE_ID", WS)


def _client(rows=None):
    session = FakeSession(rows)
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app), session


def teardown_function():
    app.dependency_overrides.clear()


@pytest.mark.parametrize("bad", ["abc", "123", "not-a-uuid", "11111111-1111-1111-1111"])
def test_bad_connection_uuid_rejected(bad):
    client, _ = _client()
    r = client.get(f"/connections/{bad}/tables", headers=AUTH)
    assert r.status_code == 422


@pytest.mark.parametrize("table", ["bad name", "1leading", "tbl-dash", "a" * 129, "drop;table", "tbl'); --"])
def test_illegal_or_oversized_table_rejected(table):
    client, session = _client()
    r = client.get(f"/connections/{CID}/tables/{table}/columns", headers=AUTH)
    assert r.status_code == 422
    assert session.calls == []  # rejected before any DB lookup


def test_valid_inputs_pass_validation_and_reach_lookup():
    # Valid UUID + valid identifier -> validation passes; empty session -> 404
    # (connection not found), proving the request reached the handler.
    client, _ = _client(rows=[])
    r = client.get(f"/connections/{CID}/tables/AP_SUPPLIERS/columns", headers=AUTH)
    assert r.status_code == 404


def test_validation_runs_even_without_auth_is_still_401():
    # Auth guard precedes handler; a bad token still yields 401, not 422.
    client, _ = _client()
    r = client.get(f"/connections/{CID}/tables/AP_SUPPLIERS/columns")
    assert r.status_code == 401
