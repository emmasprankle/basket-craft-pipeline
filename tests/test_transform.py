import pandas as pd
import pytest
from sqlalchemy import text
from transform import run_transform


def _load_fixtures(pg_engine):
    """Insert known fixture rows into raw schema for transform testing."""
    with pg_engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))

        conn.execute(text("DROP TABLE IF EXISTS raw.products"))
        conn.execute(text("""
            CREATE TABLE raw.products (
                product_id INT,
                created_at TIMESTAMP,
                product_name VARCHAR(50)
            )
        """))
        conn.execute(text("""
            INSERT INTO raw.products VALUES
            (1, '2023-01-01', 'The Original Gift Basket'),
            (2, '2024-01-01', 'The Valentine''s Gift Basket')
        """))

        conn.execute(text("DROP TABLE IF EXISTS raw.order_items"))
        conn.execute(text("""
            CREATE TABLE raw.order_items (
                order_item_id INT,
                created_at TIMESTAMP,
                order_id INT,
                product_id INT,
                is_primary_item SMALLINT,
                price_usd DECIMAL(6,2),
                cogs_usd DECIMAL(6,2)
            )
        """))
        conn.execute(text("""
            INSERT INTO raw.order_items VALUES
            (1, '2024-01-15', 101, 1, 1, 50.00, 20.00),
            (2, '2024-01-20', 102, 1, 1, 50.00, 20.00),
            (3, '2024-01-25', 103, 2, 1, 75.00, 30.00),
            (4, '2024-02-10', 104, 1, 1, 50.00, 20.00)
        """))


@pytest.fixture(autouse=True)
def clean_analytics_schema(pg_engine):
    """Drop analytics schema before and after each test."""
    with pg_engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS analytics CASCADE"))
    yield
    with pg_engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS analytics CASCADE"))


def test_transform_creates_analytics_schema(pg_engine):
    _load_fixtures(pg_engine)
    run_transform(pg_engine)
    with pg_engine.connect() as conn:
        schemas = conn.execute(
            text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'analytics'")
        ).fetchall()
    assert len(schemas) == 1


def test_transform_produces_correct_row_count(pg_engine):
    _load_fixtures(pg_engine)
    run_transform(pg_engine)
    result = pd.read_sql("SELECT * FROM analytics.monthly_sales_summary", pg_engine)
    # Jan/Original, Jan/Valentine's, Feb/Original = 3 rows
    assert len(result) == 3


def test_transform_january_original_revenue(pg_engine):
    _load_fixtures(pg_engine)
    run_transform(pg_engine)
    result = pd.read_sql(
        text(
            "SELECT * FROM analytics.monthly_sales_summary "
            "WHERE product_name = 'The Original Gift Basket' "
            "AND year_month::text LIKE '2024-01%'"
        ),
        pg_engine
    )
    assert len(result) == 1
    assert float(result.iloc[0]["revenue"]) == pytest.approx(100.00)
    assert int(result.iloc[0]["order_count"]) == 2
    assert float(result.iloc[0]["avg_order_value"]) == pytest.approx(50.00)


def test_transform_february_original_revenue(pg_engine):
    _load_fixtures(pg_engine)
    run_transform(pg_engine)
    result = pd.read_sql(
        text(
            "SELECT * FROM analytics.monthly_sales_summary "
            "WHERE product_name = 'The Original Gift Basket' "
            "AND year_month::text LIKE '2024-02%'"
        ),
        pg_engine
    )
    assert len(result) == 1
    assert float(result.iloc[0]["revenue"]) == pytest.approx(50.00)
    assert int(result.iloc[0]["order_count"]) == 1
    assert float(result.iloc[0]["avg_order_value"]) == pytest.approx(50.00)
