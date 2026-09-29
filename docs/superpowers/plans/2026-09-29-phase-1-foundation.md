# AgentForge Phase 1 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create an installable, quality-checked AgentForge Python skeleton with a minimal `agentctl --version` command and verified local PostgreSQL/pgvector infrastructure.

**Architecture:** Keep the project version in `pyproject.toml` and the package to a thin `argparse` entry point that reads installed distribution metadata. Treat Docker Compose as the infrastructure interface, with tests split between fast package/CLI behavior and real Compose/PostgreSQL integration behavior.

**Tech Stack:** Python 3.12+, uv, pytest, Ruff, Pyright, pre-commit, Docker Compose, PostgreSQL 17, pgvector 0.8.6.

**Spec:** `docs/superpowers/specs/2026-09-29-phase-1-foundation-design.md`

## Global Constraints

- Implement Phase 1 only; do not migrate the existing Registar `agentctl`.
- Do not implement RAG, ingestion, embeddings, memory, context, project discovery, or application schemas.
- Use a `src/` package layout and expose the executable as `agentctl`.
- Use `compose.yaml`, a version-pinned pgvector image, a persistent named volume, a healthcheck, and a localhost-only port binding.
- Keep CLI behavior thin and avoid duplicating Docker Compose orchestration.
- Preserve the existing research and architecture documents.
- In the shared checkout, only the delegated implementer edits; the coordinator and reviewers remain read-only.

## Review Focus

- A wheel installed outside the repository must still expose `agentctl --version` without relying on the working directory.
- Invalid CLI arguments must return a nonzero status through standard `argparse` behavior.
- Compose interpolation must not require an uncommitted `.env` file for validation or startup.
- The PostgreSQL readiness probe must test the configured database and user, not merely process existence.
- Persistence verification must cross an actual container restart and compare a previously written sentinel value.

---

### Task 1: Git, packaging, and CLI foundation (`delegated`)

**Dependencies:** None.

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `uv.lock`
- Create: `src/agentforge/__init__.py`
- Create: `src/agentforge/cli.py`
- Create: `tests/unit/test_cli.py`

**Interfaces:**
- Reads the version from installed `agentforge` distribution metadata.
- Produces: `agentforge.cli.main(argv: Sequence[str] | None = None) -> int`
- Produces: the `agentctl` console script.

- [ ] **Step 1: Initialize Git and add ignores for Python, uv, editor, macOS, test, and local environment artifacts without deleting existing files.**

- [ ] **Step 2: Write failing unit tests for invoking `agentctl --version` and rejecting an unknown argument.**

- [ ] **Step 3: Run the focused tests and confirm they fail because the package/entry point does not exist.**

- [ ] **Step 4: Add the minimal package, `argparse` CLI, package metadata, pytest marker configuration, and development dependency groups. Generate `uv.lock`.**

- [ ] **Step 5: Run `uv sync --all-groups` and the unit tests; confirm all pass.**

- [ ] **Step 6: Build the wheel, install it into a temporary isolated uv environment, and verify `agentctl --version` from outside the repository.**

- [ ] **Step 7: Commit the task with a focused conventional commit.**

### Task 2: Quality tooling and local infrastructure (`delegated`)

**Dependencies:** Task 1 package metadata and lockfile.

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Create: `.pre-commit-config.yaml`
- Create: `compose.yaml`
- Create: `tests/integration/test_compose.py`

**Interfaces:**
- Consumes: pytest configuration from Task 1.
- Produces: Compose project `agentforge`, service `postgres`, named volume `postgres_data`, and integration marker `integration`.

- [ ] **Step 1: Write integration tests that render the Compose configuration, start the real service, wait for health, enable/detect `vector`, persist a sentinel table row, restart the service, and read the same sentinel.**

- [ ] **Step 2: Run the Compose test and confirm it fails because `compose.yaml` does not exist.**

- [ ] **Step 3: Add `compose.yaml` using `pgvector/pgvector:0.8.6-pg17-bookworm`, deterministic service/container naming, localhost binding, a named volume, local development credentials, and `pg_isready` healthcheck.**

- [ ] **Step 4: Add Pyright, Ruff lint/format, and pre-commit configuration without introducing product dependencies.**

- [ ] **Step 5: Run Compose validation and the real integration test; confirm pgvector and restart persistence pass.**

- [ ] **Step 6: Run unit tests, Ruff check, Ruff format check, and Pyright; correct only Phase 1 issues.**

- [ ] **Step 7: Commit the task with a focused conventional commit.**

### Task 3: Documentation and Phase 1 verification (`delegated`)

**Dependencies:** Tasks 1 and 2.

**Files:**
- Create: `README.md`
- Add unchanged to Git: `AGENTFORGE_RAG_IMPLEMENTATION_PLAN.md`
- Add unchanged to Git: `docs/research/agent-memory-market-evaluation.md`
- Add unchanged to Git: `docs/research/spikes/langgraph_store_spike.py`
- Add to Git: `docs/superpowers/specs/2026-09-29-phase-1-foundation-design.md`
- Add to Git: `docs/superpowers/plans/2026-09-29-phase-1-foundation.md`
- Modify only if verification exposes a Phase 1 defect: files from Tasks 1–2.

**Interfaces:**
- Consumes: all Phase 1 commands and configuration.
- Produces: copy-pasteable setup, quality, Compose, pgvector, persistence, teardown, and `uv tool install .` instructions.

- [ ] **Step 1: Write README instructions for prerequisites, `uv sync`, CLI use, quality checks, Compose lifecycle, pgvector inspection, persistence verification, cleanup, and machine-level installation. Clearly label destructive volume removal. Track the preserved research documents and this phase's spec/plan unchanged.**

- [ ] **Step 2: Execute the README commands that are safe and non-destructive, including a real `uv tool install` into a temporary tool directory.**

- [ ] **Step 3: Run the full unit and integration suite, Ruff checks, Pyright, Compose validation, and wheel build.**

- [ ] **Step 4: Inspect the exact repository diff and self-review against the Phase 1 exclusions and architecture checklist.**

- [ ] **Step 5: Commit documentation or verification-driven corrections with a focused conventional commit.**
