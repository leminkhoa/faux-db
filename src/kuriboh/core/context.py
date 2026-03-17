from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from faker import Faker


@dataclass
class GenerationContext:
    faker: Faker
    catalogs: Dict[str, Any]

    # bind_to consistency cache:
    # { col_name -> { bound_value -> generated_value } }
    # E.g. { "price": { "Wooden Sofa": 342, "Steel Bed": 178 } }
    bind_cache: Dict[str, Dict[Any, Any]] = field(default_factory=dict)

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
