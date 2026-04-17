"""Build the PM-oriented email and Claude-context markdown from the fetched items."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from .diff import Change

def _is_epic(item: dict[str, Any]) -> bool:
    """An item is an epic when GitHub's native Issue Type == "Epic"."""
    return (item.get("issue_type") or "").lower() == "epic"


def _epic_progress(epic: dict[str, Any]) -> tuple[int, int, int]:
    """Return (done, total, percent) from GitHub's own subIssuesSummary."""
    total = epic.get("sub_issues_total") or 0
    done = epic.get("sub_issues_completed") or 0
    percent = epic.get("sub_issues_percent") or 0
    return done, total, percent


def _group_by_epic(items: list[dict[str, Any]]) -> dict[str | None, list[dict[str, Any]]]:
    grouped: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        key = item.get("parent_title") if item.get("parent_number") else None
        grouped[key].append(item)
    return grouped


def _item_line(item: dict[str, Any]) -> str:
    fields = item.get("fields") or {}
    status = fields.get("Status") or "—"
    priority = fields.get("Priority") or ""
    size = fields.get("Size") or ""
    assignees = ", ".join(item.get("assignees") or []) or "unassigned"
    ref = f"{item.get('repo')}#{item.get('number')}" if item.get("repo") else item.get("title", "")
    tags = " ".join(filter(None, [f"[{status}]", f"({priority})" if priority else "", f"<{size}>" if size else ""]))
    return f"- {ref} {tags} — {item.get('title')} — {assignees}"


def build_email_body(
    items: list[dict[str, Any]],
    changes: list[Change],
    first_run: bool,
) -> tuple[str, str]:
    """Return (subject, body_markdown) for the PM email.

    When there are no changes after the first run, returns subject/body=("", "")
    so the orchestrator can decide to skip the draft.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if first_run:
        subject = f"[DocumentAI tracker] initial baseline — {today}"
    elif changes:
        completed = [c for c in changes if c.kind == "closed"]
        if completed:
            titles = ", ".join(c.title for c in completed[:3])
            more = f" (+{len(completed) - 3} more)" if len(completed) > 3 else ""
            subject = f"[DocumentAI] {len(completed)} completed: {titles}{more}"
        else:
            subject = f"[DocumentAI] {len(changes)} updates — {today}"
    else:
        return "", ""

    lines: list[str] = []
    lines.append(f"# DocumentAI tracker — {today}\n")

    if first_run:
        lines.append("_First run — this is the baseline. Future emails will highlight changes._\n")
    else:
        lines.append("## What changed since the last run\n")
        by_kind: dict[str, list[Change]] = defaultdict(list)
        for c in changes:
            by_kind[c.kind].append(c)
        order = [
            ("closed", "Completed"),
            ("new", "Newly added"),
            ("reopened", "Reopened"),
            ("field", "Field changes"),
            ("assignees", "Assignee changes"),
        ]
        for kind, heading in order:
            chunk = by_kind.get(kind) or []
            if not chunk:
                continue
            lines.append(f"### {heading} ({len(chunk)})")
            for c in chunk:
                lines.append(f"- {c.as_line()}")
                if c.url:
                    lines.append(f"  {c.url}")
            lines.append("")

    lines.append("## Current epic progress\n")
    epics = [it for it in items if _is_epic(it)]
    if epics:
        for epic in sorted(epics, key=lambda e: (e.get("state") == "CLOSED", e.get("number") or 0)):
            done, total, percent = _epic_progress(epic)
            pct = f"{percent}%" if total else "—"
            ref = f"{epic.get('repo')}#{epic.get('number')}"
            status = (epic.get("fields") or {}).get("Status") or "—"
            lines.append(f"- {ref} [{status}] — {epic.get('title')} — {done}/{total} ({pct})")
            if epic.get("url"):
                lines.append(f"  {epic.get('url')}")
    else:
        lines.append("_No items tagged as epics in this workstream._")
    lines.append("")

    lines.append("## All DocumentAI items\n")
    grouped = _group_by_epic(items)
    for parent_title, group in sorted(grouped.items(), key=lambda kv: (kv[0] is None, kv[0] or "")):
        heading = parent_title or "Top-level items"
        lines.append(f"### {heading}")
        for item in sorted(group, key=lambda it: (it.get("state") == "CLOSED", it.get("number") or 0)):
            lines.append(_item_line(item))
        lines.append("")

    return subject, "\n".join(lines)


def build_context_doc(items: list[dict[str, Any]]) -> str:
    """Full point-in-time context intended for the Claude Project knowledge base.

    This is the always-overwritten Google Doc (or markdown file) used to keep
    Claude up to speed on the DocumentAI workstream.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines: list[str] = [
        f"# DocumentAI workstream context — {today}",
        "",
        "_Auto-generated by 14-documentai-tracker. Do not hand-edit; this file is overwritten on each run._",
        "",
        f"Source: navapbc GitHub project #4, filtered to items with the `Product = DocumentAI` field value (or a `DocumentAI` label).",
        f"Item count: {len(items)}",
        "",
    ]

    epics = [it for it in items if _is_epic(it)]
    if epics:
        lines.append("## Epics")
        lines.append("")
        for epic in sorted(epics, key=lambda e: e.get("number") or 0):
            done, total, percent = _epic_progress(epic)
            pct = f"{percent}%" if total else "—"
            status = (epic.get("fields") or {}).get("Status") or "—"
            priority = (epic.get("fields") or {}).get("Priority") or "—"
            size = (epic.get("fields") or {}).get("Size") or "—"
            lines.append(f"### {epic.get('repo')}#{epic.get('number')} — {epic.get('title')}")
            lines.append("")
            lines.append(f"- Status: {status} | Priority: {priority} | Size: {size}")
            lines.append(f"- Progress: {done}/{total} sub-issues closed ({pct})")
            if epic.get("assignees"):
                lines.append(f"- Assignees: {', '.join(epic['assignees'])}")
            if epic.get("url"):
                lines.append(f"- URL: {epic['url']}")
            if epic.get("sub_issues"):
                lines.append("")
                lines.append("Sub-issues:")
                for sub in epic["sub_issues"]:
                    marker = "x" if sub.get("state") == "CLOSED" else " "
                    lines.append(f"- [{marker}] #{sub['number']} — {sub['title']}")
            lines.append("")

    lines.append("## All items")
    lines.append("")
    grouped = _group_by_epic(items)
    for parent_title, group in sorted(grouped.items(), key=lambda kv: (kv[0] is None, kv[0] or "")):
        lines.append(f"### {parent_title or 'Top-level items'}")
        lines.append("")
        for item in sorted(group, key=lambda it: it.get("number") or 0):
            lines.append(_item_line(item))
        lines.append("")

    return "\n".join(lines)
