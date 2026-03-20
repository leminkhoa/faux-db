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
