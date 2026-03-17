from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from ..core.context import GenerationContext


class BaseResolver(ABC):
    def __init__(self, bind_to_col: str | None = None, cache_key: str | None = None) -> None:
        """
        bind_to_col:  the column name in the current row whose value is the cache key.
        cache_key:    identifier used as the first dimension in GenerationContext.bind_cache.
                      Defaults to the resolver's own identity; subclasses should pass a
                      stable name (e.g. the faker method or provider target).
        """
        self._bind_to_col = bind_to_col
        self._cache_key = cache_key

    def resolve(self, context: "GenerationContext", row: Dict[str, Any]) -> Any:
        if self._bind_to_col is not None and self._cache_key is not None:
            bound_value = row.get(self._bind_to_col)
            if context.has_cached(self._cache_key, bound_value):
                return context.get_cached(self._cache_key, bound_value)
            value = self._generate(context, row)
            context.set_cached(self._cache_key, bound_value, value)
            return value

        return self._generate(context, row)

    @abstractmethod
    def _generate(self, context: "GenerationContext", row: Dict[str, Any]) -> Any:
        """Produce a new value, called only when no cached value is available."""
        ...