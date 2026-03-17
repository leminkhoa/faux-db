from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List


class BaseSink(ABC):
    @abstractmethod
    def write_rows(self, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> None:
        ...