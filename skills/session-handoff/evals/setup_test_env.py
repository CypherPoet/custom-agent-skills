#!/usr/bin/env python3
"""
Set up a test environment for evaluating the session-handoff skill.

Creates a mock project with:
- Git repository with commit history
- Sample source files (including the runtime-string-import pattern that
  fixture C depends on)
- Sample handoffs (fresh / stale / incomplete) using the new template format
- Hand-crafted fixture handoffs copied from evals/fixtures/

Usage:
    python setup_test_env.py [--path /tmp/handoff-eval-project]
    python setup_test_env.py --clean
"""

import argparse
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path


DEFAULT_TEST_PATH = "/tmp/handoff-eval-project"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def run_cmd(cmd: list[str], cwd: str = None) -> bool:
    try:
        subprocess.run(cmd, cwd=cwd, capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def create_test_project(base_path: str) -> Path:
    """Create a mock project structure."""
    path = Path(base_path)
    if path.exists():
        shutil.rmtree(path)

    (path / "src").mkdir(parents=True)
    (path / "tests").mkdir()
    (path / "config").mkdir()
    (path / "workers").mkdir()
    (path / "migrations").mkdir()

    (path / "README.md").write_text("""# Test Project

A sample project for testing the session-handoff skill.

## Features
- User authentication
- Queue-worker dispatch via runtime string imports
- Phased schema migrations
""")

    (path / "src" / "index.js").write_text("""// Main entry point
const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.send('Hello World');
});

module.exports = app;
""")

    # Fixture A references this file with a specific line number and regex.
    # Keep the regex at line 12 so the agent can navigate accurately —
    # the header comment + early return are sized to land it there.
    (path / "src" / "auth.js").write_text("""// Authentication module
//  Validates bearer-prefixed Authorization headers.
//  Uses HS256 + JWT_SECRET; line 12 is the bearer-prefix regex.

const jwt = require('jsonwebtoken');

function validateToken(token) {
    if (typeof token !== 'string') {
        return false;
    }

    return /^bearer\\s/i.test(token);
}

function generateToken(user) {
    return jwt.sign({ id: user.id }, process.env.JWT_SECRET);
}

const BEARER_PREFIX = /^bearer\\s/i;

module.exports = { validateToken, generateToken, BEARER_PREFIX };
""")

    (path / "src" / "database.js").write_text("""// Database connection
const mongoose = require('mongoose');

async function connect() {
    await mongoose.connect(process.env.DATABASE_URL);
}

module.exports = { connect };
""")

    # Fixture C depends on this file existing AND containing the
    # importlib.import_module pattern. Without that, the agent can't verify
    # the gotcha via grep, weakening the test.
    (path / "src" / "legacy_adapter.py").write_text("""\"\"\"Legacy queue adapter — looks unused per static analysis.

This module is loaded by workers/queue.py via importlib.import_module()
from a config-driven adapter name. Grep will not find that reference.
Do not delete this file without checking workers/queue.py:104 and the
queue config.
\"\"\"


def handle(message):
    return {"handled_by": "legacy_adapter", "payload": message}
""")

    (path / "workers" / "__init__.py").write_text("")
    (path / "workers" / "queue.py").write_text("""\"\"\"Queue worker that dispatches messages to adapters by runtime config.\"\"\"

import importlib
import yaml


def load_config(path="config/queue.yml"):
    with open(path) as f:
        return yaml.safe_load(f)


def dispatch(message, adapters):
    adapter_name = adapters.get(message["type"], "default_adapter")
    module = importlib.import_module(adapter_name)  # line 14 — see fixture
    return module.handle(message)


def run(message):
    config = load_config()
    return dispatch(message, config["adapters"])
""")

    # Note: fixture C references workers/queue.py:104, but the test project's
    # version is much shorter. The line number is a fixture detail intended
    # for verisimilitude; the agent should follow the gotcha guidance by name,
    # not by line number. If they grep for `import_module` they'll find it.

    (path / "config" / "queue.yml").write_text("""adapters:
  default: src.default_adapter
  legacy: src.legacy_adapter
""")

    (path / "migrations" / "plan.md").write_text("""# Migration plan

See the predecessor handoff for the canonical three-phase rollout.

Phases:
1. Add nullable `display_name` column + backfill (DONE)
2. Add NOT NULL constraint + index (NEXT)
3. Swap application code from `username` to `display_name` (LATER)
""")

    (path / "migrations" / "run.py").write_text("""\"\"\"Phased migration driver.

Usage: python migrations/run.py --phase=N [--dry-run]
\"\"\"

import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(f"[phase={args.phase}] dry_run={args.dry_run} — stub for tests")


if __name__ == "__main__":
    main()
""")

    (path / "tests" / "auth.test.js").write_text("""// Auth tests
const { validateToken } = require('../src/auth');

describe('Authentication', () => {
    test('accepts a well-formed bearer token', () => {
        expect(validateToken('bearer abc.def.ghi')).toBe(true);
    });

    test('rejects null and non-string inputs', () => {
        expect(validateToken(null)).toBe(false);
        expect(validateToken(42)).toBe(false);
    });

    test('rejects \"bearer\" with no token after it', () => {
        // Pinned by current failing test — fixture A's Next Action fixes this
        expect(validateToken('bearer')).toBe(false);
    });

    test('case-insensitive prefix', () => {
        expect(validateToken('Bearer abc')).toBe(true);
        expect(validateToken('BEARER abc')).toBe(true);
    });

    test('rejects entirely missing prefix', () => {
        expect(validateToken('abc.def.ghi')).toBe(false);
    });
});
""")

    (path / "config" / "default.json").write_text("""{
    "port": 3000,
    "database": {
        "host": "localhost",
        "name": "testdb"
    }
}
""")

    (path / "package.json").write_text("""{
    "name": "test-project",
    "version": "1.0.0",
    "main": "src/index.js",
    "scripts": {
        "start": "node src/index.js",
        "test": "jest"
    }
}
""")

    # Seeded for eval 10 (reference-not-restate). These artifacts exist so the
    # author has somewhere concrete to link instead of restating PRD/ADR content
    # in the handoff body.
    (path / "docs").mkdir(exist_ok=True)
    (path / "docs" / "auth-prd.md").write_text("""# Auth middleware PRD

## Requirements
- JWT validation on every request to `/api/*`.
- 1-hour access-token TTL.
- Refresh-token rotation on each `/auth/refresh` call.
- Role-based scopes: `user`, `admin`, `service`.

## Out of scope
- OAuth/SSO. Tracked separately.

## Acceptance
- `validateToken` returns true only for unexpired tokens signed with JWT_SECRET.
- Rate-limit shim caps unauthenticated requests at 30/min/IP.
""")

    (path / "docs" / "adrs").mkdir(exist_ok=True)
    (path / "docs" / "adrs" / "0042-jwt-over-sessions.md").write_text("""# ADR-0042: JWT over server-side sessions

## Status
Accepted

## Context
The API is stateless and scales horizontally behind a load balancer. Server-side
sessions would require sticky routing or a shared session store; both add ops
complexity.

## Decision
Use JWTs signed with HS256 + JWT_SECRET. Validate on every request.

## Consequences
- No session store needed.
- Token revocation requires a deny-list or short TTLs (we picked short TTLs +
  refresh tokens — see Auth PRD).
""")

    print(f"Created project structure at {path}")
    return path


def init_git_repo(path: Path):
    """Initialize git repo with commit history."""
    run_cmd(["git", "init"], cwd=str(path))
    run_cmd(["git", "config", "user.email", "test@example.com"], cwd=str(path))
    run_cmd(["git", "config", "user.name", "Test User"], cwd=str(path))

    run_cmd(["git", "add", "."], cwd=str(path))
    run_cmd(["git", "commit", "-m", "Initial commit: project setup"], cwd=str(path))

    commits = [
        ("src/auth.js", "// Added validation logic\n", "Add token validation"),
        ("src/database.js", "// Added connection pooling\n", "Implement connection pooling"),
        ("tests/auth.test.js", "// More tests\n", "Add authentication tests"),
        ("src/index.js", "// Added middleware\n", "Add auth middleware"),
        ("README.md", "\n## API Docs\n", "Update documentation"),
    ]
    for file, content, message in commits:
        file_path = path / file
        with open(file_path, "a") as f:
            f.write(content)
        run_cmd(["git", "add", file], cwd=str(path))
        run_cmd(["git", "commit", "-m", message], cwd=str(path))

    print(f"Initialized git repo with {len(commits) + 1} commits")


def create_sample_handoffs(path: Path):
    """Create three inline-generated handoffs (fresh / stale / incomplete) in
    the new template format. These cover the existing evals 1–6."""
    handoffs_dir = path / ".claude" / "handoffs"
    handoffs_dir.mkdir(parents=True)

    now = datetime.now(timezone.utc)

    # Fresh handoff — new format, ready to resume
    fresh_name = now.strftime("%Y-%m-%d-%H%M%S") + "-auth-implementation.md"
    fresh_content = f"""# 🤝 Handoff: JWT auth middleware — integration partial

> 🎯 **Next Action**: Wire `validateToken` into the Express middleware chain in `src/index.js` (insert before route handlers) and re-run `npm test`.

## 🧾 Session Metadata
- Created: {now.strftime("%Y-%m-%dT%H:%M:%SZ")}
- Branch: main

### Recent Commits (for context)
  - Add auth middleware
  - Add authentication tests
  - Implement connection pooling
  - Add token validation
  - Initial commit: project setup

## 🔗 Handoff Chain

- **Continues from**: None (fresh start)
- **Supersedes**: None

> This is the first handoff for this task.

## 📍 Current State Summary

Working on JWT-based authentication for the API. Token generation and basic validation are committed and tested. Middleware integration is the remaining piece — needs to slot into the Express app before route handlers fire.

## 💡 Important Context

The `validateToken` function lives in `src/auth.js`. It expects the raw `Authorization` header value (with `bearer` prefix). The JWT_SECRET env var must be set; without it, `generateToken` will throw.

## 🚧 Pending Work

### Immediate Next Steps

1. Wire middleware in `src/index.js`.
2. Add a refresh-token flow.
3. Write integration tests against the middleware.

### Blockers / Open Questions

- [ ] Token expiry: 1h vs 24h — needs product call.

### Deferred Items

- OAuth integration (future sprint).

## ⚠️ Constraints for Resuming Agent

### Potential Gotchas

- Don't forget JWT_SECRET — middleware will fail closed without it.
- Database connection must be established before middleware runs.

### 🧰 Skills to Use

| Skill | When to invoke | Why |
|-------|---------------|-----|
| (none specialized) | Standard Express middleware wiring | Direct edit suffices |

## 🧠 Codebase Understanding

### Critical Files

| File | Purpose | Relevance |
|------|---------|-----------|
| `src/auth.js` | Auth logic | Source of `validateToken` |
| `src/index.js` | App entry point | Where middleware gets wired |

## 🏁 Work Completed

- [x] JWT token generation
- [x] Basic validation function

### Files Modified

- `src/auth.js` — Added `validateToken`, `generateToken`

### Decisions Made

- **JWT over server-side sessions** — Stateless, scales better for API-only deployments.

## 🌐 Environment State

### Environment Variables

- JWT_SECRET
- DATABASE_URL

## 📚 Related Resources

- JWT spec: https://datatracker.ietf.org/doc/html/rfc7519
"""
    (handoffs_dir / fresh_name).write_text(fresh_content)

    # Stale handoff — older, intentionally older format-light for staleness checks
    old_date = now - timedelta(days=14)
    stale_name = old_date.strftime("%Y-%m-%d-%H%M%S") + "-database-setup.md"
    stale_content = f"""# 🤝 Handoff: Database setup — schema scaffolding

> 🎯 **Next Action**: Define the User schema in `src/models/user.js` (file does not exist yet — create it).

## 🧾 Session Metadata
- Created: {old_date.strftime("%Y-%m-%dT%H:%M:%SZ")}
- Branch: main

## 🔗 Handoff Chain

- **Continues from**: None (fresh start)
- **Supersedes**: None

## 📍 Current State Summary

Set up initial MongoDB connection in `src/database.js`. Schema not yet defined. Older session — significant codebase drift likely since this was written.

## 💡 Important Context

Using MongoDB Atlas (DATABASE_URL points there). Mongoose 7.x.

## 🚧 Pending Work

### Immediate Next Steps

1. Define User schema.
2. Add connection pooling.
3. Implement error handling for connection drops.

## ⚠️ Constraints for Resuming Agent

### Potential Gotchas

- Some files referenced may no longer exist (codebase has moved on since this handoff).
"""
    (handoffs_dir / stale_name).write_text(stale_content)

    # Incomplete handoff — new format, TODO-stuffed for the validator eval
    incomplete_name = (
        now.strftime("%Y-%m-%d-%H%M%S") + "-incomplete-test.md"
    )
    incomplete_content = f"""# 🤝 Handoff: [TASK_TITLE - replace this]

> 🎯 **Next Action**: [TODO: One sentence — the FIRST thing the resuming agent should do.]

## 🧾 Session Metadata
- Created: {now.strftime("%Y-%m-%dT%H:%M:%SZ")}
- Branch: main

## 📍 Current State Summary

[TODO: Write one paragraph describing what was being worked on]

## 💡 Important Context

[TODO: The MOST important section]

## 🚧 Pending Work

### Immediate Next Steps

1. [TODO: Most critical next action]
2. [TODO: Second priority]
"""
    (handoffs_dir / incomplete_name).write_text(incomplete_content)

    print(f"Created 3 inline-generated handoffs:")
    print(f"  - {fresh_name} (fresh, ready-to-resume)")
    print(f"  - {stale_name} (stale, 14 days old)")
    print(f"  - {incomplete_name} (incomplete, has TODOs)")


def copy_fixture_handoffs(path: Path) -> dict[str, str]:
    """Copy the hand-crafted fixture handoffs into the test project, with
    date-prefixed filenames so list_handoffs / staleness scripts handle them
    correctly. Returns a map of fixture_id -> seeded_filename so the eval
    prompts can reference them by relative path."""
    handoffs_dir = path / ".claude" / "handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    seeded: dict[str, str] = {}

    # Fixture A — clean resume
    fixture_a = FIXTURES_DIR / "clean-resume.md"
    if fixture_a.exists():
        dst_name = now.strftime("%Y-%m-%d-%H%M%S") + "-fixture-a-clean-resume.md"
        (handoffs_dir / dst_name).write_text(fixture_a.read_text())
        seeded["clean-resume"] = dst_name

    # Fixture B — chain. Predecessor must land first so the current handoff's
    # link resolves. We rewrite the PREDECESSOR_FILENAME placeholder in the
    # current handoff so the link points at the seeded predecessor.
    predecessor_src = FIXTURES_DIR / "chained-context-predecessor.md"
    current_src = FIXTURES_DIR / "chained-context.md"
    if predecessor_src.exists() and current_src.exists():
        predecessor_date = now - timedelta(days=4)
        predecessor_name = (
            predecessor_date.strftime("%Y-%m-%d-%H%M%S")
            + "-fixture-b-predecessor.md"
        )
        (handoffs_dir / predecessor_name).write_text(predecessor_src.read_text())

        current_name = (
            now.strftime("%Y-%m-%d-%H%M%S") + "-fixture-b-current.md"
        )
        current_content = current_src.read_text().replace(
            "PREDECESSOR_FILENAME", predecessor_name
        )
        (handoffs_dir / current_name).write_text(current_content)

        seeded["chained-predecessor"] = predecessor_name
        seeded["chained-current"] = current_name

    # Fixture C — gotcha
    fixture_c = FIXTURES_DIR / "gotcha-resume.md"
    if fixture_c.exists():
        dst_name = now.strftime("%Y-%m-%d-%H%M%S") + "-fixture-c-gotcha.md"
        (handoffs_dir / dst_name).write_text(fixture_c.read_text())
        seeded["gotcha-resume"] = dst_name

    if seeded:
        print(f"Copied {len(seeded)} fixture handoff(s):")
        for key, name in seeded.items():
            print(f"  - {key}: {name}")

    return seeded


def clean_test_env(path: str):
    if Path(path).exists():
        shutil.rmtree(path)
        print(f"Cleaned up test environment at {path}")
    else:
        print(f"No test environment found at {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Set up test environment for session-handoff skill"
    )
    parser.add_argument(
        "--path",
        default=DEFAULT_TEST_PATH,
        help=f"Path for test project (default: {DEFAULT_TEST_PATH})"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove test environment instead of creating"
    )

    args = parser.parse_args()

    if args.clean:
        clean_test_env(args.path)
        return

    path = create_test_project(args.path)
    init_git_repo(path)
    create_sample_handoffs(path)
    copy_fixture_handoffs(path)
    print(f"\nTest environment ready at: {args.path}")
    print(f"\nTo test, run:")
    print(f"  cd {args.path}")
    print(f"  # Then use Claude Code with the session-handoff skill")


if __name__ == "__main__":
    main()
