"""Tests for :class:`~kuriboh.providers.random_choice.RandomChoiceProvider`."""

from __future__ import annotations

from kuriboh.providers.random_choice import RandomChoiceProvider


def test_random_choice_seed_reproduces_first_value():
    a = RandomChoiceProvider([1, 2, 3, 4, 5], seed=42)
    b = RandomChoiceProvider([1, 2, 3, 4, 5], seed=42)
    assert a.generate({}) == b.generate({})


def test_random_choice_weights():
    p = RandomChoiceProvider(["a"], weights=[1.0], seed=0)
    assert p.generate({}) == "a"
