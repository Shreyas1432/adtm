"""Job retry policy (ADR-0012): backoff growth/cap and retry-vs-dead-letter."""
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "workers"))

from retry import backoff_seconds, next_action  # noqa: E402


def test_backoff_grows_exponentially():
    assert [backoff_seconds(a, base=2.0) for a in (1, 2, 3, 4)] == [2.0, 4.0, 8.0, 16.0]


def test_backoff_is_capped():
    assert backoff_seconds(50, base=2.0, cap=300.0) == 300.0


def test_backoff_floor_for_zero_or_negative_attempt():
    assert backoff_seconds(0, base=2.0) == 2.0
    assert backoff_seconds(-5, base=2.0) == 2.0


def test_retry_until_final_attempt():
    assert next_action(1, 3)[0] == "retry"
    assert next_action(2, 3)[0] == "retry"


def test_dead_letter_on_last_attempt():
    assert next_action(3, 3) == ("dead", None)


def test_dead_letter_when_attempt_exceeds_max():
    assert next_action(9, 3) == ("dead", None)


def test_single_attempt_job_never_retries():
    assert next_action(1, 1) == ("dead", None)


def test_retry_returns_positive_delay():
    action, delay = next_action(1, 5)
    assert action == "retry" and delay > 0
