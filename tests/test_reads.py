"""Read-side queries + endpoints (raw rows, workspace-scoped)."""
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "api"))

from fastapi.testclient import TestClient  # noqa: E402

from app import reads  # noqa: E402
from app.db import get_session  # noqa: E402
from app.main import app  # noqa: E402
from tests.support import FakeSession  # noqa: E402

TOKEN = "t"
WS = "00000000-0000-0000-0000-000000000001"
ROWS = [
    {"id": "d1", "run_id": "r1", "rule_type": "null", "params": {"column": "TAX_ID"},
     "passed": 1281, "failed": 3, "sample": [None, None, None], "created_at": "t1"},
    {"id": "d2", "run_id": "r1", "rule_type": "ri", "params": {"column": "COUNTRY_CODE"},
     "passed": 1283, "failed": 1, "sample": ["ZZ"], "created_at": "t2"},
]


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("ADTM_API_TOKEN", TOKEN)
    monkeypatch.setenv("ADTM_WORKSPACE_ID", WS)


def teardown_function():
    app.dependency_overrides.clear()


def test_dq_results_scopes_to_workspace_and_run():
    s = FakeSession(ROWS)
    out = reads.dq_results(s, WS, run_id="r1", limit=50)
    assert out == ROWS
    sql, params = s.calls[-1]
    assert params["ws"] == WS and params["run_id"] == "r1" and params["lim"] == 50
    assert "p.workspace_id = :ws" in sql and "JOIN dq_rule" in sql


def test_dq_results_without_run_omits_filter():
    s = FakeSession([])
    reads.dq_results(s, WS)
    sql, params = s.calls[-1]
    assert "run_id" not in params and "r.run_id = :run_id" not in sql


def test_dq_results_endpoint_returns_rows():
    s = FakeSession(ROWS)
    app.dependency_overrides[get_session] = lambda: s
    r = TestClient(app).get("/dq/results?run_id=r1", headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 200
    body = r.json()
    assert [row["rule_type"] for row in body] == ["null", "ri"]


def test_dq_results_endpoint_requires_auth():
    app.dependency_overrides[get_session] = lambda: FakeSession([])
    assert TestClient(app).get("/dq/results").status_code == 401
