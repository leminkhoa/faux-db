"""Tests for :mod:`kuriboh.providers.registry`."""

from __future__ import annotations

import pytest
from pathlib import Path

import kuriboh.providers.registry as registry_mod
from kuriboh.providers.registry import build_registry


def test_build_registry_random_choice(tmp_path: Path) -> None:
    cfg = {"P": {"type": "random_choice", "choices": ["a", "b"], "seed": 1}}
    reg = build_registry(tmp_path, cfg)
    assert reg.get("P").generate({}) in ("a", "b")


def test_build_registry_file_reader_seed_csv(tmp_path: Path) -> None:
    (tmp_path / "seeds").mkdir()
    (tmp_path / "seeds" / "t.csv").write_text("col\nv1\nv2\n", encoding="utf-8")
    cfg = {"P": {"type": "file_reader", "filepath": "t.csv", "column": "col"}}
    reg = build_registry(tmp_path, cfg)
    assert reg.get("P").generate({}) == "v1"
    assert reg.get("P").generate({}) == "v2"


def test_build_registry_file_reader_missing_csv_loads_no_rows(tmp_path: Path) -> None:
    """Missing seed file hits :func:`_load_seed_csv` early return (empty rows)."""
    cfg = {
        "P": {
            "type": "file_reader",
            "filepath": "does_not_exist.csv",
            "column": "col",
        }
    }
    reg = build_registry(tmp_path, cfg)
    assert reg.get("P").generate({}) is None


def test_build_registry_template_choice(tmp_path: Path) -> None:
    cfg = {
        "T": {
            "type": "template_choice",
            "templates": ["fixed"],
            "seed": 42,
        }
    }
    reg = build_registry(tmp_path, cfg)
    assert reg.get("T").generate({"catalogs": {}}) == "fixed"


def test_build_registry_expression(tmp_path: Path) -> None:
    cfg = {
        "E": {
            "type": "expression",
            "exp": "{{ random_int(5, 5) }}",
            "seed": 7,
        }
    }
    reg = build_registry(tmp_path, cfg)
    assert reg.get("E").generate({}) == 5


def test_build_registry_unsupported_type_raises_when_factory_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Covers the guard when ``_PROVIDER_FACTORIES`` has no entry for a valid type."""
    pruned = {
        k: v
        for k, v in registry_mod._PROVIDER_FACTORIES.items()
        if k != "random_choice"
    }
    monkeypatch.setattr(registry_mod, "_PROVIDER_FACTORIES", pruned)
    cfg = {"P": {"type": "random_choice", "choices": ["x"]}}
    with pytest.raises(ValueError, match="Unsupported provider type 'random_choice'"):
        build_registry(tmp_path, cfg)
