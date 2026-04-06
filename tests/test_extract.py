import pandas as pd
from extract import extract_tables
from db import get_mysql_engine


def test_extract_returns_three_dataframes():
    engine = get_mysql_engine()
    tables = extract_tables(engine)
    assert set(tables.keys()) == {"orders", "order_items", "products"}
    for name, df in tables.items():
        assert isinstance(df, pd.DataFrame), f"{name} is not a DataFrame"
        assert len(df) > 0, f"{name} is empty"


def test_orders_has_expected_columns():
    engine = get_mysql_engine()
    tables = extract_tables(engine)
    expected = {"order_id", "created_at", "user_id", "primary_product_id",
                "items_purchased", "price_usd", "cogs_usd"}
    assert expected.issubset(set(tables["orders"].columns))


def test_order_items_has_expected_columns():
    engine = get_mysql_engine()
    tables = extract_tables(engine)
    expected = {"order_item_id", "created_at", "order_id", "product_id",
                "is_primary_item", "price_usd", "cogs_usd"}
    assert expected.issubset(set(tables["order_items"].columns))


def test_products_has_expected_columns():
    engine = get_mysql_engine()
    tables = extract_tables(engine)
    expected = {"product_id", "product_name"}
    assert expected.issubset(set(tables["products"].columns))


def test_products_has_four_rows():
    engine = get_mysql_engine()
    tables = extract_tables(engine)
    assert len(tables["products"]) == 4
