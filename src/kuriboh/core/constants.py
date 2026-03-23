from __future__ import annotations

from typing import Literal, TypeAlias

# Centralized filesystem conventions (relative to a "base_dir")
PROVIDERS_DIRNAME = "providers"
CATALOGS_DIRNAME = "catalogs"
SCHEMAS_DIRNAME = "schemas"
SEEDS_DIRNAME = "seeds"
OUTPUTS_DIRNAME = "outputs"
FUNCTIONS_DIRNAME = "functions"

# Column generation type tokens
COLUMN_GEN_TYPE__FAKER = "$faker"
COLUMN_GEN_TYPE__PROVIDER = "$provider"
COLUMN_GEN_TYPE__REL = "$rel"
COLUMN_GEN_TYPE__FUNC = "$func"

ColumnGenType: TypeAlias = Literal[
    COLUMN_GEN_TYPE__FAKER,
    COLUMN_GEN_TYPE__PROVIDER,
    COLUMN_GEN_TYPE__REL,
    COLUMN_GEN_TYPE__FUNC,
]

RelStrategy: TypeAlias = Literal["random", "sequential"]
