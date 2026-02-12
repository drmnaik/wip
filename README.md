# wip — Where did I leave off?

A morning briefing for developers. **wip** scans your git repositories and shows you what you were working on, what's dirty, what's stashed, and what needs your attention.

## Features

- 🔍 **Auto-discover** git repos in configured directories
- 📊 **Status overview** — dirty files, stashes, ahead/behind tracking
- 🌿 **Recent branches** — see branches you've touched recently
- 💬 **Recent commits** — your commits from the last 24 hours
- 📝 **Work-in-progress tracker** — jot down tasks, link them to repos, see them in your briefing
- 🎨 **Rich terminal output** — color-coded status with icons
- 📦 **Multiple output modes** — human-friendly or JSON for scripting

## Installation

```bash
# Clone the repository
git clone git@github.com:drmnaik/wip.git
cd wip

# Install in editable mode
pip install -e .
```

**Requirements:** Python 3.9+

## Quick Start

```bash
# First-time setup (interactive)
wip config init

# Show your morning briefing
wip

# Verbose mode with full details
wip --verbose

# JSON output for scripting
wip --json
```

## Configuration

Config is stored at `~/.wip/config.toml`:

```toml
directories = ["/Users/you/projects", "/Users/you/work"]
author = "Your Name"
scan_depth = 3
recent_days = 14
```

- **directories** — which directories to scan for git repos
- **author** — your git author name (filters commits to show only yours)
- **scan_depth** — how deep to search for repos (default: 3 levels)
- **recent_days** — how far back to look for recent branches (default: 14 days)

### Commands

```bash
wip               # Show briefing (default command)
wip scan          # Alias for wip
wip --json        # Output as JSON
wip --verbose     # Show full details
wip config init   # Interactive setup
wip config show   # Display current config
wip version       # Show version

# Work-in-progress tracker
wip add "fix auth bug"          # Add item (auto-links to current repo)
wip add "read docs" --repo /path/to/repo  # Add item linked to specific repo
wip done 1                      # Mark item #1 as done
wip list                        # Show open items
wip list --all                  # Show all items including completed
```

## Example Output

```
 wip — 3 repos scanned

 work-in-progress — 2 items

  #1  fix auth token refresh (auth-service) — 2h ago
  #3  update API docs (api-gateway) — 1d ago

auth-service (fix/token-refresh) ⚠
  3 dirty · 1 stash · last commit 14h ago
  2 ahead, 0 behind origin
  wip:
    #1 fix auth token refresh (2h ago)
  recent: main (3d), feat/oauth (5d)
  commits today:
    a1b2c3 fix retry logic for token refresh (2h ago)

frontend (main) ✓
  clean · 2 stashes
  0 ahead, 0 behind origin

api-gateway (main) ↓
  clean · 3 behind origin
  wip:
    #3 update API docs (1d ago)
```

### Status Icons

- ✓ — Clean repo, up to date
- ⚠ — Dirty files (modified, staged, or untracked)
- ↓ — Behind remote (needs pull)

## Development

```bash
# Install dependencies
pip install -e .

# Run from source
python -m wip.cli
```

## Roadmap

**Phase 0+1: Foundation + Scanner** ✅
- Config management
- Repo discovery
- Git status scanning
- Terminal output

**Phase 2: Interactive Worklist** ✅ (Current)
- `wip add/done/list` commands
- Items optionally linked to repos (auto-detected from cwd)
- Persistent state in `~/.wip/worklist.json`
- Worklist shown in briefing and under linked repos
- Completed items hidden by default (`--all` to show)

**Phase 3: Smart Suggestions** (Planned)
- Stale branch detection
- Uncommitted work alerts
- Intelligent next steps

## License

MIT

## Author

Built by Mahesh Naik with Claude Sonnet 4.5
