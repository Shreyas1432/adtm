"""Audit persistence + chain verification (ADR-0008): a real run is stamped onto
the workspace chain, persisted, and verified; tampering breaks verification."""
import sys
import pathlib
import json

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "api"))

from fastapi.testclient import TestClient  # noqa: E402

from app import audit_repo  # noqa: E402
from app.db import get_session  # noqa: E402
from app.main import app  # noqa: E402
from security import audit  # noqa: E402

WS = "ws-1"
RUN = [
    {"action": "extract", "object_ref": "suppliers", "details": {"rows": 2}},
    {"action": "load", "object_ref": "suppliers", "details": {"accepted": 2}},
    {"action": "reconcile", "object_ref": "suppliers", "details": {"status": "reconciled"}},
]


class _Res:
    def __init__(self, scalar=None, rows=None):
        self._scalar, self._rows = scalar, rows or []

    def scalar(self):
        return self._scalar

    def mappings(self):
        return self

    def all(self):
        return self._rows


class InMemoryAuditSession:
    """Stores inserted audit rows and serves last_hash / load_chain from them."""

    def __init__(self):
        self.rows = []
        self.commits = 0

    def execute(self, stmt, params=None):
        sql, params = str(stmt), params or {}
        ws = [r for r in self.rows if r["workspace_id"] == params.get("ws")]
        if sql.startswith("SELECT hash"):
            return _Res(scalar=ws[-1]["hash"] if ws else None)
        if sql.startswith("INSERT INTO audit_log"):
            self.rows.append({
                "id": len(self.rows) + 1, "workspace_id": params["ws"],
                "actor": params["actor"], "action": params["action"],
                "object_ref": params["object_ref"], "details": json.loads(params["details"]),
                "prev_hash": params["prev_hash"], "hash": params["hash"],
            })
            return _Res()
        if sql.startswith("SELECT action"):
            keys = ("action", "object_ref", "details", "prev_hash", "hash")
            return _Res(rows=[{k: r[k] for k in keys} for r in ws])
        if sql.startswith("SELECT id,"):
            lim = params.get("lim", 50)
            recent = sorted(ws, key=lambda r: r["id"], reverse=True)[:lim]
            keys = ("id", "action", "object_ref", "actor", "hash")
            return _Res(rows=[{**{k: r[k] for k in keys}, "created_at": f"t{r['id']}"} for r in recent])
        return _Res()

    def commit(self):
        self.commits += 1

    def close(self):
        pass


def test_persist_then_verify_round_trip():
    s = InMemoryAuditSession()
    stamped = audit_repo.persist(s, WS, actor="dev", entries=RUN)
    assert len(stamped) == 3 and s.commits == 1
    assert stamped[0]["prev_hash"] == audit.GENESIS
    assert audit.verify(audit_repo.load_chain(s, WS)) is True


def test_second_persist_continues_the_chain():
    s = InMemoryAuditSession()
    audit_repo.persist(s, WS, "dev", RUN[:1])
    audit_repo.persist(s, WS, "dev", RUN[1:])  # continues from the stored last hash
    chain = audit_repo.load_chain(s, WS)
    assert len(chain) == 3 and audit.verify(chain) is True


def test_tampered_detail_breaks_the_chain():
    s = InMemoryAuditSession()
    audit_repo.persist(s, WS, "dev", RUN)
    s.rows[1]["details"]["accepted"] = 999  # tamper a persisted row
    assert audit.verify(audit_repo.load_chain(s, WS)) is False


def test_deleting_a_row_breaks_the_chain():
    s = InMemoryAuditSession()
    audit_repo.persist(s, WS, "dev", RUN)
    del s.rows[1]  # drop a link
    assert audit.verify(audit_repo.load_chain(s, WS)) is False


def test_workspace_isolation_of_chain():
    s = InMemoryAuditSession()
    audit_repo.persist(s, "ws-a", "dev", RUN[:1])
    audit_repo.persist(s, "ws-b", "dev", RUN[:1])
    assert audit.verify(audit_repo.load_chain(s, "ws-a")) is True
    assert len(audit_repo.load_chain(s, "ws-b")) == 1


def test_list_entries_newest_first_and_limited():
    s = InMemoryAuditSession()
    audit_repo.persist(s, WS, "dev", RUN)  # 3 entries
    entries = audit_repo.list_entries(s, WS, limit=2)
    assert [e["action"] for e in entries] == ["reconcile", "load"]  # newest first
    assert all({"id", "action", "object_ref", "actor", "hash", "created_at"} <= e.keys() for e in entries)


# ---- endpoint ----

TOKEN = "t"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("ADTM_API_TOKEN", TOKEN)
    monkeypatch.setenv("ADTM_WORKSPACE_ID", WS)


def teardown_function():
    app.dependency_overrides.clear()


def test_verify_endpoint_ok_on_valid_chain():
    s = InMemoryAuditSession()
    audit_repo.persist(s, WS, "dev", RUN)
    app.dependency_overrides[get_session] = lambda: s
    r = TestClient(app).get("/audit/verify", headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 200 and r.json() == {"ok": True, "count": 3}


def test_verify_endpoint_flags_tamper():
    s = InMemoryAuditSession()
    audit_repo.persist(s, WS, "dev", RUN)
    s.rows[0]["action"] = "forged"
    app.dependency_overrides[get_session] = lambda: s
    r = TestClient(app).get("/audit/verify", headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.json() == {"ok": False, "count": 3}


def test_verify_endpoint_requires_auth():
    app.dependency_overrides[get_session] = lambda: InMemoryAuditSession()
    r = TestClient(app).get("/audit/verify")
    assert r.status_code == 401


def test_list_audit_endpoint_returns_entries():
    s = InMemoryAuditSession()
    audit_repo.persist(s, WS, "dev", RUN)
    app.dependency_overrides[get_session] = lambda: s
    r = TestClient(app).get("/audit", headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 3 and body[0]["action"] == "reconcile"


def test_list_audit_requires_auth():
    app.dependency_overrides[get_session] = lambda: InMemoryAuditSession()
    r = TestClient(app).get("/audit")
    assert r.status_code == 401
