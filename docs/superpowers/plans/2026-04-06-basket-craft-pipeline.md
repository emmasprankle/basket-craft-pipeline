# Basket Craft ELT Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a manually triggered ELT pipeline that extracts sales data from MySQL, loads raw copies into a local Docker PostgreSQL instance, and produces a `monthly_sales_summary` analytics table broken down by product and month.

**Architecture:** Python scripts extract three MySQL tables (`orders`, `order_items`, `products`) into pandas DataFrames, load them into a `raw` PostgreSQL schema via SQLAlchemy, then execute a SQL aggregation query to populate `analytics.monthly_sales_summary`. The pipeline is triggered by `python run_pipeline.py` and runs all three stages in sequence with connection validation and per-stage error handling.

**Tech Stack:** Python 3.11+, SQLAlchemy 2.x, pandas, psycopg2-binary, pymysql, python-dotenv, pytest, Docker / docker-compose

---

## File Map

| File | Responsibility |
|---|---|
| `docker-compose.yml` | Defines the local PostgreSQL container |
| `.env.example` | Documents required environment variables (committed; `.env` is git-ignored) |
| `requirements.txt` | Python dependencies |
| `db.py` | Returns configured SQLAlchemy engines for MySQL and PostgreSQL; validates connections |
| `extract.py` | Reads `orders`, `order_items`, `products` from MySQL → returns DataFrames |
| `load.py` | Creates `raw` schema if absent; truncates and reloads raw tables from DataFrames |
| `transform.py` | Creates `analytics` schema if absent; executes `sql/transform.sql` |
| `sql/transform.sql` | Aggregation query that builds `analytics.monthly_sales_summary` |
| `run_pipeline.py` | Entry point — validates connections, runs extract → load → transform in sequence |
| `tests/conftest.py` | Shared pytest fixtures (PostgreSQL engine scoped to session) |
| `tests/test_transform.py` | Unit tests — loads fixture rows into raw schema, asserts aggregation output |
| `tests/test_smoke.py` | Smoke test — runs full pipeline via subprocess, checks output table has rows |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `requirements.txt`
- Create: `sql/` directory placeholder

- [ ] **Step 1: Create `docker-compose.yml`**

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: pipeline
      POSTGRES_PASSWORD: pipeline
      POSTGRES_DB: basket_craft_dw
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

- [ ] **Step 2: Create `.env.example`**

```dotenv
# MySQL source (Basket Craft)
MYSQL_HOST=db.isba.co
MYSQL_PORT=3306
MYSQL_USER=analyst
MYSQL_PASSWORD=go_lions
MYSQL_DATABASE=basket_craft

# PostgreSQL destination (local Docker)
PG_HOST=localhost
PG_PORT=5432
PG_USER=pipeline
PG_PASSWORD=pipeline
PG_DATABASE=basket_craft_dw
```

- [ ] **Step 3: Create `requirements.txt`**

```
sqlalchemy>=2.0
pymysql
psycopg2-binary
pandas
python-dotenv
pytest
```

- [ ] **Step 4: Copy `.env.example` to `.env` and fill in real values**

```bash
cp .env.example .env
# .env is already git-ignored via the project .gitignore
```

- [ ] **Step 5: Start PostgreSQL container**

```bash
docker compose up -d
```

Expected: container `basket-craft-pipeline-postgres-1` running. Verify:

```bash
docker compose ps
```

Expected output includes `postgres` with state `running`.

- [ ] **Step 6: Install dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 7: Create `sql/` directory with a `.gitkeep`**

```bash
mkdir -p sql && touch sql/.gitkeep
```

- [ ] **Step 8: Commit**

```bash
git add docker-compose.yml .env.example requirements.txt sql/.gitkeep
git commit -m "feat: add project scaffolding, docker-compose, requirements"
```

---

## Task 2: Database Connection Module

**Files:**
- Create: `db.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create `tests/conftest.py` with a PostgreSQL engine fixture**

```python
import os
import pytest
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="session")
def pg_engine():
    engine = create_engine(
        f"postgresql+psycopg2://{os.environ['PG_USER']}:{os.environ['PG_PASSWORD']}"
        f"@{os.environ['PG_HOST']}:{os.environ['PG_PORT']}/{os.environ['PG_DATABASE']}"
    )
    yield engine
    engine.dispose()
```

- [ ] **Step 2: Write the failing test for `db.py`**

Create `tests/test_db.py`:

```python
from db import get_mysql_engine, get_pg_engine, validate_connections


def test_get_mysql_engine_returns_engine():
    engine = get_mysql_engine()
    assert engine is not None
    assert "mysql" in str(engine.url)


def test_get_pg_engine_returns_engine():
    engine = get_pg_engine()
    assert engine is not None
    assert "postgresql" in str(engine.url)


def test_validate_connections_succeeds_with_real_dbs():
    mysql = get_mysql_engine()
    pg = get_pg_engine()
    # Should not raise
    validate_connections(mysql, pg)


def test_validate_connections_raises_on_bad_pg():
    import sqlalchemy
    mysql = get_mysql_engine()
    bad_pg = sqlalchemy.create_engine("postgresql+psycopg2://x:x@localhost:9999/x")
    try:
        validate_connections(mysql, bad_pg)
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "PostgreSQL" in str(e)
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
pytest tests/test_db.py -v
```

Expected: `ModuleNotFoundError: No module named 'db'`

- [ ] **Step 4: Implement `db.py`**

```python
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def get_mysql_engine():
    url = (
        f"mysql+pymysql://{os.environ['MYSQL_USER']}:{os.environ['MYSQL_PASSWORD']}"
        f"@{os.environ['MYSQL_HOST']}:{os.environ['MYSQL_PORT']}/{os.environ['MYSQL_DATABASE']}"
    )
    return create_engine(url)


def get_pg_engine():
    url = (
        f"postgresql+psycopg2://{os.environ['PG_USER']}:{os.environ['PG_PASSWORD']}"
        f"@{os.environ['PG_HOST']}:{os.environ['PG_PORT']}/{os.environ['PG_DATABASE']}"
    )
    return create_engine(url)


def validate_connections(mysql_engine, pg_engine):
    """Verify both databases are reachable. Raises RuntimeError on failure."""
    try:
        with mysql_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError(f"MySQL connection failed: {e}") from e

    try:
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError(f"PostgreSQL connection failed: {e}") from e
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
pytest tests/test_db.py -v
```

Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add db.py tests/conftest.py tests/test_db.py
git commit -m "feat: add db connection module with validation"
```

---

## Task 3: Extract Module

**Files:**
- Create: `extract.py`
- Create: `tests/test_extract.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_extract.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_extract.py -v
```

Expected: `ModuleNotFoundError: No module named 'extract'`

- [ ] **Step 3: Implement `extract.py`**

```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_extract.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add extract.py tests/test_extract.py
git commit -m "feat: add extract module — reads orders, order_items, products from MySQL"
```

---

## Task 4: Load Module

**Files:**
- Create: `load.py`
- Create: `tests/test_load.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_load.py`:

```python
import pandas as pd
from sqlalchemy import text, inspect
from load import load_raw_tables


def test_load_creates_raw_schema(pg_engine):
    # Use minimal fixture DataFrames
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
            "product_name": "The Original Gift Basket", "description": None
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
            "product_name": "The Valentine's Gift Basket", "description": None
        }]),
    }
    load_raw_tables(tables, pg_engine)

    with pg_engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM raw.orders")).scalar()
    assert count == 1

    with pg_engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM raw.order_items")).scalar()
    assert count == 1
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_load.py -v
```

Expected: `ModuleNotFoundError: No module named 'load'`

- [ ] **Step 3: Implement `load.py`**

```python
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
            con=pg_engine,
            schema="raw",
            if_exists="replace",
            index=False,
        )
        print(f"  Loaded raw.{table_name}: {len(df)} rows")
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_load.py -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add load.py tests/test_load.py
git commit -m "feat: add load module — writes DataFrames to raw schema in PostgreSQL"
```

---

## Task 5: Transform SQL and Python Module

**Files:**
- Create: `sql/transform.sql`
- Create: `transform.py`
- Create: `tests/test_transform.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_transform.py`:

```python
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
                product_name VARCHAR(50),
                description TEXT
            )
        """))
        conn.execute(text("""
            INSERT INTO raw.products VALUES
            (1, '2023-01-01', 'The Original Gift Basket', NULL),
            (2, '2024-01-01', 'The Valentine''s Gift Basket', NULL)
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
        "SELECT * FROM analytics.monthly_sales_summary "
        "WHERE product_name = 'The Original Gift Basket' "
        "AND year_month::text LIKE '2024-01%'",
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
        "SELECT * FROM analytics.monthly_sales_summary "
        "WHERE product_name = 'The Original Gift Basket' "
        "AND year_month::text LIKE '2024-02%'",
        pg_engine
    )
    assert len(result) == 1
    assert float(result.iloc[0]["revenue"]) == pytest.approx(50.00)
    assert int(result.iloc[0]["order_count"]) == 1
    assert float(result.iloc[0]["avg_order_value"]) == pytest.approx(50.00)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_transform.py -v
```

Expected: `ModuleNotFoundError: No module named 'transform'`

- [ ] **Step 3: Create `sql/transform.sql`**

```sql
DROP TABLE IF EXISTS analytics.monthly_sales_summary;

CREATE TABLE analytics.monthly_sales_summary AS
SELECT
    DATE_TRUNC('month', oi.created_at)::date          AS year_month,
    p.product_name,
    SUM(oi.price_usd)                                 AS revenue,
    COUNT(DISTINCT oi.order_id)                       AS order_count,
    ROUND(
        SUM(oi.price_usd) / COUNT(DISTINCT oi.order_id),
        2
    )                                                 AS avg_order_value
FROM raw.order_items oi
JOIN raw.products p ON oi.product_id = p.product_id
GROUP BY 1, 2
ORDER BY 1, 2;
```

- [ ] **Step 4: Implement `transform.py`**

```python
from pathlib import Path
from sqlalchemy import text


def run_transform(pg_engine) -> None:
    """
    Execute sql/transform.sql against the raw schema to populate
    analytics.monthly_sales_summary.
    Creates the analytics schema if it does not exist.
    """
    sql = (Path(__file__).parent / "sql" / "transform.sql").read_text()

    with pg_engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))
        conn.execute(text(sql))

    with pg_engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM analytics.monthly_sales_summary")
        ).scalar()
    print(f"  Transformed analytics.monthly_sales_summary: {count} rows")
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
pytest tests/test_transform.py -v
```

Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add sql/transform.sql transform.py tests/test_transform.py
git commit -m "feat: add transform SQL and Python module with unit tests"
```

---

## Task 6: Pipeline Entry Point with Error Handling

**Files:**
- Create: `run_pipeline.py`

- [ ] **Step 1: Implement `run_pipeline.py`**

```python
import sys
from db import get_mysql_engine, get_pg_engine, validate_connections
from extract import extract_tables
from load import load_raw_tables
from transform import run_transform


def main():
    print("=== Basket Craft ELT Pipeline ===")

    print("\n[1/4] Validating database connections...")
    try:
        mysql_engine = get_mysql_engine()
        pg_engine = get_pg_engine()
        validate_connections(mysql_engine, pg_engine)
        print("  Connections OK")
    except RuntimeError as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

    print("\n[2/4] Extracting from MySQL...")
    try:
        tables = extract_tables(mysql_engine)
        for name, df in tables.items():
            print(f"  Extracted {name}: {len(df)} rows")
    except Exception as e:
        print(f"  ERROR during extract: {e}")
        sys.exit(1)

    print("\n[3/4] Loading into raw schema (PostgreSQL)...")
    try:
        load_raw_tables(tables, pg_engine)
    except Exception as e:
        print(f"  ERROR during load: {e}")
        sys.exit(1)

    print("\n[4/4] Transforming into analytics schema...")
    try:
        run_transform(pg_engine)
    except Exception as e:
        print(f"  ERROR during transform: {e}")
        sys.exit(1)

    print("\n=== Pipeline complete ===")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the pipeline manually to verify it works end-to-end**

```bash
python run_pipeline.py
```

Expected output:
```
=== Basket Craft ELT Pipeline ===

[1/4] Validating database connections...
  Connections OK

[2/4] Extracting from MySQL...
  Extracted orders: 32313 rows
  Extracted order_items: 40025 rows
  Extracted products: 4 rows

[3/4] Loading into raw schema (PostgreSQL)...
  Loaded raw.orders: 32313 rows
  Loaded raw.order_items: 40025 rows
  Loaded raw.products: 4 rows

[4/4] Transforming into analytics schema...
  Transformed analytics.monthly_sales_summary: <N> rows

=== Pipeline complete ===
```

- [ ] **Step 3: Spot-check the output table**

```bash
docker exec -it basket-craft-pipeline-postgres-1 psql -U pipeline -d basket_craft_dw \
  -c "SELECT * FROM analytics.monthly_sales_summary ORDER BY year_month, product_name LIMIT 20;"
```

Expected: rows with `year_month`, `product_name`, `revenue`, `order_count`, `avg_order_value` columns.

- [ ] **Step 4: Commit**

```bash
git add run_pipeline.py
git commit -m "feat: add run_pipeline.py entry point with per-stage error handling"
```

---

## Task 7: Smoke Test

**Files:**
- Create: `tests/test_smoke.py`

- [ ] **Step 1: Write the smoke test**

Create `tests/test_smoke.py`:

```python
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
```

- [ ] **Step 2: Run the smoke tests**

```bash
pytest tests/test_smoke.py -v
```

Expected: 4 passed (pipeline must already have been run at least once — Task 6 Step 2 satisfies this)

- [ ] **Step 3: Run the full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass (test_db, test_extract, test_load, test_transform, test_smoke)

- [ ] **Step 4: Commit**

```bash
git add tests/test_smoke.py
git commit -m "test: add smoke tests for end-to-end pipeline and analytics output"
```

---

## Final Checklist

- [ ] `docker compose ps` shows postgres running
- [ ] `python run_pipeline.py` exits 0 and prints row counts for all stages
- [ ] `pytest tests/ -v` passes all tests
- [ ] `analytics.monthly_sales_summary` contains rows for all 4 products across multiple months
