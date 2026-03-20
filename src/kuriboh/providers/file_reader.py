from __future__ import annotations

from typing import Any, Dict, List

from .base import BaseProvider


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
