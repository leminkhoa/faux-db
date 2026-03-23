"""
Helpers for :class:`~kuriboh.providers.file_reader.FileReaderProvider` columns:
lookup key resolution, sample session state, and spec builders.

The typed spec dataclasses live in :mod:`~kuriboh.providers.file_reader_specs`
so both this module and :mod:`~kuriboh.providers.file_reader` can import them
without a circular dependency.
"""

from __future__ import annotations

import random
from typing import Any

from ..parsers.schema import COL_REF_PATTERN, ColumnConfig, LookupConfig
from ..providers.file_reader import FileReaderProvider
from ..providers.file_reader_specs import FileReaderLookupSpec, FileReaderSampleSpec


def resolve_lookup_key_from_row(row: dict[str, Any], key_from: str | list[str]) -> tuple[Any, ...]:
    parts = [key_from] if isinstance(key_from, str) else key_from
    out: list[Any] = []
    for part in parts:
        matches = COL_REF_PATTERN.findall(part)
        if len(matches) != 1:
            raise ValueError(
                f"lookup key_from part must reference exactly one $col(name), got {part!r}"
            )
        out.append(row.get(matches[0]))
    return tuple(out)


def _make_rng(seed: int | None) -> random.Random:
    """Return a seeded Random instance. ``Random(None)`` uses system entropy."""
    return random.Random(seed)


class FileReaderSampleSession:
    """
    Per-column state for file_reader sample mode: RNG, sequential counter, and
    shuffled row order (computed once for ``shuffle`` strategy).
    """

    def __init__(self, col_cfg: ColumnConfig) -> None:
        self._col_cfg = col_cfg
        self._seq: list[int] | None = None
        self._rng: random.Random | None = None
        self._shuffle_indices: list[int] | None = None

    def seq(self) -> list[int]:
        if self._seq is None:
            self._seq = [0]
        return self._seq

    def rng(self) -> random.Random:
        if self._rng is None:
            sample = self._col_cfg.sample
            self._rng = _make_rng(sample.seed if sample else None)
        return self._rng

    def shuffle_indices(self, provider: FileReaderProvider) -> list[int]:
        if self._shuffle_indices is None:
            rng = self.rng()
            idx = list(range(len(provider.rows)))
            rng.shuffle(idx)
            self._shuffle_indices = idx
        return self._shuffle_indices


def lookup_spec(lk: LookupConfig, row: dict[str, Any]) -> FileReaderLookupSpec:
    return FileReaderLookupSpec(
        key_columns=tuple(lk.key_columns),
        value_column=lk.value_column,
        key=resolve_lookup_key_from_row(row, lk.key_from),
        on_missing=lk.on_missing,
        default_value=lk.default_value,
    )


def sample_spec(
    cfg: ColumnConfig,
    provider: FileReaderProvider,
    session: FileReaderSampleSession,
) -> FileReaderSampleSpec:
    assert cfg.column is not None
    sample = cfg.sample
    strategy = sample.strategy if sample else "sequential"
    return FileReaderSampleSpec(
        column=cfg.column,
        strategy=strategy,
        rng=session.rng(),
        seq=session.seq(),
        shuffle_indices=session.shuffle_indices(provider) if strategy == "shuffle" else None,
    )


def file_reader_cardinality(provider: FileReaderProvider, cfg: ColumnConfig) -> int | None:
    if cfg.mode == "sample" and cfg.column:
        return provider.cardinality_sample(cfg.column)
    if cfg.mode == "lookup" and cfg.lookup:
        return provider.cardinality_lookup(tuple(cfg.lookup.key_columns), cfg.lookup.value_column)
    return None


def file_reader_enumerate(provider: FileReaderProvider, cfg: ColumnConfig) -> list | None:
    if cfg.mode == "sample" and cfg.column:
        return provider.enumerate_sample(cfg.column)
    if cfg.mode == "lookup" and cfg.lookup:
        return provider.enumerate_lookup(cfg.lookup.value_column)
    return None
