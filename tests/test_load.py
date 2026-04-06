import pandas as pd
from sqlalchemy import text
from load import load_raw_tables


def test_load_creates_raw_schema(pg_engine):
    tables = {
        "orders": pd.DataFrame([{
            "order_id": 1, "created_at": "2024-01-01", "website_session_id": 1,
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
    load_raw_tables(tables, pg_engine)

    with pg_engine.connect() as conn:
        schemas = conn.execute(
            text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'raw'")
        ).fetchall()
    assert len(schemas) == 1


def test_load_populates_raw_tables(pg_engine):
    tables = {
        "orders": pd.DataFrame([{
            "order_id": 99, "created_at": "2024-06-01", "website_session_id": 1,
            "user_id": 1, "primary_product_id": 2, "items_purchased": 1,
            "price_usd": 75.00, "cogs_usd": 30.00
        }]),
        "order_items": pd.DataFrame([{
            "order_item_id": 99, "created_at": "2024-06-01", "order_id": 99,
            "product_id": 2, "is_primary_item": 1, "price_usd": 75.00, "cogs_usd": 30.00
        }]),
        "products": pd.DataFrame([{
            "product_id": 2, "created_at": "2024-01-01",
            "product_name": "The Valentine's Gift Basket"
        }]),
    }
    load_raw_tables(tables, pg_engine)

    with pg_engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM raw.orders")).scalar()
    assert count == 1

    with pg_engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM raw.order_items")).scalar()
    assert count == 1
