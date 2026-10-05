"""Structured JSON logging that redacts secrets (invariant #7).

`emit` writes one JSON object per line to stdout. Field values are passed through
`redact`, so a credential handed in by mistake is masked rather than printed.
Returns the emitted line for testability.
"""
from __future__ import annotations

import json
import sys
import time

from .redaction import redact


def emit(event: str, *, stream=None, **fields) -> str:
    record = {"ts": round(time.time(), 3), "event": event, **redact(fields)}
    line = json.dumps(record, sort_keys=True, default=str)
    print(line, file=stream or sys.stdout, flush=True)
    return line
