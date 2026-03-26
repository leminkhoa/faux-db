"""
Tests for :mod:`faux.resolvers.base`.

Scenarios covered:
- Plain resolve (no bind_to, no unique) forwards to _generate()
- bind_to caching: same bound value → same result; different bound value → independent
- Missing bound column in row falls back to None as cache key
- unique=True with a bounded provider uses a shuffled pool
- unique=True with an unbounded provider uses rejection sampling
- Exhausted pool raises ValueError
- pre_init_pool is idempotent (second call does not reset the pool)
- Base cardinality / enumerate_all defaults to None
"""

from __future__ import annotations

import pytest
from faker import Faker

from faux.core.context import GenerationContext
from faux.resolvers.base import BaseResolver


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ctx() -> GenerationContext:
    return GenerationContext(faker=Faker(), catalogs={})


class _ConstResolver(BaseResolver):
    """Always returns the same fixed value."""

    def __init__(self, value=42, **kwargs):
        super().__init__(**kwargs)
        self._value = value

    def _generate(self, context, row):
        return self._value


class _ListResolver(BaseResolver):
    """Cycles through a list of values; supports cardinality / enumerate_all."""

    def __init__(self, values: list, **kwargs):
        super().__init__(**kwargs)
        self._values = list(values)
        self._i = 0

    def _generate(self, context, row):
        v = self._values[self._i % len(self._values)]
        self._i += 1
        return v

    def cardinality(self, catalogs):
        return len(set(self._values))

    def enumerate_all(self, catalogs):
        return list(dict.fromkeys(self._values))


# ---------------------------------------------------------------------------
# Plain resolve
# ---------------------------------------------------------------------------

class TestPlainResolve:
    def test_returns_generated_value(self):
        r = _ConstResolver(value="hello")
        assert r.resolve(_ctx(), {}) == "hello"

    def test_called_multiple_times_independently(self):
        r = _ListResolver(["a", "b", "c"])
        ctx = _ctx()
        results = [r.resolve(ctx, {}) for _ in range(3)]
        assert results == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# bind_to caching
# ---------------------------------------------------------------------------

class TestBindTo:
    def test_same_bound_value_returns_cached_result(self):
        r = _ListResolver(["A", "B", "C"], bind_to_col="id", cache_key="k")
        ctx = _ctx()
        first = r.resolve(ctx, {"id": 1})

        # after first, there should be a bind_cache {'k': {1: 'A'}} -> Second should be same as first
        second = r.resolve(ctx, {"id": 1})
        assert first == second

    def test_different_bound_values_stored_separately(self):
        r = _ListResolver(["A", "B"], bind_to_col="id", cache_key="k")
        ctx = _ctx()
        v1 = r.resolve(ctx, {"id": 1})
        v2 = r.resolve(ctx, {"id": 2})
        assert ctx.has_cached("k", 1)
        assert ctx.has_cached("k", 2)
        assert ctx.get_cached("k", 1) == v1 # Should be 'A'
        assert ctx.get_cached("k", 2) == v2 # Should be 'B'

    def test_missing_bound_column_uses_none_as_key(self):
        r = _ConstResolver("X", bind_to_col="missing", cache_key="k")
        ctx = _ctx()
        r.resolve(ctx, {})
        assert ctx.has_cached("k", None)

    def test_cached_value_not_regenerated(self):
        """bind_to must return the cached value without advancing the internal counter."""
        r = _ListResolver(["first", "second"], bind_to_col="id", cache_key="k")
        ctx = _ctx()
        r.resolve(ctx, {"id": 99})   # generates "first", advances counter
        r.resolve(ctx, {"id": 99})   # must return "first" again, NOT "second"
        # Counter would have advanced to 2 without caching, producing "second".
        assert ctx.get_cached("k", 99) == "first"


# ---------------------------------------------------------------------------
# unique / pool
# ---------------------------------------------------------------------------

class TestUnique:
    def test_bounded_pool_produces_all_distinct_values(self):
        values = ["alpha", "beta", "gamma"]
        r = _ListResolver(values, unique=True, pk_cache_key="col.x")
        ctx = _ctx()
        r.pre_init_pool(ctx)
        seen = {r.resolve(ctx, {}) for _ in range(len(values))}
        assert seen == set(values)

    def test_exhausted_pool_raises(self):
        r = _ListResolver(["a", "b"], unique=True, pk_cache_key="col.x")
        ctx = _ctx()
        r.pre_init_pool(ctx)
        r.resolve(ctx, {})
        r.resolve(ctx, {})
        with pytest.raises(ValueError, match="Exhausted"):
            r.resolve(ctx, {})

    def test_unbounded_resolver_uses_rejection_sampling(self):
        counter = [0]

        class _IncrResolver(BaseResolver):
            def _generate(self, context, row):
                counter[0] += 1
                return counter[0]  # always a fresh unique int

        r = _IncrResolver(unique=True, pk_cache_key="col.y")
        ctx = _ctx()
        r.pre_init_pool(ctx)   # enumerate_all returns None → _UNBOUNDED
        val = r.resolve(ctx, {})
        assert isinstance(val, int)

    def test_unique_resolve_lazy_inits_pool_when_pre_init_not_called(self):
        r = _ListResolver(["x", "y"], unique=True, pk_cache_key="lazy.k")
        ctx = _ctx()
        assert "lazy.k" not in ctx.pk_pool
        assert r.resolve(ctx, {}) in {"x", "y"}
        assert "lazy.k" in ctx.pk_pool

    def test_unbounded_rejection_sampling_exhaustion_raises(self):
        class _AlwaysDuplicateResolver(BaseResolver):
            def _generate(self, context, row):
                return "same"

        r = _AlwaysDuplicateResolver(unique=True, pk_cache_key="dup.k")
        ctx = _ctx()
        assert r.resolve(ctx, {}) == "same"
        with pytest.raises(ValueError, match="could not generate unique value"):
            r.resolve(ctx, {})

    def test_pre_init_pool_is_idempotent(self):
        r = _ListResolver([1, 2, 3], unique=True, pk_cache_key="k")
        ctx = _ctx()
        r.pre_init_pool(ctx)
        pool_id = id(ctx.pk_pool["k"])
        r.pre_init_pool(ctx)   # second call must not replace the pool
        assert id(ctx.pk_pool["k"]) == pool_id

    def test_pool_contains_all_values(self):
        r = _ListResolver([10, 20, 30], unique=True, pk_cache_key="k")
        ctx = _ctx()
        r.pre_init_pool(ctx)
        assert set(ctx.pk_pool["k"]) == {10, 20, 30}

    def test_duplicate_input_deduplicates_pool_and_exhausts_by_distinct_count(self):
        r = _ListResolver(["a", "a", "b"], unique=True, pk_cache_key="k")
        ctx = _ctx()
        r.pre_init_pool(ctx)

        assert set(ctx.pk_pool["k"]) == {"a", "b"}

        seen = {r.resolve(ctx, {}) for _ in range(2)}
        assert seen == {"a", "b"}

        with pytest.raises(ValueError, match="Exhausted"):
            r.resolve(ctx, {})


# ---------------------------------------------------------------------------
# cardinality / enumerate_all defaults
# ---------------------------------------------------------------------------

class TestCardinalityDefaults:
    def test_base_cardinality_is_none(self):
        assert _ConstResolver().cardinality({}) is None

    def test_base_enumerate_all_is_none(self):
        assert _ConstResolver().enumerate_all({}) is None

    def test_subclass_cardinality_deduplicated(self):
        assert _ListResolver(["a", "a", "b"]).cardinality({}) == 2

    def test_subclass_enumerate_all_preserves_order(self):
        assert _ListResolver(["a", "a", "b"]).enumerate_all({}) == ["a", "b"]

    def test_pre_init_pool_returns_early_when_not_unique(self):
        r = _ListResolver(["a", "b"], unique=False, pk_cache_key="k")
        ctx = _ctx()
        r.pre_init_pool(ctx)
        assert "k" not in ctx.pk_pool
