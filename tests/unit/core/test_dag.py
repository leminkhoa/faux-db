from __future__ import annotations

import pytest

from kuriboh.core.dag import build_dag, build_table_dag
from kuriboh.parsers.schema import ColumnConfig, SchemaFile


def _schema(table_name: str, columns: dict[str, dict]) -> SchemaFile:
    return SchemaFile.model_validate(
        {
            table_name: {
                "rows": 1,
                "columns": columns,
                "output": {"format": "csv", "filepath": "./out.csv"},
            }
        }
    )


def test_build_dag_orders_bind_to_and_col_refs_before_dependents():
    columns = {
        "id": ColumnConfig(type="faker", method="uuid4"),
        "full_name": ColumnConfig(type="func", func="mod.fn", params={"id": '{{ col("id") }}'}),
        "label": ColumnConfig(type="faker", method="name", bind_to="id"),
    }

    order = build_dag(columns)

    assert order.index("id") < order.index("full_name")
    assert order.index("id") < order.index("label")


def test_build_dag_deduplicates_same_dependency_from_bind_to_and_col_ref():
    columns = {
        "id": ColumnConfig(type="faker", method="uuid4"),
        "name": ColumnConfig(
            type="func",
            func="mod.fn",
            bind_to="id",
            params={"source": '{{ col("id") }}'},
        ),
    }

    assert build_dag(columns) == ["id", "name"]


def test_build_dag_rejects_missing_bind_to_column():
    columns = {
        "name": ColumnConfig(type="faker", method="name", bind_to="missing"),
    }

    with pytest.raises(ValueError, match="bind_to 'missing'"):
        build_dag(columns)


def test_build_dag_rejects_missing_col_ref_column():
    columns = {
        "name": ColumnConfig(type="func", func="mod.fn", params={"x": '{{ col("missing") }}'}),
    }

    with pytest.raises(ValueError, match="col\\('missing'\\)"):
        build_dag(columns)


def test_build_dag_detects_cycle():
    columns = {
        "a": ColumnConfig(type="func", func="mod.fn", params={"x": '{{ col("b") }}'}),
        "b": ColumnConfig(type="func", func="mod.fn", params={"x": '{{ col("a") }}'}),
    }

    with pytest.raises(ValueError, match="Circular dependency"):
        build_dag(columns)


def test_build_table_dag_orders_rel_dependencies():
    schemas = {
        "users": _schema("users", {"id": {"type": "faker", "method": "uuid4"}}),
        "orders": _schema("orders", {"user_id": {"type": "rel", "target": "users.id"}}),
    }

    assert build_table_dag(schemas) == ["users", "orders"]


def test_build_table_dag_rejects_unknown_rel_table():
    schemas = {
        "orders": _schema("orders", {"user_id": {"type": "rel", "target": "users.id"}}),
    }

    with pytest.raises(ValueError, match="not in the domain"):
        build_table_dag(schemas)


def test_build_table_dag_ignores_self_reference():
    schemas = {
        "users": _schema("users", {"manager_id": {"type": "rel", "target": "users.id"}}),
    }

    assert build_table_dag(schemas) == ["users"]


def test_build_table_dag_detects_table_cycle():
    schemas = {
        "users": _schema("users", {"order_id": {"type": "rel", "target": "orders.id"}}),
        "orders": _schema("orders", {"user_id": {"type": "rel", "target": "users.id"}}),
    }

    with pytest.raises(ValueError, match="Circular dependency"):
        build_table_dag(schemas)
