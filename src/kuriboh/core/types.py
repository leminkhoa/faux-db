from __future__ import annotations

from typing import Literal, TypeAlias

COLUMN_GEN_TYPE__FAKER = "$faker"
COLUMN_GEN_TYPE__PROVIDER = "$provider"
COLUMN_GEN_TYPE__REL = "$rel"

ColumnGenType: TypeAlias = Literal[
    COLUMN_GEN_TYPE__FAKER,
    COLUMN_GEN_TYPE__PROVIDER,
    COLUMN_GEN_TYPE__REL,
]

RelStrategy: TypeAlias = Literal["random", "sequential"]