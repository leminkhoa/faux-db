from __future__ import annotations

import re
from typing import Any, Dict, Final

from faker import Faker

from .base import BaseProvider

# Names allowed in `{{ name(args) }}`. Each must exist on :class:`faker.Faker`.
SUPPORTED_EXPRESSIONS: Final[frozenset[str]] = frozenset({"random_int"})


def _parse_int_args(args_str: str) -> list[int]:
    args_str = args_str.strip()
    args: list[int] = []
    if not args_str:
        return args
    for part in args_str.split(","):
        part = part.strip()
        if part.isdigit():
            args.append(int(part))
        else:
            raise ValueError(f"Unsupported argument in expression: {part}")
    return args


class ExpressionProvider(BaseProvider):
    """Provider for ``{{ expression_name(args) }}`` with an explicit allowlist."""

    def __init__(self, expression: str, seed: int | None = None):
        self._expression = expression
        # Faker v40+: `Faker(seed=...)` is not a supported constructor API on the
        # proxy. `Faker.seed(n)` is a *class* method that reseeds the shared RNG
        # for *all* generators (bad with multiple expression providers). Use
        # `seed_instance` so each provider gets an isolated, reproducible RNG.
        self._faker: Faker | None = None
        if seed is not None:
            self._faker = Faker()
            self._faker.seed_instance(seed)

    def generate(self, context: Dict[str, Any]) -> Any:
        """
        Evaluates a single expression, e.g. ``{{ random_int(10, 500) }}``.

        Supported names are listed in :data:`SUPPORTED_EXPRESSIONS`.
        """
        faker_instance: Faker = self._faker if self._faker is not None else context["faker"]
        expr = self._expression.strip()
        pattern = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)\s*\}\}")
        match = pattern.fullmatch(expr)
        if not match:
            raise ValueError(f"Unsupported expression format: {expr}")
        method_name, args_str = match.groups()
        if method_name not in SUPPORTED_EXPRESSIONS:
            supported = ", ".join(sorted(SUPPORTED_EXPRESSIONS))
            raise ValueError(
                f"Unsupported expression '{method_name}'. Supported: {supported}"
            )
        method = getattr(faker_instance, method_name)
        args = _parse_int_args(args_str)
        return method(*args)

    def cardinality(self, catalogs: Dict[str, Any]) -> int | None:
        """Infer cardinality for ``random_int(min, max)``; ``None`` for other expressions."""
        pattern = re.compile(r"\{\{\s*random_int\((\d+),\s*(\d+)\)\s*\}\}")
        match = pattern.fullmatch(self._expression.strip())
        if match:
            lo, hi = int(match.group(1)), int(match.group(2))
            return hi - lo + 1
        return None
