"""Work-in-progress task tracker — data model, persistence, and operations."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

WORKLIST_DIR = Path.home() / ".wip"
WORKLIST_PATH = WORKLIST_DIR / "worklist.json"


@dataclass
class WorkItem:
    id: int
    description: str
    created_at: float
    status: str = "open"
    repo: str | None = None
    completed_at: float | None = None


def load_worklist() -> list[WorkItem]:
    """Read worklist from JSON, return empty list if missing."""
    if not WORKLIST_PATH.exists():
        return []

    try:
        data = json.loads(WORKLIST_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return []

    return [WorkItem(**item) for item in data]


def save_worklist(items: list[WorkItem]) -> None:
    """Write worklist to JSON with indent=2."""
    WORKLIST_DIR.mkdir(parents=True, exist_ok=True)
    data = [asdict(item) for item in items]
    WORKLIST_PATH.write_text(json.dumps(data, indent=2) + "\n")


def _next_id(items: list[WorkItem]) -> int:
    if not items:
        return 1
    return max(item.id for item in items) + 1


def add_item(description: str, repo: str | None = None) -> WorkItem:
    """Create a new work item, save, and return it."""
    items = load_worklist()
    item = WorkItem(
        id=_next_id(items),
        description=description,
        created_at=time.time(),
        repo=repo,
    )
    items.append(item)
    save_worklist(items)
    return item


def complete_item(item_id: int) -> WorkItem | None:
    """Mark an item as done. Return the item, or None if not found/already done."""
    items = load_worklist()
    for item in items:
        if item.id == item_id:
            if item.status == "done":
                return None
            item.status = "done"
            item.completed_at = time.time()
            save_worklist(items)
            return item
    return None


def get_items(include_done: bool = False) -> list[WorkItem]:
    """Return work items, filtering out done items by default."""
    items = load_worklist()
    if not include_done:
        items = [i for i in items if i.status != "done"]
    return items


def get_items_for_repo(repo_path: str, include_done: bool = False) -> list[WorkItem]:
    """Return work items linked to a specific repo."""
    normalized = os.path.realpath(repo_path)
    items = get_items(include_done=include_done)
    return [i for i in items if i.repo and os.path.realpath(i.repo) == normalized]


def detect_repo() -> str | None:
    """Walk cwd upward looking for .git/, return repo root path or None."""
    current = Path.cwd()
    for directory in [current, *current.parents]:
        if (directory / ".git").exists():
            return str(directory)
    return None
