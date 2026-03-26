"""
Tests for :mod:`kuriboh.resolvers.provider_node`.

Scenarios covered:

Construction
- Wrong column type raises ValueError
- Missing target raises at ColumnConfig validation

Non-FileReader provider
- Delegates generate() to the underlying provider
- cardinality() and enumerate_all() delegate to the provider

FileReader – sample mode
- Sequential strategy produces values in column order
- Wraps around at the end of the DataFrame
- cardinality() returns distinct value count
- enumerate_all() returns deduped values

FileReader – lookup mode
- Returns matched value for a known key
- on_missing="null" → None for an unknown key
- on_missing="error" → KeyError for an unknown key
- on_missing="default" → configured default value
- cardinality() returns distinct value count from the value column
- enumerate_all() returns all distinct values from the value column

FileReader – composite key lookup
- Two-column key matched correctly
- Partial match (one key col wrong) returns miss

bind_to
- Two rows sharing the same bound value get the same generated output
"""

from __future__ import annotations

import pytest
import polars as pl
from faker import Faker

from kuriboh.core.context import GenerationContext
from kuriboh.parsers.schema import ColumnConfig, LookupConfig
from kuriboh.providers.file_reader import FileReaderProvider
from kuriboh.providers.random_choice import RandomChoiceProvider
from kuriboh.providers.registry import ProviderRegistry
from kuriboh.resolvers.provider_node import ProviderResolver


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ctx() -> GenerationContext:
    return GenerationContext(faker=Faker(), catalogs={})


def _registry(**providers) -> ProviderRegistry:
    reg = ProviderRegistry()
    for name, prov in providers.items():
        reg.register(name, prov)
    return reg


def _fr(data: dict[str, list]) -> FileReaderProvider:
    df = pl.DataFrame(data)
    return FileReaderProvider(df, loaded_columns=list(data.keys()))


def _sample_col(target: str, column: str, **extra) -> ColumnConfig:
    return ColumnConfig(type="provider", target=target, mode="sample", column=column, **extra)


def _lookup_col(
    target: str,
    *,
    key_columns: list[str],
    key_from: str | list[str],
    value_column: str,
    on_missing: str = "null",
    default_value=None,
) -> ColumnConfig:
    return ColumnConfig(
        type="provider",
        target=target,
        mode="lookup",
        lookup=LookupConfig(
            key_columns=key_columns,
            key_from=key_from,
            value_column=value_column,
            on_missing=on_missing,
            default_value=default_value,
        ),
    )


# ---------------------------------------------------------------------------
# Construction guards
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_faker_type_raises(self):
        col = ColumnConfig(type="faker", method="name")
        with pytest.raises(ValueError, match="target"):
            ProviderResolver(_registry(), col)

    def test_provider_missing_target_rejected_by_schema(self):
        with pytest.raises(Exception):
            ColumnConfig(type="provider")  # schema rejects this


# ---------------------------------------------------------------------------
# Non-FileReader provider
# ---------------------------------------------------------------------------

class TestRandomChoiceProvider:
    def test_generate_returns_value_from_choices(self):
        prov = RandomChoiceProvider(["red", "green", "blue"], seed=0)
        reg = _registry(ColorP=prov)
        r = ProviderResolver(reg, _sample_col("ColorP", "color"))
        assert r.resolve(_ctx(), {}) in {"red", "green", "blue"}

    def test_cardinality_delegates_to_provider(self):
        prov = RandomChoiceProvider(["a", "b", "c"])
        reg = _registry(P=prov)
        r = ProviderResolver(reg, _sample_col("P", "x"))
        assert r.cardinality({}) == 3

    def test_enumerate_all_delegates_to_provider(self):
        prov = RandomChoiceProvider(["x", "y"])
        reg = _registry(P=prov)
        r = ProviderResolver(reg, _sample_col("P", "x"))
        assert set(r.enumerate_all({})) == {"x", "y"}


# ---------------------------------------------------------------------------
# FileReader – sample mode
# ---------------------------------------------------------------------------

class TestFileReaderSample:
    def test_sequential_returns_values_in_column_order(self):
        reg = _registry(P=_fr({"name": ["Alice", "Bob", "Carol"]}))
        r = ProviderResolver(reg, _sample_col("P", "name"))
        ctx = _ctx()
        assert [r.resolve(ctx, {}) for _ in range(3)] == ["Alice", "Bob", "Carol"]

    def test_sequential_wraps_at_end(self):
        reg = _registry(P=_fr({"name": ["X", "Y"]}))
        r = ProviderResolver(reg, _sample_col("P", "name"))
        ctx = _ctx()
        assert [r.resolve(ctx, {}) for _ in range(4)] == ["X", "Y", "X", "Y"]

    def test_cardinality_returns_distinct_count(self):
        reg = _registry(P=_fr({"name": ["A", "A", "B"]}))
        r = ProviderResolver(reg, _sample_col("P", "name"))
        assert r.cardinality({}) == 2

    def test_enumerate_all_deduplicates(self):
        reg = _registry(P=_fr({"name": ["A", "A", "B"]}))
        r = ProviderResolver(reg, _sample_col("P", "name"))
        assert r.enumerate_all({}) == ["A", "B"]


# ---------------------------------------------------------------------------
# FileReader – lookup mode (simple key)
# ---------------------------------------------------------------------------

class TestFileReaderLookup:
    def _resolver(self, *, on_missing="null", default_value=None):
        prov = _fr({"sku": ["AAA", "BBB"], "price": ["9.99", "19.99"]})
        reg = _registry(PriceP=prov)
        col = _lookup_col(
            "PriceP",
            key_columns=["sku"],
            key_from="sku",
            value_column="price",
            on_missing=on_missing,
            default_value=default_value,
        )
        return ProviderResolver(reg, col)

    def test_known_key_returns_value(self):
        assert self._resolver().resolve(_ctx(), {"sku": "AAA"}) == "9.99"

    def test_second_key_returns_correct_value(self):
        assert self._resolver().resolve(_ctx(), {"sku": "BBB"}) == "19.99"

    def test_on_missing_null_returns_none(self):
        assert self._resolver(on_missing="null").resolve(_ctx(), {"sku": "ZZZ"}) is None

    def test_on_missing_error_raises_key_error(self):
        r = self._resolver(on_missing="error")
        with pytest.raises(KeyError):
            r.resolve(_ctx(), {"sku": "MISSING"})

    def test_on_missing_default_returns_configured_value(self):
        r = self._resolver(on_missing="default", default_value="N/A")
        assert r.resolve(_ctx(), {"sku": "MISSING"}) == "N/A"

    def test_cardinality_reflects_distinct_values(self):
        assert self._resolver().cardinality({}) == 2

    def test_enumerate_all_returns_value_column_values(self):
        vals = self._resolver().enumerate_all({})
        assert set(vals) == {"9.99", "19.99"}


# ---------------------------------------------------------------------------
# FileReader – composite key lookup
# ---------------------------------------------------------------------------

class TestFileReaderCompositeKeyLookup:
    def _resolver(self):
        prov = _fr({
            "category": ["furniture", "furniture", "electronics"],
            "sku":      ["SKU-A",     "SKU-B",     "SKU-A"],
            "label":    ["Chair",     "Table",     "Adapter"],
        })
        reg = _registry(LabelP=prov)
        col = _lookup_col(
            "LabelP",
            key_columns=["category", "sku"],
            key_from=["cat", "sku"],
            value_column="label",
        )
        return ProviderResolver(reg, col)

    def test_composite_hit_returns_correct_label(self):
        r = self._resolver()
        assert r.resolve(_ctx(), {"cat": "furniture", "sku": "SKU-A"}) == "Chair"

    def test_same_sku_different_category_returns_different_label(self):
        r = self._resolver()
        assert r.resolve(_ctx(), {"cat": "electronics", "sku": "SKU-A"}) == "Adapter"

    def test_partial_match_returns_none(self):
        r = self._resolver()
        assert r.resolve(_ctx(), {"cat": "furniture", "sku": "SKU-X"}) is None


# ---------------------------------------------------------------------------
# bind_to with ProviderResolver
# ---------------------------------------------------------------------------

class TestBindTo:
    def test_same_bound_value_returns_cached_output(self):
        reg = _registry(P=_fr({"name": ["Alice", "Bob", "Carol"]}))
        col = _sample_col("P", "name", bind_to="order_id")
        r = ProviderResolver(reg, col, bind_to_col="order_id")
        ctx = _ctx()
        v1 = r.resolve(ctx, {"order_id": 42})
        v2 = r.resolve(ctx, {"order_id": 42})
        assert v1 == v2

    def test_different_bound_values_independent(self):
        reg = _registry(P=_fr({"name": ["Alice", "Bob"]}))
        col = _sample_col("P", "name", bind_to="order_id")
        r = ProviderResolver(reg, col, bind_to_col="order_id")
        ctx = _ctx()
        v1 = r.resolve(ctx, {"order_id": 1})
        v2 = r.resolve(ctx, {"order_id": 2})
        # Both are cached under their own keys
        assert ctx.has_cached("P", 1)
        assert ctx.has_cached("P", 2)
        assert ctx.get_cached("P", 1) == v1
        assert ctx.get_cached("P", 2) == v2
