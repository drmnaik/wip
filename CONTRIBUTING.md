# Contributing to wip

Thanks for your interest in contributing to **wip**! This guide will help you get started.

## Prerequisites

- Python 3.9+
- git

## Dev Setup

```bash
# Fork and clone
git clone git@github.com:<your-username>/wip.git
cd wip

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .

# Optional: AI features
pip install anthropic
```

## Code Conventions

Please read `docs/CONTEXT.md` — specifically **Section 5 (Code conventions)** and **Section 10 (Guidelines for contributors)** — for the full picture. Key rules:

- Every `.py` file **must** start with `from __future__ import annotations`
- Use **dataclasses** for data models, plain functions for logic
- No new dependencies without clear justification — prefer stdlib
- Handle errors gracefully — never crash the whole briefing because one repo is broken
- Follow existing import order: stdlib, third-party, local (`wip.*`)
- Keep CLI commands thin — delegate logic to modules

## Submitting a Pull Request

1. **Fork** the repo and create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature main
   ```
2. Make your changes following the code conventions above.
3. **Commit** with a short imperative subject line (e.g., "Add stale branch detection"). Body explains _why_, not _what_.
4. **Push** to your fork:
   ```bash
   git push origin feat/your-feature
   ```
5. Open a **Pull Request** against `main` on GitHub.

## Good First Issues

Looking for a place to start? These are great entry points:

- **Implement the OpenAI provider** — `src/wip/llm/openai.py` is scaffolded as a stub
- **Implement the Gemini provider** — `src/wip/llm/gemini.py` is scaffolded as a stub
- **Add test coverage** — there are no tests yet; adding tests for any module is valuable

## Contact

- **LinkedIn:** [Mahesh Naik](https://www.linkedin.com/in/kamaheshnaik/)
- **Issues:** [GitHub Issues](https://github.com/drmnaik/wip/issues)
