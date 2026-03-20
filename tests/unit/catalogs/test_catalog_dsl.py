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
