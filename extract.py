import pandas as pd


def extract_tables(mysql_engine) -> dict[str, pd.DataFrame]:
    """
    Read orders, order_items, and products from MySQL.
    Returns a dict mapping table name → DataFrame.
    """
    tables = {}
    with mysql_engine.connect() as conn:
        tables["orders"] = pd.read_sql("SELECT * FROM orders", conn)
        tables["order_items"] = pd.read_sql("SELECT * FROM order_items", conn)
        tables["products"] = pd.read_sql(
            "SELECT product_id, created_at, product_name, description FROM products", conn
        )
    return tables
