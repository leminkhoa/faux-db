from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from kuriboh.core.engine import run_domain

from tests.integration.scenario_helpers import clear_cached_functions_packages


@pytest.fixture
def domain_shopping_outputs(
    domain_shopping_work_root: Path,
    domain_shopping_domain_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Path]:
    """Run the shopping domain once and return paths to generated CSVs."""
    clear_cached_functions_packages()
    monkeypatch.syspath_prepend(str(domain_shopping_work_root))
    monkeypatch.chdir(domain_shopping_work_root)
    run_domain(domain_shopping_domain_path)
    out = domain_shopping_work_root / "outputs"
    return {
        "root": domain_shopping_work_root,
        "customer": out / "customer.csv",
        "store": out / "store.csv",
        "product": out / "product.csv",
        "transaction": out / "transaction.csv",
        "transaction_orders": out / "transaction_orders.csv",
    }


@pytest.fixture
def domain_shopping_work_root(tmp_path: Path) -> Path:
    scenario_fixtures = Path(__file__).parent / "fixtures"
    work_root = tmp_path / "domain_shopping"
    shutil.copytree(scenario_fixtures, work_root)
    return work_root


@pytest.fixture
def domain_shopping_domain_path(domain_shopping_work_root: Path) -> Path:
    """Directory passed to ``run_domain`` (contains ``*.yml`` schema files)."""
    return domain_shopping_work_root / "schemas" / "shopping"
