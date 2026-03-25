from __future__ import annotations

import shutil
from pathlib import Path

import pytest


@pytest.fixture
def func_simple_work_root(tmp_path: Path) -> Path:
    scenario_fixtures = Path(__file__).parent / "fixtures"
    work_root = tmp_path / "func_simple"
    shutil.copytree(scenario_fixtures, work_root)
    return work_root


@pytest.fixture
def func_simple_schema_default_prefix(func_simple_work_root: Path) -> Path:
    return func_simple_work_root / "schemas" / "line_default_prefix.yml"


@pytest.fixture
def func_simple_schema_explicit_prefix(func_simple_work_root: Path) -> Path:
    return func_simple_work_root / "schemas" / "line_explicit_prefix.yml"
