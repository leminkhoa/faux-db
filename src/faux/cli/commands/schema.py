from __future__ import annotations

from pathlib import Path

import click

from ..console import console, print_generation_summary
from ..help import CONTEXT_SETTINGS, SCHEMA_GENERATE_HELP, SCHEMA_HELP
from .common import dispatch_generate


@click.group("schema", context_settings=CONTEXT_SETTINGS, help=SCHEMA_HELP)
def schema_group() -> None:
    """Generate data from schema files or domain directories."""


@schema_group.command("generate", context_settings=CONTEXT_SETTINGS, help=SCHEMA_GENERATE_HELP)
@click.argument("path", type=click.Path(path_type=Path))
def generate_schema_command(path: Path) -> None:
    """Generate data from a schema file or schema directory."""
    with console.status("Generating data from schema..."):
        target_kind = dispatch_generate(path)
    print_generation_summary(path, target_kind)


@click.command("generate", hidden=True, context_settings=CONTEXT_SETTINGS)
@click.argument("path", type=click.Path(path_type=Path))
def generate_command(path: Path) -> None:
    """Backward-compatible alias for schema generate."""
    with console.status("Generating data from schema..."):
        target_kind = dispatch_generate(path)
    print_generation_summary(path, target_kind)
