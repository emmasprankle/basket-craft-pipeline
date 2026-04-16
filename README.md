# Basket Craft ELT Pipeline

An ELT pipeline that extracts order data from a MySQL source database, loads it into PostgreSQL, and transforms it into a monthly sales analytics table.

## What it does

```
MySQL (source)
  orders, order_items, products
        ↓  extract + load
PostgreSQL: raw schema
  raw.orders / raw.order_items / raw.products
        ↓  transform (SQL)
PostgreSQL: analytics schema
  analytics.monthly_sales_summary
    - year_month
    - product_name
    - revenue
    - order_count
    - avg_order_value
```

The pipeline runs as a one-shot job: extract all rows from MySQL, load them into the `raw` schema (full replace), then build the analytics table from scratch.

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

Open `.env` and fill in the five `MYSQL_*` values with your source database credentials. The `PG_*` values are pre-filled for the Docker-managed PostgreSQL instance — leave them as-is.

```dotenv
MYSQL_HOST=<your host>
MYSQL_PORT=3306
MYSQL_USER=<your user>
MYSQL_PASSWORD=<your password>
MYSQL_DATABASE=<your database>

# Leave these as-is for Docker
PG_USER=pipeline
PG_PASSWORD=pipeline
PG_HOST=postgres
PG_PORT=5432
PG_DATABASE=basket_craft_dw
```

## Running the pipeline

### Via Docker (recommended)

```bash
docker compose down && docker compose up
```

This starts PostgreSQL, waits for it to be healthy, runs the full pipeline, and exits. Expected output:

```
pipeline-1  | === Basket Craft ELT Pipeline ===
pipeline-1  | [1/4] Validating database connections...
pipeline-1  |   Connections OK
pipeline-1  | [2/4] Extracting from MySQL...
pipeline-1  |   Extracted orders: N rows
pipeline-1  |   Extracted order_items: N rows
pipeline-1  |   Extracted products: N rows
pipeline-1  | [3/4] Loading into raw schema (PostgreSQL)...
pipeline-1  | [4/4] Transforming into analytics schema...
pipeline-1  | === Pipeline complete ===
pipeline-1 exited with code 0
```

### Locally

```bash
# Start PostgreSQL (PG_HOST must be set to localhost in .env for local runs)
docker compose up postgres -d

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
