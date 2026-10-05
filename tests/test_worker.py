"""Worker claim/finish/reschedule glue (ADR-0012), exercised with a fake DB
connection so no Postgres/psycopg is needed."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "workers"))

import worker  # noqa: E402


class FakeCursor:
    def __init__(self, fetch=None):
        self.fetch = fetch
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self.fetch


class FakeConn:
    def __init__(self, fetch=None):
        self.cur = FakeCursor(fetch)

    def cursor(self):
        return self.cur


def test_claim_only_takes_due_pending_jobs_and_returns_attempt_fields():
    fetch = ("jid", "extract", "vid", {}, {}, 1, 3)
    conn = FakeConn(fetch)
    assert worker.claim_one(conn) == fetch
    sql, params = conn.cur.executed[-1]
    assert "status='pending'" in sql and "available_at IS NULL OR available_at <= now()" in sql
    assert "max_attempts" in sql and params == (worker.WORKER_ID,)


def test_succeed_marks_completed():
    conn = FakeConn()
    worker.succeed(conn, "jid")
    sql, params = conn.cur.executed[-1]
    assert "status='succeeded'" in sql and params == ("jid",)


def test_reschedule_requeues_with_backoff_before_exhaustion():
    conn = FakeConn()
    action, delay = worker.reschedule(conn, "jid", attempt=1, max_attempts=3, error="boom")
    assert action == "retry" and delay == 2.0
    sql, params = conn.cur.executed[-1]
    assert "status='pending'" in sql and "make_interval" in sql
    assert params == (2.0, "boom", "jid")


def test_reschedule_dead_letters_on_exhaustion():
    conn = FakeConn()
    action, delay = worker.reschedule(conn, "jid", attempt=3, max_attempts=3, error="boom")
    assert action == "dead" and delay is None
    sql, params = conn.cur.executed[-1]
    assert "status='dead'" in sql and params == ("boom", "jid")
