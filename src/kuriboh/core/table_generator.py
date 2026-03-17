from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from ..parsers.loader import load_providers, load_schema
from ..parsers.validator import validate_schema
from ..providers.registry import build_registry
from ..resolvers.base import BaseResolver
from ..sinks.base import BaseSink
from ..sinks.factory import create_sink
from .context import GenerationContext
from .dag import build_dag
from .resolver_builder import build_resolvers, compute_effective_unique


@dataclass
class TablePlan:
    """
    Immutable description of everything needed to generate one table.

    Produced by TableGenerator.plan() and consumed by TableGenerator.execute().
    Holding it as a separate object lets callers inspect (or dry-run) the plan
    before any data is written.
    """

    table_name: str
    rows_count: int
    column_order: List[str]
    resolvers: Dict[str, BaseResolver]
    fieldnames: List[str]
    sink: BaseSink


class TableGenerator:
    """
    Orchestrates single-table generation in two explicit phases:

    1. plan()   — load schema, build DAG + resolvers, apply guards.
                  Pure setup: raises early on any config error, writes nothing.
    2. execute() — run the generation loop and flush rows to the sink.
    """

    def __init__(
        self,
        schema_path: Path,
        base_dir: Path,
        context: GenerationContext,
    ) -> None:
        self._schema_path = schema_path
        self._base_dir = base_dir
        self._context = context

    def plan(self) -> TablePlan:
        """
        Load the schema, build the column DAG, construct all resolvers,
        apply the cardinality guard, and pre-initialise unique-value pools.

        No rows are generated here — all failures surface before any I/O.
        """
        raw_schema = load_schema(self._schema_path)
        schema_model = validate_schema(raw_schema)

        table_name = schema_model.table_name
        table_cfg = schema_model.table
        columns_cfg = table_cfg.columns

        providers_cfg = load_providers(self._base_dir)
        registry = build_registry(self._base_dir, providers_cfg)

        column_order = build_dag(columns_cfg)
        effective_unique = compute_effective_unique(columns_cfg)
        resolvers = build_resolvers(
            table_name,
            columns_cfg,
            effective_unique,
            self._context.faker,
            registry,
        )

        rows_count = self._apply_cardinality_guard(table_name, int(table_cfg.rows), resolvers)

        for resolver in resolvers.values():
            resolver.pre_init_pool(self._context)

        return TablePlan(
            table_name=table_name,
            rows_count=rows_count,
            column_order=column_order,
            resolvers=resolvers,
            fieldnames=list(columns_cfg.keys()),
            sink=create_sink(table_cfg.output),
        )

    def execute(self, plan: TablePlan) -> List[Dict[str, Any]]:
        """
        Run the generation loop and write all rows to the configured sink.

        The generated rows are also stored in context.generated_tables so
        subsequent tables can reference them via $rel columns.
        """
        generated_rows: List[Dict[str, Any]] = []

        for _ in range(plan.rows_count):
            row: Dict[str, Any] = {}
            for col_name in plan.column_order:
                row[col_name] = plan.resolvers[col_name].resolve(self._context, row)
            generated_rows.append(row)

        self._context.generated_tables[plan.table_name] = generated_rows
        plan.sink.write_rows(generated_rows, plan.fieldnames)

        return generated_rows

    def _apply_cardinality_guard(
        self,
        table_name: str,
        rows_count: int,
        resolvers: Dict[str, BaseResolver],
    ) -> int:
        """
        Cap rows_count to the smallest cardinality among all unique columns.
        Emits a warning when the schema-requested count is reduced.
        """
        min_cardinality: int | None = None

        for resolver in resolvers.values():
            if not resolver._unique:
                continue
            c = resolver.cardinality(self._context.catalogs)
            if c is not None and (min_cardinality is None or c < min_cardinality):
                min_cardinality = c

        if min_cardinality is not None and rows_count > min_cardinality:
            print(
                f"[kuriboh] Warning: '{table_name}' requests {rows_count} rows but "
                f"unique column(s) can only produce {min_cardinality} unique values. "
                f"Reducing rows to {min_cardinality}."
            )
            return min_cardinality

        return rows_count
