#!/usr/bin/env python3
"""Compatibility launcher for the shared plugin synchronization tooling."""

from pathlib import Path

try:
    from cypherpoet_agent_skills_tooling.sync_plugins import (
        build_codex_manifest,
        main as tooling_main,
        sync,
        validate_codex_interface,
    )
except ModuleNotFoundError as error:
    if error.name != "cypherpoet_agent_skills_tooling":
        raise
    raise SystemExit(
        "repository tooling is not installed; run: "
        "python3 -m pip install -r requirements-tooling.txt"
    ) from error


def main() -> int:
    return tooling_main(default_root=Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    raise SystemExit(main())
