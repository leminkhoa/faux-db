from __future__ import annotations

from pathlib import Path
from typing import Any, Annotated, Callable, Dict, List, Literal, Union

from enum import Enum

from pydantic import BaseModel, Field, TypeAdapter, ValidationError, model_validator

from ..core import SEEDS_DIRNAME
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


class RandomChoiceProviderConfig(BaseModel):
    type: Literal["random_choice"]
    choices: List[Any]
    weights: List[float] | None = None

    @model_validator(mode="after")
    def validate_random_choice(self) -> "RandomChoiceProviderConfig":
        if not self.choices:
            raise ValueError("choices must not be empty")
        if self.weights is not None and len(self.weights) != len(self.choices):
            raise ValueError("weights length must match choices length")
        return self


class FileReaderProviderConfig(BaseModel):
    type: Literal["file_reader"]
    filepath: str
    column: str


class TemplateChoiceProviderConfig(BaseModel):
    type: Literal["template_choice"]
    templates: List[str] = Field(..., min_length=1)


class ExpressionProviderConfig(BaseModel):
    type: Literal["expression"]
    exp: str

    @model_validator(mode="after")
    def validate_expression(self) -> "ExpressionProviderConfig":
        if not self.exp.strip():
            raise ValueError("exp must not be empty")
        return self


ProviderConfig = Annotated[
    Union[
        RandomChoiceProviderConfig,
        FileReaderProviderConfig,
        TemplateChoiceProviderConfig,
        ExpressionProviderConfig,
    ],
    Field(discriminator="type"),
]
_PROVIDER_CONFIG_ADAPTER = TypeAdapter(ProviderConfig)


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
    )


def _file_reader_factory(base_dir: Path, cfg: Dict[str, Any]) -> BaseProvider:
    rows = _load_seed_csv(base_dir, cfg["filepath"])
    return FileReaderProvider(rows, cfg["column"])


def _template_choice_factory(base_dir: Path, cfg: Dict[str, Any]) -> BaseProvider:
    return TemplateChoiceProvider(cfg["templates"])


def _expression_factory(base_dir: Path, cfg: Dict[str, Any]) -> BaseProvider:
    return ExpressionProvider(cfg["exp"])


_PROVIDER_FACTORIES: Dict[str, ProviderFactory] = {
    ProviderType.RANDOM_CHOICE.value: _random_choice_factory,
    ProviderType.FILE_READER.value: _file_reader_factory,
    ProviderType.TEMPLATE_CHOICE.value: _template_choice_factory,
    ProviderType.EXPRESSION.value: _expression_factory,
}


def build_registry(base_dir: Path, providers_cfg: Dict[str, Any]) -> ProviderRegistry:
    registry = ProviderRegistry()

    for name, cfg in providers_cfg.items():
        try:
            typed_cfg = _PROVIDER_CONFIG_ADAPTER.validate_python(cfg)
        except ValidationError as e:
            raise ValueError(f"Invalid provider config for '{name}': {e}") from e

        factory = _PROVIDER_FACTORIES.get(typed_cfg.type)
        if not factory:
            raise ValueError(f"Unsupported provider type '{typed_cfg.type}' for '{name}'")

        provider = factory(base_dir, typed_cfg.model_dump())

        registry.register(name, provider)

    return registry
