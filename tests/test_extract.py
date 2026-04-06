import pytest
import pandas as pd
from extract import extract_tables
from db import get_mysql_engine


@pytest.fixture(scope="module")
def extracted_tables():
    engine = get_mysql_engine()
    return extract_tables(engine)


def test_extract_returns_three_dataframes(extracted_tables):
    assert set(extracted_tables.keys()) == {"orders", "order_items", "products"}
    for name, df in extracted_tables.items():
        assert isinstance(df, pd.DataFrame), f"{name} is not a DataFrame"
        assert len(df) > 0, f"{name} is empty"


def test_orders_has_expected_columns(extracted_tables):
    expected = {"order_id", "created_at", "user_id", "primary_product_id",
                "items_purchased", "price_usd", "cogs_usd"}
    assert set(extracted_tables["orders"].columns) == expected


def test_order_items_has_expected_columns(extracted_tables):
    expected = {"order_item_id", "created_at", "order_id", "product_id",
                "is_primary_item", "price_usd", "cogs_usd"}
    assert set(extracted_tables["order_items"].columns) == expected


def test_products_has_expected_columns(extracted_tables):
    expected = {"product_id", "created_at", "product_name"}
    assert set(extracted_tables["products"].columns) == expected


def test_products_has_four_rows(extracted_tables):
    assert len(extracted_tables["products"]) == 4
