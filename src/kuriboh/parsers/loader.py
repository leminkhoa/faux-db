from pathlib import Path
from typing import Any, Dict

import yaml

from ..core import CATALOGS_DIRNAME, PROVIDERS_DIRNAME


def load_schema(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_providers(base_dir: Path) -> Dict[str, Any]:
    """
    Load and merge all provider YAML files found under `<base_dir>/providers/`.

    Each file is a flat mapping of provider-name -> config, so merging them
    is a simple dict update. Files are processed in alphabetical order so
    results are deterministic; later files override earlier ones on name clash.
    """
    providers_dir = base_dir / PROVIDERS_DIRNAME
    merged: Dict[str, Any] = {}
    if not providers_dir.exists():
        return merged
    for yml_path in sorted(providers_dir.glob("*.yml")):
        with yml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        merged.update(data)
    return merged


def load_catalogs(base_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load all catalog YAML files found under `<base_dir>/catalogs/`.

    Recursively discovers ``*.yml`` and ``*.yaml`` in subdirectories (not only
    the top level). Each file is keyed by its **basename** (filename stem).
    If two files in different folders share the same basename, raises
    ``ValueError`` so ``catalog('stem.key')`` remains unambiguous.

    Returns a dict keyed by that basename stem.
    """

    SUPPORTED_CATALOG_PATTERNS = ["**/*.yml", "**/*.yaml"]

    catalogs_dir = base_dir / CATALOGS_DIRNAME
    catalogs: Dict[str, Dict[str, Any]] = {}

    if not catalogs_dir.exists():
        return catalogs

    paths = sorted(
        set().union(*(catalogs_dir.glob(pattern) for pattern in SUPPORTED_CATALOG_PATTERNS))
    )

    seen: Dict[str, Path] = {}

    for yml_path in paths:
        if yml_path.is_dir():
            continue

        stem = yml_path.stem

        if stem in seen and seen[stem] != yml_path:
            raise ValueError(
                f"Duplicate catalog basename '{stem}': {seen[stem]} vs {yml_path}. "
                "Use unique filenames under catalogs/ (including subfolders)."
            )

        seen[stem] = yml_path

        with yml_path.open("r", encoding="utf-8") as f:
            catalogs[stem] = yaml.safe_load(f) or {}

    return catalogs
