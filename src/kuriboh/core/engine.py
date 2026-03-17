from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from faker import Faker

from ..parsers.loader import load_catalogs, load_providers, load_schema
from ..parsers.validator import OutputConfig, SchemaFile, validate_schema
from ..providers.registry import build_registry
from ..resolvers.faker_node import FakerResolver
from ..resolvers.provider_node import ProviderResolver
from ..resolvers.rel_node import RelResolver
from ..sinks.factory import create_sink
from .context import GenerationContext
from .dag import build_dag, build_table_dag, get_bind_to_col
from .types import COLUMN_GEN_TYPE__FAKER, COLUMN_GEN_TYPE__PROVIDER, COLUMN_GEN_TYPE__REL


def run_generation(
    schema_path: Path,
    context: GenerationContext | None = None,
    base_dir: Path | None = None,
) -> None:
    resolved_base = base_dir or schema_path.parent.parent
    if context is None:
        providers_cfg = load_providers(resolved_base)
        catalogs = load_catalogs(resolved_base)
        faker_instance = Faker()
        context = GenerationContext(faker=faker_instance, catalogs=catalogs)
    else:
        providers_cfg = load_providers(resolved_base)
        faker_instance = context.faker

    # ====  SCHEMA LOADING ===
    raw_schema = load_schema(schema_path)
    schema_model: SchemaFile = validate_schema(raw_schema)

    table_name = schema_model.table_name
    table_cfg = schema_model.table
    rows_count: int = int(table_cfg.rows)
    columns_cfg = table_cfg.columns
    output_cfg: OutputConfig = table_cfg.output

    registry = build_registry(resolved_base, providers_cfg)

    # === DAG: resolve column generation order from bind_to declarations ===
    column_order: List[str] = build_dag(columns_cfg)

    # === EFFECTIVE UNIQUENESS: explicit unique:True + inheritance through bind_to ===
    # If column B has bind_to: A and column A has unique: True, B is also treated as unique.
    effective_unique: Dict[str, bool] = {
        col_name: col_cfg.unique for col_name, col_cfg in columns_cfg.items()
    }
    for col_name, col_cfg in columns_cfg.items():
        if col_cfg.bind_to and effective_unique.get(col_cfg.bind_to, False):
            effective_unique[col_name] = True

    # === BUILD RESOLVERS ===
    resolvers: Dict[str, Any] = {}
    for col_name, col_cfg in columns_cfg.items():
        col_type = col_cfg.type
        bind_to_col = get_bind_to_col(col_cfg)
        is_unique = effective_unique[col_name]
        pk_cache_key = f"{table_name}.{col_name}" if is_unique else None
        if col_type == COLUMN_GEN_TYPE__FAKER:
            method = col_cfg.method or ""
            params = col_cfg.params or {}
            resolvers[col_name] = FakerResolver(
                faker_instance, method, params,
                bind_to_col=bind_to_col,
                unique=is_unique,
                pk_cache_key=pk_cache_key,
            )
        elif col_type == COLUMN_GEN_TYPE__PROVIDER:
            target = col_cfg.target or ""
            resolvers[col_name] = ProviderResolver(
                registry, target,
                bind_to_col=bind_to_col,
                unique=is_unique,
                pk_cache_key=pk_cache_key,
            )
        elif col_type == COLUMN_GEN_TYPE__REL:
            target = col_cfg.target or ""
            table, column = target.split(".", 1)
            resolvers[col_name] = RelResolver(table, column, col_cfg.strategy)
        else:
            raise ValueError(f"Unsupported column type: {col_type}")

    # === CARDINALITY GUARD: cap rows to the max unique values any unique column can produce ===
    min_cardinality: int | None = None
    for col_name, resolver in resolvers.items():
        if not resolver._unique:
            continue
        c = resolver.cardinality(context.catalogs)
        if c is not None and (min_cardinality is None or c < min_cardinality):
            min_cardinality = c

    if min_cardinality is not None and rows_count > min_cardinality:
        print(
            f"[kuriboh] Warning: '{table_name}' requests {rows_count} rows but "
            f"unique column(s) can only produce {min_cardinality} unique values. "
            f"Reducing rows to {min_cardinality}."
        )
        rows_count = min_cardinality

    # === PRE-INIT POOLS: eagerly build value pools for all unique columns ===
    # This ensures any enumeration failures are caught before any rows are generated.
    for resolver in resolvers.values():
        resolver.pre_init_pool(context)

    # Create sink class based on configuration
    sink = create_sink(output_cfg)

    # Generated data
    generated_rows: List[Dict[str, Any]] = []
    for _ in range(rows_count):
        row: Dict[str, Any] = {}
        for col_name in column_order:
            resolver = resolvers[col_name]
            value = resolver.resolve(context, row)
            row[col_name] = value
        generated_rows.append(row)

    context.generated_tables[table_name] = generated_rows

    fieldnames = list(columns_cfg.keys())
    sink.write_rows(generated_rows, fieldnames)


def run_domain(domain_path: Path) -> None:
    schema_files = sorted(domain_path.glob("*.yml"))
    if not schema_files:
        raise ValueError(f"No .yml schema files found in {domain_path}")

    base_dir = domain_path.parent.parent
    schemas: Dict[str, SchemaFile] = {}
    table_to_path: Dict[str, Path] = {}
    for f in schema_files:
        raw = load_schema(f)
        schema = validate_schema(raw)
        table_name = schema.table_name
        if table_name in schemas:
            raise ValueError(f"Duplicate table name '{table_name}' in domain (e.g. {f.name})")
        schemas[table_name] = schema
        table_to_path[table_name] = f

    table_order: List[str] = build_table_dag(schemas)

    catalogs = load_catalogs(base_dir)
    context = GenerationContext(faker=Faker(), catalogs=catalogs)

    for table_name in table_order:
        run_generation(table_to_path[table_name], context=context, base_dir=base_dir)
