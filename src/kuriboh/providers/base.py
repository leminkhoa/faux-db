from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Sequence


class BaseProvider(ABC):
    @abstractmethod
    def generate(self, context: Dict[str, Any]) -> Any:
        ...


class RandomChoiceProvider(BaseProvider):
    def __init__(self, choices: Sequence[Any], weights: Sequence[float] | None = None):
        self._choices = list(choices)
        self._weights = list(weights) if weights is not None else None

    def generate(self, context: Dict[str, Any]) -> Any:
        import random

        if self._weights:
            return random.choices(self._choices, weights=self._weights, k=1)[0]
        return random.choice(self._choices)


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
        import re

        # Matches: {{ catalog('furniture.material') | random }}
        pattern = re.compile(r"\{\{\s*catalog\('([^']+)'\)\s*\|\s*random\s*\}\}")

        def repl(match: re.Match) -> str:
            return eval_catalog(match.group(1))

        result = pattern.sub(repl, result)
        return result


class ExpressionProvider(BaseProvider):
    def __init__(self, expression: str):
        self._expression = expression

    def generate(self, context: Dict[str, Any]) -> Any:
        """
        Supports expressions like: "{{ faker.random_int(10, 500) }}".
        """
        from faker import Faker
        import re

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