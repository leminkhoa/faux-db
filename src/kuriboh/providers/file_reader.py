from __future__ import annotations

from typing import Any, Literal

import polars as pl

from .base import BaseProvider
from .file_reader_specs import FileReaderLookupSpec, FileReaderSampleSpec

DuplicateKeyPolicy = Literal["first", "last", "error"]

TableInput = pl.DataFrame | list[dict[str, Any]] | list


def _coerce_table(data: TableInput, loaded_columns: list[str]) -> pl.DataFrame:
    """Build a DataFrame restricted to ``loaded_columns`` (for tests and in-memory rows)."""
    empty = pl.DataFrame(schema=[(c, pl.Utf8) for c in loaded_columns])
    if isinstance(data, pl.DataFrame):
        return data.select(loaded_columns) if data.height > 0 else empty

    rows_list = list(data)
    return pl.DataFrame(rows_list).select(loaded_columns) if rows_list else empty


class FileReaderProvider(BaseProvider):
    """
    Loads seed data as a Polars DataFrame (see registry). Sampling vs lookup is driven by
    schema column config; the resolver passes a typed ``FileReaderSampleSpec`` or
    ``FileReaderLookupSpec`` via ``context["file_reader"]``.
    """

    def __init__(
        self,
        table: TableInput,
        loaded_columns: list[str],
        on_duplicate_key: DuplicateKeyPolicy = "first",
    ) -> None:
        self._df = _coerce_table(table, loaded_columns)
        self._loaded_columns = list(loaded_columns)
        self._on_duplicate_key = on_duplicate_key
        self._lookup_maps: dict[tuple[tuple[str, ...], str], dict[tuple[Any, ...], Any]] = {}
        self._bare_index = 0

    @property
    def loaded_columns(self) -> list[str]:
        return list(self._loaded_columns)

    @property
    def rows(self) -> pl.DataFrame:
        """Tabular seed rows (Polars). ``len(provider.rows)`` is supported."""
        return self._df

    @property
    def on_duplicate_key(self) -> DuplicateKeyPolicy:
        return self._on_duplicate_key

    def generate(self, context: dict[str, Any]) -> Any:
        spec = context.get("file_reader")
        if isinstance(spec, FileReaderSampleSpec):
            return self._dispatch_sample(spec)
        if isinstance(spec, FileReaderLookupSpec):
            return self._lookup_from_spec(spec)
        return self._generate_legacy_sequential()

    def _dispatch_sample(self, spec: FileReaderSampleSpec) -> Any:
        fn = getattr(self, f"_sample_{spec.strategy}", None)
        if fn is None:
            raise ValueError(f"Unknown sample strategy: {spec.strategy!r}")
        return fn(spec)

    def _sample_sequential(self, spec: FileReaderSampleSpec) -> Any:
        n = self._df.height
        if n == 0:
            return None
        i = spec.seq[0]
        spec.seq[0] = i + 1
        return self._df[spec.column][i % n]

    def _sample_random(self, spec: FileReaderSampleSpec) -> Any:
        n = self._df.height
        if n == 0:
            return None
        return self._df[spec.column][spec.rng.randrange(n)]

    def _sample_shuffle(self, spec: FileReaderSampleSpec) -> Any:
        n = self._df.height
        if n == 0:
            return None
        assert spec.shuffle_indices is not None
        i = spec.seq[0]
        spec.seq[0] = i + 1
        return self._df[spec.column][spec.shuffle_indices[i % len(spec.shuffle_indices)]]

    def _lookup_from_spec(self, spec: FileReaderLookupSpec) -> Any:
        mapping = self._lookup_map_for(spec.key_columns, spec.value_column)
        if spec.key in mapping:
            return mapping[spec.key]
        return self._lookup_miss(spec)

    def _lookup_miss(self, spec: FileReaderLookupSpec) -> Any:
        if spec.on_missing == "null":
            return None
        if spec.on_missing == "error":
            raise KeyError(
                f"Lookup miss for key {spec.key!r} in columns {spec.key_columns} "
                f"(value_column={spec.value_column!r})"
            )
        if spec.on_missing == "default":
            return spec.default_value
        raise ValueError(f"Unknown on_missing: {spec.on_missing!r}")

    def _generate_legacy_sequential(self) -> Any:
        if self._df.height == 0 or not self._loaded_columns:
            return None
        column = self._loaded_columns[0]
        n = self._df.height
        i = self._bare_index % n
        self._bare_index += 1
        return self._df[column][i]

    def _lookup_map_for(
        self,
        key_columns: tuple[str, ...],
        value_column: str,
    ) -> dict[tuple[Any, ...], Any]:
        cache_key = (key_columns, value_column)
        if cache_key not in self._lookup_maps:
            self._lookup_maps[cache_key] = self._build_lookup_map(key_columns, value_column)
        return self._lookup_maps[cache_key]

    def _build_lookup_map(
        self,
        key_columns: tuple[str, ...],
        value_column: str,
    ) -> dict[tuple[Any, ...], Any]:
        m: dict[tuple[Any, ...], Any] = {}
        for row in self._df.iter_rows(named=True):
            key = tuple(row[k] for k in key_columns)
            self._merge_lookup_key(m, key, row[value_column], key_columns, value_column)
        return m

    def _merge_lookup_key(
        self,
        m: dict[tuple[Any, ...], Any],
        key: tuple[Any, ...],
        val: Any,
        key_columns: tuple[str, ...],
        value_column: str,
    ) -> None:
        if key not in m:
            m[key] = val
            return
        if self._on_duplicate_key == "error":
            raise ValueError(
                f"Duplicate lookup key {key!r} for columns {key_columns} "
                f"(value_column={value_column!r})"
            )
        if self._on_duplicate_key == "last":
            m[key] = val

    def cardinality_sample(self, column: str) -> int | None:
        return len({str(x) for x in self._df[column].to_list()}) if self._df.height > 0 else 0

    def cardinality_lookup(self, key_columns: tuple[str, ...], value_column: str) -> int | None:
        return len({str(x) for x in self._df[value_column].to_list()}) if self._df.height > 0 else 0

    def enumerate_sample(self, column: str) -> list[Any] | None:
        return list(dict.fromkeys(self._df[column].to_list())) if self._df.height > 0 else []

    def enumerate_lookup(self, value_column: str) -> list[Any] | None:
        return list(dict.fromkeys(self._df[value_column].to_list())) if self._df.height > 0 else []

    def cardinality(self, catalogs: dict[str, Any]) -> int | None:
        return None

    def enumerate_all(self, catalogs: dict[str, Any]) -> list[Any] | None:
        return None
