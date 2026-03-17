from __future__ import annotations

from typing import Dict

from faker import Faker

from ..parsers.validator import ColumnConfig
from ..providers.registry import ProviderRegistry
from ..resolvers.base import BaseResolver
from ..resolvers.faker_node import FakerResolver
from ..resolvers.provider_node import ProviderResolver
from ..resolvers.rel_node import RelResolver
from . import COLUMN_GEN_TYPE__FAKER, COLUMN_GEN_TYPE__PROVIDER, COLUMN_GEN_TYPE__REL
from .dag import get_bind_to_col


def compute_effective_unique(columns_cfg: Dict[str, ColumnConfig]) -> Dict[str, bool]:
    """
    Compute effective uniqueness for each column.

    A column inherits unique=True if it is bound (via bind_to) to a column
    that is itself unique, so the bound pair always stays consistent.
    """
    effective: Dict[str, bool] = {
        col_name: col_cfg.unique for col_name, col_cfg in columns_cfg.items()
    }
    for col_name, col_cfg in columns_cfg.items():
        if col_cfg.bind_to and effective.get(col_cfg.bind_to, False):
            effective[col_name] = True
    return effective


def build_resolvers(
    table_name: str,
    columns_cfg: Dict[str, ColumnConfig],
    effective_unique: Dict[str, bool],
    faker_instance: Faker,
    registry: ProviderRegistry,
) -> Dict[str, BaseResolver]:
    """
    Build a resolver for every column in the table.

    Raises ValueError for unknown column types. Adding a new type only
    requires extending this function and adding the corresponding resolver.
    """
    resolvers: Dict[str, BaseResolver] = {}

    for col_name, col_cfg in columns_cfg.items():
        col_type = col_cfg.type
        bind_to_col = get_bind_to_col(col_cfg)
        is_unique = effective_unique[col_name]
        pk_cache_key = f"{table_name}.{col_name}" if is_unique else None

        if col_type == COLUMN_GEN_TYPE__FAKER:
            resolvers[col_name] = FakerResolver(
                faker_instance,
                col_cfg.method or "",
                col_cfg.params or {},
                bind_to_col=bind_to_col,
                unique=is_unique,
                pk_cache_key=pk_cache_key,
            )
        elif col_type == COLUMN_GEN_TYPE__PROVIDER:
            resolvers[col_name] = ProviderResolver(
                registry,
                col_cfg.target or "",
                bind_to_col=bind_to_col,
                unique=is_unique,
                pk_cache_key=pk_cache_key,
            )
        elif col_type == COLUMN_GEN_TYPE__REL:
            target = col_cfg.target or ""
            ref_table, ref_column = target.split(".", 1)
            resolvers[col_name] = RelResolver(ref_table, ref_column, col_cfg.strategy)
        else:
            raise ValueError(f"Unsupported column type: {col_type}")

    return resolvers
