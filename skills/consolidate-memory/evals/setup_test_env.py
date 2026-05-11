#!/usr/bin/env python3
"""
Set up test fixtures for the consolidate-memory skill evals.

Materializes three fixture memory directories (with associated project
working directories) under /tmp/consolidate-memory-fixtures/, so the
evals in evals.json can run against them on any machine.

Usage:
    python setup_test_env.py            # write fixtures
    python setup_test_env.py --clean    # remove the fixtures dir
"""

import argparse
import shutil
from pathlib import Path

BASE = Path("/tmp/consolidate-memory-fixtures")


FIXTURES = {
    'healthy-small': {
        'memory/MEMORY.md': '# Memory Index\n\n- [feedback_clear_comments.md](feedback_clear_comments.md) — Default to no comments; explain why, not what\n- [user_role.md](user_role.md) — User is a backend engineer leading the data ingestion rewrite\n- [project_current_focus.md](project_current_focus.md) — Current focus is reducing p99 ingest latency before the May freeze\n- [reference_internal_docs.md](reference_internal_docs.md) — Architecture docs for the ingest pipeline live in Notion under "Ingest v3"\n',
        'memory/feedback_clear_comments.md': "---\nname: Default to no comments; explain why, not what\ndescription: Don't add comments that restate the code; only add one when the why is non-obvious\ntype: feedback\n---\n\nDefault to writing no comments. Add one only when the *why* is non-obvious — a hidden constraint, a workaround, behavior that would surprise a reader.\n\n**Why:** Comments that restate well-named code add noise and tend to drift out of sync.\n\n**How to apply:** Before adding a comment, check whether removing it would confuse a future reader. If not, skip it.\n",
        'memory/project_current_focus.md': '---\nname: Current focus — p99 ingest latency before May freeze\ndescription: Project is heads-down reducing p99 ingest latency before the 2026-05-15 release freeze\ntype: project\n---\n\nThe team is focused on reducing p99 ingest latency before the 2026-05-15 release freeze. The bar is "under 400ms at the 99th percentile sustained over a 24h window."\n\n**Why:** A downstream customer\'s SLA is renegotiating in early June and the current p99 (~720ms) won\'t pass their threshold.\n\n**How to apply:** Until 2026-05-15, scope choices on ingest code should bias toward latency wins over feature work. Flag any change that adds work to the hot path.\n',
        'memory/reference_internal_docs.md': '---\nname: Ingest v3 architecture docs in Notion\ndescription: Architecture docs for ingest v3 live in Notion under "Ingest v3" — use when explaining or questioning pipeline design\ntype: reference\n---\n\nArchitecture docs for the ingest v3 pipeline live in the team\'s Notion under the page "Ingest v3". This is the authoritative source for stage names, queue topology, and the rationale behind the current sharding strategy.\n\nWhen the user references "the design doc" in the context of ingest, this is what they mean.\n',
        'memory/user_role.md': '---\nname: Backend engineer leading the ingest rewrite\ndescription: User is a backend engineer with ~8 years experience leading the data ingestion v3 rewrite\ntype: user\n---\n\nThe user is a backend engineer (~8 years experience) currently leading the data ingestion v3 rewrite. Strong with Python and Postgres, less familiar with the frontend stack the same team also maintains.\n\nWhen discussing ingest internals, can go deep without hand-holding. When the conversation crosses into the React side of the codebase, frame explanations in terms of backend analogues.\n',
        'project/README.md': '# tiny-project\n\nA minimal project used as the working directory for the `consolidate-memory` healthy-small fixture.\n',
    },
    'historical-reference': {
        'memory/MEMORY.md': "# Memory Index\n\n- [reference_legacy_playwright_flag.md](reference_legacy_playwright_flag.md) — Historical: pre-2025-Q4 we used `playwright-cli --full-page` for screenshots\n- [feedback_use_snapshot_module.md](feedback_use_snapshot_module.md) — Use src/snapshot.py for screenshots; don't reach for external CLIs\n- [project_screenshot_migration.md](project_screenshot_migration.md) — Why we replaced playwright-cli with the in-house snapshot module in 2025-Q4\n",
        'memory/feedback_use_snapshot_module.md': '---\nname: Use src/snapshot.py for screenshots\ndescription: For any screenshot capture work in this project, call into src/snapshot.py — don\'t shell out to external CLIs\ntype: feedback\n---\n\nWhen adding or modifying screenshot capture logic, call into the existing `src/snapshot.py` module (specifically `capture_full_page()` or `capture_viewport()`). Don\'t shell out to external CLIs.\n\n**Why:** The in-house module handles the project\'s auth, cookies, and viewport sizing consistently. External tools have drifted in past PRs.\n\n**How to apply:** Any task that says "take a screenshot of X" or "capture Y page" should be implemented against `src/snapshot.py`.\n',
        'memory/project_screenshot_migration.md': "---\nname: 2025-Q4 screenshot pipeline migration\ndescription: In 2025-Q4 we replaced playwright-cli with the in-house src/snapshot.py module — driven by CI flakiness and viewport inconsistencies\ntype: project\n---\n\nIn Q4 2025, the screenshot pipeline migrated off `playwright-cli` and onto the in-house `src/snapshot.py` module.\n\n**Why:** `playwright-cli` was flaky in CI (~8% failure rate on the screenshot job), and viewport-size handling drifted between dev and CI environments. The in-house module pins both.\n\n**How to apply:** Any new screenshot work goes through `src/snapshot.py`. Don't reintroduce playwright-cli for this purpose. Old PRs that reference it predate the migration — see `reference_legacy_playwright_flag.md` for context.\n",
        'memory/reference_legacy_playwright_flag.md': '---\nname: Historical — pre-migration playwright-cli usage\ndescription: For context when reading pre-2025-Q4 PRs and scripts — we used `playwright-cli --full-page` before the snapshot module replaced it. Not current guidance\ntype: reference\n---\n\nBefore the 2025-Q4 screenshot migration, this project used `playwright-cli --full-page` to capture screenshots in CI. Anything you see in old PRs, scripts, or branch history that calls `playwright-cli` with `--full-page` is referring to that legacy flow.\n\nThis memory exists for context — it is **not** current guidance. The flag and tool are no longer used in this codebase. The current path is `src/snapshot.py` (see `feedback_use_snapshot_module.md`).\n\nKeep this around for archaeology: it makes old PRs intelligible.\n',
        'project/README.md': '# snapshot-tool\n\nInternal screenshot pipeline. Switched from `playwright-cli` to an in-house `snapshot` module in 2025-Q4 — see `src/snapshot.py`.\n',
        'project/src/snapshot.py': 'def capture_full_page(url: str, output_path: str) -> str:\n    """Capture a full-page screenshot. Replacement for the old playwright-cli flow."""\n    return output_path\n\n\ndef capture_viewport(url: str, output_path: str) -> str:\n    return output_path\n',
    },
    'mixed-issues': {
        'memory/MEMORY.md': "# Memory Index\n\n- [feedback_real_function.md](feedback_real_function.md) — Use parse_input() in src/main.py for user-input sanitization\n- [feedback_broken_ref.md](feedback_broken_ref.md) — Update the route middleware list when adding new routes\n- [feedback_test_isolation.md](feedback_test_isolation.md) — Database tests must not use mocks\n- [feedback_no_db_mocks.md](feedback_no_db_mocks.md) — Don't mock the DB in tests\n- [project_auth_rewrite.md](project_auth_rewrite.md) — Notes on the auth rewrite\n- [feedback_deleted_old_thing.md](feedback_deleted_old_thing.md) — Old guidance about avoiding cd chaining\n",
        'memory/feedback_broken_ref.md': '---\nname: Update route middleware list when adding routes\ndescription: When adding a new route, register it in the middleware list at src/auth/middleware.ts:registerRoutes()\ntype: feedback\n---\n\nWhen adding a new route to the widget service, you must also register it in the middleware list at `src/auth/middleware.ts` inside the `registerRoutes()` function. Forgetting this means the route bypasses auth.\n\n**Why:** Missed during the v2 migration — caused two endpoints to ship unauthenticated for a week.\n\n**How to apply:** Every route addition is a two-file change: the handler, plus an entry in `registerRoutes()`.\n',
        'memory/feedback_no_db_mocks.md': "---\nname: Don't mock the database in tests\ndescription: When testing code that hits the database, use the real DB — mocks have burned us before\ntype: feedback\n---\n\nDon't mock the database when writing tests. Use the real Postgres from the test compose stack instead.\n\n**Why:** Mocked database tests passed when the prod migration was actually broken — the mock didn't enforce the same constraints, so the divergence was invisible until deploy.\n\n**How to apply:** Any new test that touches the DB layer should connect to the real test database, not a mock or stub.\n",
        'memory/feedback_orphan.md': "---\nname: Prefer slugify over manual lowercasing\ndescription: When converting user-facing labels to URL slugs, use slugify() from src/utils.py instead of hand-rolling\ntype: feedback\n---\n\nFor URL slug conversion, use the existing `slugify()` helper in `src/utils.py`. Don't write a new one inline.\n\n**Why:** The helper handles trailing whitespace consistently with the rest of the pipeline. Hand-rolled versions have drifted in past PRs.\n\n**How to apply:** Any code that lowercases + dash-replaces user-facing text should call `slugify()` first.\n",
        'memory/feedback_real_function.md': '---\nname: Use parse_input for sanitization\ndescription: When sanitizing user input in the widget service, call parse_input() from src/main.py rather than rolling your own\ntype: feedback\n---\n\nWhen parsing user-supplied data in this project, call `parse_input()` in `src/main.py`. It applies the standard sanitization rules everything else expects.\n\n**Why:** A previous PR rolled its own `strip()+lower()` and missed an edge case around trailing whitespace in URLs, which caused a routing bug.\n\n**How to apply:** Any new code that accepts raw text from a request or CLI argument should pass it through `parse_input()` before doing anything else.\n',
        'memory/feedback_test_isolation.md': "---\nname: Database tests must not use mocks\ndescription: Integration tests against the database should hit a real database, not a mock\ntype: feedback\n---\n\nTests that touch the database should be run against a real Postgres instance, not a mocked client.\n\n**Why:** Last quarter, mocked tests passed cleanly but the prod migration failed because the mock didn't model the column constraints accurately. The team lost half a day debugging.\n\n**How to apply:** When writing or reviewing tests that interact with persistence, require they hit a real DB (the test docker-compose has one).\n",
        'memory/project_auth_rewrite.md': "---\nname: Notes on the auth rewrite\ndescription: Notes on the auth rewrite\ntype: project\n---\n\nThe ongoing auth middleware rewrite is being driven by legal/compliance, not by tech-debt cleanup. Specifically, legal flagged that the old middleware stored session tokens in a way that doesn't meet the new compliance requirements taking effect this year.\n\n**Why:** Compliance deadline — not engineering ergonomics. The rewrite would not be happening on this timeline otherwise.\n\n**How to apply:** Scope decisions on this work should favor compliance over developer ergonomics. If a cleaner-looking API conflicts with the compliance rules, choose the rules and document the rough edge.\n",
        'project/README.md': '# widget-service\n\nA small toy project used as the working directory for `consolidate-memory` skill fixtures. Has a `src/` with a couple of Python modules.\n',
        'project/src/main.py': 'def parse_input(raw: str) -> dict:\n    """Standard input sanitization entry point for the widget pipeline."""\n    return {"raw": raw.strip()}\n\n\ndef run_pipeline(payload: dict) -> dict:\n    return payload\n',
        'project/src/utils.py': 'def slugify(text: str) -> str:\n    return text.strip().lower().replace(" ", "-")\n',
    },
}


def write_fixtures() -> None:
    if BASE.exists():
        shutil.rmtree(BASE)
    for fixture_name, files in FIXTURES.items():
        for rel, content in files.items():
            target = BASE / fixture_name / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
    total = sum(len(v) for v in FIXTURES.values())
    print(f"Wrote {total} files under {BASE}")


def clean() -> None:
    if BASE.exists():
        shutil.rmtree(BASE)
        print(f"Removed {BASE}")
    else:
        print(f"{BASE} does not exist; nothing to clean")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="Remove the fixtures dir")
    args = parser.parse_args()
    if args.clean:
        clean()
    else:
        write_fixtures()


if __name__ == "__main__":
    main()
