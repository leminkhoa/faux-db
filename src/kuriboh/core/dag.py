from __future__ import annotations

from typing import Dict, List

from ..parsers.validator import ColumnConfig, SchemaFile


def get_bind_to_col(col_cfg: ColumnConfig) -> str | None:
    """Return the column name this column is bound to, or None."""
    return col_cfg.bind_to or None


def build_dag(columns_cfg: Dict[str, ColumnConfig]) -> List[str]:
    """
    Build a column-level dependency graph from bind_to declarations and
    return a topologically sorted list of column names (Kahn's algorithm).

    bind_to: name  means column depends on the column named 'name',
    which must be resolved first. Raises ValueError if the referenced
    column does not exist or if circular dependencies are detected.
    """
    all_cols = list(columns_cfg.keys())

    # adjacency[col] = list of columns that depend on col
    adjacency: Dict[str, List[str]] = {col: [] for col in all_cols}
    in_degree: Dict[str, int] = {col: 0 for col in all_cols}

    for col_name, col_cfg in columns_cfg.items():
        dep_col = get_bind_to_col(col_cfg)
        if dep_col is None:
            continue
        if dep_col not in columns_cfg:
            raise ValueError(
                f"Column '{col_name}' has bind_to '{col_cfg.bind_to}' "
                f"but '{dep_col}' is not defined in this table"
            )
        adjacency[dep_col].append(col_name)
        in_degree[col_name] += 1

    # Kahn's algorithm — start from all nodes with no dependencies
    queue: List[str] = [col for col in all_cols if in_degree[col] == 0]
    order: List[str] = []

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


def build_table_dag(schemas: Dict[str, SchemaFile]) -> List[str]:
    """
    Build a table-level dependency graph from $rel targets and return
    table names in generation order (Kahn's algorithm).

    If table B has a column with $rel target "A.id", then A must be
    generated before B. Raises ValueError on unknown table references
    or circular dependencies.
    """
    all_tables = list(schemas.keys())
    adjacency: Dict[str, List[str]] = {t: [] for t in all_tables}
    in_degree: Dict[str, int] = {t: 0 for t in all_tables}

    for table_name, schema_file in schemas.items():
        for col_cfg in schema_file.table.columns.values():
            if col_cfg.type != "$rel" or not col_cfg.target:
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

    queue: List[str] = [t for t in all_tables if in_degree[t] == 0]
    order: List[str] = []

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
