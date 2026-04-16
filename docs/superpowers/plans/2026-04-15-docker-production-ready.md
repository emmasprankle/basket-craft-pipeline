# Docker Production-Ready Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Basket Craft ELT pipeline runnable end-to-end with a single `docker compose up` command.

**Architecture:** Add a `Dockerfile` that builds the pipeline image from `python:3.12-slim`, update `docker-compose.yml` to add a health check to the existing `postgres` service and a new `pipeline` service that waits for Postgres to be healthy before running `run_pipeline.py`. A `.env.example` documents all required environment variables.

**Tech Stack:** Docker, Docker Compose v2, Python 3.12-slim, existing `requirements.txt`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `Dockerfile` | Builds the pipeline image |
| Modify | `docker-compose.yml` | Adds healthcheck + pipeline service |
| Create | `.env.example` | Documents all required env vars |

---

### Task 1: Create `.env.example`

**Files:**
- Create: `.env.example`

- [ ] **Step 1: Verify the env var names expected by `db.py`**

Run:
```bash
grep "os.environ" db.py
```
Expected output — confirms these exact keys are required:
```
MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE
PG_USER, PG_PASSWORD, PG_HOST, PG_PORT, PG_DATABASE
```

- [ ] **Step 2: Create `.env.example`**

Create `.env.example` with this exact content:
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

- [ ] **Step 3: Verify all 10 keys are present**

Run:
```bash
grep -c "=" .env.example
```
Expected: `10`

- [ ] **Step 4: Commit**

```bash
git add .env.example
git commit -m "chore: add .env.example with required environment variables"
```

---

### Task 2: Create `Dockerfile` and verify it builds

**Files:**
- Create: `Dockerfile`

- [ ] **Step 1: Create `Dockerfile`**

Create `Dockerfile` with this exact content:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "run_pipeline.py"]
```

- [ ] **Step 2: Build the image to verify it succeeds**

Run:
```bash
docker build -t basket-craft-pipeline .
```
Expected: build completes with `Successfully built` or `naming to docker.io/library/basket-craft-pipeline`. No errors.

- [ ] **Step 3: Verify the entrypoint is correct**

Run:
```bash
docker inspect basket-craft-pipeline --format '{{json .Config.Cmd}}'
```
Expected:
```
["python","run_pipeline.py"]
```

- [ ] **Step 4: Commit**

```bash
git add Dockerfile
git commit -m "feat: add Dockerfile for pipeline image"
```

---

### Task 3: Update `docker-compose.yml` with healthcheck and pipeline service

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Replace the full contents of `docker-compose.yml`**

The current file only has the `postgres` service and a `pgdata` volume. Replace it entirely with:

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

- [ ] **Step 2: Validate the compose file**

Run:
```bash
docker compose config
```
Expected: YAML printed back with no errors. Confirm both `postgres` and `pipeline` services appear, and `pipeline.depends_on.postgres.condition` is `service_healthy`.

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add pipeline service and postgres healthcheck to docker-compose"
```

---

### Task 4: Verify end-to-end workflow

**Files:** none — verification only

- [ ] **Step 1: Copy `.env.example` to `.env` and fill in MySQL credentials**

```bash
cp .env.example .env
# Open .env and fill in MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE
```

- [ ] **Step 2: Confirm `.env` is gitignored**

Run:
```bash
git check-ignore -v .env
```
Expected: `.gitignore:.env` — confirms `.env` will not be committed.

- [ ] **Step 3: Run the full stack**

Run:
```bash
docker compose up
```
Expected log sequence:
```
postgres    | ... database system is ready to accept connections
pipeline_1  | === Basket Craft ELT Pipeline ===
pipeline_1  | [1/4] Validating database connections...
pipeline_1  |   Connections OK
pipeline_1  | [2/4] Extracting from MySQL...
pipeline_1  | [3/4] Loading into raw schema (PostgreSQL)...
pipeline_1  | [4/4] Transforming into analytics schema...
pipeline_1  | === Pipeline complete ===
pipeline_1 exited with code 0
```

- [ ] **Step 4: Tear down**

```bash
docker compose down
```
Expected: containers stopped and removed. The `pgdata` volume persists (intentional).
