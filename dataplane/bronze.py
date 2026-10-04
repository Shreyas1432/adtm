"""
Immutable Bronze writer (ADR-0003). Source-preserving snapshot as columnar
Parquet on client-controlled storage, with a sha256 checksum + manifest.
Bronze is WRITE-ONCE: a new extraction creates a new dataset/version, never
an overwrite. Downstream stages never mutate Bronze.
"""
from __future__ import annotations
import hashlib, json, os, datetime as dt
import pyarrow as pa
import pyarrow.parquet as pq

DATA_ROOT = os.environ.get("ADTM_DATA_ROOT", "/data")

def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def schema_fingerprint(table: pa.Table) -> str:
    sig = ",".join(f"{n}:{t}" for n, t in zip(table.schema.names, table.schema.types))
    return hashlib.sha256(sig.encode()).hexdigest()[:16]

def write_bronze(workspace_id: str, dataset_name: str, table: pa.Table,
                 version_id: str | None = None, key_version: str | None = None) -> dict:
    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    d = os.path.join(DATA_ROOT, workspace_id, "bronze", dataset_name)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{dataset_name}_{ts}.parquet")
    pq.write_table(table, path, compression="zstd")
    manifest = {
        "workspace_id": workspace_id,
        "dataset_name": dataset_name,
        "file_path": path,
        "file_sha256": _sha256(path),
        "row_count": table.num_rows,
        "schema_fingerprint": schema_fingerprint(table),
        "version_id": version_id,
        "key_version": key_version,
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    with open(path + ".manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest  # caller persists this into bronze_manifest (control plane)
