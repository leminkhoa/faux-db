"""
Catalog template DSL: parse and resolve ``{{ catalog(...) }}`` placeholders.

Used by :class:`~faux.providers.template_choice.TemplateChoiceProvider`.
YAML data under ``catalogs/*.yml`` is unrelated to this package name; this
module only handles the mini-language inside template strings.
"""

from __future__ import annotations

from .dsl import (
    CatalogSpan,
    CycleKey,
    apply_spans,
    parse_catalog_spans,
    resolve_span,
    span_values_for_enumeration,
)

__all__ = [
    "CatalogSpan",
    "CycleKey",
    "apply_spans",
    "parse_catalog_spans",
    "resolve_span",
    "span_values_for_enumeration",
]
