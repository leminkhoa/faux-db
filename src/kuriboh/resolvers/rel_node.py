from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from .base import BaseResolver

if TYPE_CHECKING:
    from ..core.context import GenerationContext


class RelResolver(BaseResolver):
    def __init__(self, table: str, column: str, strategy: str = "random") -> None:
        super().__init__(bind_to_col=None, cache_key=None)
        self._table = table
        self._column = column
        self._strategy = strategy
        self._seq_index = 0

    def _generate(self, context: "GenerationContext", row: dict[str, Any]) -> Any:
        source_rows = context.generated_tables.get(self._table, [])
        if not source_rows:
            raise ValueError(f"Table '{self._table}' has not been generated yet")
        if self._strategy == "sequential":
            value = source_rows[self._seq_index % len(source_rows)][self._column]
            self._seq_index += 1
            return value
        return random.choice(source_rows)[self._column]
