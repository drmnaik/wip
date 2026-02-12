# wip — Project Context & Development Guide

> This file is the single source of truth for understanding, contributing to, and extending the `wip` project. It is written for both human developers and AI coding agents.

---

## 1. What is wip?

**wip** ("Where did I leave off?") is a CLI tool that gives developers a morning briefing. It scans local git repositories and surfaces what you were working on: dirty files, stashes, branches, recent commits, and sync status with remotes.

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
| `wip --verbose`     | Show all branches and full commit messages       |

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
        └── display.py      # Rich-based terminal rendering
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
    │
    └── display.py: render_briefing()   → terminal output (Rich)
            or render_json()            → JSON to stdout
```

### Module responsibilities

| Module         | Responsibility                              | Key exports                                    |
|----------------|---------------------------------------------|------------------------------------------------|
| `cli.py`       | Command routing, flags, user interaction     | `app` (Typer instance)                         |
| `config.py`    | Read/write `~/.wip/config.toml`, defaults    | `WipConfig`, `load_config()`, `save_config()`, `detect_git_author()`, `CONFIG_PATH` |
| `discovery.py` | Find git repos in filesystem                 | `discover_repos(directories, depth)`           |
| `scanner.py`   | Collect git status for each repo             | `RepoStatus`, `BranchInfo`, `CommitInfo`, `scan_repo()`, `scan_repos()` |
| `display.py`   | Render output to terminal or JSON            | `render_briefing(repos, verbose)`, `render_json(repos)` |

---

## 3. Data models

### WipConfig (config.py)

```python
@dataclass
class WipConfig:
    directories: list[str]   # Paths to scan, e.g. ["~/projects", "~/work"]
    author: str              # Git author name for filtering commits
    scan_depth: int          # How deep to recurse (default: 3)
    recent_days: int         # Lookback window for branches (default: 14)
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
```

### BranchInfo (scanner.py)

```python
@dataclass
class BranchInfo:
    name: str               # Branch name
    last_commit_ago: str    # Human-readable time since branch's last commit
    timestamp: float        # Unix timestamp (for sorting)
```

### CommitInfo (scanner.py)

```python
@dataclass
class CommitInfo:
    sha: str                # Short (7-char) commit hash
    message: str            # First line of commit message
    ago: str                # Human-readable time since commit
    timestamp: float        # Unix timestamp (for sorting)
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
```

### TOML handling

- **Reading:** `tomllib` (stdlib on 3.11+) with `tomli` fallback (3.9/3.10)
- **Writing:** manual string formatting (no TOML writer library). The config structure is flat enough that simple f-string generation is sufficient
- If no config file exists, `load_config()` returns a `WipConfig` with empty defaults

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

### Phase 2: Interactive Worklist (PLANNED)

- Track work-in-progress items across repos
- `wip add "task description"` — add a WIP item
- `wip done <id>` — mark item complete
- Persistent state in `~/.wip/state.json`
- Show WIP items in the briefing

### Phase 3: Smart Suggestions (PLANNED)

- Detect stale branches (no commits in >30 days)
- Warn about uncommitted work in repos you haven't touched recently
- Suggest "you might want to pull" when behind remote
- Suggest "you left off on branch X" based on most recent activity

### Phase 4: Extensions (FUTURE)

- Plugin system for custom scanners
- GitHub/GitLab integration (open PRs, assigned issues)
- Team mode (share state across machines)

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
- **Stash count calls git twice** — `repo.git.stash("list")` is called in the conditional and again for splitlines
- **`_tracking_name()` always returns "origin"** — should inspect the actual remote name
- **No Windows testing** — paths and shell assumptions are macOS/Linux

---

## 12. File-by-file reference

### `pyproject.toml`
Package metadata. Name: `wip-cli`. Entry point: `wip = "wip.cli:app"`. Build: Hatchling with src-layout.

### `src/wip/__init__.py`
Package marker. Exports `__version__ = "0.1.0"`.

### `src/wip/cli.py`
CLI entry point. Creates Typer app with `config` subgroup. Default action (no subcommand) runs the briefing pipeline. Contains `_run_briefing()` which orchestrates config → discovery → scan → display.

### `src/wip/config.py`
Config management. `WipConfig` dataclass. `load_config()` reads TOML. `save_config()` writes TOML. `detect_git_author()` runs `git config user.name`. Config lives at `~/.wip/config.toml`.

### `src/wip/discovery.py`
Repo discovery. `discover_repos()` is the public API. `_walk_for_repos()` does recursive traversal. Stops at `.git/` dirs, skips junk directories, deduplicates.

### `src/wip/scanner.py`
Git scanner. `scan_repo()` collects all status for one repo. `scan_repos()` iterates over multiple. Helper functions: `_count_stashes()`, `_ahead_behind()`, `_recent_branches()`, `_recent_commits()`, `_time_ago()`. All wrapped in try/except for resilience.

### `src/wip/display.py`
Terminal rendering. `render_briefing()` for human output. `render_json()` for machine output. `_render_repo()` handles one repo's display with status icons and colors.
