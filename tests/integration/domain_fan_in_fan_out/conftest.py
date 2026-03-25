from __future__ import annotations

import shutil
from pathlib import Path

import pytest


@pytest.fixture
def domain_fan_in_fan_out_work_root(tmp_path: Path) -> Path:
    scenario_fixtures = Path(__file__).parent / "fixtures"
    work_root = tmp_path / "domain_fan_in_fan_out"
    shutil.copytree(scenario_fixtures, work_root)
    return work_root


@pytest.fixture
def domain_fan_in_fan_out_domain_path(domain_fan_in_fan_out_work_root: Path) -> Path:
    """Directory passed to ``run_domain`` (contains ``*.yml`` schema files)."""
    return domain_fan_in_fan_out_work_root / "schemas" / "fan_in_fan_out"
