from __future__ import annotations

import shutil
from pathlib import Path

import pytest


@pytest.fixture
def basic_faker_work_root(tmp_path: Path) -> Path:
    scenario_fixtures = Path(__file__).parent / "fixtures"
    work_root = tmp_path / "basic_faker"
    shutil.copytree(scenario_fixtures, work_root)
    return work_root


@pytest.fixture
def basic_faker_schema_path(basic_faker_work_root: Path) -> Path:
    return basic_faker_work_root / "schemas" / "product.yml"
