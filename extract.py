import pandas as pd


def extract_tables(mysql_engine) -> dict[str, pd.DataFrame]:
    """
    Read orders, order_items, and products from MySQL.
    Returns a dict mapping table name → DataFrame.
    """
    tables = {}
    with mysql_engine.connect() as conn:
        tables["orders"] = pd.read_sql(
            "SELECT order_id, created_at, user_id, primary_product_id, "
            "items_purchased, price_usd, cogs_usd FROM orders",
            conn
        )
        tables["order_items"] = pd.read_sql(
            "SELECT order_item_id, created_at, order_id, product_id, "
            "is_primary_item, price_usd, cogs_usd FROM order_items",
            conn
        )
        tables["products"] = pd.read_sql(
            "SELECT product_id, created_at, product_name FROM products",
            conn
        )
    return tables
