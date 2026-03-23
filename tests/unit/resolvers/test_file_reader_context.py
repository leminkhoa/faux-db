from __future__ import annotations

import polars as pl

import pytest

from kuriboh.parsers.schema import ColumnConfig, LookupConfig
from kuriboh.providers.file_reader import FileReaderProvider
from kuriboh.resolvers.file_reader_context import (
    FileReaderSampleSession,
    file_reader_cardinality,
    file_reader_enumerate,
    resolve_lookup_key_from_row,
    sample_spec,
)


def _provider() -> FileReaderProvider:
    return FileReaderProvider(
        pl.DataFrame(
            {
                "k": ["a", "b", "c"],
                "v": ["1", "2", "3"],
            }
        ),
        loaded_columns=["k", "v"],
    )


def test_resolve_lookup_key_from_row_rejects_invalid_part():
    with pytest.raises(ValueError, match="exactly one"):
        resolve_lookup_key_from_row({"id": "x"}, "prefix-$col(id)-$col(other)")


def test_shuffle_indices_initialized_once():
    cfg = ColumnConfig(
        type="$provider",
        target="P",
        mode="sample",
        column="v",
        sample={"strategy": "shuffle", "seed": 7},
    )
    session = FileReaderSampleSession(cfg)
    provider = _provider()

    first = session.shuffle_indices(provider)
    second = session.shuffle_indices(provider)

    assert first == second
    assert first is second
    assert len(first) == len(provider.rows)


def test_sample_spec_non_shuffle_sets_shuffle_indices_none():
    cfg = ColumnConfig(
        type="$provider",
        target="P",
        mode="sample",
        column="v",
        sample={"strategy": "sequential"},
    )
    spec = sample_spec(cfg, _provider(), FileReaderSampleSession(cfg))
    assert spec.shuffle_indices is None


def test_file_reader_cardinality_returns_none_for_invalid_combo():
    provider = _provider()
    cfg = ColumnConfig(type="$provider", target="P", mode="sample", column=None)
    assert file_reader_cardinality(provider, cfg) is None


def test_file_reader_enumerate_returns_none_for_invalid_combo():
    provider = _provider()
    cfg = ColumnConfig(type="$provider", target="P", mode="sample", column=None)
    assert file_reader_enumerate(provider, cfg) is None


def test_file_reader_cardinality_lookup_happy_path():
    provider = _provider()
    cfg = ColumnConfig(
        type="$provider",
        target="P",
        mode="lookup",
        lookup=LookupConfig(
            key_columns=["k"],
            key_from="$col(source_k)",
            value_column="v",
        ),
    )
    assert file_reader_cardinality(provider, cfg) == 3
