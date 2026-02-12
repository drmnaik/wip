"""Prompt assembly — turns scan data into LLM-ready context."""

from __future__ import annotations

from wip.scanner import RepoStatus
from wip.worklist import WorkItem


SYSTEM_PROMPT = """\
You are wip, a developer assistant that gives concise briefings.
You analyze git repository state and work-in-progress items to help developers
understand where they left off and what to focus on next.

Rules:
- Be concise and direct. No filler.
- Use plain language, not raw git output.
- When suggesting priorities, explain WHY (staleness, risk, dependencies).
- If there's nothing notable, say so briefly.
"""

BRIEFING_TEMPLATE = """\
Here is the current state of my repositories and work items.
Give me a briefing — what should I know, and what should I focus on first?

{context}
"""

STANDUP_TEMPLATE = """\
Based on my git activity and work items, draft a standup update.
Use this format:
- Yesterday: (what I worked on)
- Today: (what I should focus on)
- Blockers: (anything stuck or at risk)

{context}
"""

QUERY_TEMPLATE = """\
Here is the current state of my repositories and work items.

{context}

My question: {query}
"""


def build_context(
    repos: list[RepoStatus],
    wip_items: list[WorkItem] | None = None,
) -> str:
    """Assemble scan results + work items into a text block for the LLM."""
    parts: list[str] = []

    # Work items
    if wip_items:
        parts.append("## Work-in-progress items")
        for item in wip_items:
            status = "DONE" if item.status == "done" else "OPEN"
            repo_label = f" (repo: {item.repo})" if item.repo else ""
            parts.append(f"- [{status}] #{item.id}: {item.description}{repo_label}")
        parts.append("")

    # Repos
    if repos:
        parts.append("## Repositories")
        for repo in repos:
            parts.append(_format_repo(repo))

    return "\n".join(parts)


def build_briefing_prompt(
    repos: list[RepoStatus],
    wip_items: list[WorkItem] | None = None,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for a briefing."""
    context = build_context(repos, wip_items)
    return SYSTEM_PROMPT, BRIEFING_TEMPLATE.format(context=context)


def build_standup_prompt(
    repos: list[RepoStatus],
    wip_items: list[WorkItem] | None = None,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for a standup draft."""
    context = build_context(repos, wip_items)
    return SYSTEM_PROMPT, STANDUP_TEMPLATE.format(context=context)


def build_query_prompt(
    query: str,
    repos: list[RepoStatus],
    wip_items: list[WorkItem] | None = None,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for a free-form question."""
    context = build_context(repos, wip_items)
    return SYSTEM_PROMPT, QUERY_TEMPLATE.format(context=context, query=query)


def _format_repo(repo: RepoStatus) -> str:
    """Format a single repo's state as text for the LLM."""
    lines = [f"### {repo.name} (branch: {repo.current_branch})"]

    # Status summary
    parts: list[str] = []
    dirty_total = repo.dirty_files + repo.untracked_files + repo.staged_files
    if dirty_total > 0:
        parts.append(f"{dirty_total} uncommitted changes")
    else:
        parts.append("clean")
    if repo.stash_count > 0:
        parts.append(f"{repo.stash_count} stash(es)")
    if repo.last_commit_ago:
        parts.append(f"last commit {repo.last_commit_ago}")
    lines.append("Status: " + ", ".join(parts))

    # Changed files
    if repo.changed_files:
        lines.append("Changed files:")
        for f in repo.changed_files:
            stat = ""
            if f.insertions or f.deletions:
                stat = f" (+{f.insertions}/-{f.deletions})"
            lines.append(f"  - [{f.stage}] {f.path} ({f.status}){stat}")

    # Stashes
    if repo.stash_entries:
        lines.append("Stashes:")
        for entry in repo.stash_entries:
            lines.append(f"  - {entry}")

    # Ahead/behind
    if repo.ahead > 0 or repo.behind > 0:
        lines.append(f"Remote: {repo.ahead} ahead, {repo.behind} behind")

    # Recent branches
    if repo.recent_branches:
        branch_names = [f"{b.name} ({b.last_commit_ago})" for b in repo.recent_branches[:5]]
        lines.append(f"Other branches: {', '.join(branch_names)}")

    # Recent commits
    if repo.recent_commits:
        lines.append("Recent commits:")
        for c in repo.recent_commits[:5]:
            lines.append(f"  - {c.sha} {c.message} ({c.ago})")
            # Body: cap at 3 lines
            if c.body:
                body_lines = c.body.split("\n")[:3]
                for bl in body_lines:
                    lines.append(f"      {bl}")
            # Files: cap at 10 with "+N more" suffix
            if c.files:
                shown = c.files[:10]
                file_str = ", ".join(shown)
                if len(c.files) > 10:
                    file_str += f" +{len(c.files) - 10} more"
                lines.append(f"      files: {file_str}")

    # Agent activity
    if repo.agent_sessions:
        lines.append("Agent activity:")
        for s in repo.agent_sessions:
            lines.append(
                f"  - {s.agent} on {s.branch}: {s.commit_count} commits, "
                f"{s.files_changed} files changed, last commit {s.last_commit_ago} ({s.status})"
            )

    lines.append("")
    return "\n".join(lines)
