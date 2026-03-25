from __future__ import annotations

from pathlib import Path

import click

from ...core.engine import run_domain, run_generation


def dispatch_generate(path: Path) -> str:
    try:
        if path.is_file():
            run_generation(path)
            return "file"
        if path.is_dir():
            run_domain(path)
            return "domain"
        raise click.ClickException(f"Not a file or directory: {path}")
    except click.ClickException:
        raise
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
