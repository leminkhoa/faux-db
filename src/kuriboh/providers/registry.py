from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict

from enum import Enum

from ..core import SEEDS_DIRNAME
from .base import BaseProvider
from .config import validate_provider_config
from .expression import ExpressionProvider
from .file_reader import FileReaderProvider
from .random_choice import RandomChoiceProvider
from .template_choice import TemplateChoiceProvider


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

    path = base_dir / SEEDS_DIRNAME / filename
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows.extend(reader)
    return rows


def _random_choice_factory(base_dir: Path, cfg: Dict[str, Any]) -> BaseProvider:
    return RandomChoiceProvider(
        cfg["choices"],
        cfg.get("weights"),
        cfg.get("seed"),
    )


def _file_reader_factory(base_dir: Path, cfg: Dict[str, Any]) -> BaseProvider:
    rows = _load_seed_csv(base_dir, cfg["filepath"])
    return FileReaderProvider(rows, cfg["column"])


def _template_choice_factory(base_dir: Path, cfg: Dict[str, Any]) -> BaseProvider:
    return TemplateChoiceProvider(cfg["templates"], cfg.get("seed"))


def _expression_factory(base_dir: Path, cfg: Dict[str, Any]) -> BaseProvider:
    return ExpressionProvider(cfg["exp"], cfg.get("seed"))


_PROVIDER_FACTORIES: Dict[str, ProviderFactory] = {
    ProviderType.RANDOM_CHOICE.value: _random_choice_factory,
    ProviderType.FILE_READER.value: _file_reader_factory,
    ProviderType.TEMPLATE_CHOICE.value: _template_choice_factory,
    ProviderType.EXPRESSION.value: _expression_factory,
}


def build_registry(base_dir: Path, providers_cfg: Dict[str, Any]) -> ProviderRegistry:
    registry = ProviderRegistry()

    for name, cfg in providers_cfg.items():
        typed_cfg = validate_provider_config(name, cfg)

        factory = _PROVIDER_FACTORIES.get(typed_cfg.type)
        if not factory:
            raise ValueError(f"Unsupported provider type '{typed_cfg.type}' for '{name}'")

        provider = factory(base_dir, typed_cfg.model_dump())

        registry.register(name, provider)

    return registry
