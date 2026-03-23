from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from faker import Faker


def _normalize_pk(value: Any) -> Any:
    """
    Normalize a value to a canonical form for set-based uniqueness checks.
    Only uuid.UUID is coerced to str because Faker may return either uuid.UUID
    or str depending on version. All other types are kept as-is to avoid
    unnecessary string allocation (e.g. ints stay ints, strings stay strings).
    """
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


@dataclass
class GenerationContext:
    faker: Faker
    catalogs: dict[str, Any]

    # bind_to consistency cache:
    # { col_name -> { bound_value -> generated_value } }
    bind_cache: dict[str, dict[Any, Any]] = field(default_factory=dict)

    # Cross-table FK: table_name -> list of generated row dicts
    generated_tables: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    # is_pk uniqueness: { pk_cache_key -> set of seen values } (used by rejection sampling)
    pk_seen: dict[str, set[Any]] = field(default_factory=dict)

    # is_pk pool: { pk_cache_key -> remaining shuffled values } for bounded providers.
    # A value of _UNBOUNDED sentinel (from resolvers.base) means rejection sampling is used.
    pk_pool: dict[str, Any] = field(default_factory=dict)

    def pk_ensure_unique(self, col: str, value: Any) -> bool:
        """Return True if value is new and was added; False if duplicate."""
        seen = self.pk_seen.setdefault(col, set())
        key = _normalize_pk(value)
        if key in seen:
            return False
        seen.add(key)
        return True

    def has_cached(self, col_name: str, bound_value: Any) -> bool:
        return bound_value in self.bind_cache.get(col_name, {})

    def get_cached(self, col_name: str, bound_value: Any) -> Any:
        return self.bind_cache[col_name][bound_value]

    def set_cached(self, col_name: str, bound_value: Any, value: Any) -> None:
        self.bind_cache.setdefault(col_name, {})[bound_value] = value

    def to_provider_context(self, row: dict[str, Any]) -> dict[str, Any]:
        """Flatten to a plain dict for provider.generate() calls."""
        return {"faker": self.faker, "catalogs": self.catalogs, "row": row}
