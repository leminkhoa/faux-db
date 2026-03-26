"""Tests for :class:`~kuriboh.providers.random_choice.RandomChoiceProvider`."""

from __future__ import annotations

from typing import Any

from kuriboh.providers.random_choice import RandomChoiceProvider


def test_random_choice_seed_reproduces_first_value():
    a = RandomChoiceProvider([1, 2, 3, 4, 5], seed=42)
    b = RandomChoiceProvider([1, 2, 3, 4, 5], seed=42)
    assert a.generate({}) == b.generate({})


def test_random_choice_unweighted_generate_deterministic():
    """Unweighted path uses ``rng.choice``; first draw for seed 42 is ``1``."""
    p = RandomChoiceProvider([1, 2, 3, 4, 5], seed=42)
    assert p.generate({}) == 1


def test_random_choice_generate_accepts_context():
    """``context`` is unused but accepted for API compatibility."""
    p = RandomChoiceProvider(["x", "y"], seed=0)
    ctx: dict[str, Any] = {"catalogs": {}, "extra": 1}
    assert p.generate(ctx) in ("x", "y")


def test_random_choice_weights_one_choice():
    p = RandomChoiceProvider(["a"], weights=[1.0], seed=42)
    assert p.generate({}) == "a"


def test_random_choice_weights_three_choices():
    p = RandomChoiceProvider(["a", "b", "c"], weights=[0.2, 0.5, 0.3], seed=42)
    assert p.generate({}) == "b"


def test_random_choice_cardinality_counts_unique_string_forms():
    p = RandomChoiceProvider(["a", "b", "a"])
    assert p.cardinality({}) == 2


def test_random_choice_cardinality_collapses_same_str():
    r"""``1`` and ``\"1\"`` share ``str(c) == \"1\"``, so cardinality is 1."""
    p = RandomChoiceProvider([1, "1"])
    assert p.cardinality({}) == 1


def test_random_choice_enumerate_all_unique_preserves_order():
    p = RandomChoiceProvider(["a", "b", "a", "c"])
    assert p.enumerate_all({}) == ["a", "b", "c"]
