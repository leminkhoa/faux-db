from __future__ import annotations

from pathlib import Path

import click

from ...core.project_init.scaffold import init_project
from ..console import console, print_init_summary
from ..help import CONTEXT_SETTINGS, INIT_HELP


@click.command("init", context_settings=CONTEXT_SETTINGS, help=INIT_HELP)
@click.argument(
    "path",
    required=False,
    default=Path("."),
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
)
@click.option("--force", is_flag=True, help="Overwrite starter files if they already exist.")
def init_command(path: Path, force: bool) -> None:
    """Create a starter Kuriboh project structure."""
    try:
        with console.status("Creating starter Kuriboh project..."):
            summary = init_project(path, force=force)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    print_init_summary(summary)
