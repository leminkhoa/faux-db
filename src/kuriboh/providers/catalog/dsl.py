"""
Catalog-reference DSL for `template_choice` templates.

Syntax inside a template string:

    {{ catalog('stem.key1.key2') }}
    {{ catalog("stem.key1.key2") | random }}
    {{ catalog('stem.key1.key2') | first }}
    {{ catalog('stem.key1.key2') | cycle }}
    {{ catalog('stem.key1.key2') | default('N/A') }}
    {{ catalog('stem.key1.key2') | default('N/A') | random }}

Rules:
- `stem` is the catalog filename stem (maps to a file in `catalogs/`).
- Additional dot-separated segments drill into nested dict keys; the terminal
  value must be a list.
- Exactly one of `random` / `first` / `cycle` may appear (or none, which
  defaults to `random`).
- `default('<literal>')` may appear once; single or double quotes allowed.
  It is applied before the pick filter when the resolved list is empty.
- Order of pipe tokens is flexible (e.g. `| default('x') | first` is fine).
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# ──────────────────────────────────────────
# Regex: full {{ … }} span
# ──────────────────────────────────────────

_SPAN_RE = re.compile(
    r"\{\{"
    r"\s*catalog\((?:'([^']*)'|\"([^\"]*)\")\)"
    r"((?:\s*\|[^}]*)?)"
    r"\s*\}\}"
)

_DEFAULT_RE = re.compile(r"""default\((?:'([^']*)'|"([^"]*)")\)""")

_PICK_FILTERS = {"random", "first", "cycle"}


@dataclass
class CatalogSpan:
    """Parsed representation of one {{ catalog(...) }} occurrence."""

    start: int
    end: int
    path: List[str]
    pick: str
    default: Optional[str]


def parse_catalog_spans(template: str) -> List[CatalogSpan]:
    """
    Return all CatalogSpan objects found in *template*, left-to-right.
    Raises ValueError for malformed or ambiguous spans (multiple pick
    filters, missing path, etc.).
    """
    spans: List[CatalogSpan] = []
    for m in _SPAN_RE.finditer(template):
        raw_path = m.group(1) if m.group(1) is not None else m.group(2)
        pipe_str = m.group(3) or ""

        path = [seg for seg in raw_path.split(".") if seg]
        if len(path) < 2:
            raise ValueError(
                f"catalog() path must be at least 'stem.key', got: '{raw_path}'"
            )

        tokens = [t.strip() for t in pipe_str.split("|") if t.strip()]

        default_value: Optional[str] = None
        remaining: List[str] = []
        for tok in tokens:
            dm = _DEFAULT_RE.fullmatch(tok)
            if dm:
                if default_value is not None:
                    raise ValueError(
                        f"duplicate default() in template span: '{m.group(0)}'"
                    )
                default_value = dm.group(1) if dm.group(1) is not None else dm.group(2)
            else:
                remaining.append(tok)

        picks_found = [t for t in remaining if t in _PICK_FILTERS]
        unknown = [t for t in remaining if t not in _PICK_FILTERS]

        if unknown:
            raise ValueError(
                f"Unknown filter(s) {unknown!r} in template span: '{m.group(0)}'"
            )
        if len(picks_found) > 1:
            raise ValueError(
                f"Only one pick filter (random/first/cycle) allowed per span, "
                f"got {picks_found!r} in: '{m.group(0)}'"
            )

        pick = picks_found[0] if picks_found else "random"

        spans.append(
            CatalogSpan(
                start=m.start(),
                end=m.end(),
                path=path,
                pick=pick,
                default=default_value,
            )
        )

    return spans


def _deep_get(catalogs: Dict[str, Any], path: List[str]) -> List[Any]:
    stem, *keys = path
    node: Any = catalogs.get(stem)
    for key in keys:
        if not isinstance(node, dict):
            return []
        node = node.get(key)
    if isinstance(node, list):
        return node
    return []


CycleKey = Tuple[int, int]


def resolve_span(
    span: CatalogSpan,
    catalogs: Dict[str, Any],
    cycle_state: Dict[CycleKey, int],
    template_idx: int,
    slot_idx: int,
    rng: random.Random | None = None,
) -> str:
    values = _deep_get(catalogs, span.path)

    if not values:
        return span.default if span.default is not None else ""

    pick = span.pick

    if pick == "random":
        src = rng if rng is not None else random
        return str(src.choice(values))

    if pick == "first":
        return str(values[0])

    if pick == "cycle":
        key: CycleKey = (template_idx, slot_idx)
        idx = cycle_state.get(key, 0)
        value = values[idx % len(values)]
        cycle_state[key] = idx + 1
        return str(value)

    raise AssertionError(f"Unhandled pick filter: {pick!r}")


def apply_spans(
    template: str,
    spans: List[CatalogSpan],
    catalogs: Dict[str, Any],
    cycle_state: Dict[CycleKey, int],
    template_idx: int,
    rng: random.Random | None = None,
) -> str:
    parts: List[str] = []
    cursor = 0
    for slot_idx, span in enumerate(spans):
        parts.append(template[cursor : span.start])
        parts.append(
            resolve_span(span, catalogs, cycle_state, template_idx, slot_idx, rng=rng)
        )
        cursor = span.end
    parts.append(template[cursor:])
    return "".join(parts)


def span_values_for_enumeration(
    span: CatalogSpan,
    catalogs: Dict[str, Any],
) -> List[str]:
    values = _deep_get(catalogs, span.path)

    if not values:
        fallback = span.default if span.default is not None else ""
        return [fallback]

    if span.pick == "first":
        return [str(values[0])]

    return list(dict.fromkeys(str(v) for v in values))
