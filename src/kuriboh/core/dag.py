from __future__ import annotations

from typing import Dict, List

from ..parsers.validator import ColumnConfig


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
