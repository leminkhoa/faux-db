from __future__ import annotations

from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from ..core.project_init import InitSummary
from ..core.validation import ValidationSummary

console = Console()


def _render_paths_tree(title: str, paths: tuple[Path, ...], style: str) -> Tree:
    tree = Tree(f"[bold]{title}[/bold]")
    for path in paths:
        tree.add(f"[{style}]{path}[/]")
    return tree


def print_init_summary(summary: InitSummary) -> None:
    console.print(
        Panel.fit(
            f"[bold green]Initialized Kuriboh project[/bold green]\n[dim]{summary.base_dir}[/dim]",
            border_style="green",
        )
    )

    if summary.created_directories:
        console.print(_render_paths_tree("Directories", summary.created_directories, "cyan"))
    if summary.created_files:
        console.print(_render_paths_tree("Starter files", summary.created_files, "magenta"))


def print_validation_summary(summary: ValidationSummary) -> None:
    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("Item", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_row("Schema files", str(summary.schema_count))
    table.add_row("Domains", str(summary.domain_count))
    table.add_row("Providers", str(summary.provider_count))
    table.add_row("Catalogs", str(summary.catalog_count))

    console.print(
        Panel.fit(
            f"[bold green]Validated configuration[/bold green]\n[dim]{summary.base_dir}[/dim]",
            border_style="green",
        )
    )
    console.print(table)


def print_generation_summary(path: Path, target_kind: str) -> None:
    kind_label = "schema file" if target_kind == "file" else "schema domain"
    console.print(
        Panel.fit(
            f"[bold green]Generation complete[/bold green]\n"
            f"[dim]{kind_label}: {path.resolve()}[/dim]",
            border_style="green",
        )
    )
