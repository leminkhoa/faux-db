from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
from enum import Enum

import polars as pl

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


ProviderFactory = Callable[[Path, dict[str, Any]], BaseProvider]


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, name: str, provider: BaseProvider) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> BaseProvider:
        return self._providers[name]


def _load_seed_csv(
    base_dir: Path,
    filename: str,
    *,
    encoding: str,
    delimiter: str,
    loaded_columns: list[str],
) -> pl.DataFrame:
    path = base_dir / SEEDS_DIRNAME / filename
    if not path.exists():
        return pl.DataFrame(schema=[(c, pl.Utf8) for c in loaded_columns])

    try:
        return pl.read_csv(
            path,
            columns=loaded_columns,
            encoding=encoding,
            separator=delimiter,
            try_parse_dates=False,
        )
    except pl.exceptions.ColumnNotFoundError as e:
        raise ValueError(
            f"Seed {filename!r} is missing one or more of loaded_columns "
            f"{loaded_columns}: {e}"
        ) from e


def _random_choice_factory(base_dir: Path, cfg: dict[str, Any]) -> BaseProvider:
    return RandomChoiceProvider(cfg["choices"], cfg.get("weights"), cfg.get("seed"))


def _file_reader_factory(base_dir: Path, cfg: dict[str, Any]) -> BaseProvider:
    loaded = cfg["loaded_columns"]
    df = _load_seed_csv(
        base_dir,
        cfg["filepath"],
        encoding=cfg.get("encoding", "utf-8"),
        delimiter=cfg.get("delimiter", ","),
        loaded_columns=loaded,
    )
    return FileReaderProvider(df, loaded_columns=loaded, on_duplicate_key=cfg.get("on_duplicate_key", "first"))


def _template_choice_factory(base_dir: Path, cfg: dict[str, Any]) -> BaseProvider:
    return TemplateChoiceProvider(cfg["templates"], cfg.get("seed"))


def _expression_factory(base_dir: Path, cfg: dict[str, Any]) -> BaseProvider:
    return ExpressionProvider(cfg["exp"], cfg.get("seed"))


_PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    ProviderType.RANDOM_CHOICE.value: _random_choice_factory,
    ProviderType.FILE_READER.value: _file_reader_factory,
    ProviderType.TEMPLATE_CHOICE.value: _template_choice_factory,
    ProviderType.EXPRESSION.value: _expression_factory,
}


def build_registry(base_dir: Path, providers_cfg: dict[str, Any]) -> ProviderRegistry:
    registry = ProviderRegistry()

    for name, cfg in providers_cfg.items():
        typed_cfg = validate_provider_config(name, cfg)
        factory = _PROVIDER_FACTORIES.get(typed_cfg.type)
        if not factory:
            raise ValueError(f"Unsupported provider type '{typed_cfg.type}' for '{name}'")
        registry.register(name, factory(base_dir, typed_cfg.model_dump()))

    return registry
