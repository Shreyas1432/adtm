"""Structured logging + redaction (invariant #7): secrets never reach a log line."""
import io
import json

from security.logs import emit
from security.redaction import REDACTED, is_secret_key, redact


def test_redact_masks_secret_keys_only():
    out = redact({"password": "p", "token": "t", "kek": "k", "dek": "d",
                  "api_key": "a", "user": "u", "host": "h"})
    assert out == {"password": REDACTED, "token": REDACTED, "kek": REDACTED,
                   "dek": REDACTED, "api_key": REDACTED, "user": "u", "host": "h"}


def test_redact_is_recursive():
    out = redact({"creds": {"password": "p"}, "list": [{"secret": "s"}]})
    assert out["creds"]["password"] == REDACTED
    assert out["list"][0]["secret"] == REDACTED


def test_redact_does_not_mask_routine_keys():
    for k in ("idempotency_key", "key_version", "worker_id", "job_type", "attempt"):
        assert not is_secret_key(k)


def test_emit_writes_json_and_redacts():
    buf = io.StringIO()
    line = emit("job_claimed", stream=buf, job_id="abc", password="hunter2", attempt=1)
    rec = json.loads(line)
    assert rec["event"] == "job_claimed" and rec["job_id"] == "abc" and rec["attempt"] == 1
    assert rec["password"] == REDACTED
    assert "hunter2" not in buf.getvalue()


def test_emit_handles_non_serializable_values():
    line = emit("x", stream=io.StringIO(), obj=object())  # default=str, no crash
    assert json.loads(line)["event"] == "x"
