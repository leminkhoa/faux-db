"""Tests for :class:`~kuriboh.providers.file_reader.FileReaderProvider`."""

from __future__ import annotations

import random

import pytest

from kuriboh.providers.file_reader import FileReaderProvider
from kuriboh.providers.file_reader_specs import FileReaderLookupSpec, FileReaderSampleSpec


def _lookup_ctx(
    *,
    key_columns: tuple[str, ...],
    value_column: str,
    key: tuple,
    on_missing: str = "null",
    default_value=None,
) -> dict:
    return {
        "file_reader": FileReaderLookupSpec(
            key_columns=key_columns,
            value_column=value_column,
            key=key,
            on_missing=on_missing,
            default_value=default_value,
        )
    }


def _sample_ctx(*, column: str, strategy: str, rng: random.Random, seq: list[int], shuffle_indices=None):
    return {
        "file_reader": FileReaderSampleSpec(
            column=column,
            strategy=strategy,
            rng=rng,
            seq=seq,
            shuffle_indices=shuffle_indices,
        )
    }


def test_file_reader_legacy_cycles_first_loaded_column():
    p = FileReaderProvider(
        [{"c": "a"}, {"c": "b"}],
        ["c"],
    )
    assert p.generate({}) == "a"
    assert p.generate({}) == "b"
    assert p.generate({}) == "a"


def test_file_reader_sample_sequential_via_context():
    p = FileReaderProvider([{"c": "a"}, {"c": "b"}], ["c"])
    rng = random.Random(0)
    seq = [0]
    ctx = _sample_ctx(column="c", strategy="sequential", rng=rng, seq=seq)
    assert p.generate(ctx) == "a"
    assert p.generate(ctx) == "b"


def test_file_reader_lookup_composite_key():
    rows = [
        {"k1": "a", "k2": "1", "v": "x"},
        {"k1": "a", "k2": "2", "v": "y"},
    ]
    p = FileReaderProvider(rows, ["k1", "k2", "v"], on_duplicate_key="first")
    ctx = _lookup_ctx(key_columns=("k1", "k2"), value_column="v", key=("a", "2"))
    assert p.generate(ctx) == "y"


def test_file_reader_lookup_duplicate_key_first_wins():
    rows = [
        {"id": 1, "name": "first"},
        {"id": 1, "name": "second"},
    ]
    p = FileReaderProvider(rows, ["id", "name"], on_duplicate_key="first")
    ctx = _lookup_ctx(key_columns=("id",), value_column="name", key=(1,))
    assert p.generate(ctx) == "first"


def test_file_reader_lookup_duplicate_key_last_wins():
    rows = [
        {"id": 1, "name": "first"},
        {"id": 1, "name": "second"},
    ]
    p = FileReaderProvider(rows, ["id", "name"], on_duplicate_key="last")
    ctx = _lookup_ctx(key_columns=("id",), value_column="name", key=(1,))
    assert p.generate(ctx) == "second"


def test_file_reader_lookup_duplicate_composite_key_error():
    rows = [
        {"a": 1, "b": 2, "v": "x"},
        {"a": 1, "b": 2, "v": "y"},
    ]
    p = FileReaderProvider(rows, ["a", "b", "v"], on_duplicate_key="error")
    ctx = _lookup_ctx(key_columns=("a", "b"), value_column="v", key=(1, 2))
    with pytest.raises(ValueError, match="Duplicate lookup key"):
        p.generate(ctx)


def test_file_reader_lookup_miss_error():
    p = FileReaderProvider([{"id": 1, "v": "ok"}], ["id", "v"], on_duplicate_key="first")
    ctx = _lookup_ctx(key_columns=("id",), value_column="v", key=(99,), on_missing="error")
    with pytest.raises(KeyError, match="Lookup miss"):
        p.generate(ctx)


def test_file_reader_lookup_miss_default():
    p = FileReaderProvider([{"id": 1, "v": "ok"}], ["id", "v"], on_duplicate_key="first")
    ctx = _lookup_ctx(
        key_columns=("id",),
        value_column="v",
        key=(99,),
        on_missing="default",
        default_value="missing",
    )
    assert p.generate(ctx) == "missing"


def test_file_reader_lookup_miss_null():
    p = FileReaderProvider([{"id": 1, "v": "ok"}], ["id", "v"], on_duplicate_key="first")
    ctx = _lookup_ctx(key_columns=("id",), value_column="v", key=(99,))
    assert p.generate(ctx) is None


def test_file_reader_empty_returns_none():
    p = FileReaderProvider([], ["c"])
    assert p.generate({}) is None


def test_file_reader_sample_random_deterministic_with_seed():
    p = FileReaderProvider([{"c": "a"}, {"c": "b"}, {"c": "c"}], ["c"])
    rng = random.Random(42)
    seq = [0]
    ctx = _sample_ctx(column="c", strategy="random", rng=rng, seq=seq)
    values = {p.generate(ctx) for _ in range(50)}
    assert values <= {"a", "b", "c"}
    assert len(values) >= 1


def test_file_reader_sample_shuffle_sequential_uses_shuffle_indices():
    p = FileReaderProvider([{"c": "a"}, {"c": "b"}, {"c": "c"}], ["c"])
    rng = random.Random(0)
    seq = [0]
    shuffle_indices = [2, 0, 1]
    ctx = _sample_ctx(column="c", strategy="shuffle", rng=rng, seq=seq, shuffle_indices=shuffle_indices)
    assert p.generate(ctx) == "c"
    assert p.generate(ctx) == "a"
    assert p.generate(ctx) == "b"


def test_file_reader_cardinality_sample_counts_distinct_stringified_values_with_duplicates():
    p = FileReaderProvider([{"x": 1}, {"x": 1}, {"x": 2}], ["x"])
    assert p.cardinality_sample("x") == 2


def test_file_reader_enumerate_sample_preserves_first_occurrence_order():
    p = FileReaderProvider([{"x": "a"}, {"x": "b"}, {"x": "a"}], ["x"])
    assert p.enumerate_sample("x") == ["a", "b"]


def test_file_reader_cardinality_lookup_distinct_values_with_duplicate_keys():
    """Duplicate keys do not inflate distinct value count for cardinality_lookup."""
    rows = [{"id": 1, "v": "A"}, {"id": 1, "v": "B"}]
    p = FileReaderProvider(rows, ["id", "v"], on_duplicate_key="last")
    assert p.cardinality_lookup(("id",), "v") == 2
