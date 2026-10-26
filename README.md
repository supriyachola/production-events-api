# Production Events API

Task C backend (1-year scope): scanner-authenticated scan ingestion, ordered
piece timelines, manager-authenticated daily throughput, PostgreSQL persistence,
Alembic migrations, and a Compose stack with PostgreSQL and Redis. Celery,
WebSockets, and other stretch features are not included.

## Start the services

PowerShell:

```powershell
Copy-Item .env.example .env
# Edit .env and replace the development-only passwords and JWT secret.
docker compose up --build -d
docker compose ps
```

The API is at `http://localhost:8000`; Swagger UI is at
`http://localhost:8000/docs`. The API container applies all migrations and seeds
`piece-001`, `piece-002`, and `piece-003` before starting. PostgreSQL and Redis
are also exposed on ports 5432 and 6379 for local development. Compose reads
values from `.env`; the example values are for local assessment only. `.env`
files are ignored by Git and excluded from the Docker build context.

To stop the services, run `docker compose down`. To also delete the local
PostgreSQL volume and its data, run `docker compose down -v`.

## Migrations and seed data

Container startup runs these commands automatically. To run them explicitly:

```powershell
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seed
```

The initial migration creates the `pieces` and `scans` tables. A second
migration adds the `scans.piece_id` foreign key without changing the initial
migration, which may already have been applied to existing databases. SQLite
uses Alembic batch table recreation for this constraint; PostgreSQL uses
`ALTER TABLE ... ADD CONSTRAINT`. Existing orphan scan rows must be repaired
before upgrading, or the foreign-key migration will fail rather than discard
those rows.

To check that the current database schema matches the models:

```powershell
docker compose exec api alembic check
```

## Authentication and requests

Obtain a bearer token. Use the corresponding credentials from your `.env`:

```powershell
$managerToken = (Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/auth/token `
  -ContentType 'application/json' `
  -Body '{"username":"manager","password":"manager-dev-password"}').access_token
$scannerToken = (Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/auth/token `
  -ContentType 'application/json' `
  -Body '{"username":"scanner","password":"scanner-dev-password"}').access_token
```

`scanner` can submit `POST /scans`; `manager` can read
`GET /pieces/{piece_id}/timeline` and
`GET /reports/daily-throughput?date=YYYY-MM-DD`.

Submit a scan:

```powershell
$scan = @{
  scan_id = 'scan-001'
  piece_id = 'piece-001'
  stage = 'cutting'
  employee_id = 'employee-001'
  ts = '2026-10-26T10:00:00Z'
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/scans `
  -Headers @{ Authorization = "Bearer $scannerToken" } `
  -ContentType 'application/json' -Body $scan
$duplicate = Invoke-RestMethod -Method Post -Uri http://localhost:8000/scans `
  -Headers @{ Authorization = "Bearer $scannerToken" } `
  -ContentType 'application/json' -Body $scan
```

Stages must progress through `cutting`, `stitching`, `finishing`, `qc`, and
`packed`. Timestamps must include a timezone and are normalized to UTC. A
repeated `scan_id` with the same payload returns the original scan; a different
payload using that ID receives `409 Conflict`. The second command above repeats
the same scan and should return the original response with HTTP 200. Out-of-order
stages also return `409`; unknown pieces return `404`.

Read the timeline and the report:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/pieces/piece-001/timeline `
  -Headers @{ Authorization = "Bearer $managerToken" }
Invoke-RestMethod -Uri 'http://localhost:8000/reports/daily-throughput?date=2026-10-26' `
  -Headers @{ Authorization = "Bearer $managerToken" }
```

## Install dependencies and run tests

On Windows PowerShell, install the pinned dependencies into the project virtual
environment and run all tests:

```powershell
py -3.11 -m venv .venv-assessment
.\.venv-assessment\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-assessment\Scripts\python.exe -m pytest -q
```

The tests use an isolated SQLite database and do not require Docker or
PostgreSQL. To run migrations locally against the Compose PostgreSQL database,
set `DATABASE_URL` in your environment to that database's connection URL before
running `alembic upgrade head`.
