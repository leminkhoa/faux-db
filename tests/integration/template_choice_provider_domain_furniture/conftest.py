from __future__ import annotations

import shutil
from pathlib import Path

import pytest


@pytest.fixture
def template_catalog_work_root(tmp_path: Path) -> Path:
    scenario_fixtures = Path(__file__).parent / "fixtures"
    work_root = tmp_path / "template_catalog_furniture"
    shutil.copytree(scenario_fixtures, work_root)
    return work_root


@pytest.fixture
def template_catalog_schema_path(template_catalog_work_root: Path) -> Path:
    return template_catalog_work_root / "schemas" / "furniture.yml"
