"""Configuration management for wip."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

CONFIG_DIR = Path.home() / ".wip"
CONFIG_PATH = CONFIG_DIR / "config.toml"

DEFAULTS = {
    "directories": [],
    "author": "",
    "scan_depth": 3,
    "recent_days": 14,
}


@dataclass
class AgentsConfig:
    authors: list[str] = field(default_factory=lambda: [
        "claude", "copilot", "cursor", "devin", "codex",
        "github-actions", "bot",
    ])
    branch_patterns: list[str] = field(default_factory=lambda: [
        "agent/", "claude/", "copilot/", "devin/", "cursor/",
    ])


@dataclass
class LLMConfig:
    provider: str = ""       # "anthropic", "openai", "gemini"
    model: str = ""          # provider-specific model ID (uses provider default if empty)
    api_key_env: str = ""    # env var name holding the key (e.g. "ANTHROPIC_API_KEY")


@dataclass
class WipConfig:
    directories: list[str] = field(default_factory=list)
    author: str = ""
    scan_depth: int = 3
    recent_days: int = 14
    llm: LLMConfig = field(default_factory=LLMConfig)
    agents: AgentsConfig = field(default_factory=AgentsConfig)


def load_config() -> WipConfig:
    """Load config from TOML file, falling back to defaults."""
    if not CONFIG_PATH.exists():
        return WipConfig()

    with open(CONFIG_PATH, "rb") as f:
        data = tomllib.load(f)

    llm_data = data.get("llm", {})
    llm_config = LLMConfig(
        provider=llm_data.get("provider", ""),
        model=llm_data.get("model", ""),
        api_key_env=llm_data.get("api_key_env", ""),
    )

    agents_data = data.get("agents", {})
    agents_defaults = AgentsConfig()
    agents_config = AgentsConfig(
        authors=agents_data.get("authors", agents_defaults.authors),
        branch_patterns=agents_data.get("branch_patterns", agents_defaults.branch_patterns),
    )

    return WipConfig(
        directories=data.get("directories", []),
        author=data.get("author", ""),
        scan_depth=data.get("scan_depth", 3),
        recent_days=data.get("recent_days", 14),
        llm=llm_config,
        agents=agents_config,
    )


def save_config(config: WipConfig) -> None:
    """Write config to TOML file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    lines = []
    # directories
    dir_items = ", ".join(f'"{d}"' for d in config.directories)
    lines.append(f"directories = [{dir_items}]")
    lines.append(f'author = "{config.author}"')
    lines.append(f"scan_depth = {config.scan_depth}")
    lines.append(f"recent_days = {config.recent_days}")

    # LLM section
    if config.llm.provider:
        lines.append("")
        lines.append("[llm]")
        lines.append(f'provider = "{config.llm.provider}"')
        if config.llm.model:
            lines.append(f'model = "{config.llm.model}"')
        if config.llm.api_key_env:
            lines.append(f'api_key_env = "{config.llm.api_key_env}"')

    # Agents section (only if non-default)
    defaults = AgentsConfig()
    if config.agents.authors != defaults.authors or config.agents.branch_patterns != defaults.branch_patterns:
        lines.append("")
        lines.append("[agents]")
        author_items = ", ".join(f'"{a}"' for a in config.agents.authors)
        lines.append(f"authors = [{author_items}]")
        pattern_items = ", ".join(f'"{p}"' for p in config.agents.branch_patterns)
        lines.append(f"branch_patterns = [{pattern_items}]")

    CONFIG_PATH.write_text("\n".join(lines) + "\n")


def detect_git_author() -> str:
    """Try to detect the git author name from global git config."""
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""
