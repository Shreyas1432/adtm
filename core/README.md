# core
Domain logic for the control plane. In Phase 0 the thin domain lives in
`api/app` (models + routers). As Phase 1 grows, extract shared domain
services here (workflow/version management, mapping engine, DQ engine,
reconciliation) so both `api/` and `workers/` import one source of truth.
