from pathlib import Path
from typing import Any, Dict

import yaml


def load_schema(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_providers(base_dir: Path) -> Dict[str, Any]:
    providers_path = base_dir / "providers" / "ecommerce.yml"
    with providers_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_catalogs(base_dir: Path) -> Dict[str, Dict[str, Any]]:
    catalogs_dir = base_dir / "catalogs"
    catalogs: Dict[str, Dict[str, Any]] = {}
    if not catalogs_dir.exists():
        return catalogs
    for yml_path in catalogs_dir.glob("*.yml"):
        with yml_path.open("r", encoding="utf-8") as f:
            catalogs[yml_path.stem] = yaml.safe_load(f)
    return catalogs