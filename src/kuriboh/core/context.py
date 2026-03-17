from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

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
    catalogs: Dict[str, Any]

    # bind_to consistency cache:
    # { col_name -> { bound_value -> generated_value } }
    bind_cache: Dict[str, Dict[Any, Any]] = field(default_factory=dict)

    # Cross-table FK: table_name -> list of generated row dicts
    generated_tables: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    # is_pk uniqueness: { pk_cache_key -> set of seen values } (used by rejection sampling)
    pk_seen: Dict[str, Set[Any]] = field(default_factory=dict)

    # is_pk pool: { pk_cache_key -> remaining shuffled values } for bounded providers.
    # A value of _UNBOUNDED sentinel (from resolvers.base) means rejection sampling is used.
    pk_pool: Dict[str, Any] = field(default_factory=dict)

    def pk_ensure_unique(self, col: str, value: Any) -> bool:
        """Return True if value is new and was added; False if duplicate."""
        if col not in self.pk_seen:
            self.pk_seen[col] = set()
        key = _normalize_pk(value)
        if key in self.pk_seen[col]:
            return False
        self.pk_seen[col].add(key)
        return True

    def has_cached(self, col_name: str, bound_value: Any) -> bool:
        return bound_value in self.bind_cache.get(col_name, {})

    def get_cached(self, col_name: str, bound_value: Any) -> Any:
        return self.bind_cache[col_name][bound_value]

    def set_cached(self, col_name: str, bound_value: Any, value: Any) -> None:
        self.bind_cache.setdefault(col_name, {})[bound_value] = value

    def to_provider_context(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten to a plain dict for provider.generate() calls."""
        return {
            "faker": self.faker,
            "catalogs": self.catalogs,
            "row": row,
        }
