from __future__ import annotations

import random
from typing import Any

from .base import BaseProvider


class RandomChoiceProvider(BaseProvider):
    """Provider that returns one item from a fixed sequence of choices.

    Unweighted mode uses :func:`random.choice` (or the seeded RNG's
    equivalent). When ``weights`` is provided and non-empty,
    :func:`random.choices` is used so draws follow the given weights.

    ``cardinality`` counts distinct ``str(choice)`` values; ``enumerate_all``
    returns unique choices in first-seen order (see :func:`dict.fromkeys`).

    Args:
        choices: Candidate values to sample from.
        weights: Optional weights aligned with ``choices``. If ``None`` or
            empty, choices are uniform.
        seed: If set, sampling uses a dedicated :class:`random.Random` for
            reproducible output; if ``None``, the global :mod:`random` module
            is used.
    """

    def __init__(
        self,
        choices: list[Any],
        weights: list[float] | None = None,
        seed: int | None = None,
    ):
        self._choices = list(choices)
        self._weights = list(weights) if weights is not None else None
        self._rng = random.Random(seed)

    def generate(self, context: dict[str, Any]) -> Any:
        if self._weights:
            return self._rng.choices(self._choices, weights=self._weights, k=1)[0]
        return self._rng.choice(self._choices)

    def cardinality(self, catalogs: dict[str, Any]) -> int | None:
        return len({str(c) for c in self._choices})

    def enumerate_all(self, catalogs: dict[str, Any]) -> list[Any] | None:
        return list(dict.fromkeys(self._choices))
