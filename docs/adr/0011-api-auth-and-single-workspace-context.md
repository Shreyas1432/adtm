# ADR-0011: API authentication + single-workspace request context

**Status:** Accepted

## Context
The Phase-0 control-plane API had open endpoints and no per-request workspace
binding (noted in the backlog). ADTM runs inside the client's environment as a
single-tenant appliance, so a heavyweight IdP/multi-tenant model is out of scope
(see CLAUDE.md "Do NOT build yet"). We still must authenticate every control-plane
call and bind it to the one workspace the appliance serves.

## Decision
A thin bearer-token guard protects every API route except the unauthenticated
`/health` liveness probe. The expected token and the workspace id are injected at
deploy time from the client's secrets manager via environment (`ADTM_API_TOKEN`,
`ADTM_WORKSPACE_ID`); neither is ever stored in the DB, source, config files, or
logs (invariant #7). Tokens are compared in constant time. Each authenticated
request carries a `Principal(workspace_id, subject)`, and control-plane data
reads are scoped to `principal.workspace_id`. The guard fails closed: if the
token is unset it rejects all requests.

## Consequences
No unauthenticated access to control-plane data; requests cannot read outside the
appliance's workspace. A full IdP / per-user RBAC remains a later phase; this
closes the Phase-0 gap with minimal surface. Rotating the token is an env change,
not a code change.
