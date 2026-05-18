#!/usr/bin/env python3
"""
Validate a handoff document for completeness and security.

Checks (in order of severity):
- Potential secrets (BLOCKING — handoffs get committed; secrets must not ship)
- Required sections present and populated
- 🎯 Next Action line populated (top-of-document load-bearing instruction)
- Remaining [TODO: ...] placeholders
- Referenced files exist on disk (advisory)
- Recommended sections missing (advisory)

Verdict rules:
- BLOCKED: secrets detected
- NEEDS_WORK: required section missing/incomplete, Next Action unfilled, or TODOs remain
- READY: everything required is in place

The earlier numeric quality score was removed — it nudged users toward filling
every section even when the content was filler, and didn't differentiate a
useful handoff from a complete one. Pass/fail/warn lines + a clear verdict
carry the same actionable information without the false precision.

Usage:
    python validate_handoff.py <handoff-file>
    python validate_handoff.py .claude/handoffs/2024-01-15-143022-auth.md
"""

import re
import sys
from pathlib import Path

# Secret detection patterns
SECRET_PATTERNS = [
    (r'["\']?[a-zA-Z_]*api[_-]?key["\']?\s*[:=]\s*["\'][^"\']{10,}["\']', "API key"),
    (r'["\']?[a-zA-Z_]*password["\']?\s*[:=]\s*["\'][^"\']+["\']', "Password"),
    (r'["\']?[a-zA-Z_]*secret["\']?\s*[:=]\s*["\'][^"\']{10,}["\']', "Secret"),
    (r'["\']?[a-zA-Z_]*token["\']?\s*[:=]\s*["\'][^"\']{20,}["\']', "Token"),
    (r'["\']?[a-zA-Z_]*private[_-]?key["\']?\s*[:=]', "Private key"),
    (r'-----BEGIN [A-Z]+ PRIVATE KEY-----', "PEM private key"),
    (r'mongodb(\+srv)?://[^/\s]+:[^@\s]+@', "MongoDB connection string with password"),
    (r'postgres://[^/\s]+:[^@\s]+@', "PostgreSQL connection string with password"),
    (r'mysql://[^/\s]+:[^@\s]+@', "MySQL connection string with password"),
    (r'Bearer\s+[a-zA-Z0-9_\-\.]+', "Bearer token"),
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub personal access token"),
    (r'sk-[a-zA-Z0-9]{48}', "OpenAI API key"),
    (r'xox[baprs]-[a-zA-Z0-9-]+', "Slack token"),
]

# Required sections — missing or TODO-ridden means NEEDS_WORK.
REQUIRED_SECTIONS = [
    "Current State Summary",
    "Important Context",
    "Immediate Next Steps",
]

# Recommended sections — missing means an [INFO] line, doesn't block readiness.
# Trimmed from the previous seven entries: dropped Architecture Overview (often
# "unchanged" filler), Files Modified (auto-prefilled, low rationale signal),
# and Assumptions Made (folded into Important Context in the new template).
RECOMMENDED_SECTIONS = [
    "Critical Files",
    "Decisions Made",
    "Potential Gotchas",
    "Skills to Use",
]


def check_todos(content: str) -> tuple[bool, list[str]]:
    """Check for remaining TODO placeholders."""
    todos = re.findall(r'\[TODO:[^\]]*\]', content)
    return len(todos) == 0, todos


def check_next_action(content: str) -> tuple[bool, str]:
    """Check the 🎯 Next Action blockquote line at the top of the document.

    Lives as `> 🎯 **Next Action**: <text>` rather than a `## Heading`, so the
    section-matching regex below can't catch it. Dedicated check keeps the
    intent clear: this single line is the most load-bearing field in a
    handoff, and an empty/TODO one fails the handoff regardless of what's
    further down.
    """
    match = re.search(
        r'^>\s*(?:[^\s\w]+\s+)?\*\*Next Action\*\*\s*:\s*(.+?)$',
        content,
        re.MULTILINE,
    )
    if not match:
        return False, "missing"
    value = match.group(1).strip()
    if value.startswith("[TODO") or not value:
        return False, "unfilled (still has [TODO: ...] placeholder)"
    return True, value


def check_required_sections(content: str) -> tuple[bool, list[str]]:
    """Check that required sections exist and have content."""
    missing = []
    for section in REQUIRED_SECTIONS:
        # Match `## Name` and `## 🧠 Name` alike — the optional non-word run
        # absorbs an emoji prefix without pulling in the section's own letters.
        pattern = rf'(?:^|\n)#{{1,6}}\s*(?:[^\s\w]+\s+)?{re.escape(section)}'
        match = re.search(pattern, content, re.IGNORECASE)
        if not match:
            missing.append(f"{section} (missing)")
        else:
            section_start = match.end()
            next_section = re.search(r'\n#{1,6}\s+', content[section_start:])
            section_end = section_start + next_section.start() if next_section else len(content)
            section_content = content[section_start:section_end].strip()

            if '[TODO' in section_content:
                missing.append(f"{section} (incomplete — has [TODO: ...])")

    return len(missing) == 0, missing


def check_recommended_sections(content: str) -> list[str]:
    """Check which recommended sections are missing."""
    missing = []
    for section in RECOMMENDED_SECTIONS:
        pattern = rf'(?:^|\n)#{{1,6}}\s*(?:[^\s\w]+\s+)?{re.escape(section)}'
        if not re.search(pattern, content, re.IGNORECASE):
            missing.append(section)
    return missing


def scan_for_secrets(content: str) -> list[tuple[str, str]]:
    """Scan content for potential secrets."""
    findings = []
    for pattern, description in SECRET_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            findings.append((description, f"Found {len(matches)} potential match(es)"))
    return findings


def check_file_references(content: str, base_path: str) -> tuple[list[str], list[str]]:
    """Check if referenced files exist."""
    patterns = [
        r'\|\s*([a-zA-Z0-9_\-./]+\.[a-zA-Z]+)\s*\|',  # Table cells
        r'`([a-zA-Z0-9_\-./]+\.[a-zA-Z]+(?::\d+)?)`',  # Inline code
        r'(?:^|\s)([a-zA-Z0-9_\-./]+\.[a-zA-Z]+:\d+)',  # With line numbers
    ]

    found_files = set()
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            filepath = match.split(':')[0]
            if filepath and not filepath.startswith('http') and '/' in filepath:
                found_files.add(filepath)

    existing = []
    missing = []
    for filepath in found_files:
        full_path = Path(base_path) / filepath
        if full_path.exists():
            existing.append(filepath)
        else:
            missing.append(filepath)

    return existing, missing


def validate_handoff(filepath: str) -> dict:
    """Run all validations on a handoff file."""
    path = Path(filepath)
    if not path.exists():
        return {"error": f"File not found: {filepath}"}

    content = path.read_text()
    base_path = path.parent.parent.parent  # Up from .claude/handoffs/

    todos_clear, remaining_todos = check_todos(content)
    next_action_filled, next_action_value = check_next_action(content)
    required_complete, missing_required = check_required_sections(content)
    missing_recommended = check_recommended_sections(content)
    secrets_found = scan_for_secrets(content)
    existing_files, missing_files = check_file_references(content, str(base_path))

    # Verdict: severity-ordered. Secrets dominate (commits would leak them);
    # required-section gaps and TODOs both block readiness without blocking
    # commits; recommended-section absence is purely advisory.
    if secrets_found:
        verdict = "BLOCKED"
        verdict_reason = "Remove detected secrets before handoff"
    elif not next_action_filled:
        verdict = "NEEDS_WORK"
        verdict_reason = f"🎯 Next Action is {next_action_value}"
    elif not required_complete:
        verdict = "NEEDS_WORK"
        verdict_reason = f"Required section incomplete: {missing_required[0]}"
    elif not todos_clear:
        verdict = "NEEDS_WORK"
        verdict_reason = f"{len(remaining_todos)} TODO placeholder(s) remain"
    else:
        verdict = "READY"
        verdict_reason = "Handoff is complete"

    return {
        "filepath": str(path),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "todos_clear": todos_clear,
        "remaining_todos": remaining_todos[:5],
        "todo_count": len(remaining_todos),
        "next_action_filled": next_action_filled,
        "next_action_value": next_action_value,
        "required_complete": required_complete,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "secrets_found": secrets_found,
        "files_verified": len(existing_files),
        "files_missing": missing_files[:5],
    }


def print_report(result: dict) -> bool:
    """Print a structured validation report. Returns True if READY."""
    if "error" in result:
        print(f"Error: {result['error']}")
        return False

    print(f"\n{'='*60}")
    print("Handoff Validation Report")
    print(f"{'='*60}")
    print(f"File: {result['filepath']}\n")

    print("CHECKS")
    print("-" * 6)

    if result["secrets_found"]:
        for secret_type, detail in result["secrets_found"]:
            print(f"[FAIL]  Secret detected — {secret_type}: {detail}")
    else:
        print("[PASS]  No potential secrets detected")

    if result["next_action_filled"]:
        snippet = result["next_action_value"]
        if len(snippet) > 70:
            snippet = snippet[:67] + "..."
        print(f"[PASS]  🎯 Next Action filled: \"{snippet}\"")
    else:
        print(f"[FAIL]  🎯 Next Action is {result['next_action_value']}")

    if result["required_complete"]:
        print(f"[PASS]  Required sections present ({', '.join(REQUIRED_SECTIONS)})")
    else:
        for section in result["missing_required"]:
            print(f"[FAIL]  Required section: {section}")

    if result["todos_clear"]:
        print("[PASS]  No TODO placeholders remaining")
    else:
        print(f"[FAIL]  {result['todo_count']} TODO placeholder(s) remain:")
        for todo in result["remaining_todos"]:
            display = todo if len(todo) <= 60 else todo[:57] + "..."
            print(f"        - {display}")

    if result["files_missing"]:
        print(f"[WARN]  {len(result['files_missing'])} referenced file(s) not found on disk:")
        for f in result["files_missing"]:
            print(f"        - {f}")
    elif result["files_verified"]:
        print(f"[INFO]  {result['files_verified']} file reference(s) verified")

    if result["missing_recommended"]:
        print(f"[INFO]  Recommended sections missing (consider adding):")
        for section in result["missing_recommended"]:
            print(f"        - {section}")

    print(f"\nVERDICT")
    print("-" * 7)
    print(f"{result['verdict']} — {result['verdict_reason']}")
    print(f"{'='*60}")

    return result["verdict"] == "READY"


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_handoff.py <handoff-file>")
        print("Example: python validate_handoff.py .claude/handoffs/2024-01-15-auth.md")
        sys.exit(1)

    filepath = sys.argv[1]
    result = validate_handoff(filepath)
    ready = print_report(result)
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
