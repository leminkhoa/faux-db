"""Unit tests for the catalog template DSL in ``kuriboh.providers.catalog.dsl``."""

from __future__ import annotations

import pytest

from kuriboh.providers.catalog.dsl import (
    CatalogSpan,
    apply_spans,
    parse_catalog_spans,
    resolve_span,
)


def test_parse_catalog_spans_minimal_path():
    spans = parse_catalog_spans('{{ catalog("furniture.material") }}')
    assert len(spans) == 1
    assert spans[0].path == ["furniture", "material"]
    assert spans[0].pick == "random"


def test_parse_invalid_path_too_short():
    with pytest.raises(ValueError, match="at least 'stem.key'"):
        parse_catalog_spans('{{ catalog("furniture") }}')


def test_apply_spans_first():
    template = 'x {{ catalog("furniture.material") | first }} y'
    spans = parse_catalog_spans(template)
    catalogs = {"furniture": {"material": ["Steel", "Wood"]}}
    out = apply_spans(template, spans, catalogs, {}, 0, rng=None)
    assert out == "x Steel y"


def test_resolve_span_default_when_empty():
    span = CatalogSpan(
        start=0,
        end=10,
        path=["missing", "list"],
        pick="random",
        default="N/A",
    )
    assert resolve_span(span, {}, {}, 0, 0, rng=None) == "N/A"


def test_parse_duplicate_default_raises():
    with pytest.raises(ValueError, match="duplicate default"):
        parse_catalog_spans(
            '{{ catalog("furniture.material") | default(\'a\') | default(\'b\') }}'
        )


def test_parse_unknown_filter_raises():
    with pytest.raises(ValueError, match="Unknown filter"):
        parse_catalog_spans(
            '{{ catalog("furniture.material") | not_a_real_filter }}'
        )


def test_parse_multiple_pick_filters_raises():
    with pytest.raises(ValueError, match="Only one pick filter"):
        parse_catalog_spans(
            '{{ catalog("furniture.material") | random | first }}'
        )


def test_resolve_span_empty_when_terminal_not_list():
    """`_deep_get` returns [] when the catalog path ends on a non-list value."""
    span = CatalogSpan(
        start=0,
        end=10,
        path=["furniture", "material"],
        pick="first",
        default=None,
    )
    catalogs = {"furniture": {"material": "scalar-not-a-list"}}
    assert resolve_span(span, catalogs, {}, 0, 0, rng=None) == ""


def test_resolve_span_unhandled_pick_raises_assertion():
    """Unreachable via parsing; guards against bad :class:`CatalogSpan` construction."""
    span = CatalogSpan(
        start=0,
        end=10,
        path=["furniture", "material"],
        pick="invalid_pick",
        default=None,
    )
    catalogs = {"furniture": {"material": ["a"]}}
    with pytest.raises(AssertionError, match="Unhandled pick filter"):
        resolve_span(span, catalogs, {}, 0, 0, rng=None)
