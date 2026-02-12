# wip — Where did I leave off?

A morning briefing for developers. **wip** scans your git repositories and shows you what you were working on, what's dirty, what's stashed, and what needs your attention.

## Features

- 🔍 **Auto-discover** git repos in configured directories
- 📊 **Status overview** — dirty files, stashes, ahead/behind tracking
- 🌿 **Recent branches** — see branches you've touched recently
- 💬 **Recent commits** — your commits from the last 24 hours
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
wip config init    # Interactive setup
wip config show    # Display current config
wip               # Show briefing (default command)
wip scan          # Alias for wip
wip --json        # Output as JSON
wip --verbose     # Show full details
wip version       # Show version
```

## Example Output

```
 wip — 3 repos scanned

auth-service (fix/token-refresh) ⚠
  3 dirty · 1 stash · last commit 14h ago
  2 ahead, 0 behind origin
  recent: main (3d), feat/oauth (5d)
  commits today:
    a1b2c3 fix retry logic for token refresh (2h ago)

frontend (main) ✓
  clean · 2 stashes
  0 ahead, 0 behind origin

api-gateway (main) ↓
  clean · 3 behind origin
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

**Phase 0+1: Foundation + Scanner** ✅ (Current)
- Config management
- Repo discovery
- Git status scanning
- Terminal output

**Phase 2: Interactive Worklist** (Coming soon)
- Track work-in-progress across repos
- Add/complete tasks
- Persist state

**Phase 3: Smart Suggestions** (Planned)
- Stale branch detection
- Uncommitted work alerts
- Intelligent next steps

## License

MIT

## Author

Built by Mahesh Naik with Claude Sonnet 4.5
