"""
DuckDB helper (ADR-0002). Default analytical/transform engine over Parquet.
Spark is NOT used; revisit only on benchmark evidence (see docs/adr/0002).
"""
from __future__ import annotations
import duckdb

def query_parquet(sql: str, **parquet_paths) -> list[dict]:
    con = duckdb.connect()
    try:
        for name, path in parquet_paths.items():
            # A bound parameter is not retained inside a VIEW definition, so the
            # (internal, control-plane) path is quote-escaped and inlined.
            con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_parquet('{path.replace(chr(39), chr(39) * 2)}')")
        return [dict(zip([c[0] for c in con.description], row))
                for row in con.execute(sql).fetchall()]
    finally:
        con.close()
