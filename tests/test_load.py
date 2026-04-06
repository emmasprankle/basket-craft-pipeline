import pytest
import pandas as pd
from sqlalchemy import text
from load import load_raw_tables


@pytest.fixture(autouse=True)
def clean_raw_schema(pg_engine):
    """Drop and recreate raw schema before each test for isolation."""
    with pg_engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS raw CASCADE"))
    yield
    with pg_engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS raw CASCADE"))


FIXTURE_TABLES = {
    "orders": pd.DataFrame([{
        "order_id": 1, "created_at": "2024-01-01",
        "user_id": 1, "primary_product_id": 1, "items_purchased": 1,
        "price_usd": 50.00, "cogs_usd": 20.00
    }]),
    "order_items": pd.DataFrame([{
        "order_item_id": 1, "created_at": "2024-01-01", "order_id": 1,
        "product_id": 1, "is_primary_item": 1, "price_usd": 50.00, "cogs_usd": 20.00
    }]),
    "products": pd.DataFrame([{
        "product_id": 1, "created_at": "2023-01-01",
        "product_name": "The Original Gift Basket"
    }]),
}


def test_load_creates_raw_schema(pg_engine):
    load_raw_tables(FIXTURE_TABLES, pg_engine)
    with pg_engine.connect() as conn:
        schemas = conn.execute(
            text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'raw'")
        ).fetchall()
    assert len(schemas) == 1


def test_load_populates_raw_tables(pg_engine):
    load_raw_tables(FIXTURE_TABLES, pg_engine)
    with pg_engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM raw.orders")).scalar() == 1
        assert conn.execute(text("SELECT COUNT(*) FROM raw.order_items")).scalar() == 1
        assert conn.execute(text("SELECT COUNT(*) FROM raw.products")).scalar() == 1
