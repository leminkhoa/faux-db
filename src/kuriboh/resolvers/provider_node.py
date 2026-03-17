from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from .base import BaseResolver
from ..providers.registry import ProviderRegistry

if TYPE_CHECKING:
    from ..core.context import GenerationContext


class ProviderResolver(BaseResolver):
    def __init__(
        self,
        registry: ProviderRegistry,
        target: str,
        bind_to_col: str | None = None,
        unique: bool = False,
        pk_cache_key: str | None = None,
    ):
        # cache_key: the provider target name keeps entries unique per provider
        super().__init__(
            bind_to_col=bind_to_col,
            cache_key=target,
            unique=unique,
            pk_cache_key=pk_cache_key,
        )
        self._registry = registry
        self._target = target

    def cardinality(self, catalogs: Dict[str, Any]) -> int | None:
        provider = self._registry.get(self._target)
        return provider.cardinality(catalogs)

    def enumerate_all(self, catalogs: Dict[str, Any]) -> list | None:
        provider = self._registry.get(self._target)
        return provider.enumerate_all(catalogs)

    def _generate(self, context: "GenerationContext", row: Dict[str, Any]) -> Any:
        provider = self._registry.get(self._target)
        return provider.generate(context.to_provider_context(row))
