# CLAUDE.md — Agent instructions for wip

> Read `docs/CONTEXT.md` for full project architecture, data models, and roadmap.

## Quick reference

- **What:** CLI morning briefing tool for developers — scans git repos, shows status
- **Stack:** Python 3.9+, Typer (CLI), GitPython (git), Rich (display), TOML (config)
- **Build:** Hatchling, src-layout (`src/wip/`), entry point `wip = "wip.cli:app"`
- **Config:** `~/.wip/config.toml`

## Rules

1. Every `.py` file MUST start with `from __future__ import annotations`
2. Python 3.9 minimum — no match/case, no `TypeAlias`, no 3.10+ features
3. Use dataclasses for data models, plain functions for logic — no service classes
4. Prefix private helpers with `_` — public API is everything without underscore
5. Wrap all GitPython calls in try/except — never crash because one repo is broken
6. No new dependencies without clear justification — prefer stdlib
7. CLI commands go in `cli.py`, keep them thin, delegate to modules
8. Errors use `raise typer.Exit(1)`, user messages use `typer.echo()`

## Module map

| Module         | Does what                        | Key exports                                  |
|----------------|----------------------------------|----------------------------------------------|
| `cli.py`       | Commands, flags, orchestration   | `app`                                        |
| `config.py`    | TOML config read/write           | `WipConfig`, `load_config()`, `save_config()`|
| `discovery.py` | Find git repos on disk           | `discover_repos()`                           |
| `scanner.py`   | Collect git status per repo      | `RepoStatus`, `scan_repo()`, `scan_repos()`  |
| `display.py`   | Rich terminal output             | `render_briefing()`, `render_json()`         |

## How to extend

- **New scan data:** Add field to `RepoStatus` → populate in `scan_repo()` → render in `_render_repo()`
- **New config field:** Add to `WipConfig` with default → update `load_config()`/`save_config()` → optionally add prompt in `config_init()`
- **New CLI command:** Add `@app.command()` in `cli.py` → delegate to relevant module

## Commands

```bash
pip install -e .          # Install in dev mode
wip                       # Run briefing
wip --json                # JSON output
wip --verbose             # Full detail
wip config init           # Interactive setup
wip config show           # Show config
```
