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
class WipConfig:
    directories: list[str] = field(default_factory=list)
    author: str = ""
    scan_depth: int = 3
    recent_days: int = 14


def load_config() -> WipConfig:
    """Load config from TOML file, falling back to defaults."""
    if not CONFIG_PATH.exists():
        return WipConfig()

    with open(CONFIG_PATH, "rb") as f:
        data = tomllib.load(f)

    return WipConfig(
        directories=data.get("directories", []),
        author=data.get("author", ""),
        scan_depth=data.get("scan_depth", 3),
        recent_days=data.get("recent_days", 14),
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
