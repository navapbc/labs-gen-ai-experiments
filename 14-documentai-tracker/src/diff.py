"""Compute changes between the previous snapshot and the current fetch."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TRACKED_FIELDS = ("Status", "Priority", "Size", "Start date", "Target date")


@dataclass
class Change:
    kind: str  # "new" | "closed" | "reopened" | "field" | "assignees"
    item_id: str
    title: str
    url: str | None
    repo: str | None
    number: int | None
    details: dict[str, Any] = field(default_factory=dict)

    def as_line(self) -> str:
        ref = f"{self.repo}#{self.number}" if self.repo and self.number else self.title
        if self.kind == "new":
            return f"NEW: {ref} — {self.title} (status: {self.details.get('status', '?')})"
        if self.kind == "closed":
            reason = self.details.get("state_reason") or "closed"
            return f"DONE: {ref} — {self.title} (reason: {reason.lower()})"
        if self.kind == "reopened":
            return f"REOPENED: {ref} — {self.title}"
        if self.kind == "field":
            field_name = self.details["field"]
            prev = self.details.get("from")
            curr = self.details.get("to")
            return f"CHANGED: {ref} — {field_name}: {prev!r} -> {curr!r} ({self.title})"
        if self.kind == "assignees":
            added = self.details.get("added", [])
            removed = self.details.get("removed", [])
            parts = []
            if added:
                parts.append(f"+{','.join(added)}")
            if removed:
                parts.append(f"-{','.join(removed)}")
            return f"ASSIGNEES: {ref} — {' '.join(parts)} ({self.title})"
        return f"{self.kind}: {ref} — {self.title}"


def _index(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {it["item_id"]: it for it in items}


def compute_changes(
    previous: list[dict[str, Any]] | None,
    current: list[dict[str, Any]],
) -> list[Change]:
    """Compare two snapshots and return a list of semantic changes.

    If `previous` is None (first run), only NEW events are emitted.
    """
    prev_by_id = _index(previous or [])
    curr_by_id = _index(current)
    changes: list[Change] = []

    for item_id, curr in curr_by_id.items():
        prev = prev_by_id.get(item_id)
        ref_args = {
            "item_id": item_id,
            "title": curr.get("title", ""),
            "url": curr.get("url"),
            "repo": curr.get("repo"),
            "number": curr.get("number"),
        }
        if prev is None:
            changes.append(
                Change(
                    kind="new",
                    details={"status": (curr.get("fields") or {}).get("Status")},
                    **ref_args,
                )
            )
            continue

        prev_state = prev.get("state")
        curr_state = curr.get("state")
        if prev_state != curr_state:
            if curr_state == "CLOSED":
                changes.append(
                    Change(
                        kind="closed",
                        details={"state_reason": curr.get("state_reason")},
                        **ref_args,
                    )
                )
            elif curr_state == "OPEN" and prev_state == "CLOSED":
                changes.append(Change(kind="reopened", **ref_args))

        prev_fields = prev.get("fields") or {}
        curr_fields = curr.get("fields") or {}
        for fname in TRACKED_FIELDS:
            if prev_fields.get(fname) != curr_fields.get(fname):
                changes.append(
                    Change(
                        kind="field",
                        details={
                            "field": fname,
                            "from": prev_fields.get(fname),
                            "to": curr_fields.get(fname),
                        },
                        **ref_args,
                    )
                )

        prev_assignees = set(prev.get("assignees") or [])
        curr_assignees = set(curr.get("assignees") or [])
        if prev_assignees != curr_assignees:
            changes.append(
                Change(
                    kind="assignees",
                    details={
                        "added": sorted(curr_assignees - prev_assignees),
                        "removed": sorted(prev_assignees - curr_assignees),
                    },
                    **ref_args,
                )
            )

    return changes
