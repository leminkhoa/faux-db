from __future__ import annotations

from pathlib import Path

import click

from ...core.validation import validate_project
from ..console import console, print_validation_summary
from ..help import CONFIG_HELP, CONFIG_VALIDATE_HELP, CONTEXT_SETTINGS


@click.group("config", context_settings=CONTEXT_SETTINGS, help=CONFIG_HELP)
def config_group() -> None:
    """Inspect and validate project configuration."""


@config_group.command("validate", context_settings=CONTEXT_SETTINGS, help=CONFIG_VALIDATE_HELP)
@click.argument(
    "path",
    required=False,
    default=Path("."),
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
)
def validate_config_command(path: Path) -> None:
    """Validate providers, catalogs, and schemas under a project root."""
    try:
        with console.status("Validating project configuration..."):
            summary = validate_project(path)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    print_validation_summary(summary)
