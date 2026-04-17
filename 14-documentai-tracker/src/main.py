"""Orchestrator CLI: fetch -> diff -> write report artifacts -> save new baseline.

Side effects (Gmail draft, Google Doc push) are intentionally NOT performed by
this Python script. The scheduled Claude agent reads the artifacts this produces
and then calls the Gmail + Drive MCP tools itself. This keeps the Python code
free of MCP/auth plumbing and lets the Claude agent judge when an email is worth
sending.

Usage:
    python -m src.main                 # full run, writes artifacts, updates baseline
    python -m src.main --dry-run       # does not update the saved baseline
    python -m src.main --no-save       # alias for --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .diff import compute_changes
from .fetch import fetch_documentai_items
from .report import build_context_doc, build_email_body
from .state import load_snapshot, save_snapshot

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"


def _write_artifact(name: str, content: str) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    path = ARTIFACT_DIR / name
    path.write_text(content)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        "--no-save",
        action="store_true",
        dest="dry_run",
        help="Do not update the baseline snapshot; useful for testing.",
    )
    parser.add_argument(
        "--owner",
        default="navapbc",
        help="GitHub org that owns the project (default: navapbc).",
    )
    parser.add_argument(
        "--project-number",
        type=int,
        default=4,
        help="Project v2 number within the org (default: 4).",
    )
    args = parser.parse_args(argv)

    print(f"Fetching DocumentAI items from {args.owner}/projects/{args.project_number}...", file=sys.stderr)
    items = fetch_documentai_items(args.owner, args.project_number)
    print(f"  {len(items)} items matched DocumentAI filter.", file=sys.stderr)

    current = [it.to_dict() for it in items]
    previous = load_snapshot()
    first_run = previous is None

    changes = compute_changes(previous["items"] if previous else None, current)
    print(f"  {len(changes)} changes since last snapshot.", file=sys.stderr)

    subject, email_body = build_email_body(current, changes, first_run=first_run)
    context = build_context_doc(current)

    _write_artifact("email_subject.txt", subject + "\n")
    _write_artifact("email_body.md", email_body)
    _write_artifact("context.md", context)
    _write_artifact("changes.json", json.dumps([c.__dict__ for c in changes], indent=2, default=str))
    _write_artifact(
        "summary.json",
        json.dumps(
            {
                "first_run": first_run,
                "item_count": len(current),
                "change_count": len(changes),
                "has_email": bool(subject),
            },
            indent=2,
        ),
    )

    if args.dry_run:
        print("--dry-run set; baseline NOT updated.", file=sys.stderr)
    else:
        save_snapshot(current)
        print("Baseline snapshot updated.", file=sys.stderr)

    print(f"Artifacts written to {ARTIFACT_DIR}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
