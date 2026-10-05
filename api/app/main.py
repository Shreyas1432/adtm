"""ADTM control-plane API. Control plane only (ADR-0001).

Every route except /health requires a bearer token and is bound to the
appliance's single workspace (ADR-0011); data reads are scoped to that workspace.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path
from sqlalchemy import text

from security import audit

from . import audit_repo
from .auth import CurrentPrincipal, Principal, require_principal
from .db import engine, get_session
from .discovery import IDENTIFIER_RE, MAX_IDENTIFIER_LEN, build_ebs_adapter, discover_columns

app = FastAPI(title="ADTM Control Plane", version="0.0.1")

# Authenticated routes live on this router; /health stays open (ADR-0011).
api = APIRouter(dependencies=[Depends(require_principal)])


@app.get("/health")
def health():
    try:
        with engine().connect() as c:
            c.execute(text("SELECT 1"))
        return {"status": "ok", "db": "up"}
    except Exception:
        # Never echo the raw error: it can carry connection details (invariant #7).
        return {"status": "degraded", "db": "down"}


@api.get("/workspaces")
def list_workspaces(principal: Principal = CurrentPrincipal, s=Depends(get_session)):
    rows = s.execute(text(
        "SELECT id, name, created_at FROM workspace WHERE id=:ws"
    ), {"ws": principal.workspace_id}).mappings().all()
    return [dict(r) for r in rows]


@api.get("/projects")
def list_projects(principal: Principal = CurrentPrincipal, s=Depends(get_session)):
    rows = s.execute(text(
        "SELECT id, workspace_id, name FROM project WHERE workspace_id=:ws ORDER BY created_at"
    ), {"ws": principal.workspace_id}).mappings().all()
    return [dict(r) for r in rows]


@api.get("/jobs")
def list_jobs(principal: Principal = CurrentPrincipal, s=Depends(get_session)):
    rows = s.execute(text(
        "SELECT j.id, j.job_type, j.status, j.attempt, j.created_at FROM job j "
        "JOIN workflow w ON w.id=j.workflow_id "
        "JOIN project p ON p.id=w.project_id "
        "WHERE p.workspace_id=:ws ORDER BY j.created_at DESC LIMIT 50"
    ), {"ws": principal.workspace_id}).mappings().all()
    return [dict(r) for r in rows]


# ---- Schema discovery (control-plane metadata only; read-only source) ----
def _ebs_connection(s, connection_id: UUID, workspace_id: str) -> dict:
    row = s.execute(text(
        "SELECT id, kind, secret_ref, config FROM connection WHERE id=:id AND workspace_id=:ws"
    ), {"id": str(connection_id), "ws": workspace_id}).mappings().first()
    if not row:
        raise HTTPException(404, "connection not found")
    if row["kind"] != "source_ebs":
        raise HTTPException(400, "not an EBS source connection")
    return dict(row)


_TABLE = Path(min_length=1, max_length=MAX_IDENTIFIER_LEN, pattern=IDENTIFIER_RE)


@api.post("/connections/{connection_id}/test")
def test_connection(connection_id: UUID, principal: Principal = CurrentPrincipal, s=Depends(get_session)):
    return {"ok": build_ebs_adapter(_ebs_connection(s, connection_id, principal.workspace_id)).test_connection()}


@api.get("/connections/{connection_id}/tables")
def list_source_tables(connection_id: UUID, principal: Principal = CurrentPrincipal, s=Depends(get_session)):
    return build_ebs_adapter(_ebs_connection(s, connection_id, principal.workspace_id)).list_tables()


@api.get("/connections/{connection_id}/tables/{table}/columns")
def list_source_columns(connection_id: UUID, table: str = _TABLE, principal: Principal = CurrentPrincipal, s=Depends(get_session)):
    return discover_columns(build_ebs_adapter(_ebs_connection(s, connection_id, principal.workspace_id)), table)


# ---- Audit: verify the workspace's hash chain over its persisted run (ADR-0008) ----
@api.get("/audit/verify")
def verify_audit(principal: Principal = CurrentPrincipal, s=Depends(get_session)):
    chain = audit_repo.load_chain(s, principal.workspace_id)
    return {"ok": audit.verify(chain), "count": len(chain)}


app.include_router(api)

# Phase 1 routers still to add: extraction, dq, mapping, simulation, load,
# readback, reconciliation, ai-suggestions, audit.
