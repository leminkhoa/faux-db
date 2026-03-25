from __future__ import annotations

import shutil
from pathlib import Path

import pytest


@pytest.fixture
def random_choice_work_root(tmp_path: Path) -> Path:
    scenario_fixtures = Path(__file__).parent / "fixtures"
    work_root = tmp_path / "random_choice_provider"
    shutil.copytree(scenario_fixtures, work_root)
    return work_root


@pytest.fixture
def random_choice_schema_path(random_choice_work_root: Path) -> Path:
    return random_choice_work_root / "schemas" / "customers.yml"
