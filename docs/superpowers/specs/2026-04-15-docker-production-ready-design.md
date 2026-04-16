# Design: Docker Production-Ready Pipeline

**Date:** 2026-04-15
**Goal:** Make the existing Basket Craft ELT pipeline runnable end-to-end with a single `docker compose up` command.

---

## Context

The pipeline already has:
- `extract.py` — reads `orders`, `order_items`, `products` from external MySQL
- `load.py` — writes raw tables to PostgreSQL
- `transform.py` + `sql/transform.sql` — builds `analytics.monthly_sales_summary`
- `run_pipeline.py` — orchestrates all four stages
- `docker-compose.yml` — PostgreSQL service only
- `requirements.txt` — core dependencies

MySQL is always an external database reached via environment variables. It is never containerized.

---

## Approach

**Option 1 selected:** Add a `pipeline` service to `docker-compose.yml` that builds from a new `Dockerfile`, waits for Postgres to be healthy, then runs `python run_pipeline.py` and exits.

---

## Files Changed

| File | Change |
|---|---|
| `Dockerfile` | New — builds the pipeline image |
| `docker-compose.yml` | Modified — adds healthcheck to `postgres`, adds `pipeline` service |
| `.env.example` | New — documents all required environment variables |

---

## Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "run_pipeline.py"]
```

- `python:3.12-slim` keeps the image small.
- Dependencies are installed before source is copied so Docker's layer cache avoids re-running `pip install` on every code change.

---

## docker-compose.yml Changes

Add a `healthcheck` to the existing `postgres` service and introduce a new `pipeline` service:

```yaml
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
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pipeline"]
      interval: 5s
      retries: 5

  pipeline:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
    env_file: .env
    restart: "no"

volumes:
  pgdata:
```

- `healthcheck` ensures Postgres is accepting connections before the pipeline starts.
- `depends_on: condition: service_healthy` blocks the pipeline container until Postgres passes its health check.
- `env_file: .env` injects all MySQL and Postgres credentials into the pipeline container.
- `restart: "no"` means the container exits cleanly after the pipeline finishes rather than restarting.

---

## .env.example

```dotenv
# MySQL (external source — fill in your credentials)
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_HOST=
MYSQL_PORT=3306
MYSQL_DATABASE=

# PostgreSQL (managed by Docker — use these values as-is when running via docker compose)
PG_USER=pipeline
PG_PASSWORD=pipeline
PG_HOST=postgres
PG_PORT=5432
PG_DATABASE=basket_craft_dw
```

- Postgres values are pre-filled to match the `docker-compose.yml` service definition.
- `PG_HOST=postgres` refers to Docker's internal service name, not `localhost`.
- MySQL values are intentionally left blank for the developer to supply.

---

## Developer Workflow

```bash
cp .env.example .env
# Fill in MYSQL_* values in .env
docker compose up
```

One command starts Postgres, waits for it to be healthy, runs the full ELT pipeline, and exits.

---

## Out of Scope

- Dependency locking (pip-compile / uv)
- Makefile targets
- Scheduling / cron
- MySQL containerization
