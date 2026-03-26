"""
Integration: multi-table domain with parallel branches and fan-in.

DAG (``$rel`` edges, table-level)::

    wave_a ──► wave_b ──┐
                        ├──► junction_e ──► terminal_f
    wave_c ──► wave_d ──┘

``build_table_dag`` uses Kahn with a FIFO queue; for this fixture the
deterministic generation order is
``wave_a, wave_c, wave_b, wave_d, junction_e, terminal_f``.
"""

from __future__ import annotations

import csv
from pathlib import Path

from faux.core.dag import build_table_dag
from faux.core.engine import run_domain
from faux.parsers.loader import load_schema
from faux.parsers.schema import SchemaFile, validate_schema


def _load_domain_schemas(domain_path: Path) -> dict[str, SchemaFile]:
    """Match ``run_domain``: load every ``*.yml`` in lexical order."""
    schemas: dict[str, SchemaFile] = {}
    for schema_file in sorted(domain_path.glob("*.yml")):
        raw = load_schema(schema_file)
        model = validate_schema(raw)
        schemas[model.table_name] = model
    return schemas


def _col_values(csv_path: Path, column: str) -> list[str]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        return [row[column] for row in csv.DictReader(f)]


def test_domain_fan_in_fan_out_build_table_dag_order(
    domain_fan_in_fan_out_domain_path: Path,
) -> None:
    schemas = _load_domain_schemas(domain_fan_in_fan_out_domain_path)
    assert build_table_dag(schemas) == [
        "wave_a",
        "wave_c",
        "wave_b",
        "wave_d",
        "junction_e",
        "terminal_f",
    ]


def test_domain_fan_in_fan_out_generates_csvs_with_referential_integrity(
    domain_fan_in_fan_out_work_root: Path,
    domain_fan_in_fan_out_domain_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(domain_fan_in_fan_out_work_root)
    run_domain(domain_fan_in_fan_out_domain_path)

    out = domain_fan_in_fan_out_work_root / "outputs"
    paths = {
        "wave_a": out / "wave_a.csv",
        "wave_c": out / "wave_c.csv",
        "wave_b": out / "wave_b.csv",
        "wave_d": out / "wave_d.csv",
        "junction_e": out / "junction_e.csv",
        "terminal_f": out / "terminal_f.csv",
    }
    for p in paths.values():
        assert p.exists(), f"missing output {p}"

    ids_a = set(_col_values(paths["wave_a"], "id"))
    ids_c = set(_col_values(paths["wave_c"], "id"))
    ids_b = set(_col_values(paths["wave_b"], "id"))
    ids_d = set(_col_values(paths["wave_d"], "id"))
    ids_e = set(_col_values(paths["junction_e"], "id"))

    link_a = _col_values(paths["wave_b"], "link_a")
    link_c = _col_values(paths["wave_d"], "link_c")
    link_b = _col_values(paths["junction_e"], "link_b")
    link_d = _col_values(paths["junction_e"], "link_d")
    link_e = _col_values(paths["terminal_f"], "link_e")

    assert len(link_a) == 2
    assert set(link_a) <= ids_a
    assert set(link_c) <= ids_c
    assert set(link_b) <= ids_b
    assert set(link_d) <= ids_d
    assert set(link_e) <= ids_e
