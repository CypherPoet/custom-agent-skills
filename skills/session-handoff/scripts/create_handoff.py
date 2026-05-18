#!/usr/bin/env python3
"""
Smart scaffold generator for handoff documents.

Reads the canonical layout from references/handoff-template.md, gathers
runtime context (git state, repo URL, open PR, session plan, prior handoff
chain), and substitutes the {{placeholders}} declared in that template.
There is no separate template body kept inside this script — the markdown
file is the single source of truth.

Usage:
    python create_handoff.py [task-slug] [--continues-from <previous-handoff>]
    python create_handoff.py "implementing-auth"
    python create_handoff.py "auth-part-2" --continues-from 2024-01-15-auth.md
    python create_handoff.py  # auto-generates slug from timestamp
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_cmd(cmd: list[str], cwd: str = None) -> tuple[bool, str]:
    """Run a command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10
        )
        return result.returncode == 0, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, ""


def get_git_info(project_path: str) -> dict:
    """Gather git information from the project."""
    info = {
        "is_git_repo": False,
        "branch": None,
        "repo_url": None,
        "pr_url": None,
        "recent_commits": [],
        "modified_files": [],
        "staged_files": [],
    }

    success, _ = run_cmd(["git", "rev-parse", "--git-dir"], cwd=project_path)
    if not success:
        return info

    info["is_git_repo"] = True

    success, branch = run_cmd(["git", "branch", "--show-current"], cwd=project_path)
    if success and branch:
        info["branch"] = branch

    # origin URL — best effort; missing remote is fine, just leaves the line empty.
    success, repo_url = run_cmd(["git", "remote", "get-url", "origin"], cwd=project_path)
    if success and repo_url:
        info["repo_url"] = repo_url

    # Open PR for current branch — best effort via `gh`. Skips silently when gh
    # is unavailable, the user isn't authenticated, or no PR is open.
    success, pr_url = run_cmd(
        ["gh", "pr", "view", "--json", "url", "--jq", ".url"],
        cwd=project_path
    )
    if success and pr_url:
        info["pr_url"] = pr_url

    success, log = run_cmd(
        ["git", "log", "--oneline", "-5", "--no-decorate"],
        cwd=project_path
    )
    if success and log:
        info["recent_commits"] = log.split("\n")

    success, modified = run_cmd(["git", "diff", "--name-only"], cwd=project_path)
    if success and modified:
        info["modified_files"] = modified.split("\n")

    success, staged = run_cmd(
        ["git", "diff", "--name-only", "--cached"],
        cwd=project_path
    )
    if success and staged:
        info["staged_files"] = staged.split("\n")

    return info


def find_session_plan(branch: str | None, project_path: str | None = None) -> Path | None:
    """Look for a Claude Code session plan tied to the current session.

    Plans live at ~/.claude/plans/<slug>.md. Claude Code derives the slug from
    the session context — usually it matches the git branch, but inside a
    worktree the slug typically matches the worktree directory basename and
    the branch carries a "worktree-" prefix.

    Check candidates in order, returning the first hit:
      1. The branch name as-is.
      2. The branch with a leading "worktree-" stripped.
      3. The project directory's basename.

    Returns None if nothing matches. We don't fuzzy-match further — a wrong
    plan reference in a handoff is worse than no reference.
    """
    plans_dir = Path.home() / ".claude" / "plans"
    if not plans_dir.exists():
        return None

    candidates: list[str] = []
    if branch:
        candidates.append(branch)
        if branch.startswith("worktree-"):
            candidates.append(branch[len("worktree-"):])
    if project_path:
        candidates.append(Path(project_path).name)

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        plan_path = plans_dir / f"{candidate}.md"
        if plan_path.exists():
            return plan_path

    return None


def find_previous_handoffs(project_path: str) -> list[dict]:
    """Find existing handoffs in the project."""
    handoffs_dir = Path(project_path) / ".claude" / "handoffs"
    if not handoffs_dir.exists():
        return []

    handoffs = []
    for filepath in handoffs_dir.glob("*.md"):
        try:
            content = filepath.read_text()
            # Strip an optional emoji prefix (e.g. `# 🤝 Handoff: foo`) before
            # the optional `Handoff:` literal so the captured title is just the
            # slug ("foo"), not the redundant emoji + "Handoff:" preamble.
            match = re.search(
                r'^#\s+(?:[^\s\w]+\s+)?(?:Handoff:\s*)?(.+)$',
                content,
                re.MULTILINE,
            )
            title = match.group(1).strip() if match else filepath.stem
        except Exception:
            title = filepath.stem

        date_match = re.match(r'(\d{4}-\d{2}-\d{2})-(\d{6})', filepath.name)
        if date_match:
            try:
                date = datetime.strptime(
                    f"{date_match.group(1)} {date_match.group(2)}",
                    "%Y-%m-%d %H%M%S"
                )
            except ValueError:
                date = None
        else:
            date = None

        handoffs.append({
            "filename": filepath.name,
            "path": str(filepath),
            "title": title,
            "date": date,
        })

    handoffs.sort(key=lambda x: x["date"] or datetime.min, reverse=True)
    return handoffs


def get_previous_handoff_info(project_path: str, continues_from: str = None) -> dict:
    """Get information about the previous handoff for chaining."""
    handoffs = find_previous_handoffs(project_path)

    if continues_from:
        for h in handoffs:
            if continues_from in h["filename"]:
                return {
                    "exists": True,
                    "filename": h["filename"],
                    "title": h["title"],
                }
        return {"exists": False, "filename": continues_from, "title": "Not found"}

    elif handoffs:
        most_recent = handoffs[0]
        return {
            "exists": True,
            "filename": most_recent["filename"],
            "title": most_recent["title"],
            "suggested": True,
        }

    return {"exists": False}


# The template body lives in references/handoff-template.md. We slice at the
# first H1 that starts a line ("# 🤝 Handoff:"), not the inline code reference
# to that same string in the file's own documentation header — hence the
# anchored regex with MULTILINE rather than a plain str.find().
TEMPLATE_BODY_MARKER = re.compile(r'^# 🤝 Handoff:', re.MULTILINE)


def load_template_body() -> str:
    """Read the canonical template body from the references markdown file."""
    template_path = Path(__file__).resolve().parent.parent / "references" / "handoff-template.md"
    content = template_path.read_text()
    match = TEMPLATE_BODY_MARKER.search(content)
    if not match:
        raise RuntimeError(
            f"Template body marker '# 🤝 Handoff:' not found at line start in "
            f"{template_path}. The reference template is malformed."
        )
    return content[match.start():]


def render_template(template_body: str, fields: dict[str, str]) -> str:
    """Substitute {{placeholder}} tokens. Simple replace loop — no escaping
    needed because the template body is fully under our control."""
    rendered = template_body
    for key, value in fields.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def build_commits_section(commits: list[str]) -> str:
    if not commits:
        return "  - [no recent commits or not a git repo]"
    return "\n".join(f"  - {c}" for c in commits)


def build_modified_files_section(modified: list[str], staged: list[str]) -> str:
    """Render modified files as bullets, not a table. The 3-column 'Files
    Modified' table in the previous template was almost always dropped in
    favor of prose during real handoff authoring; bullets match how the
    section actually gets used."""
    combined = list(dict.fromkeys(staged + modified))  # preserve order, dedupe
    if not combined:
        return "- [no modified files detected at scaffold time]"
    lines = [f"- `{f}` — [describe what changed and why]" for f in combined[:10]]
    if len(combined) > 10:
        lines.append(f"- ... and {len(combined) - 10} more files")
    return "\n".join(lines)


def build_chain_section(prev_handoff: dict) -> str:
    """Render the handoff-chain block. Always present (a 'None / fresh start'
    block is still useful provenance), so this returns a populated block in
    both cases. Includes a trailing blank line so the next placeholder lands
    cleanly."""
    if prev_handoff.get("exists"):
        block = f"""## 🔗 Handoff Chain

- **Continues from**: [{prev_handoff['filename']}](./{prev_handoff['filename']})
  - Previous title: {prev_handoff.get('title', 'Unknown')}
- **Supersedes**: [list any older handoffs this replaces, or "None"]

> Review the previous handoff for full context before filling this one.
"""
    else:
        block = """## 🔗 Handoff Chain

- **Continues from**: None (fresh start)
- **Supersedes**: None

> This is the first handoff for this task.
"""
    return block + "\n"


def build_plan_section(session_plan: Path | None) -> str:
    """Render the active-session-plan block when a plan exists. Link-only —
    the resuming agent reads the plan file directly, keeping the handoff
    lean and avoiding drift between two copies of the same plan."""
    if not session_plan:
        return ""
    plan_display = f"~/{session_plan.relative_to(Path.home())}"
    return f"""## 📋 Active Session Plan

- **File**: `{plan_display}`
- **Status**: [TODO: still authoritative? superseded? partially executed?]

> A live plan exists for this branch. The resuming agent should read it before starting work.

"""


def generate_handoff(
    project_path: str,
    slug: str = None,
    continues_from: str = None
) -> str:
    """Generate a handoff document with pre-filled metadata."""

    # The in-document timestamp uses ISO-8601 UTC with a Z suffix so it's
    # unambiguous across machines and parses cleanly in check_staleness.py.
    # The filename keeps a path-safe form without separators.
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    file_timestamp = now.strftime("%Y-%m-%d-%H%M%S")

    if not slug:
        slug = "handoff"
    slug = slug.lower().replace(" ", "-").replace("_", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")

    filename = f"{file_timestamp}-{slug}.md"

    handoffs_dir = Path(project_path) / ".claude" / "handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)
    filepath = handoffs_dir / filename

    git_info = get_git_info(project_path)
    prev_handoff = get_previous_handoff_info(project_path, continues_from)
    session_plan = find_session_plan(git_info.get("branch"), project_path)

    branch_line = git_info["branch"] if git_info["branch"] else "[not a git repo or detached HEAD]"
    repo_line = f"\n- Repo: {git_info['repo_url']}" if git_info.get("repo_url") else ""
    pr_line = f"\n- Source PR: {git_info['pr_url']}" if git_info.get("pr_url") else ""

    fields = {
        "timestamp": timestamp,
        "project_path": project_path,
        "branch_line": branch_line,
        "repo_line": repo_line,
        "pr_line": pr_line,
        "commits_section": build_commits_section(git_info["recent_commits"]),
        "chain_section": build_chain_section(prev_handoff),
        "plan_section": build_plan_section(session_plan),
        "modified_files_section": build_modified_files_section(
            git_info["modified_files"], git_info["staged_files"]
        ),
    }

    template_body = load_template_body()
    rendered = render_template(template_body, fields)

    filepath.write_text(rendered)
    return str(filepath)


def main():
    parser = argparse.ArgumentParser(
        description="Create a new handoff document with smart scaffolding"
    )
    parser.add_argument(
        "slug",
        nargs="?",
        default=None,
        help="Short identifier for the handoff (e.g., 'implementing-auth')"
    )
    parser.add_argument(
        "--continues-from",
        dest="continues_from",
        help="Filename of previous handoff this continues from"
    )

    args = parser.parse_args()
    project_path = os.getcwd()

    if not args.continues_from:
        prev_handoffs = find_previous_handoffs(project_path)
        if prev_handoffs:
            print(f"Found {len(prev_handoffs)} existing handoff(s).")
            print(f"Most recent: {prev_handoffs[0]['filename']}")
            print(f"Use --continues-from <filename> to link handoffs.\n")

    filepath = generate_handoff(project_path, args.slug, args.continues_from)

    print(f"Created handoff document: {filepath}")

    # Re-detect the plan to surface it in CLI output. Cheap — small set of
    # Path.exists() checks.
    git_info = get_git_info(project_path)
    session_plan = find_session_plan(git_info.get("branch"), project_path)
    if session_plan:
        plan_display = f"~/{session_plan.relative_to(Path.home())}"
        print(f"\nActive session plan detected: {plan_display}")
        print(f"  -> The handoff links to it under '📋 Active Session Plan'.")
        print(f"  -> Ask the user whether to keep that section before finalizing.")

    print(f"\nNext steps:")
    print(f"1. Open {filepath}")
    print(f"2. Fill in the 🎯 Next Action line at the top first — it's the most important field")
    print(f"3. Replace remaining [TODO: ...] placeholders, especially Important Context")
    print(f"4. Run: python validate_handoff.py {filepath}")

    return filepath


if __name__ == "__main__":
    main()
