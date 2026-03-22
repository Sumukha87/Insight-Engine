#!/usr/bin/env python3
"""
Sync .claude/docs/progress.md → CLAUDE.md Phase Status section.

Run automatically via Claude Code PostToolUse hook whenever progress.md is edited.
Also safe to run manually: python scripts/sync_progress.py
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PROGRESS_FILE = REPO_ROOT / ".claude/docs/progress.md"
CLAUDE_MD = REPO_ROOT / ".claude/CLAUDE.md"

SECTION_START = "## Phase Status"
SECTION_END_MARKER = "## Coding Conventions"


def parse_progress(text: str) -> dict:
    # Current phase + status
    phase_match = re.search(r"\*\*(Phase \d+[^*]+)\*\*\nStatus: ([^\n]+)", text)
    current_phase = phase_match.group(1) if phase_match else "Unknown"
    current_status = phase_match.group(2) if phase_match else "Unknown"

    # Completed items (all [x] checkboxes)
    completed = re.findall(r"- \[x\] (.+)", text)

    # Open blockers from Blockers table (rows with | Issue | Open |)
    blocker_rows = re.findall(r"\|([^|]+)\|\s*Open\s*\|([^|]+)\|", text)
    blockers = [f"{row[0].strip()} — {row[1].strip()}" for row in blocker_rows]

    # Recent decisions — last 3 rows in the Decisions table
    decision_rows = re.findall(
        r"\|\s*(202\d-\d{2}-\d{2})\s*\|\s*([^|]+)\|\s*([^|]+)\|", text
    )
    decisions = [
        f"{d[0]}: {d[1].strip()} ({d[2].strip()})" for d in decision_rows[-3:]
    ]

    # Key numbers block
    numbers: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^- (.+?):\s*(.+)$", line)
        if m and m.group(1) in (
            "Papers ingested",
            "Entities extracted",
            "Graph nodes",
            "Graph edges",
            "GraphRAG query latency (p95)",
        ):
            numbers[m.group(1)] = m.group(2)

    return {
        "phase": current_phase,
        "status": current_status,
        "completed": completed,
        "blockers": blockers,
        "decisions": decisions,
        "numbers": numbers,
    }


def build_section(data: dict) -> str:
    lines = [
        "## Phase Status",
        "",
        f"> **Active:** {data['phase']} — Status: `{data['status']}`",
        "> Full checklist: @docs/progress.md | Architecture: @docs/architecture.md | Stack: @docs/stack.md",
        "",
        "### Completed (this phase)",
    ]

    if data["completed"]:
        for item in data["completed"]:
            lines.append(f"- [x] {item}")
    else:
        lines.append("- _(nothing completed yet)_")

    lines += ["", "### Open Blockers"]
    if data["blockers"]:
        for b in data["blockers"]:
            lines.append(f"- {b}")
    else:
        lines.append("- _(none)_")

    lines += ["", "### Recent Decisions"]
    if data["decisions"]:
        for d in data["decisions"]:
            lines.append(f"- {d}")
    else:
        lines.append("- _(none recorded)_")

    lines += ["", "### Key Numbers"]
    if data["numbers"]:
        for k, v in data["numbers"].items():
            lines.append(f"- {k}: {v}")
    else:
        lines.append("- _(no data yet)_")

    lines.append("")
    return "\n".join(lines)


def should_run(stdin_data: str | None) -> bool:
    """Return True if hook stdin indicates progress.md was touched, or if run directly."""
    if stdin_data is None:
        return True  # manual run — always proceed
    try:
        payload = json.loads(stdin_data)
        tool_input = payload.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        return "progress.md" in file_path
    except (json.JSONDecodeError, KeyError):
        return True  # can't parse — run anyway


def main() -> None:
    # When called from a hook, Claude Code pipes JSON to stdin
    stdin_data = None
    if not sys.stdin.isatty():
        stdin_data = sys.stdin.read()

    if not should_run(stdin_data):
        return  # edited file wasn't progress.md — nothing to do

    progress_text = PROGRESS_FILE.read_text()
    claude_md_text = CLAUDE_MD.read_text()

    data = parse_progress(progress_text)
    new_section = build_section(data)

    # Replace everything between SECTION_START and SECTION_END_MARKER
    pattern = re.compile(
        rf"^{re.escape(SECTION_START)}.*?(?=^{re.escape(SECTION_END_MARKER)})",
        re.MULTILINE | re.DOTALL,
    )

    if not pattern.search(claude_md_text):
        print(
            f"ERROR: Could not find '{SECTION_START}' ... '{SECTION_END_MARKER}' in CLAUDE.md",
            file=sys.stderr,
        )
        sys.exit(1)

    updated = pattern.sub(new_section + "\n", claude_md_text)

    if updated == claude_md_text:
        print("CLAUDE.md Phase Status already up to date.")
        return

    CLAUDE_MD.write_text(updated)
    print(f"CLAUDE.md updated — phase: {data['phase']}, status: {data['status']}")


if __name__ == "__main__":
    main()
