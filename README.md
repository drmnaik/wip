# wip — Where did I leave off?

A developer briefing tool. **wip** scans your git repositories and shows you what you were working on, what's dirty, what's stashed, and what needs your attention. With optional AI features, it turns raw git data into narrative briefings, standup drafts, and answers to natural language questions about your work.

## Features

- 🔍 **Auto-discover** git repos in configured directories
- 📊 **Status overview** — dirty files, stashes, ahead/behind tracking
- 🌿 **Recent branches** — see branches you've touched recently
- 💬 **Recent commits** — your commits from the last 24 hours
- 📝 **Work-in-progress tracker** — jot down tasks, link them to repos, see them in your briefing
- 🎨 **Rich terminal output** — color-coded status with icons
- 📦 **Multiple output modes** — human-friendly or JSON for scripting
- 🕵️ **Agent detection** — passively detect coding agent activity (Claude, Copilot, Cursor, Devin) from git signals
- 📂 **Enriched file-level context** — changed files with diff stats, stash descriptions, commit bodies and file lists in LLM prompts and verbose output
- 🤖 **AI-powered briefings** — narrative summaries, standup drafts, natural language queries
- 🧭 **Context-aware git help** — ask how to untangle branches, recover stashes, or fix mistakes — the AI sees your actual repo state
- 🔌 **Provider abstraction** — Anthropic and OpenAI implemented, Gemini — all implemented

## Installation

### From PyPI (recommended)

```bash
pip install wip-cli
```

Or with [pipx](https://pipx.pypa.io/) for an isolated install:

```bash
pipx install wip-cli
```

### From source

```bash
git clone git@github.com:drmnaik/wip.git
cd wip
pip install -e .
```

**Requirements:** Python 3.9+
**PyPI:** https://pypi.org/project/wip-cli/

## Quick Start

```bash
# First-time setup (interactive)
wip config init

# Show your briefing
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

[llm]
provider = "anthropic"
model = "claude-haiku-4-5-20251001"
api_key_env = "ANTHROPIC_API_KEY"

# Optional: customize agent detection patterns
[agents]
authors = ["claude", "copilot", "cursor", "devin", "codex", "github-actions", "bot"]
branch_patterns = ["agent/", "claude/", "copilot/", "devin/", "cursor/"]
```

- **directories** — which directories to scan for git repos
- **author** — your git author name (filters commits to show only yours)
- **scan_depth** — how deep to search for repos (default: 3 levels)
- **recent_days** — how far back to look for recent branches (default: 14 days)
- **[llm]** — optional LLM configuration for AI features
  - **provider** — `anthropic`, `openai`, or `gemini`
  - **model** — model ID (leave empty for provider default)
  - **api_key_env** — environment variable name holding your API key
- **[agents]** — optional overrides for agent detection (works out of the box with defaults)
  - **authors** — substrings matched case-insensitively against commit author names
  - **branch_patterns** — branch name prefixes that indicate agent activity

## Commands

### Core

```bash
wip               # Show briefing (default command)
wip scan          # Alias for wip
wip --json        # Output as JSON
wip --verbose     # Show full details
wip config init   # Interactive setup
wip config show   # Display current config
wip version       # Show version
```

### Work-in-progress tracker

```bash
wip add "fix auth bug"                     # Add item (auto-links to current repo)
wip add "read docs" --repo /path/to/repo   # Add item linked to specific repo
wip done 1                                 # Mark item #1 as done
wip list                                   # Show open items
wip list --all                             # Show all items including completed
```

### AI-powered commands

Requires an LLM provider configured in `~/.wip/config.toml` and the corresponding API key set as an environment variable.

```bash
wip ai briefing                 # Narrative briefing
wip ai standup                  # Generate a standup update from git activity
wip ai ask "what was I working on yesterday?"
wip ai ask "anything I forgot to push?"
wip ai ask "summarize my week"

# Context-aware git help — the AI sees your actual branches, dirty files, and stashes
wip ai ask "I have diverged branches, how do I cleanly get back to main?"
wip ai ask "how do I recover what I stashed last week?"
wip ai ask "what git commands do I need to untangle this mess?"
```

## Example Output

### Standard briefing (`wip`)

```
 wip — 3 repos scanned

 work-in-progress — 2 items

  #1  fix auth token refresh (auth-service) — 2h ago
  #3  update API docs (api-gateway) — 1d ago

auth-service (fix/token-refresh) ⚠
  3 dirty · 1 stash · last commit 14h ago
  2 ahead, 0 behind origin
  agents:
    claude on agent/add-tests — 12 commits, 14 files (23m ago) ● active
    copilot on copilot/logout — 4 commits, 3 files (7h ago) ○ stale
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

### AI briefing (`wip ai briefing`)

```
## Briefing

You were deep in a token refresh bug in auth-service yesterday evening.
You changed the retry logic in 3 files but stashed something — probably
an alternative approach. Your note says the issue is around line 340.
You might want to start by comparing your stash against your current changes.

The frontend is clean but you left a TODO about form validation on Tuesday.
api-gateway just needs a pull — 3 commits behind, low priority.

Suggested focus: finish auth-service first (uncommitted work at risk),
then circle back to the frontend TODO.
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
- Config management, repo discovery, git status scanning, terminal output

**Phase 2: Interactive Worklist** ✅
- `wip add/done/list` commands with repo linking and persistent state

**Phase 4: LLM Integration** ✅
- Provider abstraction (Anthropic, OpenAI, and Gemini all implemented)
- `wip ai briefing`, `wip ai standup`, `wip ai ask` with streaming
- Prompt assembly from scan data, config-driven provider/model selection

**Phase 5: Passive Agent Detection** ✅
- Detect coding agent activity from git signals (author names, branch patterns)
- Agent sessions surface in `wip`, `wip --json`, and all AI commands automatically
- Configurable author/branch patterns with sensible defaults (zero config required)
- Status tracking: active (<1h), recent (<24h), stale (>24h)

**Phase 6: Enriched File-Level Context** ✅
- Changed files with diff stats (insertions/deletions), color-coded by stage in verbose output
- Stash descriptions surfaced in verbose display and LLM prompts
- Commit bodies (capped at 3 lines) and per-commit file lists (capped at 10 paths) in LLM context

Ideas and contributions welcome — see `docs/CONTEXT.md` for architecture details.

## Contact

- **LinkedIn:** [Mahesh Naik](https://www.linkedin.com/in/kamaheshnaik/)
- **Issues:** [GitHub Issues](https://github.com/drmnaik/wip/issues)

## License

MIT

## Author

Built by Mahesh Naik with Claude
