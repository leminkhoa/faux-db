from __future__ import annotations

from typing import Any, Annotated, List, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter, ValidationError, model_validator


class RandomChoiceProviderConfig(BaseModel):
    type: Literal["random_choice"]
    choices: List[Any]
    weights: List[float] | None = None
    seed: int | None = Field(
        default=None,
        description="Optional RNG seed for reproducible random_choice output.",
    )

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
    seed: int | None = Field(
        default=None,
        description="Optional RNG seed for template pick and catalog | random slots.",
    )


class ExpressionProviderConfig(BaseModel):
    type: Literal["expression"]
    exp: str
    seed: int | None = Field(
        default=None,
        description="Optional seed; expression uses Faker().seed_instance(seed) for isolation.",
    )

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


def validate_provider_config(name: str, raw_cfg: Any) -> ProviderConfig:
    try:
        return _PROVIDER_CONFIG_ADAPTER.validate_python(raw_cfg)
    except ValidationError as e:
        raise ValueError(f"Invalid provider config for '{name}': {e}") from e
