import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

PROJECT_ROOT = Path(__file__).parents[2]
PROJECT_NAME = "agentforge"


def _run_compose(
    *arguments: str, timeout: int = 180
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", "--project-name", PROJECT_NAME, *arguments],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=False,
        text=True,
        timeout=timeout,
    )


def _run_psql(statement: str) -> str:
    result = _run_compose(
        "exec",
        "-T",
        "postgres",
        "psql",
        "--no-psqlrc",
        "--set",
        "ON_ERROR_STOP=1",
        "--quiet",
        "--tuples-only",
        "--no-align",
        "--username",
        "agentforge",
        "--dbname",
        "agentforge",
        "--command",
        statement,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@pytest.mark.integration
def test_compose_configuration_renders() -> None:
    result = _run_compose("config", "--quiet")

    assert result.returncode == 0, result.stderr


@pytest.mark.integration
def test_postgres_has_vector_and_persists_data_across_restart() -> None:
    table = f"public.agentforge_compose_sentinel_{uuid4().hex}"
    started = _run_compose("up", "--detach", "--wait", timeout=600)
    assert started.returncode == 0, started.stderr
    table_created = False

    try:
        _run_psql("CREATE EXTENSION IF NOT EXISTS vector;")
        extension = _run_psql(
            "SELECT extname FROM pg_extension WHERE extname = 'vector';"
        )
        assert extension == "vector"

        _run_psql(
            f"CREATE TABLE {table} (sentinel_key text PRIMARY KEY, sentinel_value text NOT NULL);"
        )
        table_created = True
        _run_psql(
            f"INSERT INTO {table} VALUES ('persistence-check', 'sentinel-survived-restart') "
            "ON CONFLICT (sentinel_key) DO UPDATE "
            "SET sentinel_value = EXCLUDED.sentinel_value;"
        )

        restarted = _run_compose("restart", "postgres")
        assert restarted.returncode == 0, restarted.stderr

        ready = _run_compose("up", "--detach", "--wait")
        assert ready.returncode == 0, ready.stderr

        persisted_value = _run_psql(
            f"SELECT sentinel_value FROM {table} WHERE sentinel_key = 'persistence-check';"
        )
        assert persisted_value == "sentinel-survived-restart"
    finally:
        ready = _run_compose("up", "--detach", "--wait")
        assert ready.returncode == 0, ready.stderr
        if table_created:
            _run_psql(f"DROP TABLE {table};")
