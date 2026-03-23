from __future__ import annotations

from typing import TYPE_CHECKING, Any

from faker import Faker

from .base import BaseResolver

if TYPE_CHECKING:
    from ..core.context import GenerationContext


class FakerResolver(BaseResolver):
    def __init__(
        self,
        faker_instance: Faker,
        method: str,
        params: dict[str, Any] | None = None,
        bind_to_col: str | None = None,
        unique: bool = False,
        pk_cache_key: str | None = None,
    ):
        # cache_key: "faker.<method>" keeps it unique and descriptive in the cache
        super().__init__(
            bind_to_col=bind_to_col,
            cache_key=f"faker.{method}",
            unique=unique,
            pk_cache_key=pk_cache_key,
        )
        self._faker = faker_instance
        self._method = method
        self._params = params or {}

    def _generate(self, context: "GenerationContext", row: dict[str, Any]) -> Any:
        func = getattr(self._faker, self._method)
        return func(**self._params)
