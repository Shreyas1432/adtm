"""Shared test doubles for API-layer tests (no live DB)."""


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def first(self):
        return self._rows[0] if self._rows else None


class FakeSession:
    """SQLAlchemy-session stand-in that records (sql, params) per execute."""

    def __init__(self, rows=None):
        self.rows = rows or []
        self.calls = []

    def execute(self, stmt, params=None):
        self.calls.append((str(stmt), params or {}))
        return _Result(self.rows)

    def close(self):
        pass
