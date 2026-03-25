from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from faker import Faker

from ..parsers.loader import load_catalogs, load_providers, load_schema
from ..parsers.schema import SchemaFile, validate_schema
from ..providers.registry import build_registry
from .constants import SCHEMAS_DIRNAME
from .context import GenerationContext
from .dag import build_table_dag
from .table_generator import TableGenerator

_SCHEMA_SUFFIXES = (".yml", ".yaml")


@dataclass(frozen=True)
class ValidationSummary:
    base_dir: Path
    schema_count: int
    domain_count: int
    provider_count: int
    catalog_count: int


def _infer_base_dir(path: Path) -> Path:
    resolved = path.resolve()
    for parent in (resolved, *resolved.parents):
        if parent.name == SCHEMAS_DIRNAME:
            return parent.parent
    return resolved.parent.parent if resolved.is_file() else resolved.parent


def _list_schema_files(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix in _SCHEMA_SUFFIXES
    )


def discover_schema_files(base_dir: Path) -> list[Path]:
    schemas_root = base_dir / SCHEMAS_DIRNAME
    if not schemas_root.exists():
        return []

    return sorted(
        path
        for path in schemas_root.rglob("*")
        if path.is_file() and path.suffix in _SCHEMA_SUFFIXES
    )


def validate_schema_file(
    schema_path: Path,
    *,
    base_dir: Path | None = None,
    context: GenerationContext | None = None,
) -> None:
    resolved_base = (base_dir or _infer_base_dir(schema_path)).resolve()
    resolved_schema_path = schema_path.resolve()
    validation_context = context or GenerationContext(
        faker=Faker(),
        catalogs=load_catalogs(resolved_base),
    )
    TableGenerator(resolved_schema_path, resolved_base, validation_context).plan()


def validate_domain(
    domain_path: Path,
    *,
    base_dir: Path | None = None,
    context: GenerationContext | None = None,
) -> list[Path]:
    resolved_domain_path = domain_path.resolve()
    resolved_base = (base_dir or _infer_base_dir(resolved_domain_path)).resolve()
    schema_files = _list_schema_files(resolved_domain_path)

    if not schema_files:
        raise ValueError(f"No schema files found in {resolved_domain_path}")

    validation_context = context or GenerationContext(
        faker=Faker(),
        catalogs=load_catalogs(resolved_base),
    )

    schemas: dict[str, SchemaFile] = {}
    for schema_file in schema_files:
        raw_schema = load_schema(schema_file)
        schema_model = validate_schema(raw_schema)
        table_name = schema_model.table_name
        if table_name in schemas:
            raise ValueError(
                f"Duplicate table name '{table_name}' in domain (e.g. {schema_file.name})"
            )
        schemas[table_name] = schema_model

    build_table_dag(schemas)

    for schema_file in schema_files:
        validate_schema_file(
            schema_file,
            base_dir=resolved_base,
            context=validation_context,
        )

    return schema_files


def validate_project(base_dir: Path) -> ValidationSummary:
    resolved_base = base_dir.resolve()
    catalogs = load_catalogs(resolved_base)
    providers_cfg = load_providers(resolved_base)
    build_registry(resolved_base, providers_cfg)

    schema_files = discover_schema_files(resolved_base)
    validation_context = GenerationContext(faker=Faker(), catalogs=catalogs)

    domain_paths = sorted({schema_file.parent for schema_file in schema_files})
    for domain_path in domain_paths:
        validate_domain(domain_path, base_dir=resolved_base, context=validation_context)

    return ValidationSummary(
        base_dir=resolved_base,
        schema_count=len(schema_files),
        domain_count=len(domain_paths),
        provider_count=len(providers_cfg),
        catalog_count=len(catalogs),
    )
