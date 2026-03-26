"""Tests for :class:`~faux.providers.expression.ExpressionProvider`."""

from __future__ import annotations

import pytest
from faker import Faker

from faux.providers.expression import ExpressionProvider, SUPPORTED_EXPRESSIONS


def test_supported_expressions_lists_random_int():
    assert "random_int" in SUPPORTED_EXPRESSIONS


def test_expression_random_int_with_context_faker():
    ctx = {"faker": Faker()}
    p = ExpressionProvider("{{ random_int(10, 12) }}")
    x = p.generate(ctx)
    assert 10 <= x <= 12


def test_expression_seed_instance_deterministic():
    p = ExpressionProvider("{{ random_int(1, 1000) }}", seed=12345)
    x = p.generate({})
    y = p.generate({})
    assert x != y  # successive calls differ; not testing exact values

    q = ExpressionProvider("{{ random_int(1, 1000) }}", seed=12345)
    assert q.generate({}) == x


def test_expression_unsupported_format_raises():
    p = ExpressionProvider("not a template")
    with pytest.raises(ValueError, match="Unsupported expression format"):
        p.generate({"faker": Faker()})


def test_expression_unknown_name_raises():
    p = ExpressionProvider("{{ unknown_fn(1, 2) }}")
    with pytest.raises(ValueError, match="Unsupported expression 'unknown_fn'"):
        p.generate({"faker": Faker()})


def test_expression_cardinality_random_int():
    p = ExpressionProvider("{{ random_int(1, 3) }}")
    assert p.cardinality({}) == 3
