"""Tests for :mod:`kuriboh.parsers.schema`.

Covers:
- SampleConfig defaults and validation
- LookupConfig normalisation and cross-field length check
- ColumnConfig per-type required-field enforcement (faker / rel / func / provider)
- ColumnConfig provider sample vs lookup guard
- SchemaFile single-table constraint and property accessors
- validate_schema happy path and $col(...) dangling-reference detection
- get_col_refs extracts references from params and lookup.key_from
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from kuriboh.parsers.schema import (
    ColumnConfig,
    LookupConfig,
    SampleConfig,
    SchemaFile,
    TableSchema,
    get_col_refs,
    validate_schema,
)


# ---------------------------------------------------------------------------
# SampleConfig
# ---------------------------------------------------------------------------

class TestSampleConfig:
    def test_defaults(self):
        cfg = SampleConfig()
        assert cfg.strategy == "sequential"
        assert cfg.seed is None

    def test_explicit_values(self):
        cfg = SampleConfig(strategy="shuffle", seed=42)
        assert cfg.strategy == "shuffle"
        assert cfg.seed == 42

    def test_invalid_strategy_raises(self):
        with pytest.raises(ValidationError):
            SampleConfig(strategy="unknown")


# ---------------------------------------------------------------------------
# LookupConfig
# ---------------------------------------------------------------------------

class TestLookupConfig:
    def _valid(self, **overrides):
        base = dict(
            key_columns=["sku"],
            key_from="$col(sku)",
            value_column="price",
        )
        return LookupConfig(**(base | overrides))

    def test_defaults(self):
        lk = self._valid()
        assert lk.on_missing == "null"
        assert lk.default_value is None

    def test_normalize_key_from_string_stays_string(self):
        lk = self._valid(key_from="$col(sku)")
        assert isinstance(lk.key_from, str)

    def test_normalize_key_from_list_stays_list(self):
        lk = LookupConfig(
            key_columns=["a", "b"],
            key_from=["$col(a)", "$col(b)"],
            value_column="v",
        )
        assert isinstance(lk.key_from, list)
        assert len(lk.key_from) == 2

    def test_mismatched_key_lengths_raises(self):
        with pytest.raises(ValidationError, match="same length"):
            LookupConfig(
                key_columns=["a", "b"],
                key_from="$col(a)",  # length 1 vs 2
                value_column="v",
            )

    def test_invalid_key_from_type_raises(self):
        with pytest.raises((ValidationError, TypeError)):
            LookupConfig(key_columns=["a"], key_from=123, value_column="v")

    def test_on_missing_default_requires_no_default_value(self):
        # default_value can be None for on_missing="default"; callers handle it
        lk = self._valid(on_missing="default", default_value="UNKNOWN")
        assert lk.default_value == "UNKNOWN"

    def test_on_missing_invalid_raises(self):
        with pytest.raises(ValidationError):
            self._valid(on_missing="skip")

    def test_empty_key_columns_raises(self):
        with pytest.raises(ValidationError):
            LookupConfig(key_columns=[], key_from="$col(x)", value_column="v")


# ---------------------------------------------------------------------------
# ColumnConfig — $faker
# ---------------------------------------------------------------------------

class TestColumnConfigFaker:
    def test_valid(self):
        col = ColumnConfig(type="$faker", method="name")
        assert col.method == "name"

    def test_missing_method_raises(self):
        with pytest.raises(ValidationError, match="method"):
            ColumnConfig(type="$faker")


# ---------------------------------------------------------------------------
# ColumnConfig — $rel
# ---------------------------------------------------------------------------

class TestColumnConfigRel:
    def test_valid(self):
        col = ColumnConfig(type="$rel", target="orders.user_id")
        assert col.target == "orders.user_id"

    def test_missing_target_raises(self):
        with pytest.raises(ValidationError, match="target"):
            ColumnConfig(type="$rel")

    def test_target_without_dot_raises(self):
        with pytest.raises(ValidationError, match="target"):
            ColumnConfig(type="$rel", target="users")


# ---------------------------------------------------------------------------
# ColumnConfig — $func
# ---------------------------------------------------------------------------

class TestColumnConfigFunc:
    def test_valid(self):
        col = ColumnConfig(type="$func", func="mymod.my_fn")
        assert col.func == "mymod.my_fn"

    def test_missing_func_raises(self):
        with pytest.raises(ValidationError, match="func"):
            ColumnConfig(type="$func")

    def test_func_without_dot_raises(self):
        with pytest.raises(ValidationError, match="func"):
            ColumnConfig(type="$func", func="my_fn")


# ---------------------------------------------------------------------------
# ColumnConfig — $provider
# ---------------------------------------------------------------------------

class TestColumnConfigProvider:
    def _lookup(self, **overrides):
        base = dict(
            key_columns=["sku"],
            key_from="$col(sku)",
            value_column="price",
        )
        return LookupConfig(**(base | overrides))

    def test_sample_mode_defaults(self):
        col = ColumnConfig(type="$provider", target="MyProvider", column="name")
        assert col.mode == "sample"
        assert col.lookup is None

    def test_missing_target_raises(self):
        with pytest.raises(ValidationError, match="target"):
            ColumnConfig(type="$provider")

    def test_lookup_mode_requires_lookup_block(self):
        with pytest.raises(ValidationError, match="lookup"):
            ColumnConfig(type="$provider", target="MyProvider", mode="lookup")

    def test_sample_mode_must_not_have_lookup_block(self):
        with pytest.raises(ValidationError, match="lookup"):
            ColumnConfig(
                type="$provider",
                target="MyProvider",
                mode="sample",
                lookup=self._lookup(),
            )

    def test_lookup_mode_valid(self):
        col = ColumnConfig(
            type="$provider",
            target="MyProvider",
            mode="lookup",
            lookup=self._lookup(),
        )
        assert col.mode == "lookup"
        assert col.lookup is not None

    def test_sample_with_sample_config(self):
        col = ColumnConfig(
            type="$provider",
            target="MyProvider",
            column="name",
            sample=SampleConfig(strategy="random", seed=7),
        )
        assert col.sample.strategy == "random"
        assert col.sample.seed == 7


# ---------------------------------------------------------------------------
# SchemaFile
# ---------------------------------------------------------------------------

def _minimal_schema_dict(table_name: str = "orders", rows: int = 10):
    return {
        table_name: {
            "rows": rows,
            "columns": {
                "id": {"type": "$faker", "method": "uuid4"},
            },
            "output": {"format": "csv", "filepath": "./outputs/out.csv"},
        }
    }


class TestSchemaFile:
    def test_table_name_property(self):
        sf = SchemaFile.model_validate(_minimal_schema_dict("orders"))
        assert sf.table_name == "orders"

    def test_table_property_returns_table_schema(self):
        sf = SchemaFile.model_validate(_minimal_schema_dict("orders"))
        assert isinstance(sf.table, TableSchema)

    def test_rows_must_be_positive(self):
        with pytest.raises(ValidationError):
            SchemaFile.model_validate(_minimal_schema_dict(rows=0))

    def test_multiple_tables_raises_on_table_name(self):
        data = {
            **_minimal_schema_dict("orders"),
            **_minimal_schema_dict("users"),
        }
        sf = SchemaFile.model_validate(data)
        with pytest.raises(ValueError, match="exactly one"):
            _ = sf.table_name

    def test_invalid_output_format_raises(self):
        d = _minimal_schema_dict()
        d["orders"]["output"]["format"] = "parquet"
        with pytest.raises(ValidationError):
            SchemaFile.model_validate(d)


# ---------------------------------------------------------------------------
# validate_schema
# ---------------------------------------------------------------------------

class TestValidateSchema:
    def test_happy_path_returns_schema_file(self):
        result = validate_schema(_minimal_schema_dict("users"))
        assert result.table_name == "users"

    def test_dangling_col_ref_in_params_raises(self):
        schema = {
            "orders": {
                "rows": 5,
                "columns": {
                    "name": {
                        "type": "$func",
                        "func": "mymod.fn",
                        "params": {"prefix": "$col(missing_col)"},
                    },
                },
                "output": {"format": "csv", "filepath": "./out.csv"},
            }
        }
        with pytest.raises(ValueError, match="missing_col"):
            validate_schema(schema)

    def test_dangling_col_ref_in_lookup_key_from_raises(self):
        schema = {
            "orders": {
                "rows": 5,
                "columns": {
                    "price": {
                        "type": "$provider",
                        "target": "PriceProvider",
                        "mode": "lookup",
                        "lookup": {
                            "key_columns": ["sku"],
                            "key_from": "$col(nonexistent)",
                            "value_column": "price",
                        },
                    },
                },
                "output": {"format": "csv", "filepath": "./out.csv"},
            }
        }
        with pytest.raises(ValueError, match="nonexistent"):
            validate_schema(schema)

    def test_col_ref_pointing_to_existing_column_passes(self):
        schema = {
            "orders": {
                "rows": 5,
                "columns": {
                    "sku": {"type": "$faker", "method": "uuid4"},
                    "price": {
                        "type": "$provider",
                        "target": "PriceProvider",
                        "mode": "lookup",
                        "lookup": {
                            "key_columns": ["sku"],
                            "key_from": "$col(sku)",
                            "value_column": "price",
                        },
                    },
                },
                "output": {"format": "csv", "filepath": "./out.csv"},
            }
        }
        result = validate_schema(schema)
        assert result.table_name == "orders"

    def test_invalid_schema_wraps_validation_error(self):
        with pytest.raises(ValueError):
            validate_schema({"orders": {"rows": -1, "columns": {}, "output": {}}})


# ---------------------------------------------------------------------------
# get_col_refs
# ---------------------------------------------------------------------------

class TestGetColRefs:
    def test_no_refs_returns_empty(self):
        col = ColumnConfig(type="$faker", method="name")
        assert get_col_refs(col) == []

    def test_params_single_ref(self):
        col = ColumnConfig(
            type="$func",
            func="mymod.fn",
            params={"x": "$col(user_id)"},
        )
        assert get_col_refs(col) == ["user_id"]

    def test_params_multiple_refs_in_same_value(self):
        col = ColumnConfig(
            type="$func",
            func="mymod.fn",
            params={"x": "$col(a) $col(b)"},
        )
        assert get_col_refs(col) == ["a", "b"]

    def test_params_non_string_values_ignored(self):
        col = ColumnConfig(
            type="$func",
            func="mymod.fn",
            params={"x": 42, "y": True},
        )
        assert get_col_refs(col) == []

    def test_lookup_key_from_string_ref(self):
        col = ColumnConfig(
            type="$provider",
            target="P",
            mode="lookup",
            lookup=LookupConfig(
                key_columns=["sku"],
                key_from="$col(sku)",
                value_column="price",
            ),
        )
        assert "sku" in get_col_refs(col)

    def test_lookup_key_from_list_refs(self):
        col = ColumnConfig(
            type="$provider",
            target="P",
            mode="lookup",
            lookup=LookupConfig(
                key_columns=["a", "b"],
                key_from=["$col(a)", "$col(b)"],
                value_column="v",
            ),
        )
        refs = get_col_refs(col)
        assert "a" in refs
        assert "b" in refs
