from db import get_mysql_engine, get_pg_engine, validate_connections


def test_get_mysql_engine_returns_engine():
    engine = get_mysql_engine()
    assert engine is not None
    assert "mysql" in str(engine.url)


def test_get_pg_engine_returns_engine():
    engine = get_pg_engine()
    assert engine is not None
    assert "postgresql" in str(engine.url)


def test_validate_connections_succeeds_with_real_dbs():
    mysql = get_mysql_engine()
    pg = get_pg_engine()
    # Should not raise
    validate_connections(mysql, pg)


def test_validate_connections_raises_on_bad_pg():
    import sqlalchemy
    mysql = get_mysql_engine()
    bad_pg = sqlalchemy.create_engine("postgresql+psycopg2://x:x@localhost:9999/x")
    try:
        validate_connections(mysql, bad_pg)
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "PostgreSQL" in str(e)
