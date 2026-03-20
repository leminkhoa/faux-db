"""Tests for :mod:`kuriboh.providers.registry`."""

from __future__ import annotations

from pathlib import Path

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
