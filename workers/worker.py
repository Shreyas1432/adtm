"""
ADTM durable-jobs worker (ADR-0004, ADR-0012). Claims jobs with transactional
locking (SELECT ... FOR UPDATE SKIP LOCKED), dispatches to idempotent handlers,
checkpoints, and on failure retries with backoff or dead-letters the job.
No Temporal/Celery; revisit only on benchmarked need.
"""
from __future__ import annotations
import os, time, socket

from handlers import extract, dq, mapping, simulate, load, readback, reconcile
from retry import next_action
from security.logs import emit

HANDLERS = {
    "extract": extract.run, "dq": dq.run, "map": mapping.run,
    "simulate": simulate.run, "load": load.run,
    "readback": readback.run, "reconcile": reconcile.run,
}
WORKER_ID = f"{socket.gethostname()}-{os.getpid()}"


def dsn() -> str:
    return (f"host={os.environ.get('POSTGRES_HOST','postgres')} "
            f"port={os.environ.get('POSTGRES_PORT','5432')} "
            f"dbname={os.environ['POSTGRES_DB']} user={os.environ['POSTGRES_USER']} "
            f"password={os.environ['POSTGRES_PASSWORD']}")


def claim_one(conn):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE job SET status='running', worker_id=%s, attempt=attempt+1,
                   locked_at=now(), started_at=COALESCE(started_at, now())
            WHERE id = (
                SELECT id FROM job
                WHERE status='pending' AND (available_at IS NULL OR available_at <= now())
                ORDER BY priority, created_at
                FOR UPDATE SKIP LOCKED LIMIT 1
            )
            RETURNING id, job_type, version_id, payload, checkpoint, attempt, max_attempts;
        """, (WORKER_ID,))
        return cur.fetchone()


def succeed(conn, job_id):
    with conn.cursor() as cur:
        cur.execute("UPDATE job SET status='succeeded', completed_at=now() WHERE id=%s", (job_id,))


def reschedule(conn, job_id, attempt, max_attempts, error):
    """Requeue with backoff, or dead-letter on exhaustion. Returns (action, delay)."""
    action, delay = next_action(attempt, max_attempts)
    with conn.cursor() as cur:
        if action == "retry":
            cur.execute(
                "UPDATE job SET status='pending', worker_id=NULL, locked_at=NULL, "
                "available_at = now() + make_interval(secs => %s), error=%s WHERE id=%s",
                (delay, error, job_id))
        else:
            cur.execute(
                "UPDATE job SET status='dead', completed_at=now(), error=%s WHERE id=%s",
                (error, job_id))
    return action, delay


def main():
    import psycopg  # lazy: not needed to import this module (tests inject fakes)

    emit("worker_start", worker_id=WORKER_ID)
    with psycopg.connect(dsn(), autocommit=False) as conn:
        while True:
            row = claim_one(conn)
            if not row:
                conn.commit(); time.sleep(2); continue
            job_id, job_type, version_id, payload, checkpoint, attempt, max_attempts = row
            conn.commit()
            emit("job_claimed", job_id=str(job_id), job_type=job_type, attempt=attempt)
            try:
                handler = HANDLERS.get(job_type)
                if not handler:
                    raise RuntimeError(f"no handler for job_type={job_type}")
                handler(job_id, version_id, payload or {}, checkpoint or {})
                with psycopg.connect(dsn(), autocommit=True) as c2:
                    succeed(c2, job_id)
                emit("job_succeeded", job_id=str(job_id), job_type=job_type, attempt=attempt)
            except Exception as e:  # noqa: BLE001 - worker boundary: never crash the loop
                with psycopg.connect(dsn(), autocommit=True) as c2:
                    action, delay = reschedule(c2, job_id, attempt, max_attempts, str(e))
                emit("job_retry" if action == "retry" else "job_dead_letter",
                     job_id=str(job_id), job_type=job_type, attempt=attempt,
                     max_attempts=max_attempts, delay_s=delay, error_type=type(e).__name__)


if __name__ == "__main__":
    main()
