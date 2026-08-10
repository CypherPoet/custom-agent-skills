import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Fixture git repos must not inherit the developer's global/system git config —
# commit signing, hook paths, and templates break `git commit` on machines
# where signing is interactive, while CI runners stay green.
GIT_ENVIRONMENT = dict(
    os.environ,
    GIT_CONFIG_GLOBAL=os.devnull,
    GIT_CONFIG_SYSTEM=os.devnull,
)


def load_module(name, relative_path):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_directory(case):
    """A per-test TemporaryDirectory cleaned via addCleanup, so it is removed
    deterministically even when setUp fails partway."""
    temporary_directory = tempfile.TemporaryDirectory()
    case.addCleanup(temporary_directory.cleanup)
    return Path(temporary_directory.name)


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path, value):
    write(path, json.dumps(value, indent=2) + "\n")


def write_plugin_manifest(root, name, **fields):
    write_json(
        root / f"plugins/{name}/.claude-plugin/plugin.json",
        {"name": name, **fields},
    )


def write_plugin_registry(root, vendored_skills, dual_plugins, claude_only=None):
    write_json(
        root / "plugin-registry.json",
        {
            "vendored_skills": vendored_skills,
            "dual_harness_plugins": dual_plugins,
            "claude_only_plugins": claude_only or {},
        },
    )


def run(command, cwd, check=True, env=None):
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
        env=env,
    )


def git(repo, *args, check=True):
    return run(["git", *args], repo, check=check, env=GIT_ENVIRONMENT)


def initialize_git_repo(repo):
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Test User")
    git(repo, "config", "user.email", "test@example.com")


def commit_all(repo, message="fixture"):
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)
