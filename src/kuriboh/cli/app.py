from __future__ import annotations

import click
from importlib.metadata import PackageNotFoundError, version

from .commands import config_group, generate_command, init_command, schema_group
from .help import CONTEXT_SETTINGS, ROOT_HELP


def _pkg_version() -> str:
    try:
        return version("kuriboh-faker")
    except PackageNotFoundError:
        # Fallback for editable/dev contexts where distribution metadata may be absent.
        return "0+unknown"


@click.group(
    context_settings=CONTEXT_SETTINGS,
    help=ROOT_HELP,
)
@click.version_option(version=_pkg_version(), prog_name="kuriboh", message=_pkg_version())
def cli() -> None:
    """Generate sample data and validate Kuriboh projects."""


cli.add_command(init_command)
cli.add_command(config_group)
cli.add_command(schema_group)
cli.add_command(generate_command)


def main() -> None:
    cli()
