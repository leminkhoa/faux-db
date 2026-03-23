from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import BaseResolver
from .file_reader_context import (
    FileReaderSampleSession,
    file_reader_cardinality,
    file_reader_enumerate,
    lookup_spec,
    sample_spec,
)
from ..core import COLUMN_GEN_TYPE__PROVIDER
from ..parsers.schema import ColumnConfig
from ..providers.file_reader import FileReaderProvider
from ..providers.registry import ProviderRegistry

if TYPE_CHECKING:
    from ..core.context import GenerationContext


class ProviderResolver(BaseResolver):
    def __init__(
        self,
        registry: ProviderRegistry,
        col_cfg: ColumnConfig,
        bind_to_col: str | None = None,
        unique: bool = False,
        pk_cache_key: str | None = None,
    ) -> None:
        if col_cfg.type != COLUMN_GEN_TYPE__PROVIDER or not col_cfg.target:
            raise ValueError("ProviderResolver requires a $provider column with 'target'")
        super().__init__(
            bind_to_col=bind_to_col,
            cache_key=col_cfg.target,
            unique=unique,
            pk_cache_key=pk_cache_key,
        )
        self._registry = registry
        self._col_cfg = col_cfg
        self._target = col_cfg.target
        self._fr_sample_session = FileReaderSampleSession(col_cfg)

    def cardinality(self, catalogs: dict[str, Any]) -> int | None:
        provider = self._registry.get(self._target)
        if isinstance(provider, FileReaderProvider):
            c = file_reader_cardinality(provider, self._col_cfg)
            if c is not None:
                return c
        return provider.cardinality(catalogs)

    def enumerate_all(self, catalogs: dict[str, Any]) -> list | None:
        provider = self._registry.get(self._target)
        if isinstance(provider, FileReaderProvider):
            values = file_reader_enumerate(provider, self._col_cfg)
            if values is not None:
                return values
        return provider.enumerate_all(catalogs)

    def _generate(self, context: "GenerationContext", row: dict[str, Any]) -> Any:
        provider = self._registry.get(self._target)
        base_ctx = context.to_provider_context(row)

        if not isinstance(provider, FileReaderProvider):
            return provider.generate(base_ctx)

        cfg = self._col_cfg
        ctx = dict(base_ctx)

        if cfg.mode == "lookup":
            lk = cfg.lookup
            assert lk is not None
            ctx["file_reader"] = lookup_spec(lk, row)
        else:
            ctx["file_reader"] = sample_spec(cfg, provider, self._fr_sample_session)

        return provider.generate(ctx)
