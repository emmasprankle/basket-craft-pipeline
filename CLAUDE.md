# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

Use a Python virtual environment to manage dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Common Commands

```bash
# Run the full ELT pipeline locally (requires .env with credentials)
python run_pipeline.py

# Run all tests
pytest

# Run a single test file
pytest tests/test_transform.py -v

# Run a single test
pytest tests/test_transform.py::test_transform_produces_correct_row_count -v

# Start PostgreSQL via Docker (required for tests and local pipeline runs)
docker compose up postgres -d

# Run the full stack end-to-end in Docker
docker compose down && docker compose up
```

## Architecture

This is a four-stage ELT pipeline: **Extract → Load → Transform**, orchestrated by `run_pipeline.py`.

```
MySQL (external source)
    ↓ extract.py          reads orders, order_items, products via pandas read_sql
    ↓ load.py             writes to PostgreSQL raw schema (full replace each run)
    ↓ transform.py        executes sql/transform.sql inside a transaction
PostgreSQL
    raw.orders / raw.order_items / raw.products   ← landing zone
    analytics.monthly_sales_summary               ← output table
```

**Key design decisions:**
- Each stage is a separate module (`extract.py`, `load.py`, `transform.py`) called in sequence by `run_pipeline.py`, which handles per-stage error reporting and `sys.exit(1)` on failure.
- The load step does a **full replace** on every run — no incremental logic.
- The transform step runs `sql/transform.sql` as a single transaction. If the output table has zero rows after the SQL runs, `transform.py` raises a `RuntimeError` to catch silent data failures.
- All database credentials are read from environment variables (via `python-dotenv`). `db.py` constructs both engines and exposes `validate_connections()` to do a `SELECT 1` ping before any work begins.

## Running Tests

Tests require a live PostgreSQL connection. Start Postgres first:

```bash
docker compose up postgres -d
```

Unit tests (`test_transform.py`, `test_extract.py`, `test_load.py`) create and tear down their own fixtures — `test_transform.py` drops and recreates `raw` and `analytics` schemas around each test for isolation. Smoke tests (`test_smoke.py`) run the full pipeline and assert against the real output table.

`pytest.ini` sets `pythonpath = .` so all imports resolve from the project root without installing the package.

## Docker

The pipeline runs in Docker via `docker compose up`. The `pipeline` service waits for the `postgres` service to pass its healthcheck (`pg_isready`) before starting.

**First-time setup:**
```bash
cp .env.example .env
# fill in MYSQL_* values — PG_* values are pre-filled for Docker
docker compose down && docker compose up
```

All credentials (both MySQL and PostgreSQL) come from `.env`. The `docker-compose.yml` uses `${PG_USER}` / `${PG_PASSWORD}` / `${PG_DATABASE}` substitution for the postgres service itself, and `env_file: .env` to inject all variables into the pipeline container.
