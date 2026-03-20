"""
Shared pytest fixtures for the whole suite.

``fixtures_root`` resolves via :attr:`pytest.Config.rootpath` (the directory
containing ``pyproject.toml``), so it stays correct no matter whether
``conftest.py`` lives under ``tests/`` or ``tests/unit/``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Any

import pytest


@pytest.fixture(scope="session")
def fixtures_root(request: pytest.FixtureRequest) -> Path:
    """``<project root>/tests/fixtures`` — stable for any test file location."""
    return Path(request.config.rootpath) / "tests" / "fixtures"


@pytest.fixture
def fixtures_join(fixtures_root: Path) -> Callable[..., Path]:
    """
    Build paths under ``tests/fixtures`` without hardcoding parents in each test::

        def test_x(fixtures_join):
            p = fixtures_join("catalogs", "common", "materials.yaml")
    """

    def _join(*parts: str) -> Path:
        return fixtures_root.joinpath(*parts)

    return _join

@pytest.fixture(scope="session")
def loaded_catalogs(fixtures_root: Path) -> dict[str, Any]:
    from kuriboh.parsers.loader import load_catalogs

    return load_catalogs(fixtures_root)
