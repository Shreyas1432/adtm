import os
def pg_dsn() -> str:
    return (f"postgresql+psycopg://{os.environ['POSTGRES_USER']}:"
            f"{os.environ['POSTGRES_PASSWORD']}@{os.environ.get('POSTGRES_HOST','postgres')}:"
            f"{os.environ.get('POSTGRES_PORT','5432')}/{os.environ['POSTGRES_DB']}")
