from __future__ import annotations

import re
from typing import Any, Literal
from collections.abc import Mapping

from pydantic import BaseModel, Field, RootModel, ValidationError, field_validator, model_validator

from ..core import (
    COLUMN_GEN_TYPE__FAKER,
    COLUMN_GEN_TYPE__FUNC,
    COLUMN_GEN_TYPE__PROVIDER,
    COLUMN_GEN_TYPE__REL,
)
from ..core import ColumnGenType, RelStrategy

# Matches column reference templates in param string values.
# Supported syntax (template-only for now):
# - {{ col("column_name") }}
# - {{ col('column_name') }}
# Shared with dag.py (for DAG edge extraction) and func_node.py (for runtime resolution).
COL_REF_PATTERN = re.compile(r"\{\{\s*col\(\s*['\"](\w+)['\"]\s*\)\s*\}\}")


def get_col_refs(col_cfg: ColumnConfig) -> list[str]:
    """Return all column names referenced via {{ col(...) }} in this config."""
    refs: list[str] = []
    for v in (col_cfg.params or {}).values():
        if not isinstance(v, str):
            continue
        for m in COL_REF_PATTERN.finditer(v):
            refs.append(m.group(1))

    if col_cfg.type == COLUMN_GEN_TYPE__PROVIDER and col_cfg.lookup is not None:
        key_from = col_cfg.lookup.key_from
        parts = [key_from] if isinstance(key_from, str) else key_from
        for part in parts:
            refs.append(part)

    return refs


class SampleConfig(BaseModel):
    strategy: Literal["sequential", "random", "shuffle"] = "sequential"
    seed: int | None = Field(
        default=None,
        description="Optional RNG seed for random/shuffle sample strategies.",
    )


class LookupConfig(BaseModel):
    key_columns: list[str] = Field(..., min_length=1)
    key_from: str | list[str]
    value_column: str
    on_missing: Literal["null", "error", "default"] = "null"
    default_value: Any | None = None

    @field_validator("key_from", mode="before")
    @classmethod
    def normalize_key_from(cls, v: Any) -> str | list[str]:
        if not isinstance(v, (str, list)):
            raise TypeError("key_from must be a string or list of strings")
        if isinstance(v, list) and not all(isinstance(x, str) for x in v):
            raise TypeError("key_from must be a string or list of strings")
        return v

    @model_validator(mode="after")
    def key_lengths(self) -> LookupConfig:
        kf = self.key_from
        parts = [kf] if isinstance(kf, str) else kf
        if len(self.key_columns) != len(parts):
            raise ValueError(
                "lookup.key_columns and lookup.key_from must have the same length "
                f"({len(self.key_columns)} vs {len(parts)})"
            )
        return self


class ColumnConfig(BaseModel):
    type: ColumnGenType
    method: str | None = None
    target: str | None = None
    func: str | None = None
    params: dict[str, Any] | None = None
    bind_to: str | None = None
    strategy: RelStrategy = "random"
    unique: bool = False
    mode: Literal["sample", "lookup"] = "sample"
    column: str | None = None
    sample: SampleConfig | None = None
    lookup: LookupConfig | None = None

    @model_validator(mode="after")
    def check_required_fields(self) -> ColumnConfig:
        if self.type == COLUMN_GEN_TYPE__FAKER and not self.method:
            raise ValueError("Faker column must define 'method'")
        if self.type == COLUMN_GEN_TYPE__REL:
            if not self.target or "." not in self.target:
                raise ValueError("Rel column must define 'target' as '<table>.<column>'")
        if self.type == COLUMN_GEN_TYPE__FUNC:
            if not self.func or "." not in self.func:
                raise ValueError(
                    "Func column must define 'func' as '<module>.<callable>' "
                    "(e.g. 'test.country_of_origin')"
                )
        if self.type == COLUMN_GEN_TYPE__PROVIDER:
            if not self.target:
                raise ValueError("Provider column must define 'target'")
            if self.mode == "lookup" and not self.lookup:
                raise ValueError("Provider column with mode 'lookup' must define 'lookup'")
            if self.mode == "sample" and self.lookup is not None:
                raise ValueError("Provider column with mode 'sample' must not define 'lookup'")
        return self


class OutputConfig(BaseModel):
    format: Literal["csv", "json"] = "csv"
    filepath: str


class TableSchema(BaseModel):
    rows: int = Field(..., gt=0)
    columns: dict[str, ColumnConfig]
    output: OutputConfig


class SchemaFile(RootModel[dict[str, TableSchema]]):

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

    Beyond Pydantic field validation this also verifies that every column reference
    (e.g. {{ col("name") }}) points to a real column defined in the
    same table.
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
                    f"Column '{col_name}': {{ col('{ref_col}') }} references "
                    f"unknown column '{ref_col}'"
                )

    return schema_model
