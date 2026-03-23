"""
Tests for :mod:`kuriboh.resolvers.rel_node`.

Scenarios covered:
- random strategy picks a value from the source table rows
- sequential strategy returns rows in order and wraps at the end
- sequential index is per-resolver-instance (two resolvers do not share state)
- table not yet generated raises ValueError
- empty source table raises ValueError
- missing column in source row raises KeyError
"""

from __future__ import annotations

import pytest
from faker import Faker

from kuriboh.core.context import GenerationContext
from kuriboh.resolvers.rel_node import RelResolver


def _ctx(tables: dict | None = None) -> GenerationContext:
    ctx = GenerationContext(faker=Faker(), catalogs={})
    if tables:
        ctx.generated_tables.update(tables)
    return ctx


class TestRelResolverRandom:
    def test_returns_value_from_source_column(self):
        rows = [{"name": "Alice"}, {"name": "Bob"}]
        r = RelResolver("users", "name", strategy="random")
        result = r.resolve(_ctx({"users": rows}), {})
        assert result in {"Alice", "Bob"}

    def test_multiple_calls_draw_from_source(self):
        rows = [{"v": i} for i in range(10)]
        r = RelResolver("t", "v", strategy="random")
        ctx = _ctx({"t": rows})
        results = {r.resolve(ctx, {}) for _ in range(20)}
        # With 10 distinct values and 20 draws, we expect more than 1 unique result
        assert len(results) > 1


class TestRelResolverSequential:
    def test_cycles_in_insertion_order(self):
        rows = [{"id": 1}, {"id": 2}, {"id": 3}]
        r = RelResolver("orders", "id", strategy="sequential")
        ctx = _ctx({"orders": rows})
        assert [r.resolve(ctx, {}) for _ in range(3)] == [1, 2, 3]

    def test_wraps_around_after_last_row(self):
        rows = [{"v": "a"}, {"v": "b"}]
        r = RelResolver("t", "v", strategy="sequential")
        ctx = _ctx({"t": rows})
        assert [r.resolve(ctx, {}) for _ in range(5)] == ["a", "b", "a", "b", "a"]

    def test_two_resolvers_have_independent_counters(self):
        rows = [{"x": 10}, {"x": 20}, {"x": 30}]
        ctx = _ctx({"t": rows})
        r1 = RelResolver("t", "x", strategy="sequential")
        r2 = RelResolver("t", "x", strategy="sequential")
        r1.resolve(ctx, {})  # advances r1 to index 1
        r1.resolve(ctx, {})  # advances r1 to index 2
        # r2 should still start at 0
        assert r2.resolve(ctx, {}) == 10


class TestRelResolverErrors:
    def test_missing_table_raises_value_error(self):
        r = RelResolver("nonexistent", "col")
        with pytest.raises(ValueError, match="nonexistent"):
            r.resolve(_ctx(), {})

    def test_empty_table_raises_value_error(self):
        r = RelResolver("users", "name")
        with pytest.raises(ValueError, match="users"):
            r.resolve(_ctx({"users": []}), {})

    def test_missing_column_in_row_raises(self):
        rows = [{"id": 1}]
        r = RelResolver("users", "nonexistent_col")
        # random.choice returns the row dict, then key access raises KeyError
        with pytest.raises(KeyError):
            r.resolve(_ctx({"users": rows}), {})
