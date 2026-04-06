import pandas as pd
from sqlalchemy import text


def load_raw_tables(tables: dict[str, pd.DataFrame], pg_engine) -> None:
    """
    Write DataFrames to the raw schema in PostgreSQL.
    Creates the schema if it does not exist.
    Replaces tables on each run (full refresh).
    """
    with pg_engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        for table_name, df in tables.items():
            df.to_sql(
                name=table_name,
                con=conn,
                schema="raw",
                if_exists="replace",
                index=False,
            )
            print(f"  Loaded raw.{table_name}: {len(df)} rows")
