"""Rich-based terminal output for the wip briefing."""

from __future__ import annotations

import json
from dataclasses import asdict

from rich.console import Console
from rich.text import Text

from wip.scanner import RepoStatus

console = Console()


def render_briefing(repos: list[RepoStatus], verbose: bool = False) -> None:
    """Render the morning briefing to the terminal."""
    count = len(repos)
    header = Text()
    header.append(" wip", style="bold cyan")
    header.append(f" — {count} repo{'s' if count != 1 else ''} scanned\n")
    console.print(header)

    for repo in repos:
        _render_repo(repo, verbose)


def render_json(repos: list[RepoStatus]) -> None:
    """Output scan results as JSON."""
    data = [asdict(r) for r in repos]
    console.print_json(json.dumps(data))


def _render_repo(repo: RepoStatus, verbose: bool) -> None:
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


def _tracking_name(repo: RepoStatus) -> str:
    return "origin"


def _truncate(text: str, length: int) -> str:
    if len(text) <= length:
        return text
    return text[: length - 1] + "…"
