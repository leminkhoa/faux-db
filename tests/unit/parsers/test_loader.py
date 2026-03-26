from __future__ import annotations

import pytest

from kuriboh.parsers.loader import load_schema, load_providers, load_catalogs


def test_load_schema_returns_table_with_rows_columns_output(tmp_path):
    schema_path = tmp_path / "product.yml"
    schema_path.write_text(
        """
product:
  rows: 5
  columns:
    id:
      type: "faker"
      method: "uuid4"
  output:
    format: csv
    filepath: "./outputs/products.csv"
""".strip(),
        encoding="utf-8",
    )
    schema = load_schema(schema_path)
    assert isinstance(schema, dict)
    assert "product" in schema
    assert list(schema["product"].keys()) == ["rows", "columns", "output"]


def test_load_providers_merges_all_yaml_under_providers_dir(tmp_path):
    providers_dir = tmp_path / "providers"
    providers_dir.mkdir()
    (providers_dir / "a.yml").write_text(
        """\
AlphaProvider:
  type: random_choice
  choices: ["x"]
BetaProvider:
  type: random_choice
  choices: ["y"]
""",
        encoding="utf-8",
    )
    (providers_dir / "b.yml").write_text(
        """\
GammaProvider:
  type: random_choice
  choices: ["z"]
""",
        encoding="utf-8",
    )
    providers_dict = load_providers(tmp_path)
    assert len(providers_dict) == 3
    assert {"AlphaProvider", "BetaProvider", "GammaProvider"} == set(providers_dict.keys())


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


def test_load_catalogs_returns_expected_catalog_keys_for_nested_fixture_shape(tmp_path):
    catalogs_dir = tmp_path / "catalogs"
    (catalogs_dir / "common").mkdir(parents=True)
    (catalogs_dir / "furnitures").mkdir(parents=True)

    (catalogs_dir / "common" / "adjective.yaml").write_text(
        "adjective:\n  style:\n    - Sleek\n",
        encoding="utf-8",
    )
    (catalogs_dir / "common" / "color.yaml").write_text(
        "color:\n  - Red\n  - Blue\n",
        encoding="utf-8",
    )
    (catalogs_dir / "common" / "material.yaml").write_text(
        "material:\n  - Steel\n  - Wood\n",
        encoding="utf-8",
    )
    (catalogs_dir / "furnitures" / "bedroom.yaml").write_text(
        "sleeping_quarters:\n  beds:\n    - Platform Bed\n",
        encoding="utf-8",
    )
    (catalogs_dir / "furnitures" / "kitchen.yaml").write_text(
        "dining_fixtures:\n  tables:\n    - Bistro Table\n",
        encoding="utf-8",
    )
    (catalogs_dir / "furnitures" / "living_room.yaml").write_text(
        "seating_arrangements:\n  sofas:\n    - Sectional\n",
        encoding="utf-8",
    )

    loaded_catalogs = load_catalogs(tmp_path)
    expected_keys = {"bedroom", "kitchen", "living_room", "adjective", "material", "color"}
    assert expected_keys.issubset(loaded_catalogs.keys())
    for key in expected_keys:
        assert isinstance(loaded_catalogs[key], dict)
