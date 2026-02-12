"""Git repository scanner — collects status info for each repo."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from git import Repo, InvalidGitRepositoryError, GitCommandError

from wip.config import AgentsConfig


@dataclass
class AgentSession:
    agent: str                 # Inferred agent name (e.g. "claude", "copilot")
    branch: str                # Branch the agent worked on
    commit_count: int          # Number of commits in this session
    files_changed: int         # Total files touched (from diff stats)
    first_commit_ago: str      # Human-readable time of first commit
    last_commit_ago: str       # Human-readable time of last commit
    first_commit_ts: float     # For sorting
    last_commit_ts: float      # For recency checks
    status: str                # "active" (<1h), "recent" (<24h), "stale" (>24h)


@dataclass
class CommitInfo:
    sha: str
    message: str
    ago: str
    timestamp: float
    body: str = ""
    files: list[str] = field(default_factory=list)


@dataclass
class BranchInfo:
    name: str
    last_commit_ago: str
    timestamp: float


@dataclass
class FileChange:
    path: str
    status: str    # "modified", "added", "deleted", "renamed", "untracked"
    stage: str     # "unstaged", "staged", "untracked"
    insertions: int = 0
    deletions: int = 0


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
    agent_sessions: list[AgentSession] = field(default_factory=list)
    changed_files: list[FileChange] = field(default_factory=list)
    stash_entries: list[str] = field(default_factory=list)


def scan_repo(
    repo_path: str,
    author: str = "",
    recent_days: int = 14,
    agents_config: AgentsConfig | None = None,
) -> RepoStatus | None:
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

    # Stash count + descriptions
    stash_count, stash_entries = _collect_stashes(repo)

    # Changed files (with diff stats)
    changed_files = _collect_changed_files(repo)

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

    # Agent session detection
    if agents_config is None:
        agents_config = AgentsConfig()
    agent_sessions = _detect_agent_sessions(repo, agents_config, now)

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
        agent_sessions=agent_sessions,
        changed_files=changed_files,
        stash_entries=stash_entries,
    )


def scan_repos(
    repo_paths: list[str],
    author: str = "",
    recent_days: int = 14,
    agents_config: AgentsConfig | None = None,
) -> list[RepoStatus]:
    """Scan multiple repos and return their statuses."""
    results = []
    for path in repo_paths:
        status = scan_repo(path, author, recent_days, agents_config)
        if status is not None:
            results.append(status)
    return results


def _collect_stashes(repo: Repo) -> tuple[int, list[str]]:
    """Return (count, descriptions) for stash entries."""
    try:
        output = repo.git.stash("list")
        if not output:
            return 0, []
        lines = output.splitlines()
        return len(lines), lines
    except GitCommandError:
        return 0, []


def _parse_numstat(numstat_output: str) -> dict[str, tuple[int, int]]:
    """Parse `git diff --numstat` output into {path: (insertions, deletions)}."""
    result: dict[str, tuple[int, int]] = {}
    for line in numstat_output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) < 3:
            continue
        ins_str, del_str, path = parts
        # Binary files show "-" for insertions/deletions
        ins = int(ins_str) if ins_str != "-" else 0
        dels = int(del_str) if del_str != "-" else 0
        result[path] = (ins, dels)
    return result


def _collect_changed_files(repo: Repo) -> list[FileChange]:
    """Collect unstaged, staged, and untracked files with diff stats."""
    files: list[FileChange] = []

    if not repo.head.is_valid():
        # No commits yet — everything is untracked or staged for initial commit
        for path in repo.untracked_files:
            files.append(FileChange(path=path, status="untracked", stage="untracked"))
        return files

    # --- Unstaged changes ---
    try:
        unstaged_numstat = _parse_numstat(repo.git.diff("--numstat"))
    except GitCommandError:
        unstaged_numstat = {}

    _STATUS_MAP = {"M": "modified", "A": "added", "D": "deleted", "R": "renamed"}

    try:
        for diff_item in repo.index.diff(None):
            path = diff_item.b_path or diff_item.a_path
            status = _STATUS_MAP.get(diff_item.change_type, "modified")
            ins, dels = unstaged_numstat.get(path, (0, 0))
            files.append(FileChange(
                path=path, status=status, stage="unstaged",
                insertions=ins, deletions=dels,
            ))
    except GitCommandError:
        pass

    # --- Staged changes ---
    try:
        staged_numstat = _parse_numstat(repo.git.diff("--cached", "--numstat"))
    except GitCommandError:
        staged_numstat = {}

    try:
        for diff_item in repo.index.diff("HEAD"):
            path = diff_item.b_path or diff_item.a_path
            status = _STATUS_MAP.get(diff_item.change_type, "modified")
            ins, dels = staged_numstat.get(path, (0, 0))
            files.append(FileChange(
                path=path, status=status, stage="staged",
                insertions=ins, deletions=dels,
            ))
    except GitCommandError:
        pass

    # --- Untracked files ---
    for path in repo.untracked_files:
        files.append(FileChange(path=path, status="untracked", stage="untracked"))

    return files


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

            # Extract body (lines after the first, stripped)
            msg_lines = commit.message.strip().split("\n")
            first_line = msg_lines[0]
            body = "\n".join(msg_lines[1:]).strip()

            # Collect changed file paths (capped at 20)
            try:
                commit_files = list(commit.stats.files.keys())[:20]
            except Exception:
                commit_files = []

            commits.append(CommitInfo(
                sha=commit.hexsha[:7],
                message=first_line,
                ago=_time_ago(now, ts),
                timestamp=commit.committed_date,
                body=body,
                files=commit_files,
            ))
    except Exception:
        pass

    return commits


def _detect_agent_sessions(
    repo: Repo, agents_config: AgentsConfig, now: datetime
) -> list[AgentSession]:
    """Detect agent activity across all local branches."""
    # Map: (agent, branch) -> list of (commit_ts, files_changed)
    sessions_map: dict[tuple[str, str], list[tuple[float, int]]] = {}

    for ref in repo.branches:
        branch_name = ref.name

        # Check if branch name matches any agent pattern
        branch_agent = _match_branch_agent(branch_name, agents_config.branch_patterns)

        try:
            for commit in repo.iter_commits(ref, max_count=100):
                # Check author against agent patterns
                author_agent = _match_author_agent(
                    commit.author.name, agents_config.authors
                )

                agent = author_agent or branch_agent
                if not agent:
                    # On non-agent branches, stop at first non-agent commit
                    if not branch_agent:
                        continue
                    break

                key = (agent, branch_name)
                try:
                    files = commit.stats.total.get("files", 0)
                except Exception:
                    files = 0

                if key not in sessions_map:
                    sessions_map[key] = []
                sessions_map[key].append((float(commit.committed_date), files))
        except Exception:
            continue

    # Build AgentSession objects
    sessions: list[AgentSession] = []
    for (agent, branch), commit_data in sessions_map.items():
        if not commit_data:
            continue

        timestamps = [ts for ts, _ in commit_data]
        first_ts = min(timestamps)
        last_ts = max(timestamps)
        total_files = sum(fc for _, fc in commit_data)

        first_dt = datetime.fromtimestamp(first_ts, tz=timezone.utc)
        last_dt = datetime.fromtimestamp(last_ts, tz=timezone.utc)

        hours_since_last = (now - last_dt).total_seconds() / 3600
        if hours_since_last < 1:
            status = "active"
        elif hours_since_last < 24:
            status = "recent"
        else:
            status = "stale"

        sessions.append(AgentSession(
            agent=agent,
            branch=branch,
            commit_count=len(commit_data),
            files_changed=total_files,
            first_commit_ago=_time_ago(now, first_dt),
            last_commit_ago=_time_ago(now, last_dt),
            first_commit_ts=first_ts,
            last_commit_ts=last_ts,
            status=status,
        ))

    # Sort by most recent first
    sessions.sort(key=lambda s: s.last_commit_ts, reverse=True)
    return sessions


def _match_author_agent(author_name: str, patterns: list[str]) -> str:
    """Return the matched agent name if author matches any pattern, else empty string."""
    author_lower = author_name.lower()
    for pattern in patterns:
        if pattern.lower() in author_lower:
            return pattern.lower().rstrip("-")
    return ""


def _match_branch_agent(branch_name: str, branch_patterns: list[str]) -> str:
    """Return the inferred agent name if branch matches any prefix pattern, else empty string."""
    for pattern in branch_patterns:
        if branch_name.startswith(pattern):
            # Agent name is the prefix without trailing slash
            return pattern.rstrip("/")
    return ""


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
