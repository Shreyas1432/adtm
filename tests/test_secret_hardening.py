"""Secret-handling hardening (invariant #7): keys, credentials and connection
secrets never surface in error messages, logs, process objects, or /health."""
import base64
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "api"))

from fastapi.testclient import TestClient  # noqa: E402

from adapters.secrets import dev_env_resolver  # noqa: E402
from adapters.source_ebs import EbsSourceAdapter  # noqa: E402
from security import crypto  # noqa: E402
from security.logs import emit  # noqa: E402
import io  # noqa: E402


def test_kek_error_does_not_leak_key_material(monkeypatch):
    bad = base64.b64encode(b"SECRETKEY_TOO_SHORT").decode()
    monkeypatch.setenv("ADTM_KEK_DEV", bad)
    with pytest.raises(RuntimeError) as ei:
        crypto.wrap_dek(crypto.generate_dek())  # no KEK arg -> reads env
    msg = str(ei.value)
    assert bad not in msg and "SECRETKEY_TOO_SHORT" not in msg


def test_blind_index_key_error_does_not_leak(monkeypatch):
    bad = base64.b64encode(b"short-blind-key").decode()
    monkeypatch.setenv("ADTM_BLIND_INDEX_KEY_DEV", bad)
    with pytest.raises(RuntimeError) as ei:
        crypto.blind_index("value", "TAX_ID")
    assert bad not in str(ei.value) and "short-blind-key" not in str(ei.value)


def test_resolver_error_does_not_leak_password(monkeypatch):
    monkeypatch.setenv("EBS_REF", '{"user":"u","password":"TOPSECRETPW" BROKEN')
    with pytest.raises(RuntimeError) as ei:
        dev_env_resolver("EBS_REF")
    assert "TOPSECRETPW" not in str(ei.value)


def test_resolver_missing_fields_error_does_not_leak_value(monkeypatch):
    monkeypatch.setenv("EBS_REF", '{"password":"TOPSECRETPW"}')  # missing user
    with pytest.raises(RuntimeError) as ei:
        dev_env_resolver("EBS_REF")
    assert "TOPSECRETPW" not in str(ei.value)


def test_adapter_object_holds_only_the_handle_not_credentials():
    adapter = EbsSourceAdapter("EBS_REF", {"host": "db", "service_name": "svc"})
    dump = repr(vars(adapter))
    assert "EBS_REF" in dump  # the handle is fine to hold/log
    assert "password" not in dump and "pwd" not in dump


def test_health_does_not_echo_internal_error(monkeypatch):
    monkeypatch.setenv("POSTGRES_USER", "adtm")
    monkeypatch.setenv("POSTGRES_PASSWORD", "PWLEAKCHECK")
    monkeypatch.setenv("POSTGRES_DB", "adtm")
    # engine() is lru_cached; clear so this test's env is used.
    from app.db import engine
    engine.cache_clear()
    from app.main import app
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "degraded", "db": "down"}
    assert "PWLEAKCHECK" not in r.text


def test_log_sweep_masks_every_secret_field():
    buf = io.StringIO()
    secrets = {
        "password": "LEAK_pw", "token": "LEAK_tok", "authorization": "LEAK_auth",
        "kek": "LEAK_kek", "dek": "LEAK_dek", "api_key": "LEAK_ak",
        "client_secret": "LEAK_cs", "secret_ref": "LEAK_ref",
    }
    emit("diag", stream=buf, **secrets)
    out = buf.getvalue()
    for value in secrets.values():
        assert value not in out
