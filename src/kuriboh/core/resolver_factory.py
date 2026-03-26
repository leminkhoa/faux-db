from __future__ import annotations

from faker import Faker

from ..parsers.schema import ColumnConfig
from ..providers.file_reader import FileReaderProvider
from ..providers.registry import ProviderRegistry
from ..resolvers.base import BaseResolver
from ..resolvers.faker_node import FakerResolver
from ..resolvers.func_node import FuncResolver
from ..resolvers.provider_node import ProviderResolver
from ..resolvers.rel_node import RelResolver
from . import (
    COLUMN_GEN_TYPE__FAKER,
    COLUMN_GEN_TYPE__FUNC,
    COLUMN_GEN_TYPE__PROVIDER,
    COLUMN_GEN_TYPE__REL,
    FUNCTIONS_DIRNAME,
)


def _validate_file_reader_column(
    col_name: str,
    col_cfg: ColumnConfig,
    provider: FileReaderProvider,
) -> None:
    target = col_cfg.target or ""
    loaded = set(provider.loaded_columns)
    if col_cfg.mode == "sample":
        if not col_cfg.column:
            raise ValueError(
                f"Column '{col_name}': file_reader sample mode requires 'column' "
                f"(provider '{target}')"
            )
        if col_cfg.column not in loaded:
            raise ValueError(
                f"Column '{col_name}': sample column '{col_cfg.column}' is not listed in "
                f"provider '{target}' loaded_columns ({sorted(loaded)})"
            )
        return

    lk = col_cfg.lookup
    assert lk is not None
    for k in lk.key_columns:
        if k not in loaded:
            raise ValueError(
                f"Column '{col_name}': lookup key column '{k}' is not in "
                f"provider '{target}' loaded_columns"
            )
    if lk.value_column not in loaded:
        raise ValueError(
            f"Column '{col_name}': lookup value_column '{lk.value_column}' is not in "
            f"provider '{target}' loaded_columns"
        )


def _validate_non_file_provider_column(col_name: str, col_cfg: ColumnConfig) -> None:
    if col_cfg.mode == "lookup":
        raise ValueError(
            f"Column '{col_name}': mode 'lookup' is only supported for file_reader providers"
        )
    if col_cfg.column is not None:
        raise ValueError(
            f"Column '{col_name}': 'column' is only valid for file_reader sample mode"
        )
    if col_cfg.sample is not None:
        raise ValueError(
            f"Column '{col_name}': 'sample' is only valid for file_reader sample mode"
        )


def validate_provider_columns_for_plan(
    registry: ProviderRegistry,
    columns_cfg: dict[str, ColumnConfig],
) -> None:
    """
    Validate provider columns against concrete provider implementations (e.g. file_reader
    loaded_columns vs schema column / lookup declarations).
    """
    for col_name, col_cfg in columns_cfg.items():
        if col_cfg.type != COLUMN_GEN_TYPE__PROVIDER or not col_cfg.target:
            continue
        provider = registry.get(col_cfg.target)
        if isinstance(provider, FileReaderProvider):
            _validate_file_reader_column(col_name, col_cfg, provider)
        else:
            _validate_non_file_provider_column(col_name, col_cfg)


def _resolve_func_path(user_func: str) -> str:
    """Prepend default functions package if user did not specify it."""
    prefix = f"{FUNCTIONS_DIRNAME}."
    return user_func if user_func.startswith(prefix) else f"{prefix}{user_func}"


def compute_effective_unique(columns_cfg: dict[str, ColumnConfig]) -> dict[str, bool]:
    """
    Compute effective uniqueness for each column.

    A column inherits unique=True if it is bound (via bind_to) to a column
    that is itself unique, so the bound pair always stays consistent.
    """
    effective = {col_name: col_cfg.unique for col_name, col_cfg in columns_cfg.items()}
    for col_name, col_cfg in columns_cfg.items():
        if col_cfg.bind_to and effective.get(col_cfg.bind_to, False):
            effective[col_name] = True
    return effective


def build_resolvers(
    table_name: str,
    columns_cfg: dict[str, ColumnConfig],
    effective_unique: dict[str, bool],
    faker_instance: Faker,
    registry: ProviderRegistry,
) -> dict[str, BaseResolver]:
    """
    Build a resolver for every column in the table.

    Raises ValueError for unknown column types. Adding a new type only
    requires extending this function and adding the corresponding resolver.
    """
    resolvers: dict[str, BaseResolver] = {}

    for col_name, col_cfg in columns_cfg.items():
        col_type = col_cfg.type
        bind_to_col = col_cfg.bind_to or None
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
                col_cfg,
                bind_to_col=bind_to_col,
                unique=is_unique,
                pk_cache_key=pk_cache_key,
            )
        elif col_type == COLUMN_GEN_TYPE__REL:
            ref_table, ref_column = (col_cfg.target or "").split(".", 1)
            resolvers[col_name] = RelResolver(ref_table, ref_column, col_cfg.strategy)
        elif col_type == COLUMN_GEN_TYPE__FUNC:
            resolvers[col_name] = FuncResolver(
                _resolve_func_path(col_cfg.func or ""),
                params=col_cfg.params or {},
                bind_to_col=bind_to_col,
                unique=is_unique,
                pk_cache_key=pk_cache_key,
            )
        else:
            raise ValueError(f"Unsupported column type: {col_type}")

    return resolvers
