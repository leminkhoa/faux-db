from __future__ import annotations

import itertools
import random
from typing import Any

from .base import BaseProvider
from .catalog import (
    CatalogSpan,
    CycleKey,
    apply_spans,
    parse_catalog_spans,
    span_values_for_enumeration,
)


class TemplateChoiceProvider(BaseProvider):
    """
    Picks a random template string and substitutes all
    ``{{ catalog('stem.key1…') | <filter> }}`` placeholders.

    Supported filters per placeholder:
      - ``random``         uniform pick from list (default when omitted)
      - ``first``          always pick the first element
      - ``cycle``          round-robin across rows, keyed by
                           (template_index, slot_index)
      - ``default('x')``   fallback literal when the resolved list is empty

    Optional ``seed`` fixes template selection and all ``| random`` slots to a
    reproducible sequence (per provider instance). ``| cycle`` is unchanged
    (deterministic by row order).
    """

    def __init__(self, templates: list[str], seed: int | None = None) -> None:
        self._templates = list(templates)
        if not self._templates:
            raise ValueError(
                "TemplateChoiceProvider requires at least one template; "
                "got an empty iterable."
            )
        self._spans: list[list[CatalogSpan]] = [
            parse_catalog_spans(t) for t in self._templates
        ]
        self._cycle_state: dict[CycleKey, int] = {}
        self._rng = random.Random(seed)

    def generate(self, context: dict[str, Any]) -> Any:
        template_idx = self._rng.randrange(len(self._templates))
        template = self._templates[template_idx]
        spans = self._spans[template_idx]
        catalogs = context.get("catalogs", {})

        if not spans:
            return template

        return apply_spans(template, spans, catalogs, self._cycle_state, template_idx, rng=self._rng)

    def cardinality(self, catalogs: dict[str, Any]) -> int | None:
        total = 0
        for spans in self._spans:
            if not spans:
                total += 1
                continue
            combo = 1
            for span in spans:
                slot_values = span_values_for_enumeration(span, catalogs)
                combo *= max(len(slot_values), 1)
            total += combo
        return total

    def enumerate_all(self, catalogs: dict[str, Any]) -> list[Any] | None:
        results: dict[str, None] = {}

        for _template_idx, (template, spans) in enumerate(
            zip(self._templates, self._spans, strict=True)
        ):
            if not spans:
                results[template] = None
                continue

            slot_value_sets = [
                span_values_for_enumeration(span, catalogs) for span in spans
            ]

            for combo in itertools.product(*slot_value_sets):
                result = template
                for span, value in reversed(list(zip(spans, combo, strict=True))):
                    result = result[: span.start] + value + result[span.end :]
                results[result] = None

        return list(results.keys())
