from pathlib import Path
from sqlalchemy import text


def run_transform(pg_engine) -> None:
    sql = (Path(__file__).parent / "sql" / "transform.sql").read_text()

    with pg_engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))
        conn.execute(text(sql))

    with pg_engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM analytics.monthly_sales_summary")
        ).scalar()

    if count == 0:
        raise RuntimeError(
            "Transform produced 0 rows — check that raw.order_items and raw.products are populated"
        )

    print(f"  Transformed analytics.monthly_sales_summary: {count} rows")
