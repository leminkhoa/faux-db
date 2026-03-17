from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Sequence

_CATALOG_REF_PATTERN = re.compile(r"\{\{\s*catalog\('([^']+)'\)\s*\|\s*random\s*\}\}")


class BaseProvider(ABC):
    @abstractmethod
    def generate(self, context: Dict[str, Any]) -> Any:
        ...

    def cardinality(self, catalogs: Dict[str, Any]) -> int | None:
        """Return the max number of unique values this provider can produce, or None if unbounded."""
        return None

    def enumerate_all(self, catalogs: Dict[str, Any]) -> List[Any] | None:
        """Return every possible distinct value, or None if the space is too large / unknown."""
        return None


class RandomChoiceProvider(BaseProvider):
    def __init__(self, choices: Sequence[Any], weights: Sequence[float] | None = None):
        self._choices = list(choices)
        self._weights = list(weights) if weights is not None else None

    def generate(self, context: Dict[str, Any]) -> Any:
        import random

        if self._weights:
            return random.choices(self._choices, weights=self._weights, k=1)[0]
        return random.choice(self._choices)

    def cardinality(self, catalogs: Dict[str, Any]) -> int | None:
        return len(set(str(c) for c in self._choices))

    def enumerate_all(self, catalogs: Dict[str, Any]) -> List[Any] | None:
        return list(dict.fromkeys(self._choices))


class FileReaderProvider(BaseProvider):
    def __init__(self, rows: List[Dict[str, Any]], column: str):
        self._rows = rows
        self._column = column
        self._index = 0

    def generate(self, context: Dict[str, Any]) -> Any:
        if not self._rows:
            return None
        row = self._rows[self._index % len(self._rows)]
        self._index += 1
        return row.get(self._column)

    def cardinality(self, catalogs: Dict[str, Any]) -> int | None:
        return len(set(str(r.get(self._column)) for r in self._rows))

    def enumerate_all(self, catalogs: Dict[str, Any]) -> List[Any] | None:
        return list(dict.fromkeys(r.get(self._column) for r in self._rows))


class TemplateChoiceProvider(BaseProvider):
    def __init__(self, templates: Iterable[str]):
        self._templates = list(templates)

    def generate(self, context: Dict[str, Any]) -> Any:
        import random

        template = random.choice(self._templates)
        catalogs = context.get("catalogs", {})

        def eval_catalog(expr: str) -> str:
            # expr form: "furniture.material"
            catalog_name, key = expr.split(".", 1)
            values = catalogs.get(catalog_name, {}).get(key, [])
            if not values:
                return ""
            return random.choice(values)

        result = template

        # Matches: {{ catalog('furniture.material') | random }}
        def repl(match: re.Match) -> str:
            return eval_catalog(match.group(1))

        result = _CATALOG_REF_PATTERN.sub(repl, result)
        return result

    def cardinality(self, catalogs: Dict[str, Any]) -> int | None:
        """
        Sum of cartesian-product sizes across all templates.
        Each {{ catalog('x.y') | random }} slot multiplies the combination count
        by the size of that catalog list.
        """
        total = 0
        for template in self._templates:
            refs = _CATALOG_REF_PATTERN.findall(template)
            if not refs:
                total += 1
                continue
            combo = 1
            for ref in refs:
                catalog_name, key = ref.split(".", 1)
                values = catalogs.get(catalog_name, {}).get(key, [])
                combo *= max(len(values), 1)
            total += combo
        return total

    def enumerate_all(self, catalogs: Dict[str, Any]) -> List[Any] | None:
        """
        Expand each template into its full cartesian product of catalog values
        and return all distinct resulting strings.
        """
        import itertools

        results: dict[str, None] = {}
        for template in self._templates:
            matches = list(_CATALOG_REF_PATTERN.finditer(template))
            if not matches:
                results[template] = None
                continue
            slot_choices = []
            for m in matches:
                catalog_name, key = m.group(1).split(".", 1)
                values = catalogs.get(catalog_name, {}).get(key, [])
                slot_choices.append(values if values else [""])
            for combo in itertools.product(*slot_choices):
                result = template
                # Replace right-to-left to keep match positions valid
                for m, value in reversed(list(zip(matches, combo))):
                    result = result[: m.start()] + str(value) + result[m.end() :]
                results[result] = None
        return list(results.keys())


class ExpressionProvider(BaseProvider):
    def __init__(self, expression: str):
        self._expression = expression

    def generate(self, context: Dict[str, Any]) -> Any:
        """
        Supports expressions like: "{{ faker.random_int(10, 500) }}".
        """
        from faker import Faker

        faker_instance: Faker = context["faker"]
        expr = self._expression.strip()
        # Matches: {{ faker.random_int(10, 500) }}
        pattern = re.compile(r"\{\{\s*faker\.([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)\s*\}\}")
        match = pattern.fullmatch(expr)
        if not match:
            raise ValueError(f"Unsupported expression format: {expr}")
        method_name, args_str = match.groups()
        method = getattr(faker_instance, method_name)
        args_str = args_str.strip()
        args = []
        if args_str:
            # Very naive arg parser for int literals: "10, 500"
            for part in args_str.split(","):
                part = part.strip()
                if part.isdigit():
                    args.append(int(part))
                else:
                    raise ValueError(f"Unsupported argument in expression: {part}")
        return method(*args)

    def cardinality(self, catalogs: Dict[str, Any]) -> int | None:
        """Infer cardinality for random_int(min, max) expressions; None otherwise."""
        pattern = re.compile(r"\{\{\s*faker\.random_int\((\d+),\s*(\d+)\)\s*\}\}")
        match = pattern.fullmatch(self._expression.strip())
        if match:
            lo, hi = int(match.group(1)), int(match.group(2))
            return hi - lo + 1
        return None