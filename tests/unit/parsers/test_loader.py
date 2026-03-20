from __future__ import annotations

import pytest
from pathlib import Path

from kuriboh.parsers.loader import load_schema, load_providers, load_catalogs


def test_load_case_simple_schema_product(fixtures_root):
    schema_path = Path(fixtures_root) / "schemas" / "test_case_simple" / "product.yml"
    schema = load_schema(schema_path)
    assert isinstance(schema, dict)
    assert "product" in schema.keys()
    assert list(schema["product"].keys()) == ["rows", "columns", "output"]


def test_load_providers(fixtures_root):
    providers_dict = load_providers(fixtures_root)
    provider_keys = providers_dict.keys()
    assert(len(provider_keys) == 2)
    assert "SleepingQuarterProvider" in provider_keys
    assert "StorageWardrobeProvider" in provider_keys


def test_load_catalogs_empty_when_no_catalogs_dir(tmp_path):
    assert load_catalogs(tmp_path) == {}


def test_load_catalogs_recursively_loads_yaml_and_yml_by_stem(tmp_path):
    catalogs_dir = tmp_path / "catalogs"
    (catalogs_dir / "common").mkdir(parents=True)
    (catalogs_dir / "furnitures" / "nested").mkdir(parents=True)

    # Ensure both extensions are discovered.
    (catalogs_dir / "common" / "material.yaml").write_text("material: wood\n", encoding="utf-8")
    (catalogs_dir / "furnitures" / "bedroom.yml").write_text("bedroom: ok\n", encoding="utf-8")
    (catalogs_dir / "furnitures" / "nested" / "adjective.yml").write_text(
        "adjective: cool\n", encoding="utf-8"
    )

    catalogs = load_catalogs(tmp_path)

    assert {"material", "bedroom", "adjective"} == set(catalogs.keys())
    assert isinstance(catalogs["material"], dict)
    assert isinstance(catalogs["bedroom"], dict)
    assert isinstance(catalogs["adjective"], dict)
    assert catalogs["material"]["material"] == "wood"
    assert catalogs["bedroom"]["bedroom"] == "ok"
    assert catalogs["adjective"]["adjective"] == "cool"


def test_load_catalogs_duplicate_basename_raises_value_error(tmp_path):
    catalogs_dir = tmp_path / "catalogs"
    (catalogs_dir / "a").mkdir(parents=True)
    (catalogs_dir / "b").mkdir(parents=True)

    # Same stem ("dup") but in different folders should be rejected.
    (catalogs_dir / "a" / "dup.yaml").write_text("x: 1\n", encoding="utf-8")
    (catalogs_dir / "b" / "dup.yml").write_text("x: 2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate catalog basename 'dup'"):
        load_catalogs(tmp_path)


def test_load_catalogs_fixtures_contains_expected_catalogs(loaded_catalogs):
    expected_keys = {"bedroom", "kitchen", "living_room", "adjective", "material", "color"}
    assert expected_keys.issubset(loaded_catalogs.keys())
    for key in expected_keys:
        assert isinstance(loaded_catalogs[key], dict)
