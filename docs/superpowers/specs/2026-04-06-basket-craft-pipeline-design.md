# Basket Craft ELT Pipeline — Design Spec

**Date:** 2026-04-06  
**Project:** ISBA 4715 — basket-craft-pipeline  
**Status:** Approved

---

## Overview

A manually triggered ELT pipeline that extracts sales data from the Basket Craft MySQL database, loads raw copies into a local PostgreSQL instance (Docker), and transforms them into a monthly sales dashboard table broken down by product category.

---

## Source

**Database:** MySQL at `db.isba.co:3306`, database `basket_craft`  
**Credentials:** Loaded from `.env` (`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`)

**Tables extracted:**

| Table | Key columns |
|---|---|
| `orders` | `order_id`, `created_at`, `user_id`, `primary_product_id`, `items_purchased`, `price_usd`, `cogs_usd` |
| `order_items` | `order_item_id`, `created_at`, `order_id`, `product_id`, `is_primary_item`, `price_usd`, `cogs_usd` |
| `products` | `product_id`, `product_name` |

**Not extracted:** `employees`, `users`, `website_pageviews`, `website_sessions`, `order_item_refunds`

**Volume:** ~32,313 orders, ~40,025 order items, 4 products (2023–2026)

---

## Destination

**Database:** PostgreSQL running in Docker on `localhost:5432`  
**Credentials:** Loaded from `.env` (`PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`, `PG_DATABASE`)

### Raw Schema (`raw`)

Faithful copies of source tables — no transformations applied:

- `raw.orders`
- `raw.order_items`
- `raw.products`

### Analytics Schema (`analytics`)

Business-ready aggregated table:

**`analytics.monthly_sales_summary`**

| Column | Type | Description |
|---|---|---|
| `year_month` | date | First day of the month (truncated from `order_items.created_at`) |
| `product_name` | varchar | Product category (one of 4 basket types) |
| `revenue` | numeric | Gross revenue — `SUM(order_items.price_usd)` |
| `order_count` | integer | Distinct orders — `COUNT(DISTINCT order_id)` |
| `avg_order_value` | numeric | `revenue / order_count` |

> **Note:** Revenue is gross only. Refunds (`order_item_refunds`) are excluded.

---

## Pipeline Stages

### 1. Extract (`extract.py`)

- Connects to MySQL using SQLAlchemy
- Reads `orders`, `order_items`, `products` into pandas DataFrames
- Full refresh on every run (no incremental logic)
- Returns DataFrames to the caller

### 2. Load (`load.py`)

- Connects to PostgreSQL using psycopg2 / pandas `to_sql`
- Truncates and reloads `raw.orders`, `raw.order_items`, `raw.products`
- Creates schemas and tables if they don't exist

### 3. Transform (`transform.py` + `sql/transform.sql`)

- Executes `sql/transform.sql` against the raw schema via psycopg2
- Drops and recreates `analytics.monthly_sales_summary`

**Transform SQL:**
```sql
CREATE TABLE analytics.monthly_sales_summary AS
SELECT
    DATE_TRUNC('month', oi.created_at)::date AS year_month,
    p.product_name,
    SUM(oi.price_usd)                        AS revenue,
    COUNT(DISTINCT oi.order_id)              AS order_count,
    SUM(oi.price_usd) / COUNT(DISTINCT oi.order_id) AS avg_order_value
FROM raw.order_items oi
JOIN raw.products p ON oi.product_id = p.product_id
GROUP BY 1, 2
ORDER BY 1, 2;
```

### 4. Entry Point (`run_pipeline.py`)

- Manually triggered: `python run_pipeline.py`
- Validates database connections before moving data
- Runs stages in sequence: extract → load → transform
- Wraps each stage in `try/except` — prints stage name on failure, exits with non-zero code

---

## Project Structure

```
basket-craft-pipeline/
├── .env                        # MySQL + PostgreSQL credentials (git-ignored)
├── run_pipeline.py             # Entry point
├── extract.py                  # MySQL → DataFrames
├── load.py                     # DataFrames → raw schema
├── transform.py                # Executes SQL transform
├── sql/
│   └── transform.sql           # Aggregation query
├── requirements.txt
├── docker-compose.yml          # PostgreSQL container definition
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-06-basket-craft-pipeline-design.md
```

---

## Error Handling

- Connections validated at startup; pipeline aborts if either database is unreachable
- Each stage (`extract`, `load`, `transform`) wrapped in `try/except` with a clear failure message
- If transform fails, raw tables remain intact — pipeline is re-runnable without full re-extract

---

## Error Handling (In Scope)

- Validate MySQL and PostgreSQL connections at startup; abort with a clear message if either is unreachable
- Wrap each stage (`extract`, `load`, `transform`) in `try/except`; print stage name and error, exit with non-zero code on failure
- Raw tables preserved on transform failure — pipeline is re-runnable from any stage

## Testing (In Scope)

- Unit tests for the transform logic using a small in-memory fixture loaded into a test PostgreSQL schema
- Smoke test for `run_pipeline.py` end-to-end against the real databases (verify `analytics.monthly_sales_summary` has rows after a run)
- Test framework: `pytest`

## Out of Scope

- Scheduling / automation (manual trigger only)
- Incremental / CDC loading
- Refund netting (gross revenue only)
