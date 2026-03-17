from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict

from enum import Enum

from .base import (
    BaseProvider,
    ExpressionProvider,
    FileReaderProvider,
    RandomChoiceProvider,
    TemplateChoiceProvider,
)


class ProviderType(str, Enum):
    RANDOM_CHOICE = "random_choice"
    FILE_READER = "file_reader"
    TEMPLATE_CHOICE = "template_choice"
    EXPRESSION = "expression"


ProviderFactory = Callable[[Path, Dict[str, Any]], BaseProvider]


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, BaseProvider] = {}

    def register(self, name: str, provider: BaseProvider) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> BaseProvider:
        return self._providers[name]


def _load_seed_csv(base_dir: Path, filename: str) -> list[dict[str, Any]]:
    import csv

    path = base_dir / "seeds" / filename
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows.extend(reader)
    return rows


def _random_choice_factory(base_dir: Path, cfg: Dict[str, Any]) -> BaseProvider:
    return RandomChoiceProvider(
        cfg.get("choices", []),
        cfg.get("weights"),
    )


def _file_reader_factory(base_dir: Path, cfg: Dict[str, Any]) -> BaseProvider:
    filepath = cfg.get("filepath")
    column = cfg.get("column")
    rows = _load_seed_csv(base_dir, filepath)
    return FileReaderProvider(rows, column)


def _template_choice_factory(base_dir: Path, cfg: Dict[str, Any]) -> BaseProvider:
    return TemplateChoiceProvider(cfg.get("templates", []))


def _expression_factory(base_dir: Path, cfg: Dict[str, Any]) -> BaseProvider:
    return ExpressionProvider(cfg.get("exp", ""))


_PROVIDER_FACTORIES: Dict[str, ProviderFactory] = {
    ProviderType.RANDOM_CHOICE.value: _random_choice_factory,
    ProviderType.FILE_READER.value: _file_reader_factory,
    ProviderType.TEMPLATE_CHOICE.value: _template_choice_factory,
    ProviderType.EXPRESSION.value: _expression_factory,
}


def build_registry(base_dir: Path, providers_cfg: Dict[str, Any]) -> ProviderRegistry:
    registry = ProviderRegistry()

    for name, cfg in providers_cfg.items():
        p_type = cfg.get("type")
        factory = _PROVIDER_FACTORIES.get(p_type)
        if not factory:
            continue

        provider = factory(base_dir, cfg)

        registry.register(name, provider)

    return registry