"""CLI entry point for wip."""

from __future__ import annotations

import os
from pathlib import Path

import typer

from wip.config import WipConfig, load_config, save_config, detect_git_author, CONFIG_PATH
from wip.discovery import discover_repos
from wip.scanner import scan_repos
from wip.display import render_briefing, render_json
from wip.worklist import (
    add_item,
    complete_item,
    detect_repo,
    get_items,
    get_items_for_repo,
)

app = typer.Typer(
    name="wip",
    help="Where did I leave off? A morning briefing for developers.",
    no_args_is_help=False,
)

config_app = typer.Typer(help="Manage wip configuration.")
app.add_typer(config_app, name="config")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    output_json: bool = typer.Option(False, "--json", help="Output as JSON."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full detail."),
):
    """Show your morning briefing."""
    if ctx.invoked_subcommand is not None:
        return

    _run_briefing(output_json=output_json, verbose=verbose)


@app.command()
def scan(
    output_json: bool = typer.Option(False, "--json", help="Output as JSON."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full detail."),
):
    """Scan repos and show briefing (same as running `wip` with no args)."""
    _run_briefing(output_json=output_json, verbose=verbose)


@app.command()
def version():
    """Show the current version."""
    typer.echo("wip v0.1.0")


@app.command()
def add(
    description: str = typer.Argument(..., help="What are you working on?"),
    repo: str = typer.Option(None, "--repo", "-r", help="Repo path (auto-detected if inside one)."),
):
    """Add a work-in-progress item."""
    if repo is None:
        repo = detect_repo()
    elif repo is not None:
        repo = os.path.realpath(repo)

    item = add_item(description, repo=repo)
    repo_label = f" ({Path(item.repo).name})" if item.repo else ""
    typer.echo(f"Added #{item.id}: {item.description}{repo_label}")


@app.command()
def done(
    item_id: int = typer.Argument(..., help="Item ID to mark as done."),
):
    """Mark a work-in-progress item as done."""
    item = complete_item(item_id)
    if item is None:
        typer.echo(f"Item #{item_id} not found or already done.")
        raise typer.Exit(1)
    typer.echo(f"Done #{item.id}: {item.description}")


@app.command(name="list")
def list_items(
    all_items: bool = typer.Option(False, "--all", "-a", help="Include completed items."),
):
    """List work-in-progress items."""
    from wip.display import render_worklist

    items = get_items(include_done=all_items)
    if not items:
        typer.echo("No items." if not all_items else "No items found.")
        return

    render_worklist(items)


@config_app.command("init")
def config_init():
    """Set up wip configuration interactively."""
    import os

    typer.echo("Setting up wip configuration...\n")

    # Directories
    default_dir = os.getcwd()
    dirs_input = typer.prompt(
        "Which directories should wip scan? (comma-separated)",
        default=default_dir,
    )
    directories = [d.strip() for d in dirs_input.split(",") if d.strip()]

    # Author
    detected = detect_git_author()
    default_author = detected if detected else ""
    prompt_text = "What is your git author name?"
    if detected:
        prompt_text += f" (detected: {detected})"
    author = typer.prompt(prompt_text, default=default_author)

    config = WipConfig(directories=directories, author=author)
    save_config(config)
    typer.echo(f"\nConfig saved to {CONFIG_PATH}")


@config_app.command("show")
def config_show():
    """Print the current configuration."""
    if not CONFIG_PATH.exists():
        typer.echo("No config found. Run `wip config init` to create one.")
        raise typer.Exit(1)

    config = load_config()
    typer.echo(f"Config: {CONFIG_PATH}\n")
    typer.echo(f"directories = {config.directories}")
    typer.echo(f"author      = {config.author}")
    typer.echo(f"scan_depth  = {config.scan_depth}")
    typer.echo(f"recent_days = {config.recent_days}")


def _run_briefing(output_json: bool = False, verbose: bool = False) -> None:
    config = load_config()

    if not config.directories:
        typer.echo("No directories configured. Run `wip config init` to get started.")
        raise typer.Exit(1)

    repo_paths = discover_repos(config.directories, config.scan_depth)

    if not repo_paths:
        typer.echo("No git repos found in configured directories.")
        raise typer.Exit(0)

    results = scan_repos(repo_paths, config.author, config.recent_days)

    wip_items = get_items()

    # Build repo -> items mapping
    repo_items: dict[str, list] = {}
    for repo in results:
        items_for_repo = get_items_for_repo(repo.path)
        if items_for_repo:
            repo_items[repo.path] = items_for_repo

    if output_json:
        render_json(results, wip_items=wip_items)
    else:
        render_briefing(results, verbose=verbose, wip_items=wip_items, repo_items=repo_items)


if __name__ == "__main__":
    app()
