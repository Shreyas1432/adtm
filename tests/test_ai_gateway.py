"""AI gateway guardrail (ADR-0005, invariant #3): AI is design-time only and
disabled by default; when enabled it returns metadata-only suggestions."""
import pytest

from ai_gateway import gateway

COLS = [{"name": "VENDOR_ID", "type": "NUMBER", "pk": True},
        {"name": "VENDOR_NAME", "type": "VARCHAR2"}]
CONTEXT = {"columns": COLS}


def test_disabled_by_default_raises(monkeypatch):
    monkeypatch.setattr(gateway, "AI_ENABLED", False)
    with pytest.raises(RuntimeError):
        gateway.AIGateway().suggest("mapping", CONTEXT)


def test_enabled_mapping_returns_metadata_only_suggestion(monkeypatch):
    monkeypatch.setattr(gateway, "AI_ENABLED", True)
    s = gateway.AIGateway().suggest("mapping", CONTEXT)
    assert s.kind == "mapping" and s.model_ref == "local-heuristic-v0"
    assert s.context_fields == ["VENDOR_ID", "VENDOR_NAME"]  # names only, no PII
    assert 0 < s.confidence <= 1


def test_enabled_dq_rule_supported(monkeypatch):
    monkeypatch.setattr(gateway, "AI_ENABLED", True)
    assert gateway.AIGateway().suggest("dq_rule", CONTEXT).kind == "dq_rule"


def test_enabled_unknown_kind_not_implemented(monkeypatch):
    monkeypatch.setattr(gateway, "AI_ENABLED", True)
    with pytest.raises(NotImplementedError):
        gateway.AIGateway().suggest("sql", CONTEXT)
