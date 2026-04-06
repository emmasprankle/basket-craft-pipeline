import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def get_mysql_engine():
    url = (
        f"mysql+pymysql://{os.environ['MYSQL_USER']}:{os.environ['MYSQL_PASSWORD']}"
        f"@{os.environ['MYSQL_HOST']}:{os.environ['MYSQL_PORT']}/{os.environ['MYSQL_DATABASE']}"
    )
    return create_engine(url)


def get_pg_engine():
    url = (
        f"postgresql+psycopg2://{os.environ['PG_USER']}:{os.environ['PG_PASSWORD']}"
        f"@{os.environ['PG_HOST']}:{os.environ['PG_PORT']}/{os.environ['PG_DATABASE']}"
    )
    return create_engine(url)


def validate_connections(mysql_engine, pg_engine):
    """Verify both databases are reachable. Raises RuntimeError on failure."""
    try:
        with mysql_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError(f"MySQL connection failed: {e}") from e

    try:
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError(f"PostgreSQL connection failed: {e}") from e
