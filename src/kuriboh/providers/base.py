from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


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