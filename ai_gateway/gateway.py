"""
AI gateway (ADR-0005). Model-agnostic interface (vLLM/Ollama). AI is DESIGN-TIME
ASSISTANCE ONLY: it returns suggestions that a human approves and that become
versioned config. NO execution path calls a model at runtime.

Every suggestion is instrumented (t_generated_ms, t_review_ms, decision) so
Gate 2 can measure T_AI vs T_manual. By default the model sees schema/metadata/
profiles/masked samples - never raw PII.
"""
from __future__ import annotations
import os, time
from dataclasses import dataclass, field

AI_ENABLED = os.environ.get("ADTM_AI_ENABLED", "false").lower() == "true"

@dataclass
class Suggestion:
    kind: str                      # table|sql|mapping|dq_rule|error_explanation
    suggestion: dict
    confidence: float
    model_ref: str
    t_generated_ms: int
    context_fields: list[str] = field(default_factory=list)  # what the model saw (no raw PII)

class AIGateway:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.environ.get("ADTM_AI_BASE_URL", "")

    def suggest(self, kind: str, context: dict) -> Suggestion:
        if not AI_ENABLED:
            raise RuntimeError("AI disabled (ADTM_AI_ENABLED=false). Enable per client/model review.")
        # Phase 1: call local model via base_url with metadata/masked-sample context only.
        t0 = time.monotonic()
        raise NotImplementedError("Phase 1: implement local model call (metadata-only context)")
