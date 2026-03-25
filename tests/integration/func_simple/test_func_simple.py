"""Integration tests: ``$func`` columns load scenario-local ``functions`` modules."""

from __future__ import annotations

import csv

from kuriboh.core.engine import run_generation

from tests.integration.scenario_helpers import clear_cached_functions_packages


def _run_scenario(work_root, schema_path, monkeypatch) -> None:
    """Put scenario root on ``sys.path`` so ``import functions.simple`` resolves."""
    clear_cached_functions_packages()
    monkeypatch.syspath_prepend(str(work_root))
    monkeypatch.chdir(work_root)
    run_generation(schema_path)


def test_func_simple_default_prefix_resolves_add_vat(
    func_simple_work_root,
    func_simple_schema_default_prefix,
    monkeypatch,
) -> None:
    _run_scenario(func_simple_work_root, func_simple_schema_default_prefix, monkeypatch)

    out = func_simple_work_root / "outputs" / "lines.csv"
    assert out.exists()
    with out.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 3
    assert list(rows[0].keys()) == ["price", "price_with_vat"]
    for row in rows:
        assert row["price"] == "100"
        assert row["price_with_vat"] == "110.00"


def test_func_simple_explicit_functions_prefix_same_behavior(
    func_simple_work_root,
    func_simple_schema_explicit_prefix,
    monkeypatch,
) -> None:
    _run_scenario(func_simple_work_root, func_simple_schema_explicit_prefix, monkeypatch)

    out = func_simple_work_root / "outputs" / "lines_explicit.csv"
    assert out.exists()
    with out.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    for row in rows:
        assert row["price"] == "100"
        assert row["price_with_vat"] == "110.00"
