from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..core.context import GenerationContext

MAX_PK_RETRIES = 1_000

# Sentinel stored in context.pk_pool to mark "this key uses rejection sampling"
_UNBOUNDED = object()


class BaseResolver(ABC):
    def __init__(
        self,
        bind_to_col: str | None = None,
        cache_key: str | None = None,
        unique: bool = False,
        pk_cache_key: str | None = None,
    ) -> None:
        """
        bind_to_col:  the column name in the current row whose value is the cache key.
        cache_key:    identifier used as the first dimension in GenerationContext.bind_cache.
        unique:       if True, enforce unique values via pool or rejection sampling.
        pk_cache_key: identifier for pk_seen / pk_pool (e.g. "table_name.col_name").
        """
        self._bind_to_col = bind_to_col
        self._cache_key = cache_key
        self._unique = unique
        self._pk_cache_key = pk_cache_key or cache_key

    def resolve(self, context: GenerationContext, row: dict[str, Any]) -> Any:
        if self._unique and self._pk_cache_key:
            return self._resolve_pk(context, row)

        if self._bind_to_col is not None and self._cache_key is not None:
            bound_value = row.get(self._bind_to_col)
            if context.has_cached(self._cache_key, bound_value):
                return context.get_cached(self._cache_key, bound_value)
            value = self._generate(context, row)
            context.set_cached(self._cache_key, bound_value, value)
            return value

        return self._generate(context, row)

    def pre_init_pool(self, context: GenerationContext) -> None:
        """
        Eagerly initialize the value pool before generation starts.
        Bounded providers get a shuffled list; unbounded are marked with _UNBOUNDED.
        Call this after the cardinality guard and before the row loop so failures are caught early.
        """
        if not self._unique or self._pk_cache_key is None:
            return
        key = self._pk_cache_key
        if key in context.pk_pool:
            return
        all_values = self.enumerate_all(context.catalogs)
        if all_values:
            random.shuffle(all_values)
            context.pk_pool[key] = all_values
        else:
            context.pk_pool[key] = _UNBOUNDED  # type: ignore[assignment]

    def _resolve_pk(self, context: GenerationContext, row: dict[str, Any]) -> Any:
        key = self._pk_cache_key
        assert key is not None

        # Pool is expected to already be initialized by pre_init_pool().
        # Fall back to lazy-init only if called without prior initialization.
        if key not in context.pk_pool:
            self.pre_init_pool(context)

        pool = context.pk_pool[key]

        if pool is not _UNBOUNDED:
            if not pool:
                raise ValueError(
                    f"Exhausted all unique values for is_pk column '{key}' "
                    f"(pool is empty — this should not happen after row capping)"
                )
            return pool.pop()  # type: ignore[union-attr]

        # Rejection sampling for unbounded generators (e.g. uuid4)
        for _ in range(MAX_PK_RETRIES):
            value = self._generate(context, row)
            if context.pk_ensure_unique(key, value):
                return value
        raise ValueError(
            f"Column is_pk but could not generate unique value after {MAX_PK_RETRIES} retries "
            "(value space may be too small)"
        )

    def cardinality(self, catalogs: dict[str, Any]) -> int | None:
        """Return the max unique values this resolver can produce, or None if unbounded."""
        return None

    def enumerate_all(self, catalogs: dict[str, Any]) -> list[Any] | None:
        """Return every possible distinct value, or None if the space is unbounded/unknown."""
        return None

    @abstractmethod
    def _generate(self, context: GenerationContext, row: dict[str, Any]) -> Any:
        """Produce a new value, called only when no cached value is available."""
        ...
