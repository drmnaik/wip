# wip — Developer situational awareness for the agentic coding era

![PyPI](https://img.shields.io/pypi/v/wip-cli) ![Python](https://img.shields.io/pypi/pyversions/wip-cli) ![License](https://img.shields.io/github/license/drmnaik/wip) ![Privacy](https://img.shields.io/badge/privacy-no_telemetry-green) ![Data](https://img.shields.io/badge/data-local_only_by_default-blue)

AI agents ship code while you sleep. They merge PRs, create branches, and push commits across your repos — and you need to know what happened. **wip** scans your git repositories, passively detects agent activity (Claude, Copilot, Cursor, Devin), and gives you a complete picture: what changed, what's dirty, what's stashed, and what needs your attention. With AI-powered briefings, it turns raw git signals into narrative summaries so you can pick up exactly where you — and your agents — left off.

## Demo

![demo](assets/demo.gif)

## Features

- 🕵️ **Agent detection** — passively detect coding agent activity (Claude, Copilot, Cursor, Devin) from git signals, with active/recent/stale status tracking
- 🤖 **AI-powered briefings** — narrative summaries, standup drafts, natural language queries — all agent-aware
- 🧭 **Context-aware git help** — ask how to untangle branches, recover stashes, or fix mistakes — the AI sees your actual repo state
- 🔌 **Multi-provider LLM** — Anthropic, OpenAI, and Gemini all implemented
- 🔍 **Auto-discover** git repos in configured directories
- 📊 **Status overview** — dirty files, stashes, ahead/behind tracking
- 🌿 **Recent branches** — see branches you've touched recently
- 💬 **Recent commits** — your commits from the last 24 hours
- 📂 **Enriched file-level context** — changed files with diff stats, stash descriptions, commit bodies and file lists
- 📝 **Work-in-progress tracker** — jot down tasks, link them to repos, see them in your briefing
- 🎨 **Rich terminal output** — color-coded status with icons
- 📦 **Multiple output modes** — human-friendly or JSON for scripting

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

### 1. Set up wip (interactive)

```bash
wip config init
```

This walks you through:
- **Directories** — which folders to scan for git repos
- **Author name** — your git identity (auto-detected from `git config`)
- **LLM provider** — optional, enables AI-powered briefings (Anthropic, OpenAI, or Gemini)

### 2. Run your first briefing

```bash
wip                # Show briefing
wip --verbose      # Full details
wip --json         # JSON output for scripting
```

### 3. Set up an LLM provider (optional)

AI features (`wip ai briefing`, `wip ai standup`, `wip ai ask`) require an LLM provider. You can configure this during `wip config init`, or manually — pick one below.

#### Anthropic (Claude)

1. Get an API key at [console.anthropic.com](https://console.anthropic.com/)
2. Export it: `export ANTHROPIC_API_KEY="sk-ant-..."`
3. Add to your config:
```toml
[llm]
provider = "anthropic"
model = "claude-haiku-4-5-20251001"
api_key_env = "ANTHROPIC_API_KEY"
```

#### OpenAI (GPT)

1. Get an API key at [platform.openai.com](https://platform.openai.com/api-keys)
2. Export it: `export OPENAI_API_KEY="sk-..."`
3. Add to your config:
```toml
[llm]
provider = "openai"
model = "gpt-4o"
api_key_env = "OPENAI_API_KEY"
```

#### Google Gemini

1. Get an API key at [aistudio.google.com](https://aistudio.google.com/apikey)
2. Export it: `export GEMINI_API_KEY="..."`
3. Add to your config:
```toml
[llm]
provider = "gemini"
model = "gemini-2.0-flash"
api_key_env = "GEMINI_API_KEY"
```

> **Tip:** Add the `export` line to your `~/.bashrc` or `~/.zshrc` so the key persists across sessions. Leave `model` empty to use the provider's default.

## Configuration Reference

Config is stored at `~/.wip/config.toml`. You can edit it directly or re-run `wip config init`. View current settings with `wip config show`.

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

| Field | Description | Default |
|-------|-------------|---------|
| `directories` | Folders to scan for git repos | current directory |
| `author` | Your git author name (filters commits) | auto-detected |
| `scan_depth` | How deep to recurse into directories | `3` |
| `recent_days` | Lookback window for recent branches | `14` |
| `[llm] provider` | `anthropic`, `openai`, or `gemini` | — |
| `[llm] model` | Model ID (empty = provider default) | — |
| `[llm] api_key_env` | Env var name holding your API key | — |
| `[agents] authors` | Substrings matched against commit author names | Claude, Copilot, Cursor, Devin, etc. |
| `[agents] branch_patterns` | Branch prefixes indicating agent activity | `agent/`, `claude/`, `copilot/`, etc. |

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

### auth-service
Claude was busy overnight — 12 commits on agent/add-tests, touching
14 files. It added unit tests for the token refresh flow and the retry
logic you were working on. The branch is still active (last commit 23m ago).
Meanwhile, you have 3 dirty files on fix/token-refresh with a stash that
looks like an alternative approach. Review Claude's test coverage before
resuming your fix — there may be overlap.

### frontend
Clean, nothing to do here. You left a TODO about form validation on
Tuesday but no urgency.

### api-gateway
3 commits behind origin — just needs a pull. Your note says to update
the API docs once auth-service lands.

Suggested focus: review Claude's agent/add-tests branch in auth-service,
then resume your token refresh fix.
```

### Status Icons

- ✓ — Clean repo, up to date
- ⚠ — Dirty files (modified, staged, or untracked)
- ↓ — Behind remote (needs pull)

## Privacy

- `wip scan` runs entirely locally — no data leaves your machine.
- `wip ai` commands send repository metadata (commit messages, branch names, file paths, work items) to your configured LLM provider (Anthropic, OpenAI, or Gemini). No file contents or diffs are sent.
- API keys are never stored in config — only the environment variable name is saved.

## Development

```bash
# Install dependencies
pip install -e .

# Run from source
python -m wip.cli
```

## Roadmap

**Phase 1: Foundation + Scanner** ✅
- Config management, repo discovery, git status scanning, terminal output

**Phase 2: Interactive Worklist** ✅
- `wip add/done/list` commands with repo linking and persistent state

**Phase 3: LLM Integration** ✅
- Provider abstraction (Anthropic, OpenAI, and Gemini all implemented)
- `wip ai briefing`, `wip ai standup`, `wip ai ask` with streaming
- Prompt assembly from scan data, config-driven provider/model selection

**Phase 4: Passive Agent Detection** ✅
- Detect coding agent activity from git signals (author names, branch patterns)
- Agent sessions surface in `wip`, `wip --json`, and all AI commands automatically
- Configurable author/branch patterns with sensible defaults (zero config required)
- Status tracking: active (<1h), recent (<24h), stale (>24h)

**Phase 5: Enriched File-Level Context** ✅
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
