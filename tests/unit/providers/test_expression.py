"""Tests for :class:`~kuriboh.providers.expression.ExpressionProvider`."""

from __future__ import annotations

import pytest
from faker import Faker

from kuriboh.providers.expression import ExpressionProvider


def test_expression_random_int_with_context_faker():
    ctx = {"faker": Faker()}
    p = ExpressionProvider("{{ faker.random_int(10, 12) }}")
    x = p.generate(ctx)
    assert 10 <= x <= 12


def test_expression_seed_instance_deterministic():
    p = ExpressionProvider("{{ faker.random_int(1, 1000) }}", seed=12345)
    x = p.generate({})
    y = p.generate({})
    assert x != y  # successive calls differ; not testing exact values

    q = ExpressionProvider("{{ faker.random_int(1, 1000) }}", seed=12345)
    assert q.generate({}) == x


def test_expression_unsupported_format_raises():
    p = ExpressionProvider("not a template")
    with pytest.raises(ValueError, match="Unsupported expression format"):
        p.generate({"faker": Faker()})


def test_expression_cardinality_random_int():
    p = ExpressionProvider("{{ faker.random_int(1, 3) }}")
    assert p.cardinality({}) == 3
