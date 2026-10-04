"""ADTM control-plane API (Phase 0). Control plane only (ADR-0001).
Endpoints are thin skeletons; Phase 1 fills extraction/DQ/mapping/etc."""
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from .db import get_session, engine
from .discovery import build_ebs_adapter, discover_columns

app = FastAPI(title="ADTM Control Plane", version="0.0.1")

@app.get("/health")
def health():
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        return {"status": "ok", "db": "up"}
    except Exception as e:
        return {"status": "degraded", "db": str(e)}

@app.get("/workspaces")
def list_workspaces(s=Depends(get_session)):
    rows = s.execute(text("SELECT id, name, created_at FROM workspace ORDER BY created_at")).mappings().all()
    return [dict(r) for r in rows]

@app.get("/projects")
def list_projects(s=Depends(get_session)):
    rows = s.execute(text("SELECT id, workspace_id, name FROM project ORDER BY created_at")).mappings().all()
    return [dict(r) for r in rows]

@app.get("/jobs")
def list_jobs(s=Depends(get_session)):
    rows = s.execute(text(
        "SELECT id, job_type, status, attempt, created_at FROM job ORDER BY created_at DESC LIMIT 50"
    )).mappings().all()
    return [dict(r) for r in rows]

# ---- Schema discovery (control-plane metadata only; read-only source) ----
def _ebs_connection(s, connection_id: str) -> dict:
    row = s.execute(text(
        "SELECT id, kind, secret_ref, config FROM connection WHERE id=:id"
    ), {"id": connection_id}).mappings().first()
    if not row:
        raise HTTPException(404, "connection not found")
    if row["kind"] != "source_ebs":
        raise HTTPException(400, "not an EBS source connection")
    return dict(row)

@app.post("/connections/{connection_id}/test")
def test_connection(connection_id: str, s=Depends(get_session)):
    return {"ok": build_ebs_adapter(_ebs_connection(s, connection_id)).test_connection()}

@app.get("/connections/{connection_id}/tables")
def list_source_tables(connection_id: str, s=Depends(get_session)):
    return build_ebs_adapter(_ebs_connection(s, connection_id)).list_tables()

@app.get("/connections/{connection_id}/tables/{table}/columns")
def list_source_columns(connection_id: str, table: str, s=Depends(get_session)):
    return discover_columns(build_ebs_adapter(_ebs_connection(s, connection_id)), table)

# Phase 1 routers still to add: extraction, dq, mapping, simulation, load,
# readback, reconciliation, ai-suggestions, audit.
