"""ADTM control-plane API (Phase 0). Control plane only (ADR-0001).
Endpoints are thin skeletons; Phase 1 fills extraction/DQ/mapping/etc."""
from fastapi import FastAPI, Depends
from sqlalchemy import text
from .db import get_session, engine

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

# Phase 1 routers to add: connections, schema-discovery, extraction, dq,
# mapping, simulation, load, readback, reconciliation, ai-suggestions, audit.
