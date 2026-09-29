# AgentForge Phase 1 Foundation Design

## Status and authority

This focused design records Phase 1 of the owner-supplied *AgentForge — Incremental Implementation Brief*. The owner explicitly instructed Codex to begin Phase 1 only. The pasted brief is the source of truth; the older `AGENTFORGE_RAG_IMPLEMENTATION_PLAN.md` remains background material and is not implementation authority.

## Goal

Create a reproducible standalone Python project that installs an `agentctl` executable and provides local PostgreSQL with pgvector through Docker Compose. This phase establishes foundations only.

## Scope

- Initialize this directory as a Git repository without removing existing research documents.
- Package AgentForge from `src/agentforge` with uv and a committed lockfile.
- Expose `agentctl --version` through a thin standard-library CLI.
- Configure pytest, Ruff, Pyright, and pre-commit.
- Provide one Docker Compose PostgreSQL service using a version-pinned pgvector image, a named volume, host-only port binding, and a healthcheck.
- Test package import, CLI version output, Compose rendering, database health, pgvector availability, and persistence across a container restart.
- Document setup, verification, and cleanup commands.

## Architecture and decisions

The package contains only `agentforge.__init__` and `agentforge.cli`. `pyproject.toml` owns the package version; `cli` reads installed distribution metadata and owns argument parsing and rendering. No application, domain, storage, ingestion, embedding, RAG, memory, or context packages are created yet.

The CLI uses `argparse` rather than adding a framework dependency for one option. Phase 1 does not add `system up`, `system down`, or `system status`: Compose remains the direct infrastructure interface, avoiding packaging and path-discovery behavior that is not yet required.

The Compose service uses `pgvector/pgvector:0.8.6-pg17-bookworm`, which pins both the pgvector and PostgreSQL major versions. It binds PostgreSQL to `127.0.0.1`, stores data in a named volume, and uses `pg_isready` for health. Credentials are local-development defaults and are documented as such.

Integration tests operate through Docker Compose and are marked `integration`. They verify the real service, extension creation, and persistence through `docker compose restart`; they do not create future application schemas. Unit tests do not require Docker.

## Error handling

`agentctl` delegates invalid arguments and help behavior to `argparse`. Infrastructure failures remain visible through Docker Compose exit codes and test failures. No wrapper obscures Compose diagnostics.

## Verification

- `uv sync --all-groups`
- `uv run pytest -m "not integration"`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `docker compose config --quiet`
- `docker compose up -d --wait`
- `uv run pytest -m integration`
- `docker compose restart postgres` followed by the persistence assertion
- `uv build`

## Explicit exclusions

No existing `agentctl` migration, project discovery, database schema, Alembic, RAG, document ingestion, embeddings, structured memory, context building, or speculative future package structure.
