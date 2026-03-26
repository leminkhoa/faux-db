from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from collections.abc import Iterable


class BaseSink(ABC):
    @abstractmethod
    def write_rows(self, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
        ...
