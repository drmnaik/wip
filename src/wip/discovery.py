"""Discover git repositories in configured directories."""

from __future__ import annotations

import os
from pathlib import Path


def discover_repos(directories: list[str], depth: int = 3) -> list[str]:
    """Find git repos in the given directories up to `depth` levels deep.

    Skips repos nested inside other repos (submodules).
    Returns sorted list of absolute paths.
    """
    repos: list[str] = []
    seen: set[str] = set()

    for directory in directories:
        root = Path(directory).expanduser().resolve()
        if not root.is_dir():
            continue
        _walk_for_repos(root, depth, repos, seen)

    repos.sort()
    return repos


def _walk_for_repos(
    directory: Path,
    remaining_depth: int,
    repos: list[str],
    seen: set[str],
) -> None:
    """Recursively walk directories looking for .git folders."""
    if remaining_depth < 0:
        return

    git_dir = directory / ".git"
    if git_dir.exists():
        abs_path = str(directory)
        if abs_path not in seen:
            seen.add(abs_path)
            repos.append(abs_path)
        # Don't descend into a repo's subdirectories (skip submodules)
        return

    try:
        entries = sorted(directory.iterdir())
    except PermissionError:
        return

    for entry in entries:
        if not entry.is_dir():
            continue
        # Skip hidden directories and common non-project dirs
        name = entry.name
        if name.startswith(".") or name in ("node_modules", "__pycache__", ".venv", "venv"):
            continue
        _walk_for_repos(entry, remaining_depth - 1, repos, seen)
