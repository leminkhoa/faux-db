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

    Returns a dict keyed by filename stem (without `.yml`).
    """
    catalogs_dir = base_dir / CATALOGS_DIRNAME
    catalogs: Dict[str, Dict[str, Any]] = {}
    if not catalogs_dir.exists():
        return catalogs
    for yml_path in sorted(catalogs_dir.glob("*.yml")):
        with yml_path.open("r", encoding="utf-8") as f:
            catalogs[yml_path.stem] = yaml.safe_load(f)
    return catalogs