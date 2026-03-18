from __future__ import annotations

import re
from typing import Any, Dict, List, Literal, Mapping

from pydantic import BaseModel, Field, RootModel, ValidationError, model_validator

from ..core import (
    COLUMN_GEN_TYPE__FAKER,
    COLUMN_GEN_TYPE__FUNC,
    COLUMN_GEN_TYPE__PROVIDER,
    COLUMN_GEN_TYPE__REL,
)
from ..core import ColumnGenType, RelStrategy

# Matches $col(column_name) in param string values.
# Shared with dag.py (for DAG edge extraction) and func_node.py (for runtime resolution).
COL_REF_PATTERN = re.compile(r"\$col\((\w+)\)")


def get_col_refs(col_cfg: "ColumnConfig") -> List[str]:
    """Return all column names referenced via $col(...) in this column's params."""
    return [
        m
        for v in (col_cfg.params or {}).values()
        if isinstance(v, str)
        for m in COL_REF_PATTERN.findall(v)
    ]


class ColumnConfig(BaseModel):
    type: ColumnGenType
    method: str | None = None
    target: str | None = None
    func: str | None = None
    params: Dict[str, Any] | None = None
    bind_to: str | None = None
    strategy: RelStrategy = "random"
    unique: bool = False

    @model_validator(mode="after")
    def check_required_fields(self) -> "ColumnConfig":
        if self.type == COLUMN_GEN_TYPE__FAKER and not self.method:
            raise ValueError("Faker column must define 'method'")
        if self.type == COLUMN_GEN_TYPE__PROVIDER and not self.target:
            raise ValueError("Provider column must define 'target'")
        if self.type == COLUMN_GEN_TYPE__REL:
            if not self.target or "." not in self.target:
                raise ValueError("Rel column must define 'target' as '<table>.<column>'")
        if self.type == COLUMN_GEN_TYPE__FUNC:
            if not self.func or "." not in self.func:
                raise ValueError(
                    "Func column must define 'func' as '<module>.<callable>' "
                    "(e.g. 'test.country_of_origin')"
                )
        return self


class OutputConfig(BaseModel):
    format: Literal["csv", "json"] = "csv"
    filepath: str


class TableSchema(BaseModel):
    rows: int = Field(..., gt=0)
    columns: Dict[str, ColumnConfig]
    output: OutputConfig


class SchemaFile(RootModel[Dict[str, TableSchema]]):

    @property
    def table_name(self) -> str:
        # For now we expect exactly one table per schema file
        if len(self.root) != 1:
            raise ValueError("Schema file must define exactly one top-level table for now")
        return next(iter(self.root.keys()))

    @property
    def table(self) -> TableSchema:
        return self.root[self.table_name]


def validate_schema(schema: Mapping[str, Any]) -> SchemaFile:
    """
    Validate a raw YAML-loaded schema and return a typed model.

    Beyond Pydantic field validation this also verifies that every $col(name)
    reference points to a real column defined in the same table.
    """
    try:
        schema_model = SchemaFile.model_validate(schema)
    except ValidationError as e:
        raise ValueError(str(e)) from e

    columns = schema_model.table.columns
    col_names = set(columns.keys())

    for col_name, col_cfg in columns.items():
        for ref_col in get_col_refs(col_cfg):
            if ref_col not in col_names:
                raise ValueError(
                    f"Column '{col_name}': $col('{ref_col}') references "
                    f"unknown column '{ref_col}'"
                )

    return schema_model
