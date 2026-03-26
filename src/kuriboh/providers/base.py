from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    @abstractmethod
    def generate(self, context: dict[str, Any]) -> Any:
        ...

    def cardinality(self, catalogs: dict[str, Any]) -> int | None:
        """Return the max number of unique values this provider can produce, or None if unbounded."""
        return None

    def enumerate_all(self, catalogs: dict[str, Any]) -> list[Any] | None:
        """Return every possible distinct value, or None if the space is too large / unknown."""
        return None
