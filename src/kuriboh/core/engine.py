from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from faker import Faker

from ..parsers.loader import load_catalogs, load_providers, load_schema
from ..parsers.validator import OutputConfig, SchemaFile, validate_schema
from ..providers.registry import build_registry
from ..resolvers.faker_node import FakerResolver
from ..resolvers.provider_node import ProviderResolver
from ..sinks.csv_sink import CsvSink
from .context import GenerationContext
from .dag import build_dag, get_bind_to_col


def run_generation(schema_path: Path) -> None:
    base_dir = schema_path.parent.parent  # assume schemas/ under project root

    # ====  SCHEMA LOADING ===
    raw_schema = load_schema(schema_path)
    schema_model: SchemaFile = validate_schema(raw_schema)

    table_name = schema_model.table_name
    table_cfg = schema_model.table
    rows_count: int = int(table_cfg.rows)
    columns_cfg = table_cfg.columns
    output_cfg: OutputConfig = table_cfg.output

    # === PROVIDER & CATALOGS LOADING ===
    providers_cfg = load_providers(base_dir)
    catalogs = load_catalogs(base_dir)

    registry = build_registry(base_dir, providers_cfg)
    faker_instance = Faker()

    # === DAG: resolve column generation order from bind_to declarations ===
    column_order: List[str] = build_dag(columns_cfg)

    # === BUILD RESOLVERS ===
    resolvers: Dict[str, Any] = {}
    for col_name, col_cfg in columns_cfg.items():
        col_type = col_cfg.type
        bind_to_col = get_bind_to_col(col_cfg)
        if col_type == "$faker":
            method = col_cfg.method or ""
            params = col_cfg.params or {}
            resolvers[col_name] = FakerResolver(faker_instance, method, params, bind_to_col)
        elif col_type == "$provider":
            target = col_cfg.target or ""
            resolvers[col_name] = ProviderResolver(registry, target, bind_to_col)
        else:
            raise ValueError(f"Unsupported column type: {col_type}")

    output_path = Path(output_cfg.filepath)
    sink = CsvSink(output_path)

    # Single context instance shared across all rows — bind_cache persists here
    context = GenerationContext(faker=faker_instance, catalogs=catalogs)

    generated_rows: List[Dict[str, Any]] = []
    for _ in range(rows_count):
        row: Dict[str, Any] = {}
        # Resolve columns in DAG order so dependencies are always available in `row`
        for col_name in column_order:
            resolver = resolvers[col_name]
            value = resolver.resolve(context, row)
            row[col_name] = value
        generated_rows.append(row)

    # Write output in original schema column order
    fieldnames = list(columns_cfg.keys())
    sink.write_rows(generated_rows, fieldnames)
