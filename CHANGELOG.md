# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-02-12

### Added

- **Foundation & Scanner (Phase 0+1):** Config management (TOML read/write, interactive init), repo discovery, git status scanning (branch, dirty, stash, ahead/behind, recent branches/commits), Rich terminal display, CLI wiring (`wip`, `wip scan`, `wip config`, `--json`, `--verbose`)
- **Interactive Worklist (Phase 2):** `wip add/done/list` commands with repo linking, persistent JSON state, worklist shown in briefing and under linked repos
- **LLM Integration (Phase 4):** Provider abstraction (Anthropic implemented, OpenAI/Gemini stubs), `wip ai briefing`, `wip ai standup`, `wip ai ask` with streaming, prompt assembly from scan data, config-driven provider/model selection
- **Passive Agent Detection (Phase 5):** Detect coding agent activity from git signals (author names, branch patterns), agent sessions in terminal/JSON/AI output, configurable patterns with sensible defaults, status tracking (active/recent/stale)
- **Enriched File-Level Context (Phase 6):** Changed files with diff stats, stash descriptions, commit bodies and per-commit file lists in verbose output and LLM prompts

[0.1.0]: https://github.com/drmnaik/wip/releases/tag/v0.1.0
