from __future__ import annotations

import random
from typing import Any, Dict, List, Sequence

from .base import BaseProvider


class RandomChoiceProvider(BaseProvider):
    def __init__(
        self,
        choices: Sequence[Any],
        weights: Sequence[float] | None = None,
        seed: int | None = None,
    ):
        self._choices = list(choices)
        self._weights = list(weights) if weights is not None else None
        self._rng: random.Random | None = (
            random.Random(seed) if seed is not None else None
        )

    def generate(self, context: Dict[str, Any]) -> Any:
        rng = self._rng if self._rng is not None else random

        if self._weights:
            return rng.choices(self._choices, weights=self._weights, k=1)[0]
        return rng.choice(self._choices)

    def cardinality(self, catalogs: Dict[str, Any]) -> int | None:
        return len(set(str(c) for c in self._choices))

    def enumerate_all(self, catalogs: Dict[str, Any]) -> List[Any] | None:
        return list(dict.fromkeys(self._choices))
