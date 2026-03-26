from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from ..constants import (
    CATALOGS_DIRNAME,
    FUNCTIONS_DIRNAME,
    OUTPUTS_DIRNAME,
    PROVIDERS_DIRNAME,
    SCHEMAS_DIRNAME,
    SEEDS_DIRNAME,
)

STARTER_TEMPLATE_PATHS = (
    Path(SCHEMAS_DIRNAME) / "example" / "users.yml",
    Path(PROVIDERS_DIRNAME) / "example.yml",
    Path(CATALOGS_DIRNAME) / "demo.yml",
    Path(FUNCTIONS_DIRNAME) / "__init__.py",
)


@dataclass(frozen=True)
class InitSummary:
    base_dir: Path
    created_directories: tuple[Path, ...]
    created_files: tuple[Path, ...]


def _write_file(path: Path, content: str, *, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _load_template(relative_path: Path) -> str:
    template_root = files("faux.core.project_init").joinpath("templates")
    template_file = template_root.joinpath(*relative_path.parts)
    return template_file.read_text(encoding="utf-8")


def init_project(base_dir: Path, *, force: bool = False) -> InitSummary:
    base_dir = base_dir.resolve()
    created_directories: list[Path] = []
    created_files: list[Path] = []

    for dirname in (
        SCHEMAS_DIRNAME,
        PROVIDERS_DIRNAME,
        CATALOGS_DIRNAME,
        SEEDS_DIRNAME,
        OUTPUTS_DIRNAME,
        FUNCTIONS_DIRNAME,
    ):
        path = base_dir / dirname
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created_directories.append(path)

    for relative_path in STARTER_TEMPLATE_PATHS:
        target_path = base_dir / relative_path
        content = _load_template(relative_path)
        if _write_file(target_path, content, force=force):
            created_files.append(target_path)

    return InitSummary(
        base_dir=base_dir,
        created_directories=tuple(created_directories),
        created_files=tuple(created_files),
    )
