"""Job retry policy (ADR-0012). Pure: given the attempt count a handler just
failed on and the job's max_attempts, decide retry-with-backoff or dead-letter.

`attempt` is 1-based (the worker increments it on claim), so attempt==max_attempts
is the final try and exhausts the job.
"""
from __future__ import annotations

DEFAULT_BASE = 2.0   # seconds
DEFAULT_CAP = 300.0  # cap a single backoff at 5 minutes


def backoff_seconds(attempt: int, base: float = DEFAULT_BASE, cap: float = DEFAULT_CAP) -> float:
    return min(cap, base * (2 ** (max(attempt, 1) - 1)))


def next_action(attempt: int, max_attempts: int,
                base: float = DEFAULT_BASE, cap: float = DEFAULT_CAP):
    """Return ('retry', delay_seconds) or ('dead', None)."""
    if attempt >= max_attempts:
        return ("dead", None)
    return ("retry", backoff_seconds(attempt, base, cap))
