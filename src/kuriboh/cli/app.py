from __future__ import annotations

import click

from .commands import config_group, generate_command, init_command, schema_group
from .help import CONTEXT_SETTINGS, ROOT_HELP


@click.group(
    context_settings=CONTEXT_SETTINGS,
    help=ROOT_HELP,
)
def cli() -> None:
    """Generate sample data and validate Kuriboh projects."""


cli.add_command(init_command)
cli.add_command(config_group)
cli.add_command(schema_group)
cli.add_command(generate_command)


def main() -> None:
    cli()
