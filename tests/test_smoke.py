import subprocess
import sys
import pandas as pd


def test_pipeline_runs_without_error():
    """Full pipeline runs end-to-end and exits 0."""
    result = subprocess.run(
        [sys.executable, "run_pipeline.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Pipeline exited with code {result.returncode}.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_analytics_table_has_rows(pg_engine):
    """Output table is non-empty after pipeline run."""
    df = pd.read_sql(
        "SELECT COUNT(*) AS n FROM analytics.monthly_sales_summary",
        pg_engine,
    )
    assert df.iloc[0]["n"] > 0


def test_analytics_table_has_expected_columns(pg_engine):
    """Output table has all required dashboard columns."""
    df = pd.read_sql(
        "SELECT * FROM analytics.monthly_sales_summary LIMIT 1",
        pg_engine,
    )
    expected_columns = {"year_month", "product_name", "revenue", "order_count", "avg_order_value"}
    assert expected_columns.issubset(set(df.columns))


def test_analytics_table_has_four_products(pg_engine):
    """All four basket product categories appear in output."""
    df = pd.read_sql(
        "SELECT DISTINCT product_name FROM analytics.monthly_sales_summary",
        pg_engine,
    )
    expected = {
        "The Original Gift Basket",
        "The Valentine's Gift Basket",
        "The Birthday Gift Basket",
        "The Holiday Gift Basket",
    }
    assert expected == set(df["product_name"].tolist())
