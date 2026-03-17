from __future__ import annotations

from typing import Any, Dict, Literal, Mapping

from pydantic import BaseModel, Field, RootModel, ValidationError, model_validator

from ..core import COLUMN_GEN_TYPE__FAKER, COLUMN_GEN_TYPE__PROVIDER, COLUMN_GEN_TYPE__REL
from ..core import ColumnGenType, RelStrategy


class ColumnConfig(BaseModel):
    type: ColumnGenType
    method: str | None = None
    target: str | None = None
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
    Validate a raw YAML-loaded schema using Pydantic and return a typed model.
    """
    try:
        return SchemaFile.model_validate(schema)
    except ValidationError as e:
        # Re-raise as ValueError to keep the surface area small for callers for now.
        raise ValueError(str(e)) from e