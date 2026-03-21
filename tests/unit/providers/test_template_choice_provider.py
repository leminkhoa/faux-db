"""Tests for :class:`~kuriboh.providers.template_choice.TemplateChoiceProvider`."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from kuriboh.providers.template_choice import TemplateChoiceProvider


# Minimal catalogs: stem "demo" with nested lists for path demo.a / demo.b
def _demo_catalogs() -> Dict[str, Any]:
    return {
        "demo": {
            "a": ["x", "y"],
            "b": ["p", "q"],
        },
        "nil": {"empty": []},
    }


def test_template_choice_first_material_from_fixture_catalogs(
    loaded_catalogs: Dict[str, Any],
) -> None:
    """
    Catalogs from ``tests/fixtures/catalogs/common/material.yaml`` are loaded
    via the session-scoped ``loaded_catalogs`` fixture (see ``tests/conftest.py``).

    ``| first`` picks the first list entry, so output is deterministic without
    relying on RNG for the catalog slot.
    """

    provider = TemplateChoiceProvider(
        templates=['{{ catalog("material.material") | first }}'],
    )
    out = provider.generate(context={"catalogs": loaded_catalogs})
    assert out == "Steel"


def test_template_choice_rejects_empty_templates_expect_error() -> None:
    """
    `TemplateChoiceProvider` should reject an empty `templates` iterable during
    initialization, rather than failing later in `generate()` (e.g., via
    `random.randrange()` on an empty range).
    """
    with pytest.raises(ValueError, match="at least one template"):
        TemplateChoiceProvider(templates=[])


# --- generate(): pick filters random / first / cycle / default ---


def test_generate_implicit_random_same_as_explicit_pipe_random() -> None:
    catalogs = _demo_catalogs()
    implicit = TemplateChoiceProvider(
        templates=['{{ catalog("demo.a") }}'],
        seed=99,
    )
    explicit = TemplateChoiceProvider(
        templates=['{{ catalog("demo.a") | random }}'],
        seed=99,
    )
    seq_i = [implicit.generate({"catalogs": catalogs}) for _ in range(20)]
    seq_e = [explicit.generate({"catalogs": catalogs}) for _ in range(20)]
    assert seq_i == seq_e


def test_generate_first_is_deterministic() -> None:
    catalogs = _demo_catalogs()
    p = TemplateChoiceProvider(
        templates=['{{ catalog("demo.a") | first }}-{{ catalog("demo.b") | first }}'],
    )
    assert p.generate({"catalogs": catalogs}) == "x-p"
    assert p.generate({"catalogs": catalogs}) == "x-p"


def test_generate_cycle_round_robin_per_slot() -> None:
    catalogs = _demo_catalogs()
    p = TemplateChoiceProvider(
        templates=['{{ catalog("demo.a") | cycle }}'],
        seed=0,
    )
    assert p.generate({"catalogs": catalogs}) == "x"
    assert p.generate({"catalogs": catalogs}) == "y"
    assert p.generate({"catalogs": catalogs}) == "x"


def test_generate_default_when_list_empty() -> None:
    catalogs = _demo_catalogs()
    p = TemplateChoiceProvider(
        templates=['{{ catalog("nil.empty") | default(\'N/A\') }}'],
    )
    assert p.generate({"catalogs": catalogs}) == "N/A"


def test_generate_empty_list_without_default_is_empty_string() -> None:
    catalogs = _demo_catalogs()
    p = TemplateChoiceProvider(
        templates=['{{ catalog("nil.empty") }}'],
    )
    assert p.generate({"catalogs": catalogs}) == ""


# --- cardinality() ---


def test_cardinality_plain_template_without_catalog_spans() -> None:
    p = TemplateChoiceProvider(templates=["no placeholders"])
    assert p.cardinality({}) == 1


def test_cardinality_random_and_cycle_count_all_distinct_values() -> None:
    catalogs = _demo_catalogs()
    pr = TemplateChoiceProvider(templates=['{{ catalog("demo.a") | random }}'])
    pc = TemplateChoiceProvider(templates=['{{ catalog("demo.a") | cycle }}'])
    assert pr.cardinality(catalogs) == 2
    assert pc.cardinality(catalogs) == 2


def test_cardinality_first_counts_single_value() -> None:
    catalogs = _demo_catalogs()
    p = TemplateChoiceProvider(templates=['{{ catalog("demo.a") | first }}'])
    assert p.cardinality(catalogs) == 1


def test_cardinality_two_slots_is_product() -> None:
    catalogs = _demo_catalogs()
    p = TemplateChoiceProvider(
        templates=['{{ catalog("demo.a") }}-{{ catalog("demo.b") }}'],
    )
    assert p.cardinality(catalogs) == 4


def test_cardinality_sums_across_templates() -> None:
    catalogs = _demo_catalogs()
    p = TemplateChoiceProvider(
        templates=[
            "literal-only",
            '{{ catalog("demo.a") }}',
        ],
    )
    assert p.cardinality(catalogs) == 1 + 2


def test_cardinality_empty_catalog_with_default() -> None:
    catalogs = _demo_catalogs()
    p = TemplateChoiceProvider(
        templates=['{{ catalog("nil.empty") | default("z") }}'],
    )
    assert p.cardinality(catalogs) == 1


# --- enumerate_all() ---


def test_enumerate_all_two_slots_lists_all_combinations() -> None:
    catalogs = _demo_catalogs()
    p = TemplateChoiceProvider(
        templates=['{{ catalog("demo.a") }}-{{ catalog("demo.b") }}'],
    )
    out = p.enumerate_all(catalogs)
    assert out is not None
    assert set(out) == {"x-p", "x-q", "y-p", "y-q"}
    assert len(out) == 4


def test_enumerate_all_first_collapses_each_slot_to_one_value() -> None:
    catalogs = _demo_catalogs()
    p = TemplateChoiceProvider(
        templates=['{{ catalog("demo.a") | first }}'],
    )
    assert p.enumerate_all(catalogs) == ["x"]


def test_enumerate_all_plain_template_and_merges_duplicate_strings() -> None:
    catalogs = _demo_catalogs()
    p = TemplateChoiceProvider(
        templates=[
            "literal-only",
            '{{ catalog("demo.a") | first }}',
        ],
    )
    out = p.enumerate_all(catalogs)
    assert out is not None
    assert set(out) == {"literal-only", "x"}
