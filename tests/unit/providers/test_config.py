"""Tests for :mod:`faux.providers.config` (Pydantic validation)."""

from __future__ import annotations

import pytest

from faux.providers.config import validate_provider_config


def test_random_choice_valid():
    c = validate_provider_config("X", {"type": "random_choice", "choices": [1, 2]})
    assert c.type == "random_choice"
    assert c.choices == [1, 2]


def test_random_choice_empty_choices_raises():
    with pytest.raises(ValueError, match="Invalid provider config"):
        validate_provider_config("X", {"type": "random_choice", "choices": []})


def test_random_choice_weights_length_mismatch_raises():
    with pytest.raises(ValueError, match="Invalid provider config"):
        validate_provider_config(
            "X",
            {"type": "random_choice", "choices": [1, 2], "weights": [1.0]},
        )


def test_expression_empty_exp_raises():
    with pytest.raises(ValueError, match="Invalid provider config"):
        validate_provider_config("X", {"type": "expression", "exp": "   "})
