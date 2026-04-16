# Basket Craft ELT Pipeline

An ELT pipeline that extracts data from a MySQL source database, loads it into PostgreSQL, and transforms it into a monthly sales analytics table. PostgreSQL is available both as a local Docker container and as an AWS RDS instance pre-loaded with the full Basket Craft dataset.

## What it does

```
MySQL (source — 8 tables)
  orders, order_items, order_item_refunds, products,
  users, employees, website_sessions, website_pageviews
        ↓  extract + load
PostgreSQL: raw schema  (Docker or AWS RDS)
  raw.*  — all source tables loaded as-is
        ↓  transform (SQL)
PostgreSQL: analytics schema
  analytics.monthly_sales_summary
    - year_month
    - product_name
    - revenue
    - order_count
    - avg_order_value
```

The pipeline runs as a one-shot job: extract rows from MySQL, load them into the `raw` schema (full replace), then build the analytics table from scratch.

## AWS RDS Instance

An RDS PostgreSQL instance is provisioned with the full raw dataset already loaded (~1.77M rows across all 8 tables):

| Table | Rows |
|---|---:|
| `raw.website_pageviews` | 1,188,124 |
| `raw.website_sessions` | 472,871 |
| `raw.users` | 31,696 |
| `raw.orders` | 32,313 |
| `raw.order_items` | 40,025 |
| `raw.order_item_refunds` | 1,731 |
| `raw.employees` | 20 |
| `raw.products` | 4 |
| `analytics.monthly_sales_summary` | 94 |

**Endpoint:** `basket-craft-db.c7mcisii27xx.us-west-1.rds.amazonaws.com`  
**Port:** `5432` | **Database:** `basket_craft` | **Username:** `student`

To run the pipeline against RDS, set these values in `.env`:
```dotenv
PG_HOST=basket-craft-db.c7mcisii27xx.us-west-1.rds.amazonaws.com
PG_USER=student
PG_PASSWORD=<password>
PG_PORT=5432
PG_DATABASE=basket_craft
```
Then run `python run_pipeline.py` directly (not via `docker compose`, which would spin up a local Postgres unnecessarily).

## Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ and a virtual environment (for local development / tests)

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd basket-craft-pipeline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
```

Open `.env` and fill in the five `MYSQL_*` values. The `PG_*` values are pre-filled for the local Docker PostgreSQL instance — leave them as-is unless targeting RDS.

```dotenv
MYSQL_HOST=<your host>
MYSQL_PORT=3306
MYSQL_USER=<your user>
MYSQL_PASSWORD=<your password>
MYSQL_DATABASE=<your database>

# Pre-filled for Docker (change PG_HOST to RDS endpoint to target AWS)
PG_USER=pipeline
PG_PASSWORD=pipeline
PG_HOST=postgres
PG_PORT=5432
PG_DATABASE=basket_craft_dw
```

## Running the pipeline

### Via Docker (recommended for local)

```bash
docker compose down && docker compose up
```

This starts PostgreSQL, waits for it to be healthy, runs the full pipeline, and exits. Expected output:

```
pipeline-1  | === Basket Craft ELT Pipeline ===
pipeline-1  | [1/4] Validating database connections...
pipeline-1  |   Connections OK
pipeline-1  | [2/4] Extracting from MySQL...
pipeline-1  | [3/4] Loading into raw schema (PostgreSQL)...
pipeline-1  | [4/4] Transforming into analytics schema...
pipeline-1  | === Pipeline complete ===
pipeline-1 exited with code 0
```

### Against AWS RDS

Update `PG_*` values in `.env` to point at the RDS endpoint, then:

```bash
python run_pipeline.py
```

## Running tests

Tests require a running PostgreSQL instance:

```bash
docker compose up postgres -d
pytest
```

Run a specific test file:

```bash
pytest tests/test_transform.py -v
```

## Project structure

```
run_pipeline.py        # Orchestrator — runs all four stages in order
db.py                  # SQLAlchemy engine factory + connection validation
extract.py             # Reads orders, order_items, products from MySQL
load.py                # Writes DataFrames to PostgreSQL raw schema
transform.py           # Executes sql/transform.sql and validates output
sql/transform.sql      # DROP + CREATE TABLE AS SELECT for analytics table
tests/                 # Unit tests per module + end-to-end smoke tests
docker-compose.yml     # PostgreSQL service + pipeline service
Dockerfile             # Pipeline image (python:3.12-slim)
.env.example           # Credential template — copy to .env and fill in
```
