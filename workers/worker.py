"""
ADTM durable-jobs worker (ADR-0004). Claims jobs with transactional locking
(SELECT ... FOR UPDATE SKIP LOCKED), dispatches to idempotent handlers, and
checkpoints. No Temporal/Celery; revisit only on benchmarked need.
"""
from __future__ import annotations
import os, time, socket, json
import psycopg
from handlers import extract, dq, mapping, simulate, load, readback, reconcile

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
                SELECT id FROM job WHERE status='pending'
                ORDER BY priority, created_at
                FOR UPDATE SKIP LOCKED LIMIT 1
            )
            RETURNING id, job_type, version_id, payload, checkpoint;
        """, (WORKER_ID,))
        return cur.fetchone()

def finish(conn, job_id, ok, error=None):
    with conn.cursor() as cur:
        cur.execute("""UPDATE job SET status=%s, error=%s, completed_at=now()
                       WHERE id=%s""",
                    ("succeeded" if ok else "failed", error, job_id))

def main():
    print(f"[worker {WORKER_ID}] starting; polling for jobs")
    with psycopg.connect(dsn(), autocommit=False) as conn:
        while True:
            row = claim_one(conn)
            if not row:
                conn.commit(); time.sleep(2); continue
            job_id, job_type, version_id, payload, checkpoint = row
            conn.commit()
            print(f"[worker] claimed {job_id} ({job_type})")
            try:
                handler = HANDLERS.get(job_type)
                if not handler:
                    raise RuntimeError(f"no handler for job_type={job_type}")
                handler(job_id, version_id, payload or {}, checkpoint or {})
                with psycopg.connect(dsn(), autocommit=True) as c2:
                    finish(c2, job_id, True)
            except Exception as e:  # noqa
                with psycopg.connect(dsn(), autocommit=True) as c2:
                    finish(c2, job_id, False, str(e))
                print(f"[worker] job {job_id} failed: {e}")

if __name__ == "__main__":
    main()
