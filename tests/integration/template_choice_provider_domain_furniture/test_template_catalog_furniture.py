"""Integration tests: ``template_choice`` catalog filters (first, random, cycle, default)."""

from __future__ import annotations

import csv

from faux.core.engine import run_generation

_EXPECTED_FIRST = "Red Platform Bed"

# ``RandomFilterProvider`` uses ``seed: 100``; sequence from a standalone provider smoke check.
_EXPECTED_RANDOM_COLORS = ["Green", "Gray", "White", "White", "Green"]

# Three beds in fixture; ``| cycle`` repeats every 3 rows.
_EXPECTED_CYCLE_BEDS = [
    "Platform Bed",
    "Four-Poster Bed",
    "Daybed",
    "Platform Bed",
    "Four-Poster Bed",
]

_EXPECTED_DEFAULT = "N/A"


def test_template_choice_catalog_filters_first_random_cycle_default(
    template_catalog_work_root,
    template_catalog_schema_path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(template_catalog_work_root)
    run_generation(template_catalog_schema_path)

    out = template_catalog_work_root / "outputs" / "furniture.csv"
    assert out.exists()
    with out.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 5
    assert list(rows[0].keys()) == [
        "label_first",
        "label_random",
        "label_cycle",
        "label_default",
    ]

    for i, row in enumerate(rows):
        assert row["label_first"] == _EXPECTED_FIRST
        assert row["label_random"] == _EXPECTED_RANDOM_COLORS[i]
        assert row["label_cycle"] == _EXPECTED_CYCLE_BEDS[i]
        assert row["label_default"] == _EXPECTED_DEFAULT
