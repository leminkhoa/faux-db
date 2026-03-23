from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from faker import Faker

from ..parsers.loader import load_catalogs, load_schema
from ..parsers.schema import SchemaFile, validate_schema
from .context import GenerationContext
from .dag import build_table_dag
from .table_generator import TableGenerator


def run_generation(
    schema_path: Path,
    context: GenerationContext | None = None,
    base_dir: Path | None = None,
) -> None:
    resolved_base = base_dir or schema_path.parent.parent

    if context is None:
        catalogs = load_catalogs(resolved_base)
        context = GenerationContext(faker=Faker(), catalogs=catalogs)

    gen = TableGenerator(schema_path, resolved_base, context)
    plan = gen.plan()
    gen.execute(plan)


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
