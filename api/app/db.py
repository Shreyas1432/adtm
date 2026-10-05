"""Control-plane DB session factory (ADR-0001).

Engine/session creation is lazy (built on first use) so the app imports without a
live database — tests override `get_session` and never touch Postgres.
"""
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import pg_dsn


@lru_cache(maxsize=1)
def engine():
    return create_engine(pg_dsn(), pool_pre_ping=True, future=True)


@lru_cache(maxsize=1)
def _sessionmaker():
    return sessionmaker(bind=engine(), expire_on_commit=False, future=True)


def get_session():
    s = _sessionmaker()()
    try:
        yield s
    finally:
        s.close()
