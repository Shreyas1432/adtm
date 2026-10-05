-- ADR-0012: worker retry/backoff + dead-letter.
-- `available_at` gates when a pending job may be re-claimed (backoff); the
-- 'dead' status is the terminal dead-letter state after max_attempts.

ALTER TABLE job ADD COLUMN IF NOT EXISTS available_at TIMESTAMPTZ;

-- Claim index: only pending jobs that are due. (Replaces the Phase-0 index.)
DROP INDEX IF EXISTS idx_job_claim;
CREATE INDEX idx_job_claim ON job (priority, created_at)
    WHERE status = 'pending';
