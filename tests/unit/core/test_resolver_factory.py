from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest
from faker import Faker

from kuriboh.core import (
    COLUMN_GEN_TYPE__FAKER,
    COLUMN_GEN_TYPE__FUNC,
    COLUMN_GEN_TYPE__PROVIDER,
    COLUMN_GEN_TYPE__REL,
)
from kuriboh.core.resolver_factory import (
    _resolve_func_path,
    build_resolvers,
    compute_effective_unique,
    validate_provider_columns_for_plan,
)
from kuriboh.parsers.schema import ColumnConfig
from kuriboh.providers.file_reader import FileReaderProvider
from kuriboh.providers.random_choice import RandomChoiceProvider
from kuriboh.providers.registry import ProviderRegistry
def _registry(**providers) -> ProviderRegistry:
    reg = ProviderRegistry()
    for name, provider in providers.items():
        reg.register(name, provider)
    return reg


def _file_reader_provider() -> FileReaderProvider:
    return FileReaderProvider(
        pl.DataFrame({"id": ["1"], "name": ["Alice"], "value": ["10"]}),
        loaded_columns=["id", "name", "value"],
    )


def test_validate_file_reader_sample_column_must_be_loaded():
    reg = _registry(P=_file_reader_provider())
    columns = {
        "x": ColumnConfig(type="$provider", target="P", mode="sample", column="missing"),
    }

    with pytest.raises(ValueError, match="sample column 'missing'"):
        validate_provider_columns_for_plan(reg, columns)


def test_validate_file_reader_lookup_key_column_must_be_loaded():
    reg = _registry(P=_file_reader_provider())
    columns = {
        "x": ColumnConfig(
            type="$provider",
            target="P",
            mode="lookup",
            lookup={
                "key_columns": ["missing_key"],
                "key_from": "$col(id)",
                "value_column": "value",
            },
        )
    }

    with pytest.raises(ValueError, match="lookup key column 'missing_key'"):
        validate_provider_columns_for_plan(reg, columns)


def test_validate_file_reader_lookup_value_column_must_be_loaded():
    reg = _registry(P=_file_reader_provider())
    columns = {
        "x": ColumnConfig(
            type="$provider",
            target="P",
            mode="lookup",
            lookup={
                "key_columns": ["id"],
                "key_from": "$col(id)",
                "value_column": "missing_value",
            },
        )
    }

    with pytest.raises(ValueError, match="lookup value_column 'missing_value'"):
        validate_provider_columns_for_plan(reg, columns)


def test_validate_non_file_provider_rejects_column_option():
    reg = _registry(P=RandomChoiceProvider(["a"]))
    columns = {
        "x": ColumnConfig(type="$provider", target="P", mode="sample", column="name"),
    }

    with pytest.raises(ValueError, match="'column' is only valid"):
        validate_provider_columns_for_plan(reg, columns)


def test_validate_non_file_provider_rejects_sample_option():
    reg = _registry(P=RandomChoiceProvider(["a"]))
    columns = {
        "x": ColumnConfig(
            type="$provider",
            target="P",
            mode="sample",
            sample={"strategy": "random", "seed": 1},
        ),
    }

    with pytest.raises(ValueError, match="'sample' is only valid"):
        validate_provider_columns_for_plan(reg, columns)


def test_resolve_func_path_adds_default_prefix():
    assert _resolve_func_path("test.country_of_origin") == "functions.test.country_of_origin"


def test_resolve_func_path_keeps_existing_prefix():
    assert _resolve_func_path("functions.test.country_of_origin") == "functions.test.country_of_origin"


def test_compute_effective_unique_inherits_from_bound_unique_column():
    columns = {
        "id": ColumnConfig(type="$faker", method="uuid4", unique=True),
        "name": ColumnConfig(type="$faker", method="name", bind_to="id"),
        "note": ColumnConfig(type="$faker", method="word"),
    }

    effective = compute_effective_unique(columns)

    assert effective == {"id": True, "name": True, "note": False}


def test_build_resolvers_constructs_all_supported_resolver_types(monkeypatch):
    registry = _registry(P=RandomChoiceProvider(["x", "y"]))
    columns = {
        "id": ColumnConfig(type="$faker", method="uuid4", unique=True),
        "country": ColumnConfig(type="$func", func="test.country_of_origin"),
        "nickname": ColumnConfig(type="$provider", target="P"),
        "ref_id": ColumnConfig(type="$rel", target="users.id", strategy="sequential"),
    }
    effective_unique = compute_effective_unique(columns)
    constructed: dict[str, tuple[tuple, dict]] = {}

    monkeypatch.setattr(
        "kuriboh.core.resolver_factory.FakerResolver",
        lambda *args, **kwargs: constructed.setdefault("id", (args, kwargs)),
    )
    monkeypatch.setattr(
        "kuriboh.core.resolver_factory.FuncResolver",
        lambda *args, **kwargs: constructed.setdefault("country", (args, kwargs)),
    )
    monkeypatch.setattr(
        "kuriboh.core.resolver_factory.ProviderResolver",
        lambda *args, **kwargs: constructed.setdefault("nickname", (args, kwargs)),
    )
    monkeypatch.setattr(
        "kuriboh.core.resolver_factory.RelResolver",
        lambda *args, **kwargs: constructed.setdefault("ref_id", (args, kwargs)),
    )

    resolvers = build_resolvers("users", columns, effective_unique, Faker(), registry)

    assert resolvers["id"] == constructed["id"]
    assert resolvers["country"] == constructed["country"]
    assert resolvers["nickname"] == constructed["nickname"]
    assert resolvers["ref_id"] == constructed["ref_id"]
    assert constructed["country"][0][0] == "functions.test.country_of_origin"
    assert constructed["ref_id"][0] == ("users", "id", "sequential")


def test_build_resolvers_assigns_pk_cache_key_for_effectively_unique_columns():
    registry = _registry(P=RandomChoiceProvider(["x"]))
    columns = {
        "id": ColumnConfig(type="$faker", method="uuid4", unique=True),
        "nickname": ColumnConfig(type="$provider", target="P", bind_to="id"),
    }

    resolvers = build_resolvers(
        "users",
        columns,
        compute_effective_unique(columns),
        Faker(),
        registry,
    )

    assert resolvers["id"]._pk_cache_key == "users.id"
    assert resolvers["nickname"]._pk_cache_key == "users.nickname"


def test_build_resolvers_rejects_unsupported_column_type():
    registry = _registry()
    bogus = ColumnConfig.model_construct(type="$bogus")

    with pytest.raises(ValueError, match="Unsupported column type"):
        build_resolvers("users", {"x": bogus}, {"x": False}, Faker(), registry)
