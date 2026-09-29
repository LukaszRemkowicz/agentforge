# AgentForge

AgentForge is a standalone Python foundation for durable, searchable knowledge for coding agents. Phase 1 provides the installable `agentctl` command and local PostgreSQL with pgvector. The current CLI supports only `--version`; coordination migration, ingestion, retrieval, and memory are out of scope for this phase.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- Docker with Docker Compose v2 (needed for the local database and integration tests)

## Set up the development environment

From the repository root:

```bash
uv sync --all-groups
uv run agentctl --version
```

The version command should print `agentctl 0.1.0`.

## Tests and quality checks

Run the fast unit suite without Docker:

```bash
uv run pytest -m "not integration"
```

Run the full suite, including tests that start and restart PostgreSQL through Compose:

```bash
uv run pytest
```

Run the configured lint, formatting, and type checks:

```bash
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

The repository's local pre-commit hooks can be run across tracked files with:

```bash
uvx pre-commit run --all-files
```

## Local PostgreSQL and pgvector

Compose starts one PostgreSQL 17 service using the pinned `pgvector/pgvector:0.8.6-pg17-bookworm` image. Port 5432 is bound to `127.0.0.1`; the database is reachable only from the local machine. The development defaults are database `agentforge`, user `agentforge`, and password `agentforge`. These values are for local development only.

Validate the Compose file and start PostgreSQL, waiting for its healthcheck:

```bash
docker compose config --quiet
docker compose up -d --wait
docker compose ps
```

Enable pgvector in the development database and confirm that PostgreSQL reports it:

```bash
docker compose exec -T postgres psql --username agentforge --dbname agentforge --command "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose exec -T postgres psql --username agentforge --dbname agentforge --command "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

### Verify data survives a restart

Create a small sentinel table and row, restart the service, then read the same value:

```bash
docker compose exec -T postgres psql --username agentforge --dbname agentforge --command "CREATE TABLE IF NOT EXISTS public.agentforge_persistence_check (sentinel_key text PRIMARY KEY, sentinel_value text NOT NULL);"
docker compose exec -T postgres psql --username agentforge --dbname agentforge --command "INSERT INTO public.agentforge_persistence_check VALUES ('restart-check', 'data-survived') ON CONFLICT (sentinel_key) DO UPDATE SET sentinel_value = EXCLUDED.sentinel_value;"
docker compose restart postgres
docker compose up -d --wait
docker compose exec -T postgres psql --username agentforge --dbname agentforge --command "SELECT sentinel_value FROM public.agentforge_persistence_check WHERE sentinel_key = 'restart-check';"
```

The final command should return `data-survived`. Remove the sentinel table when finished:

```bash
docker compose exec -T postgres psql --username agentforge --dbname agentforge --command "DROP TABLE public.agentforge_persistence_check;"
```

The integration test performs the same pgvector and persistence checks using a unique temporary table and removes that table after the test.

## Stop or remove the local database

Stop and remove the Compose container and network while keeping the named database volume:

```bash
docker compose down
```

> **Destructive: the following command deletes the PostgreSQL data volume.** Use it only when you intentionally want to permanently erase the local database contents.

```bash
docker compose down --volumes
```

## Install `agentctl` with uv

Install the project as a machine-level uv tool from the repository root, then invoke it from any directory:

```bash
uv tool install .
agentctl --version
```

The executable currently supports only `agentctl --version`.
