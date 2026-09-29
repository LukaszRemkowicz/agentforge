import importlib.metadata
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agentforge.cli import main


def test_agentctl_version_comes_from_distribution_metadata(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_version(distribution_name: str) -> str:
        assert distribution_name == "agentforge"
        return "9.8.7"

    monkeypatch.setattr(importlib.metadata, "version", fake_version)

    with pytest.raises(SystemExit) as error:
        main(["--version"])

    assert error.value.code == 0
    assert capsys.readouterr().out.strip() == "agentctl 9.8.7"


def _agentctl_path() -> Path:
    environment = Path(os.environ.get("VIRTUAL_ENV", sys.prefix))
    scripts_directory = "Scripts" if os.name == "nt" else "bin"
    executable_name = "agentctl.exe" if os.name == "nt" else "agentctl"
    executable = environment / scripts_directory / executable_name
    assert executable.is_file(), "agentctl console script is not installed"
    return executable


def test_agentctl_prints_its_version() -> None:
    result = subprocess.run(
        [str(_agentctl_path()), "--version"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "agentctl 0.1.0"
    assert result.stderr == ""


def test_agentctl_rejects_unknown_arguments() -> None:
    result = subprocess.run(
        [str(_agentctl_path()), "--unknown-argument"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode != 0
    assert "unrecognized arguments: --unknown-argument" in result.stderr
