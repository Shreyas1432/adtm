"""Build an immutable Bronze dataset from extracted source rows (ADR-0003).

Encrypts sensitive columns per the approved choices, then writes write-once
Parquet via dataplane.bronze. Pure except for the Bronze file write.
"""
from __future__ import annotations

import pyarrow as pa

from security.rowcrypt import encrypt_rows

from .bronze import write_bronze


def rows_to_table(rows) -> pa.Table:
    rows = list(rows)
    keys: dict[str, None] = {}
    for r in rows:
        keys.update(dict.fromkeys(r))
    return pa.Table.from_pylist([{k: r.get(k) for k in keys} for r in rows])


def extract_to_bronze(
    rows,
    *,
    workspace_id: str,
    dataset_name: str,
    choices: dict | None = None,
    dek: bytes | None = None,
    version_id: str | None = None,
    key_version: str | None = None,
) -> dict:
    rows = list(rows)
    if choices and dek:
        rows = encrypt_rows(rows, choices, dek)
    table = rows_to_table(rows)
    return write_bronze(workspace_id, dataset_name, table, version_id=version_id, key_version=key_version)
