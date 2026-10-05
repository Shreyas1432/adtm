"""Read-side queries that back the Phase-1 screens. Workspace-scoped, returns
raw rows (the frontend maps them to its display shape). Control-plane only.
"""
from __future__ import annotations

from sqlalchemy import text


def dq_results(s, workspace_id: str, run_id: str | None = None, limit: int = 200) -> list[dict]:
    """Raw dq_result rows joined to their rule, scoped to the workspace.

    dq_result has no workspace column, so it is scoped through
    dq_rule -> workflow_version -> workflow -> project -> workspace.
    """
    sql = (
        "SELECT r.id, r.run_id, dr.rule_type, dr.params, r.passed, r.failed, "
        "       r.sample, r.created_at "
        "FROM dq_result r "
        "JOIN dq_rule dr ON dr.id = r.rule_id "
        "JOIN workflow_version wv ON wv.id = dr.version_id "
        "JOIN workflow w ON w.id = wv.workflow_id "
        "JOIN project p ON p.id = w.project_id "
        "WHERE p.workspace_id = :ws "
    )
    params: dict = {"ws": workspace_id, "lim": limit}
    if run_id:
        sql += "AND r.run_id = :run_id "
        params["run_id"] = run_id
    sql += "ORDER BY r.created_at DESC, r.id DESC LIMIT :lim"
    rows = s.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]
