-- ADTM control-plane schema (Phase 0). Control plane only (ADR-0001).
-- Bronze/Silver/Gold bulk data live as Parquet on the data plane, NOT here.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---- Identity / isolation ----
CREATE TABLE workspace (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE app_user (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT UNIQUE NOT NULL,
    display_name  TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE workspace_member (
    workspace_id  UUID NOT NULL REFERENCES workspace(id),
    user_id       UUID NOT NULL REFERENCES app_user(id),
    role          TEXT NOT NULL DEFAULT 'member',   -- thin RBAC in Phase 0; hardened Phase 2
    PRIMARY KEY (workspace_id, user_id)
);

CREATE TABLE project (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  UUID NOT NULL REFERENCES workspace(id),
    name          TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---- Connections (secrets live in client secrets manager, NOT here - ADR note) ----
CREATE TABLE connection (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  UUID NOT NULL REFERENCES workspace(id),
    kind          TEXT NOT NULL,           -- 'source_ebs' | 'target_fusion'
    name          TEXT NOT NULL,
    secret_ref    TEXT NOT NULL,           -- reference/handle, never the secret itself
    config        JSONB NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---- Workflow + immutable versioning ----
CREATE TABLE workflow (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id    UUID NOT NULL REFERENCES project(id),
    object_name   TEXT NOT NULL,           -- e.g. 'suppliers' | 'ap_invoice'
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE workflow_version (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id   UUID NOT NULL REFERENCES workflow(id),
    version_no    INT  NOT NULL,
    config        JSONB NOT NULL,          -- frozen snapshot: extraction/mappings/rules refs
    created_by    UUID REFERENCES app_user(id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (workflow_id, version_no)
);

CREATE TABLE extraction (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id    UUID NOT NULL REFERENCES workflow_version(id),
    sql_text      TEXT NOT NULL,
    tables        JSONB NOT NULL DEFAULT '[]',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE dq_rule (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id    UUID NOT NULL REFERENCES workflow_version(id),
    rule_type     TEXT NOT NULL,           -- null|datatype|length|duplicate|ri|date|business
    params        JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE dq_result (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id       UUID NOT NULL REFERENCES dq_rule(id),
    run_id        UUID NOT NULL,
    passed        INT NOT NULL,
    failed        INT NOT NULL,
    sample        JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE mapping (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id    UUID NOT NULL REFERENCES workflow_version(id),
    source_field  TEXT NOT NULL,
    target_field  TEXT NOT NULL,
    kind          TEXT NOT NULL DEFAULT 'one_to_one',  -- one_to_one|one_to_many|static|xref|lookup
    transform     JSONB NOT NULL DEFAULT '{}',
    approved_by   UUID REFERENCES app_user(id),        -- human approval required (ADR-0005)
    approved_at   TIMESTAMPTZ
);

CREATE TABLE xref (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  UUID NOT NULL REFERENCES workspace(id),
    name          TEXT NOT NULL,
    source_value  TEXT NOT NULL,
    target_value  TEXT NOT NULL
);

-- ---- Bronze manifests (files on data plane; metadata here - ADR-0003) ----
CREATE TABLE bronze_manifest (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id     UUID NOT NULL REFERENCES workspace(id),
    connection_id    UUID NOT NULL REFERENCES connection(id),
    version_id       UUID REFERENCES workflow_version(id),
    dataset_name     TEXT NOT NULL,
    file_path        TEXT NOT NULL,         -- parquet path on data plane
    file_sha256      TEXT NOT NULL,
    row_count        BIGINT NOT NULL,
    schema_fingerprint TEXT NOT NULL,
    key_version      TEXT,                  -- which data key version encrypted sensitive cols
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
    -- immutable: new extraction => new row, never UPDATE
);

-- ---- Durable jobs (ADR-0004: Postgres jobs + idempotent workers, not Temporal) ----
CREATE TABLE job (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id   UUID REFERENCES workflow(id),
    version_id    UUID REFERENCES workflow_version(id),
    job_type      TEXT NOT NULL,           -- extract|dq|map|simulate|load|readback|reconcile
    status        TEXT NOT NULL DEFAULT 'pending',  -- pending|running|succeeded|failed
    attempt       INT NOT NULL DEFAULT 0,
    max_attempts  INT NOT NULL DEFAULT 3,
    priority      INT NOT NULL DEFAULT 100,
    worker_id     TEXT,
    idempotency_key TEXT UNIQUE,            -- prevents duplicate side effects
    checkpoint    JSONB NOT NULL DEFAULT '{}',
    payload       JSONB NOT NULL DEFAULT '{}',
    error         TEXT,
    locked_at     TIMESTAMPTZ,
    started_at    TIMESTAMPTZ,
    completed_at  TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_job_claim ON job (status, priority, created_at) WHERE status='pending';

-- ---- Load + reconciliation ----
CREATE TABLE load_run (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id      UUID NOT NULL REFERENCES workflow_version(id),
    manifest        JSONB NOT NULL DEFAULT '{}',   -- source/gold record -> payload mapping
    target_job_id   TEXT,                          -- Fusion ESS/request id
    target_file_id  TEXT,
    status          TEXT NOT NULL DEFAULT 'submitted',
    submitted_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    response_artifact JSONB
);

CREATE TABLE reconciliation (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    load_run_id     UUID NOT NULL REFERENCES load_run(id),
    source_count    BIGINT,
    expected_count  BIGINT,
    actual_count    BIGINT,                         -- from target read-back (ADR-0009)
    loaded_count    BIGINT,
    failed_count    BIGINT,
    unmatched_count BIGINT,
    control_totals  JSONB,
    status          TEXT,
    evidence_path   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---- AI suggestions (design-time only; approval gated - ADR-0005) ----
CREATE TABLE ai_suggestion (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id    UUID REFERENCES workflow_version(id),
    kind          TEXT NOT NULL,            -- table|sql|mapping|dq_rule|error_explanation
    prompt_ref    TEXT,
    model_ref     TEXT,
    suggestion    JSONB NOT NULL,
    confidence    NUMERIC,
    decision      TEXT,                     -- approved|rejected|edited
    decided_by    UUID REFERENCES app_user(id),
    t_generated_ms INT,                     -- instrumentation for Gate 2 (T_AI vs T_manual)
    t_review_ms    INT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---- Tamper-evident audit (hash-chained - ADR-0008) ----
CREATE TABLE audit_log (
    id            BIGSERIAL PRIMARY KEY,
    workspace_id  UUID,
    actor         UUID,
    action        TEXT NOT NULL,
    object_ref    TEXT,
    details       JSONB NOT NULL DEFAULT '{}',
    prev_hash     TEXT,
    hash          TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- seed a dev workspace/user so the skeleton has context
INSERT INTO workspace (id, name) VALUES ('00000000-0000-0000-0000-000000000001','dev-workspace');
INSERT INTO app_user (id, email, display_name) VALUES ('00000000-0000-0000-0000-000000000009','dev@adtm.local','Dev User');
INSERT INTO workspace_member VALUES ('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000009','admin');
