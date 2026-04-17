"""Persist a snapshot of the last run so diff.py can detect changes."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "state" / "last_snapshot.json"


def load_snapshot(path: Path = DEFAULT_PATH) -> dict[str, Any] | None:
    """Return the last saved snapshot, or None if no prior run exists."""
    if not path.exists():
        return None
    return json.loads(path.read_text())


def save_snapshot(items: list[dict[str, Any]], path: Path = DEFAULT_PATH) -> None:
    """Persist the current items as the new baseline for the next run."""
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": items,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
