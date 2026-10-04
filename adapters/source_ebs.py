"""Oracle EBS source adapter (READ-ONLY) — Phase 1.

Implements the `SourceAdapter` contract (see adapters/base.py):
  test_connection · list_tables · column_metadata · extract

Invariants enforced here:
- #1 Source is read-only. The adapter never issues DML/DDL. `extract` accepts a
  single read-only SELECT/WITH statement only, and the transaction is opened
  READ ONLY as defence-in-depth. The primary guarantee is a read-only DB account
  resolved from `secret_ref` (see adapters/secrets.py).
- #7 Credentials are resolved from a secret handle at call time and never stored
  or logged.

The Oracle driver (python-oracledb, thin mode) is imported lazily so unit tests
and non-Oracle environments do not require the driver or a live database. A
`connect_fn` can be injected to supply a connection (used by the tests).

Pilot validation (per backlog): confirm python-oracledb thin/thick mode and any
Instant Client requirement against the client's EBS version.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Iterable

from .base import SourceAdapter  # noqa: F401  (documents the contract this implements)
from .secrets import SecretResolver, dev_env_resolver

# --- read-only SQL guard -----------------------------------------------------

_LINE_COMMENT = re.compile(r"--[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_STRING_LITERAL = re.compile(r"'(?:''|[^'])*'", re.S)
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|merge|upsert|drop|alter|create|truncate|grant|"
    r"revoke|call|exec|execute|begin|declare|commit|rollback|savepoint|lock)\b",
    re.I,
)
_STARTS_READONLY = re.compile(r"^\s*(select|with)\b", re.I)


def _sanitize(sql: str) -> str:
    """Strip comments and string literals so the guard scans SQL structure only."""
    s = _BLOCK_COMMENT.sub(" ", sql)
    s = _LINE_COMMENT.sub(" ", s)
    s = _STRING_LITERAL.sub("''", s)
    return s


def is_readonly_select(sql: str) -> bool:
    """True only for a single read-only SELECT/WITH statement."""
    if not sql or not sql.strip():
        return False
    scrubbed = _sanitize(sql).strip().rstrip(";").strip()
    if not scrubbed:
        return False
    if ";" in scrubbed:  # reject multiple/stacked statements
        return False
    if not _STARTS_READONLY.match(scrubbed):
        return False
    if _FORBIDDEN.search(scrubbed):
        return False
    return True


# --- adapter -----------------------------------------------------------------


class EbsSourceAdapter:  # implements SourceAdapter
    def __init__(
        self,
        secret_ref: str,
        config: dict | None = None,
        *,
        connect_fn: Callable[[], Any] | None = None,
        secret_resolver: SecretResolver = dev_env_resolver,
    ):
        self.secret_ref = secret_ref
        self.config = dict(config or {})
        schema = (self.config.get("schema") or "").strip().upper()
        self.schema: str | None = schema or None  # Oracle owner; None => current schema
        self._connect_fn = connect_fn
        self._secret_resolver = secret_resolver

    # -- connection --
    def _connect(self):
        if self._connect_fn is not None:
            return self._connect_fn()
        import oracledb  # lazy: not needed for tests / non-Oracle envs

        creds = self._secret_resolver(self.secret_ref)
        dsn = oracledb.makedsn(
            self.config["host"],
            int(self.config.get("port", 1521)),
            service_name=self.config.get("service_name"),
            sid=self.config.get("sid"),
        )
        conn = oracledb.connect(user=creds["user"], password=creds["password"], dsn=dsn)
        try:  # defence-in-depth; the read-only account is the real guarantee
            with conn.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY")
        except Exception:
            pass
        return conn

    # -- contract methods --
    def test_connection(self) -> bool:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM dual")
                return cur.fetchone() is not None
        finally:
            conn.close()

    def list_tables(self) -> list[str]:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                if self.schema:
                    cur.execute(
                        "SELECT table_name FROM all_tables "
                        "WHERE owner = :owner ORDER BY table_name",
                        {"owner": self.schema},
                    )
                else:
                    cur.execute("SELECT table_name FROM user_tables ORDER BY table_name")
                return [r[0] for r in cur.fetchall()]
        finally:
            conn.close()

    def column_metadata(self, table: str) -> list[dict]:
        """Return [{name, type, length, nullable, pk, description}] in column order."""
        tbl = table.strip().upper()
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                pk_cols = self._primary_key_columns(cur, tbl)
                if self.schema:
                    cur.execute(_COLS_SQL_ALL, {"owner": self.schema, "tbl": tbl})
                else:
                    cur.execute(_COLS_SQL_USER, {"tbl": tbl})
                out: list[dict] = []
                for name, data_type, length, precision, scale, nullable, comments in cur.fetchall():
                    out.append(
                        {
                            "name": name,
                            "type": data_type,
                            "length": _effective_length(data_type, length, precision, scale),
                            "nullable": nullable == "Y",
                            "pk": name in pk_cols,
                            "description": comments,
                        }
                    )
                return out
        finally:
            conn.close()

    def extract(self, sql: str) -> Iterable[dict]:
        """Stream rows for a read-only SELECT. Never writes the source (#1)."""
        if not is_readonly_select(sql):
            raise ValueError(
                "EBS extract accepts a single read-only SELECT/WITH statement only "
                "(the source ERP is read-only)."
            )
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.arraysize = int(self.config.get("arraysize", 1000))
                cur.execute(sql)
                cols = [d[0] for d in cur.description]
                while True:
                    rows = cur.fetchmany(cur.arraysize)
                    if not rows:
                        break
                    for row in rows:
                        yield dict(zip(cols, row))
        finally:
            conn.close()

    # -- helpers --
    def _primary_key_columns(self, cur, tbl: str) -> set[str]:
        if self.schema:
            cur.execute(_PK_SQL_ALL, {"owner": self.schema, "tbl": tbl})
        else:
            cur.execute(_PK_SQL_USER, {"tbl": tbl})
        return {r[0] for r in cur.fetchall()}


def _effective_length(data_type: str, length, precision, scale):
    """Prefer precision/scale for NUMBER; char length otherwise."""
    t = (data_type or "").upper()
    if t.startswith("NUMBER") and precision is not None:
        return f"{precision},{scale or 0}"
    return length


# Oracle data-dictionary queries. ALL_* when an owner is known, USER_* otherwise.
_COLS_SQL_ALL = """
    SELECT c.column_name, c.data_type, c.data_length, c.data_precision,
           c.data_scale, c.nullable, cc.comments
    FROM all_tab_columns c
    LEFT JOIN all_col_comments cc
      ON cc.owner = c.owner AND cc.table_name = c.table_name
     AND cc.column_name = c.column_name
    WHERE c.owner = :owner AND c.table_name = :tbl
    ORDER BY c.column_id
"""
_COLS_SQL_USER = """
    SELECT c.column_name, c.data_type, c.data_length, c.data_precision,
           c.data_scale, c.nullable, cc.comments
    FROM user_tab_columns c
    LEFT JOIN user_col_comments cc
      ON cc.table_name = c.table_name AND cc.column_name = c.column_name
    WHERE c.table_name = :tbl
    ORDER BY c.column_id
"""
_PK_SQL_ALL = """
    SELECT col.column_name
    FROM all_constraints con
    JOIN all_cons_columns col
      ON col.owner = con.owner AND col.constraint_name = con.constraint_name
    WHERE con.owner = :owner AND con.table_name = :tbl AND con.constraint_type = 'P'
"""
_PK_SQL_USER = """
    SELECT col.column_name
    FROM user_constraints con
    JOIN user_cons_columns col
      ON col.constraint_name = con.constraint_name
    WHERE con.table_name = :tbl AND con.constraint_type = 'P'
"""
