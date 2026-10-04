from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import pg_dsn
engine = create_engine(pg_dsn(), pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
def get_session():
    s = SessionLocal()
    try: yield s
    finally: s.close()
