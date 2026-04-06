import pytest
from db import get_mysql_engine, get_pg_engine, validate_connections


def test_get_mysql_engine_returns_engine():
    engine = get_mysql_engine()
    assert engine is not None
    assert "mysql" in str(engine.url)


def test_get_pg_engine_returns_engine():
    engine = get_pg_engine()
    assert engine is not None
    assert "postgresql" in str(engine.url)


def test_validate_connections_succeeds_with_real_dbs(pg_engine):
    mysql = get_mysql_engine()
    validate_connections(mysql, pg_engine)  # Should not raise


def test_validate_connections_raises_on_bad_pg():
    import sqlalchemy
    mysql = get_mysql_engine()
    bad_pg = sqlalchemy.create_engine("postgresql+psycopg2://x:x@localhost:9999/x")
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        validate_connections(mysql, bad_pg)


def test_validate_connections_raises_on_bad_mysql():
    import sqlalchemy
    bad_mysql = sqlalchemy.create_engine("mysql+pymysql://x:x@localhost:9999/x")
    pg = get_pg_engine()
    with pytest.raises(RuntimeError, match="MySQL"):
        validate_connections(bad_mysql, pg)
