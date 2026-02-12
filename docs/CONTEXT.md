# wip — Project Context & Development Guide

> This file is the single source of truth for understanding, contributing to, and extending the `wip` project. It is written for both human developers and AI coding agents.

---

## 1. What is wip?

**wip** ("Where did I leave off?") is a CLI tool that gives developers a morning briefing. It scans local git repositories and surfaces what you were working on: dirty files, stashes, branches, recent commits, and sync status with remotes. It also includes a work-in-progress task tracker for jotting down what you're doing across repos.

**Core value proposition:** Run `wip` in your terminal and instantly know where you left off across all your projects.

### User-facing commands

| Command             | Purpose                                        |
|---------------------|-------------------------------------------------|
| `wip`               | Show morning briefing (default, no subcommand)  |
| `wip scan`          | Explicit alias for the briefing                 |
| `wip config init`   | Interactive setup (directories, author name)     |
| `wip config show`   | Print current configuration                      |
| `wip version`       | Print version string                             |
| `wip --json`        | Output scan results as machine-readable JSON     |
| `wip --verbose`     | Show all branches, full commits, changed files, stash descriptions |
| `wip add "desc"`    | Add a WIP item (auto-links to current repo)      |
| `wip add "desc" --repo /path` | Add a WIP item linked to a specific repo |
| `wip done <id>`     | Mark a WIP item as done                          |
| `wip list`          | Show open WIP items                              |
| `wip list --all`    | Show all WIP items including completed           |
| `wip ai briefing`   | AI-powered narrative morning briefing            |
| `wip ai standup`    | Generate a standup update from git activity      |
| `wip ai ask "..."`  | Ask a free-form question about your work         |

---

## 2. Architecture

### Project layout

```
wip/
├── .git/
├── .gitignore
├── pyproject.toml          # Package metadata, dependencies, build config
├── README.md
├── docs/
│   └── CONTEXT.md          # This file — full project knowledge base
└── src/
    └── wip/
        ├── __init__.py     # Package root, exports __version__
        ├── cli.py          # CLI entry point (Typer app, commands, flags)
        ├── config.py       # Config loading/saving, TOML, defaults
        ├── discovery.py    # Find git repos by walking directories
        ├── scanner.py      # Git status collection per repo (GitPython)
        ├── display.py      # Rich-based terminal rendering
        ├── worklist.py     # WIP task tracker, JSON persistence
        └── llm/
            ├── __init__.py     # Re-exports LLMProvider, get_provider, list_providers
            ├── base.py         # ABC, LLMResponse dataclass, error types
            ├── registry.py     # Provider name → class mapping, API key resolution
            ├── prompts.py      # Prompt assembly from scan data
            ├── anthropic.py    # Anthropic Claude provider (implemented)
            ├── openai.py       # OpenAI GPT provider (stub)
            └── gemini.py       # Google Gemini provider (stub)
```

### Data flow

```
User runs `wip`
    │
    ▼
cli.py: _run_briefing()
    │
    ├── config.py: load_config()        → WipConfig dataclass
    │       reads ~/.wip/config.toml
    │
    ├── discovery.py: discover_repos()  → list[str] of repo paths
    │       walks configured directories up to scan_depth
    │       detects .git/ directories
    │       skips nested repos (submodules)
    │
    ├── scanner.py: scan_repos()        → list[RepoStatus]
    │       for each repo path:
    │         opens with GitPython
    │         collects branch, dirty, staged, untracked, stash,
    │         ahead/behind, recent branches, recent commits
    │         detects agent sessions (author/branch pattern matching)
    │
    ├── worklist.py: get_items()        → list[WorkItem]
    │       reads ~/.wip/worklist.json
    │       filters by status, optionally by repo
    │
    └── display.py: render_briefing()   → terminal output (Rich)
            or render_json()            → JSON to stdout
            includes worklist section + items under repos

User runs `wip ai briefing` (or standup/ask)
    │
    ▼
cli.py: _get_llm_provider()
    │
    ├── config.py: load_config()        → WipConfig.llm (provider, model, api_key_env)
    ├── llm/registry.py: get_provider() → LLMProvider instance
    │       resolves API key from env vars
    │       lazy-imports provider class
    │
    ├── cli.py: _scan_all()             → (repos, wip_items)
    │       same scan pipeline as regular briefing
    │
    ├── llm/prompts.py: build_*_prompt() → (system, user) prompt pair
    │       assembles repo state + work items into LLM context
    │
    └── provider.stream(system, user)   → streamed text to terminal
```

### Module responsibilities

| Module         | Responsibility                              | Key exports                                    |
|----------------|---------------------------------------------|------------------------------------------------|
| `cli.py`       | Command routing, flags, user interaction     | `app` (Typer instance)                         |
| `config.py`    | Read/write `~/.wip/config.toml`, defaults    | `WipConfig`, `AgentsConfig`, `load_config()`, `save_config()`, `detect_git_author()`, `CONFIG_PATH` |
| `discovery.py` | Find git repos in filesystem                 | `discover_repos(directories, depth)`           |
| `scanner.py`   | Collect git status and agent detection per repo | `RepoStatus`, `AgentSession`, `FileChange`, `BranchInfo`, `CommitInfo`, `scan_repo()`, `scan_repos()` |
| `display.py`   | Render output to terminal or JSON            | `render_briefing()`, `render_json()`, `render_worklist()` |
| `worklist.py`  | WIP task tracker, JSON persistence           | `WorkItem`, `add_item()`, `complete_item()`, `get_items()`, `get_items_for_repo()`, `detect_repo()` |
| `llm/__init__` | Re-exports for the LLM package                | `LLMProvider`, `LLMResponse`, `get_provider()`, `list_providers()` |
| `llm/base.py`  | Abstract provider class, response type, errors | `LLMProvider`, `LLMResponse`, `LLMError`, `LLMAuthError`, `LLMRateLimitError` |
| `llm/registry.py`| Provider lookup and API key resolution       | `get_provider()`, `list_providers()` |
| `llm/prompts.py` | Assembles scan data into LLM prompts         | `build_briefing_prompt()`, `build_standup_prompt()`, `build_query_prompt()` |
| `llm/anthropic.py`| Anthropic Claude provider (implemented)      | `AnthropicProvider` |
| `llm/openai.py`  | OpenAI GPT provider (stub)                   | `OpenAIProvider` |
| `llm/gemini.py`  | Google Gemini provider (stub)                | `GeminiProvider` |

---

## 3. Data models

### AgentsConfig (config.py)

```python
@dataclass
class AgentsConfig:
    authors: list[str]         # Substrings matched case-insensitively against commit author names
    branch_patterns: list[str] # Branch name prefixes indicating agent activity
```

Defaults: authors = `["claude", "copilot", "cursor", "devin", "codex", "github-actions", "bot"]`, branch_patterns = `["agent/", "claude/", "copilot/", "devin/", "cursor/"]`.

### LLMConfig (config.py)

```python
@dataclass
class LLMConfig:
    provider: str = ""       # "anthropic", "openai", "gemini"
    model: str = ""          # Provider-specific model ID (uses provider default if empty)
    api_key_env: str = ""    # Env var name holding the API key
```

### WipConfig (config.py)

```python
@dataclass
class WipConfig:
    directories: list[str]   # Paths to scan, e.g. ["~/projects", "~/work"]
    author: str              # Git author name for filtering commits
    scan_depth: int          # How deep to recurse (default: 3)
    recent_days: int         # Lookback window for branches (default: 14)
    llm: LLMConfig           # LLM provider settings (optional)
    agents: AgentsConfig     # Agent detection patterns (works with defaults)
```

### RepoStatus (scanner.py)

```python
@dataclass
class RepoStatus:
    path: str                          # Absolute path to repo root
    name: str                          # Directory name (last path component)
    current_branch: str                # Active branch or "detached HEAD"
    dirty_files: int                   # Unstaged modifications
    untracked_files: int               # Files not tracked by git
    staged_files: int                  # Files in the index ready to commit
    stash_count: int                   # Number of stash entries
    ahead: int                         # Commits ahead of tracking remote
    behind: int                        # Commits behind tracking remote
    last_commit_ago: str               # Human-readable time since last commit
    recent_branches: list[BranchInfo]  # Branches with activity in recent_days
    recent_commits: list[CommitInfo]   # Author's commits in last 24h
    agent_sessions: list[AgentSession] # Detected agent activity sessions
    changed_files: list[FileChange]    # All changed files with diff stats
    stash_entries: list[str]           # Stash descriptions (e.g. "stash@{0}: WIP on main: abc1234 msg")
```

### AgentSession (scanner.py)

```python
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
```

### BranchInfo (scanner.py)

```python
@dataclass
class BranchInfo:
    name: str               # Branch name
    last_commit_ago: str    # Human-readable time since branch's last commit
    timestamp: float        # Unix timestamp (for sorting)
```

### FileChange (scanner.py)

```python
@dataclass
class FileChange:
    path: str               # File path relative to repo root
    status: str             # "modified", "added", "deleted", "renamed", "untracked"
    stage: str              # "unstaged", "staged", "untracked"
    insertions: int = 0     # Lines added (from diff --numstat)
    deletions: int = 0      # Lines removed (from diff --numstat)
```

### CommitInfo (scanner.py)

```python
@dataclass
class CommitInfo:
    sha: str                # Short (7-char) commit hash
    message: str            # First line of commit message
    ago: str                # Human-readable time since commit
    timestamp: float        # Unix timestamp (for sorting)
    body: str = ""          # Remaining commit message lines (after subject)
    files: list[str] = field(default_factory=list)  # Files changed in this commit
```

### WorkItem (worklist.py)

```python
@dataclass
class WorkItem:
    id: int                            # Auto-assigned sequential ID
    description: str                   # What the user is working on
    created_at: float                  # Unix timestamp
    status: str = "open"               # "open" or "done"
    repo: str | None = None            # Absolute repo path (optional)
    completed_at: float | None = None  # Unix timestamp when marked done
```

### LLMResponse (llm/base.py)

```python
@dataclass
class LLMResponse:
    text: str                # Generated text
    input_tokens: int = 0    # Tokens in the prompt
    output_tokens: int = 0   # Tokens in the response
    model: str = ""          # Model ID used
```

---

## 4. Dependencies & rationale

All dependencies are declared in `pyproject.toml`.

| Package      | Version   | Why                                                        |
|--------------|-----------|------------------------------------------------------------|
| `typer`      | `>=0.9.0` | CLI framework — clean command/subcommand routing, auto-help, type-safe options |
| `gitpython`  | `>=3.1.0` | Git repo interaction — branches, diffs, logs, stash, remotes without shelling out |
| `rich`       | `>=13.0.0`| Terminal output — colors, styled text, JSON pretty-printing |
| `tomli`      | `>=1.0.0` | TOML parsing on Python 3.9/3.10 (stdlib `tomllib` on 3.11+). Conditional: `python_version < '3.11'` |
| `anthropic`  | `>=0.79.0`| Anthropic Claude API SDK. Optional — only needed if using `anthropic` LLM provider |

### Build system

- **Build backend:** Hatchling (`hatchling`)
- **Package layout:** `src/wip/` (src-layout, configured via `[tool.hatch.build.targets.wheel]`)
- **Entry point:** `wip = "wip.cli:app"` (Typer app is callable directly)

### Adding new dependencies

When adding a dependency:
1. Add it to `pyproject.toml` under `[project] dependencies`
2. Use version lower bounds (`>=x.y.z`), not pinned versions
3. If it's only needed for older Python versions, use environment markers (e.g., `; python_version < '3.11'`)
4. Reinstall: `pip install -e .`
5. Prefer stdlib solutions when available

---

## 5. Code conventions

### Python version

- **Minimum:** Python 3.9
- **Every module** must include `from __future__ import annotations` as the first import to enable modern type annotation syntax (`list[str]`, `X | None`, etc.) on 3.9/3.10
- Do not use 3.10+ features (match/case, `TypeAlias`, etc.)

### Style & patterns

- **Dataclasses** for all data models — no Pydantic, no TypedDict, no NamedTuple
- **No classes for services** — use plain functions grouped by module. A module _is_ the namespace
- **Private helpers** prefixed with underscore (e.g., `_time_ago`, `_walk_for_repos`)
- **Public API** of each module is its non-underscored functions and dataclasses
- **Error handling:** catch specific exceptions, return `None` or safe defaults (e.g., `0` for counts), never crash the whole briefing because one repo has issues
- **No logging framework yet** — use `typer.echo()` for user-facing messages
- **Docstrings:** one-line for simple functions, multi-line only if the function has complex behavior
- **Imports:** stdlib first, then third-party, then local (`wip.*`) — separated by blank lines

### CLI patterns (Typer)

- Top-level `app` is a `typer.Typer()` instance in `cli.py`
- Subcommand groups use nested `typer.Typer()` (e.g., `config_app` added via `app.add_typer`)
- The default action (no subcommand) is handled by `@app.callback(invoke_without_command=True)`
- Options use `typer.Option()` with explicit flags (e.g., `--json`, `--verbose`/`-v`)
- User prompts use `typer.prompt()` for interactive input
- Errors exit via `raise typer.Exit(1)`

### Git interaction (GitPython)

- Always wrap GitPython calls in try/except — repos can be in unexpected states
- Use `repo.active_branch.name` (catches `TypeError` for detached HEAD)
- Use `repo.index.diff("HEAD")` for staged, `repo.index.diff(None)` for unstaged
- Use `repo.git.stash("list")` for stash count (raw git command)
- Use `repo.git.rev_list("--left-right", "--count", ...)` for ahead/behind

### Display (Rich)

- Single `Console()` instance at module level
- Use `rich.text.Text` for styled inline output
- Status icons: `✓` (clean/green), `⚠` (dirty/yellow), `↓` (behind/red)
- Compact output by default, `--verbose` shows full detail
- JSON output via `console.print_json()`

---

## 6. Configuration

### File location

```
~/.wip/config.toml
```

### Format

```toml
directories = ["/Users/you/projects", "/Users/you/work"]
author = "Your Name"
scan_depth = 3
recent_days = 14

[llm]
provider = "anthropic"
model = "claude-haiku-4-5-20251001"
api_key_env = "ANTHROPIC_API_KEY"

# Optional: customize agent detection (defaults work out of the box)
[agents]
authors = ["claude", "copilot", "cursor", "devin", "codex", "github-actions", "bot"]
branch_patterns = ["agent/", "claude/", "copilot/", "devin/", "cursor/"]
```

### TOML handling

- **Reading:** `tomllib` (stdlib on 3.11+) with `tomli` fallback (3.9/3.10)
- **Writing:** manual string formatting (no TOML writer library). The config structure is flat enough that simple f-string generation is sufficient
- If no config file exists, `load_config()` returns a `WipConfig` with empty defaults

### Worklist file

```
~/.wip/worklist.json
```

A JSON array of `WorkItem` dicts. Created on first `wip add`. ID assignment: `max(existing IDs) + 1`, starting at 1. Completed items are kept (status `"done"`) but hidden from default views. Repo paths are stored as absolute paths; queries normalize with `os.path.realpath()` for comparison.

---

## 7. Repo discovery rules

`discovery.py` walks the filesystem with these rules:

1. Start from each directory in `config.directories`
2. Recurse up to `scan_depth` levels (default: 3)
3. A directory is a git repo if it contains `.git/`
4. **Stop descending** into a repo's children (prevents submodule scanning)
5. **Skip:** hidden directories (`.`-prefix), `node_modules`, `__pycache__`, `.venv`, `venv`
6. **Skip:** directories that raise `PermissionError`
7. Deduplicate by absolute path
8. Return sorted list

---

## 8. Roadmap

### Phase 0+1: Foundation + Scanner (DONE)

- Config management (TOML read/write, interactive init)
- Repo discovery (directory walking)
- Git scanner (branch, dirty, stash, ahead/behind, recent branches/commits)
- Rich terminal display (color, icons, compact/verbose)
- CLI wiring (wip, wip scan, wip config, --json, --verbose)

### Phase 2: Interactive Worklist (DONE)

- `wip add "description"` — add a WIP item, auto-links to current repo
- `wip add "description" --repo /path` — add item linked to explicit repo
- `wip done <id>` — mark item as done (kept but hidden)
- `wip list` — show open items; `wip list --all` includes completed
- Persistent state in `~/.wip/worklist.json`
- Worklist section shown in briefing before repos
- Items shown under their linked repos in the briefing
- JSON output includes `worklist` array alongside `repos`

### Phase 4: LLM Integration (DONE)

- Provider abstraction layer (`llm/base.py`) with ABC, response type, error hierarchy
- Provider registry (`llm/registry.py`) with lazy imports and API key resolution from env vars
- Prompt assembly (`llm/prompts.py`) — builds structured context from scan data + work items
- Anthropic Claude provider (`llm/anthropic.py`) — fully implemented with streaming
- OpenAI and Gemini providers — scaffolded with stubs
- `wip ai briefing` — narrative morning briefing via LLM
- `wip ai standup` — generate standup update from git activity
- `wip ai ask "..."` — free-form questions about your work
- Config extended with `[llm]` section (provider, model, api_key_env)
- `wip config init` updated with optional LLM setup
- Clean error handling — no tracebacks, user-friendly messages
- All AI commands use streaming output

### Phase 5: Passive Agent Detection (DONE)

- Detect coding agent activity from git signals (commit authors + branch naming patterns)
- `AgentsConfig` with configurable author substrings and branch prefixes (sensible defaults, zero config)
- `AgentSession` dataclass — agent name, branch, commit count, files changed, timestamps, status
- Status: "active" (<1h since last commit), "recent" (<24h), "stale" (>24h)
- Surfaced in terminal display (color-coded), JSON output, and LLM prompt context
- All existing commands (`wip`, `wip --json`, `wip ai briefing/standup/ask`) get agent awareness automatically

### Phase 6: Enriched File-Level Context (DONE)

- `FileChange` dataclass — path, status, stage, insertions, deletions per changed file
- `CommitInfo` extended with commit body and per-commit file list
- `RepoStatus` extended with `changed_files` and `stash_entries`
- Verbose display shows changed files color-coded by stage (green=staged, yellow=untracked, dim=unstaged)
- Verbose display shows stash descriptions
- LLM prompts include changed files with diff stats, stash descriptions, commit bodies (3-line cap), and per-commit file lists (10-path cap)

Ideas and contributions welcome.

---

## 9. Development setup

```bash
# Clone
git clone git@github.com:drmnaik/wip.git
cd wip

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode (includes all dependencies)
pip install -e .

# Run
wip --help
wip config init
wip
```

### Testing locally

```bash
# Point config at this repo to test
mkdir -p ~/.wip
cat > ~/.wip/config.toml << 'EOF'
directories = ["/path/to/your/projects"]
author = "Your Name"
scan_depth = 3
recent_days = 14
EOF

# Run the briefing
wip
wip --json
wip --verbose
```

---

## 10. Guidelines for contributors (human and AI)

### Before making changes

1. Read this file to understand architecture and conventions
2. Read the module you're changing — understand what's there before modifying
3. Check `pyproject.toml` for current dependencies and Python version constraints

### When writing code

1. Add `from __future__ import annotations` to every new `.py` file
2. Use dataclasses for data, plain functions for logic
3. Keep modules focused — one responsibility per module
4. Handle errors gracefully; never let one bad repo crash the whole tool
5. Follow the existing import order: stdlib, third-party, local
6. No new dependencies without clear justification — prefer stdlib

### When adding CLI commands

1. Add commands to `cli.py` using `@app.command()` or a sub-Typer
2. Keep the command function thin — delegate to the relevant module
3. Use `typer.Option()` for flags, `typer.Argument()` for positional args
4. Interactive prompts go through `typer.prompt()`

### When adding new data to scans

1. Add fields to `RepoStatus` (or create a new dataclass if it's a separate concept)
2. Populate the field in `scan_repo()` in `scanner.py`
3. Render it in `_render_repo()` in `display.py`
4. Ensure it serializes correctly in `render_json()` (dataclasses.asdict handles this)

### When extending the worklist

1. Add fields to `WorkItem` in `worklist.py` with sensible defaults (for backward-compatible JSON)
2. Update `add_item()` to accept and populate the new field
3. Render it in `_render_work_item()` in `display.py`
4. Ensure it serializes correctly (dataclasses.asdict handles this)

### When adding a new LLM provider

1. Create `src/wip/llm/<provider>.py` with a class extending `LLMProvider`
2. Implement `complete()` (returns `LLMResponse`) and `stream()` (yields `str` chunks)
3. Map provider errors to `LLMAuthError`, `LLMRateLimitError`, `LLMError`
4. Use lazy imports for the provider SDK (catch `ImportError` with a helpful message)
5. Use lazy client creation (`_get_client()` pattern)
6. Set a `DEFAULT_MODEL` and `name` class attribute
7. Register in `llm/registry.py` `PROVIDERS` dict: `"name": ("dotted.class.path", "ENV_VAR_NAME")`

### When adding a new AI command

1. Add `@ai_app.command()` in `cli.py`
2. Use `_get_llm_provider()` to get the provider
3. Use `_scan_all()` to get repos + work items
4. Create a new `build_*_prompt()` in `llm/prompts.py` if needed
5. Use `_llm_call(provider, system, user)` for streaming with error handling

### When modifying config

1. Add the field to `WipConfig` with a sensible default
2. Update `load_config()` to read it with `.get(key, default)`
3. Update `save_config()` to write it
4. If it needs user input, add a prompt to `config_init()` in `cli.py`

### Commit conventions

- Short imperative subject line (e.g., "Add stale branch detection")
- Body explains _why_, not _what_
- One logical change per commit

---

## 11. Known limitations

- **No tests yet** — test suite is planned but not implemented
- **No parallel scanning** — repos are scanned sequentially (fine for <50 repos)
- **TOML writing is manual** — works for the flat config structure but would need a library for nested configs
- **`_tracking_name()` always returns "origin"** — should inspect the actual remote name
- **No Windows testing** — paths and shell assumptions are macOS/Linux
- **Only Anthropic provider implemented** — OpenAI and Gemini are stubs
- **`anthropic` is not in pyproject.toml dependencies** — installed separately. Provider gives clean error if missing.
- **LLM max_tokens is hardcoded to 1024** — should be configurable for longer responses
- **No token budget management** — large repos with many commits could exceed context limits

---

## 12. File-by-file reference

### `pyproject.toml`
Package metadata. Name: `wip-cli`. Entry point: `wip = "wip.cli:app"`. Build: Hatchling with src-layout.

### `src/wip/__init__.py`
Package marker. Exports `__version__ = "0.1.0"`.

### `src/wip/cli.py`
CLI entry point. Creates Typer app with `config` and `ai` subgroups. Default action (no subcommand) runs the briefing pipeline. Contains `_run_briefing()` which orchestrates config → discovery → scan → worklist → display. Also contains `add`, `done`, `list` commands for the WIP tracker, and `ai briefing`, `ai standup`, `ai ask` commands for LLM features. Helper `_get_llm_provider()` resolves provider from config, `_scan_all()` runs the scan pipeline, `_llm_call()` handles streaming with error handling.

### `src/wip/config.py`
Config management. `WipConfig` dataclass (includes nested `LLMConfig` and `AgentsConfig`). `load_config()` reads TOML including `[llm]` and `[agents]` sections. `save_config()` writes TOML (agents section only written if non-default). `detect_git_author()` runs `git config user.name`. Config lives at `~/.wip/config.toml`.

### `src/wip/discovery.py`
Repo discovery. `discover_repos()` is the public API. `_walk_for_repos()` does recursive traversal. Stops at `.git/` dirs, skips junk directories, deduplicates.

### `src/wip/scanner.py`
Git scanner. `scan_repo()` collects all status for one repo including agent session detection. `scan_repos()` iterates over multiple. Key dataclasses: `FileChange`, `CommitInfo`, `BranchInfo`, `AgentSession`, `RepoStatus`. Helper functions: `_collect_stashes()` (returns count + descriptions), `_collect_changed_files()` (staged/unstaged/untracked with diff stats), `_parse_numstat()` (parses `git diff --numstat` output), `_ahead_behind()`, `_recent_branches()`, `_recent_commits()`, `_detect_agent_sessions()`, `_match_author_agent()`, `_match_branch_agent()`, `_time_ago()`. Agent detection iterates all local branches, matches commit authors and branch prefixes against configurable patterns, groups into sessions with status (active/recent/stale). All wrapped in try/except for resilience.

### `src/wip/display.py`
Terminal rendering. `render_briefing()` for human output. `render_json()` for machine output. `_render_repo()` handles one repo's display with status icons and colors, including agent sessions (color-coded: green=active, yellow=recent, red=stale), verbose changed files (color-coded by stage: green=staged, yellow=untracked, dim=unstaged with insertions/deletions), and verbose stash descriptions. `_render_agent_session()` renders a single agent session line. `render_worklist()` renders the WIP items section. `_render_work_item()` renders a single item with done/open styling. Items also appear under their linked repos.

### `src/wip/worklist.py`
WIP task tracker. `WorkItem` dataclass. `load_worklist()`/`save_worklist()` handle JSON persistence at `~/.wip/worklist.json`. `add_item()` creates items with auto-incrementing IDs. `complete_item()` marks done. `get_items()` and `get_items_for_repo()` provide filtered queries. `detect_repo()` walks cwd upward to find the nearest git repo root.

### `src/wip/llm/__init__.py`
Package re-exports: `LLMProvider`, `LLMResponse`, `get_provider()`, `list_providers()`.

### `src/wip/llm/base.py`
Abstract base class `LLMProvider` with `complete()` and `stream()` methods. `LLMResponse` dataclass for responses. Error hierarchy: `LLMError` (base), `LLMAuthError` (bad key), `LLMRateLimitError` (429).

### `src/wip/llm/registry.py`
Maps provider names to classes with lazy imports. `get_provider()` resolves API key (explicit → provider env var → `WIP_LLM_API_KEY` fallback) and instantiates provider. `list_providers()` returns available names.

### `src/wip/llm/prompts.py`
Builds `(system, user)` prompt pairs from scan data. `build_context()` formats repos + work items as text. `build_briefing_prompt()`, `build_standup_prompt()`, `build_query_prompt()` wrap context in task-specific templates. `_format_repo()` converts a single `RepoStatus` to readable text including changed files with diff stats, stash descriptions, agent activity sections, commit bodies (capped at 3 lines), and per-commit file lists (capped at 10 paths).

### `src/wip/llm/anthropic.py`
Anthropic Claude provider. Lazy client creation. `complete()` returns `LLMResponse`. `stream()` yields text chunks via `messages.stream()`. Maps Anthropic exceptions to `LLMAuthError`/`LLMRateLimitError`/`LLMError`. Default model: `claude-sonnet-4-5-20250929`.

### `src/wip/llm/openai.py`
OpenAI GPT provider stub. `complete()` and `stream()` raise `NotImplementedError` with TODO comments. Default model: `gpt-4o`.

### `src/wip/llm/gemini.py`
Google Gemini provider stub. `complete()` and `stream()` raise `NotImplementedError` with TODO comments. Default model: `gemini-2.0-flash`.
