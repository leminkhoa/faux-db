"""
Tests for :mod:`faux.resolvers.faker_node`.

Scenarios covered:
- Basic method call returns a value
- Method with static params is forwarded correctly
- Unknown faker method raises AttributeError at generate time
- bind_to caching: same bound id returns the same generated name
- Different bind ids produce independently cached values
"""

from __future__ import annotations

import pytest
from faker import Faker

from faux.core.context import GenerationContext
from faux.resolvers.faker_node import FakerResolver


def _ctx() -> GenerationContext:
    return GenerationContext(faker=Faker(), catalogs={})


class TestFakerResolver:
    def test_name_method_returns_a_string(self):
        r = FakerResolver(Faker(), "name")
        assert isinstance(r.resolve(_ctx(), {}), str)

    def test_method_with_params_forwarded(self):
        r = FakerResolver(Faker(), "pyint", params={"min_value": 7, "max_value": 7})
        assert r.resolve(_ctx(), {}) == 7

    def test_unknown_method_raises_attribute_error(self):
        r = FakerResolver(Faker(), "no_such_method_xyz")
        with pytest.raises(AttributeError):
            r.resolve(_ctx(), {})

    def test_bind_to_same_key_returns_cached_value(self):
        r = FakerResolver(Faker(), "name", bind_to_col="user_id")
        ctx = _ctx()
        v1 = r.resolve(ctx, {"user_id": 1})
        v2 = r.resolve(ctx, {"user_id": 1})
        assert v1 == v2

    def test_bind_to_different_keys_cached_independently(self):
        r = FakerResolver(Faker(), "name", bind_to_col="user_id")
        ctx = _ctx()
        r.resolve(ctx, {"user_id": 1})
        r.resolve(ctx, {"user_id": 2})
        # Both cache slots exist and hold their own values
        assert ctx.has_cached("faker.name", 1)
        assert ctx.has_cached("faker.name", 2)

    def test_cardinality_is_none(self):
        r = FakerResolver(Faker(), "name")
        assert r.cardinality({}) is None

    def test_enumerate_all_is_none(self):
        r = FakerResolver(Faker(), "name")
        assert r.enumerate_all({}) is None
