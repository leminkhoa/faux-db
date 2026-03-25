"""Integration tests: ``random_choice`` provider with deterministic seed."""

from __future__ import annotations

import csv

from kuriboh.core.engine import run_generation

# Same sequence as ``RandomChoiceProvider(..., seed=42)`` for five draws.
_EXPECTED_TIERS = ["standard", "standard", "platinum", "gold", "gold"]


def test_random_choice_provider_seeded_tiers_in_csv(
    random_choice_work_root,
    random_choice_schema_path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(random_choice_work_root)
    run_generation(random_choice_schema_path)

    out = random_choice_work_root / "outputs" / "customers.csv"
    assert out.exists()
    with out.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 5
    assert list(rows[0].keys()) == ["tier"]
    assert [r["tier"] for r in rows] == _EXPECTED_TIERS
