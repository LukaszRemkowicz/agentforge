"""Command-line interface for AgentForge."""

import argparse
from collections.abc import Sequence
from importlib import metadata


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentctl")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {metadata.version('agentforge')}",
    )
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
