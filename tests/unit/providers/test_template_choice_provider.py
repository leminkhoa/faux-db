"""Tests for :class:`~kuriboh.providers.template_choice.TemplateChoiceProvider`."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from kuriboh.providers.template_choice import TemplateChoiceProvider



def test_template_choice_first_material_from_fixture_catalogs(
    loaded_catalogs: Dict[str, Any],
) -> None:
    """
    Catalogs from ``tests/fixtures/catalogs/common/materials.yaml`` are loaded
    via the session-scoped ``loaded_catalogs`` fixture (see
    ``tests/unit/providers/conftest.py``).

    ``| first`` picks the first list entry, so output is deterministic without
    relying on RNG for the catalog slot.
    """

    provider = TemplateChoiceProvider(
        templates=['{{ catalog("materials.material") | first }}'],
    )
    out = provider.generate(context={"catalogs": loaded_catalogs})
    assert out == "Steel"


def test_template_choice_rejects_empty_templates_expect_error() -> None:
    """
    `TemplateChoiceProvider` should reject an empty `templates` iterable during
    initialization, rather than failing later in `generate()` (e.g., via
    `random.randrange()` on an empty range).
    """
    with pytest.raises(ValueError, match="at least one template"):
        TemplateChoiceProvider(templates=[])
