from __future__ import annotations

from ..parsers.schema import ColumnConfig, SchemaFile, get_col_refs
from .constants import COLUMN_GEN_TYPE__REL


def _collect_deps(
    col_name: str,
    col_cfg: ColumnConfig,
    columns_cfg: dict[str, ColumnConfig],
) -> set[str]:
    """
    Collect all declared dependencies for a column (bind_to + column reference refs),
    deduplicated to avoid double-counting the same edge.

    Uses the full columns_cfg dict for O(1) membership checks.
    """
    deps: set[str] = set()

    if col_cfg.bind_to:
        if col_cfg.bind_to not in columns_cfg:
            raise ValueError(
                f"Column '{col_name}' has bind_to '{col_cfg.bind_to}' "
                f"but '{col_cfg.bind_to}' is not defined in this table"
            )
        deps.add(col_cfg.bind_to)

    for ref_col in get_col_refs(col_cfg):
        if ref_col not in columns_cfg:
            raise ValueError(
                f"Column '{col_name}' references {{ col('{ref_col}') }} "
                f"but '{ref_col}' is not defined in this table"
            )
        deps.add(ref_col)

    return deps


def build_dag(columns_cfg: dict[str, ColumnConfig]) -> list[str]:
    """
    Build a column-level dependency graph from bind_to and column-reference declarations
    and return a topologically sorted list of column names (Kahn's algorithm).

    Both bind_to and col() references in params create a "must come before" edge.
    Raises ValueError if a referenced column does not exist or if circular
    dependencies are detected.
    """
    all_cols = list(columns_cfg.keys())

    adjacency: dict[str, list[str]] = {col: [] for col in all_cols}
    in_degree: dict[str, int] = dict.fromkeys(all_cols, 0)

    for col_name, col_cfg in columns_cfg.items():
        for dep_col in _collect_deps(col_name, col_cfg, columns_cfg):
            adjacency[dep_col].append(col_name)
            in_degree[col_name] += 1

    queue: list[str] = [col for col in all_cols if in_degree[col] == 0]
    order: list[str] = []

    while queue:
        col = queue.pop(0)
        order.append(col)
        for dependent in adjacency[col]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(order) != len(all_cols):
        cycle_cols = [c for c in all_cols if c not in order]
        raise ValueError(f"Circular dependency detected among columns: {cycle_cols}")

    return order


def build_table_dag(schemas: dict[str, SchemaFile]) -> list[str]:
    """
    Build a table-level dependency graph from $rel targets and return
    table names in generation order (Kahn's algorithm).

    If table B has a column with $rel target "A.id", then A must be
    generated before B. Raises ValueError on unknown table references
    or circular dependencies.
    """
    all_tables = list(schemas.keys())
    adjacency: dict[str, list[str]] = {t: [] for t in all_tables}
    in_degree: dict[str, int] = dict.fromkeys(all_tables, 0)

    for table_name, schema_file in schemas.items():
        for col_cfg in schema_file.table.columns.values():
            if col_cfg.type != COLUMN_GEN_TYPE__REL or not col_cfg.target:
                continue
            ref_table = col_cfg.target.split(".", 1)[0]
            if ref_table not in schemas:
                raise ValueError(
                    f"Table '{table_name}' has $rel target '{col_cfg.target}' "
                    f"but table '{ref_table}' is not in the domain"
                )
            if ref_table == table_name:
                continue
            adjacency[ref_table].append(table_name)
            in_degree[table_name] += 1

    queue: list[str] = [t for t in all_tables if in_degree[t] == 0]
    order: list[str] = []

    while queue:
        t = queue.pop(0)
        order.append(t)
        for dependent in adjacency[t]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(order) != len(all_tables):
        cycle_tables = [t for t in all_tables if t not in order]
        raise ValueError(f"Circular dependency detected among tables: {cycle_tables}")

    return order
