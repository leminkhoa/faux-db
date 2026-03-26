"""Tests for file_reader validation at plan time."""

from __future__ import annotations

from pathlib import Path

import pytest

from kuriboh.core.resolver_factory import validate_provider_columns_for_plan
from kuriboh.parsers.schema import ColumnConfig
from kuriboh.providers.registry import build_registry


def test_validate_file_reader_sample_requires_schema_column(tmp_path: Path) -> None:
    (tmp_path / "seeds").mkdir()
    (tmp_path / "seeds" / "t.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    reg = build_registry(
        tmp_path,
        {"P": {"type": "file_reader", "filepath": "t.csv", "loaded_columns": ["a", "b"]}},
    )
    columns = {
        "x": ColumnConfig(
            type="provider",
            target="P",
            mode="sample",
            column=None,
        )
    }
    with pytest.raises(ValueError, match="requires 'column'"):
        validate_provider_columns_for_plan(reg, columns)


def test_validate_non_file_lookup_rejected(tmp_path: Path) -> None:
    reg = build_registry(
        tmp_path,
        {"T": {"type": "random_choice", "choices": ["a"]}},
    )
    columns = {
        "x": ColumnConfig(
            type="provider",
            target="T",
            mode="lookup",
            lookup={
                "key_columns": ["id"],
                "key_from": "id",
                "value_column": "v",
            },
        )
    }
    with pytest.raises(ValueError, match="lookup"):
        validate_provider_columns_for_plan(reg, columns)
