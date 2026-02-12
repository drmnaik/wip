"""Rich-based terminal output for the wip briefing."""

from __future__ import annotations

import json
import time
from dataclasses import asdict

from rich.console import Console
from rich.text import Text

from wip.scanner import RepoStatus
from wip.worklist import WorkItem

console = Console()


def render_briefing(
    repos: list[RepoStatus],
    verbose: bool = False,
    wip_items: list[WorkItem] | None = None,
    repo_items: dict[str, list[WorkItem]] | None = None,
) -> None:
    """Render the morning briefing to the terminal."""
    if wip_items is None:
        wip_items = []
    if repo_items is None:
        repo_items = {}

    count = len(repos)
    header = Text()
    header.append(" wip", style="bold cyan")
    header.append(f" — {count} repo{'s' if count != 1 else ''} scanned\n")
    console.print(header)

    if wip_items:
        render_worklist(wip_items, verbose)

    for repo in repos:
        items_for_repo = repo_items.get(repo.path, [])
        _render_repo(repo, verbose, wip_items=items_for_repo)


def render_json(
    repos: list[RepoStatus],
    wip_items: list[WorkItem] | None = None,
) -> None:
    """Output scan results as JSON."""
    data = {
        "repos": [asdict(r) for r in repos],
        "worklist": [asdict(i) for i in (wip_items or [])],
    }
    console.print_json(json.dumps(data))


def render_worklist(items: list[WorkItem], verbose: bool = False) -> None:
    """Render the worklist section before the repo list."""
    count = len(items)
    header = Text()
    header.append(" work-in-progress", style="bold magenta")
    header.append(f" — {count} item{'s' if count != 1 else ''}\n")
    console.print(header)

    for item in items:
        _render_work_item(item, show_repo=True)

    console.print()


def _render_work_item(item: WorkItem, show_repo: bool = False) -> None:
    """Render a single work item line."""
    line = Text("  ")

    if item.status == "done":
        line.append(f"#{item.id}", style="dim strikethrough")
        line.append("  ", style="dim")
        line.append(item.description, style="dim strikethrough")
    else:
        line.append(f"#{item.id}", style="bold cyan")
        line.append("  ")
        line.append(item.description)

    if show_repo and item.repo:
        from pathlib import Path
        repo_name = Path(item.repo).name
        line.append(f" ({repo_name})", style="dim")

    ago = _item_ago(item.created_at)
    line.append(f" — {ago}", style="dim")

    console.print(line)


def _render_repo(
    repo: RepoStatus, verbose: bool, wip_items: list[WorkItem] | None = None
) -> None:
    is_dirty = repo.dirty_files > 0 or repo.untracked_files > 0 or repo.staged_files > 0
    is_behind = repo.behind > 0

    if is_dirty:
        icon = "⚠"
        color = "yellow"
    elif is_behind:
        icon = "↓"
        color = "red"
    else:
        icon = "✓"
        color = "green"

    # Header: repo name (branch) icon
    line = Text()
    line.append(f"{repo.name}", style=f"bold {color}")
    line.append(f" ({repo.current_branch})", style="dim")
    line.append(f" {icon}", style=color)
    console.print(line)

    # Status line
    parts: list[str] = []
    if is_dirty:
        dirty_total = repo.dirty_files + repo.untracked_files + repo.staged_files
        parts.append(f"{dirty_total} dirty")
    else:
        parts.append("clean")

    if repo.stash_count > 0:
        parts.append(f"{repo.stash_count} stash{'es' if repo.stash_count != 1 else ''}")

    if repo.last_commit_ago:
        parts.append(f"last commit {repo.last_commit_ago}")

    console.print(f"  {' · '.join(parts)}", style="dim")

    # Ahead/behind
    if repo.ahead > 0 or repo.behind > 0:
        ab_text = Text("  ")
        ab_text.append(f"{repo.ahead} ahead", style="green" if repo.ahead > 0 else "dim")
        ab_text.append(", ")
        ab_text.append(f"{repo.behind} behind", style="red" if repo.behind > 0 else "dim")
        tracking = _tracking_name(repo)
        if tracking:
            ab_text.append(f" {tracking}", style="dim")
        console.print(ab_text)

    # Agent sessions
    if repo.agent_sessions:
        console.print("  agents:", style="dim")
        for session in repo.agent_sessions:
            _render_agent_session(session)

    # WIP items for this repo
    if wip_items:
        console.print("  wip:", style="dim")
        for item in wip_items:
            ago = _item_ago(item.created_at)
            console.print(f"    #{item.id} {item.description} ({ago})", style="dim")

    # Recent branches
    if repo.recent_branches:
        if verbose:
            for b in repo.recent_branches:
                console.print(f"    {b.name} ({b.last_commit_ago})", style="dim")
        else:
            branch_strs = [f"{b.name} ({b.last_commit_ago})" for b in repo.recent_branches[:5]]
            console.print(f"  recent: {', '.join(branch_strs)}", style="dim")

    # Recent commits
    if repo.recent_commits:
        console.print("  commits today:", style="dim")
        limit = len(repo.recent_commits) if verbose else 5
        for c in repo.recent_commits[:limit]:
            msg = c.message if verbose else _truncate(c.message, 60)
            console.print(f"    {c.sha} {msg} ({c.ago})", style="dim")

    console.print()


def _render_agent_session(session) -> None:
    """Render a single agent session line with status styling."""
    status_styles = {
        "active": ("green", "active"),
        "recent": ("yellow", "recent"),
        "stale": ("red", "stale"),
    }
    style, label = status_styles.get(session.status, ("dim", session.status))

    # Icon per status
    status_icons = {"active": "●", "recent": "◐", "stale": "○"}
    icon = status_icons.get(session.status, "○")

    line = Text("    ")
    line.append(f"{session.agent}", style="bold")
    line.append(f" on {session.branch}", style="dim")
    line.append(f" — {session.commit_count} commit{'s' if session.commit_count != 1 else ''}")
    line.append(f", {session.files_changed} file{'s' if session.files_changed != 1 else ''}")
    line.append(f" ({session.last_commit_ago})", style="dim")
    line.append(f" {icon} ", style=style)
    line.append(label, style=style)
    console.print(line)


def _tracking_name(repo: RepoStatus) -> str:
    return "origin"


def _truncate(text: str, length: int) -> str:
    if len(text) <= length:
        return text
    return text[: length - 1] + "…"


def _item_ago(timestamp: float) -> str:
    """Human-readable time ago for a unix timestamp."""
    delta = int(time.time() - timestamp)
    if delta < 60:
        return "just now"
    minutes = delta // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"
