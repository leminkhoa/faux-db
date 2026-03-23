from __future__ import annotations

import csv

from kuriboh.core.engine import run_generation


def test_basic_faker_generation_writes_csv(basic_faker_work_root, basic_faker_schema_path, monkeypatch):
    monkeypatch.chdir(basic_faker_work_root)
    run_generation(basic_faker_schema_path)

    output_path = basic_faker_work_root / "outputs" / "products.csv"
    assert output_path.exists()

    with output_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 5
    assert rows and list(rows[0].keys()) == ["id"]
    assert all(row["id"] for row in rows)
    assert len({row["id"] for row in rows}) == 5
