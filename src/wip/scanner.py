"""Git repository scanner — collects status info for each repo."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from git import Repo, InvalidGitRepositoryError, GitCommandError


@dataclass
class CommitInfo:
    sha: str
    message: str
    ago: str
    timestamp: float


@dataclass
class BranchInfo:
    name: str
    last_commit_ago: str
    timestamp: float


@dataclass
class RepoStatus:
    path: str
    name: str
    current_branch: str
    dirty_files: int
    untracked_files: int
    staged_files: int
    stash_count: int
    ahead: int
    behind: int
    last_commit_ago: str
    recent_branches: list[BranchInfo] = field(default_factory=list)
    recent_commits: list[CommitInfo] = field(default_factory=list)


def scan_repo(repo_path: str, author: str = "", recent_days: int = 14) -> RepoStatus | None:
    """Scan a single git repo and return its status, or None on error."""
    try:
        repo = Repo(repo_path)
    except InvalidGitRepositoryError:
        return None

    name = Path(repo_path).name
    now = datetime.now(timezone.utc)

    # Current branch
    try:
        current_branch = repo.active_branch.name
    except TypeError:
        current_branch = "detached HEAD"

    # Dirty / staged / untracked
    untracked = len(repo.untracked_files)
    staged = len(repo.index.diff("HEAD")) if repo.head.is_valid() else 0
    dirty = len(repo.index.diff(None))  # unstaged changes

    # Stash count
    stash_count = _count_stashes(repo)

    # Ahead / behind
    ahead, behind = _ahead_behind(repo)

    # Last commit time
    last_commit_ago = ""
    if repo.head.is_valid():
        last_commit_time = datetime.fromtimestamp(
            repo.head.commit.committed_date, tz=timezone.utc
        )
        last_commit_ago = _time_ago(now, last_commit_time)

    # Recent branches (commits within recent_days)
    recent_branches = _recent_branches(repo, now, recent_days)

    # Recent commits by author (last 24h)
    recent_commits = _recent_commits(repo, author, now)

    return RepoStatus(
        path=repo_path,
        name=name,
        current_branch=current_branch,
        dirty_files=dirty,
        untracked_files=untracked,
        staged_files=staged,
        stash_count=stash_count,
        ahead=ahead,
        behind=behind,
        last_commit_ago=last_commit_ago,
        recent_branches=recent_branches,
        recent_commits=recent_commits,
    )


def scan_repos(
    repo_paths: list[str], author: str = "", recent_days: int = 14
) -> list[RepoStatus]:
    """Scan multiple repos and return their statuses."""
    results = []
    for path in repo_paths:
        status = scan_repo(path, author, recent_days)
        if status is not None:
            results.append(status)
    return results


def _count_stashes(repo: Repo) -> int:
    try:
        return len(repo.git.stash("list").splitlines()) if repo.git.stash("list") else 0
    except GitCommandError:
        return 0


def _ahead_behind(repo: Repo) -> tuple[int, int]:
    try:
        branch = repo.active_branch
        tracking = branch.tracking_branch()
        if tracking is None:
            return 0, 0
        revs = repo.git.rev_list("--left-right", "--count", f"{branch.name}...{tracking.name}")
        ahead_str, behind_str = revs.split()
        return int(ahead_str), int(behind_str)
    except (TypeError, GitCommandError, ValueError):
        return 0, 0


def _recent_branches(repo: Repo, now: datetime, recent_days: int) -> list[BranchInfo]:
    cutoff = now.timestamp() - (recent_days * 86400)
    branches: list[BranchInfo] = []

    for ref in repo.branches:
        try:
            commit_time = ref.commit.committed_date
            if commit_time >= cutoff:
                ts = datetime.fromtimestamp(commit_time, tz=timezone.utc)
                branches.append(BranchInfo(
                    name=ref.name,
                    last_commit_ago=_time_ago(now, ts),
                    timestamp=commit_time,
                ))
        except Exception:
            continue

    # Sort by most recent first, exclude current branch
    branches.sort(key=lambda b: b.timestamp, reverse=True)
    try:
        current = repo.active_branch.name
        branches = [b for b in branches if b.name != current]
    except TypeError:
        pass

    return branches


def _recent_commits(repo: Repo, author: str, now: datetime) -> list[CommitInfo]:
    if not repo.head.is_valid():
        return []

    cutoff = now.timestamp() - 86400  # last 24h
    commits: list[CommitInfo] = []

    try:
        for commit in repo.iter_commits(max_count=50):
            if commit.committed_date < cutoff:
                break
            if author and author.lower() not in commit.author.name.lower():
                continue
            ts = datetime.fromtimestamp(commit.committed_date, tz=timezone.utc)
            commits.append(CommitInfo(
                sha=commit.hexsha[:7],
                message=commit.message.strip().split("\n")[0],
                ago=_time_ago(now, ts),
                timestamp=commit.committed_date,
            ))
    except Exception:
        pass

    return commits


def _time_ago(now: datetime, then: datetime) -> str:
    delta = now - then
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"
