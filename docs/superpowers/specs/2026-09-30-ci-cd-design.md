# AgentForge CI/CD Design

## Goal

Add GitHub automation based on Registar while using AgentForge's actual Python 3.12, uv, Ruff, Pyright basic, pytest, Docker Compose, and static `pyproject.toml` version conventions.

## Workflows

- `ci-cd.yml` runs for pull requests, pushes to `main` and `dev`, and manual dispatch. It gates quality, unit tests, Docker-backed pgvector integration tests, package builds, dependency auditing, Trivy, `dev` to `main` version bumps, and PR status.
- `release.yml` creates a version tag from `[project].version` after a push to `main`. AgentForge has no deployment target, so release tagging is the only CD behavior.
- `branch-protection.yml` permits `dev`, `hotfix/*`, and `release/*` pull requests into `main`.
- Dependabot opens grouped monthly uv and GitHub Actions updates against `dev`.

Core quality and Docker integration jobs live in AgentForge because their commands are project-specific. Generic version, release, security, branch, and PR-status behavior reuses `LukaszRemkowicz/ci-cd` workflows, matching Registar.

## Documentation cleanup

Move `AGENTFORGE_RAG_IMPLEMENTATION_PLAN.md` to `docs/AGENTFORGE_RAG_IMPLEMENTATION_PLAN.md`. Delete the superseded `docs/research/agent-memory-market-evaluation.md`. Retain the separate LangGraph spike unless explicitly removed later.

## Verification

Validate YAML syntax, inspect workflow contracts, run AgentForge quality/unit/integration/build commands locally, and review the exact diff. Do not trigger a deployment because none exists.
