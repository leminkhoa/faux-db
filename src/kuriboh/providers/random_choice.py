from __future__ import annotations

import random
from typing import Any, Dict, List, Sequence

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
        """Return how many distinct outputs ``generate`` can produce.

        Uniqueness is determined by ``str(choice)``, so values that stringify
        the same (e.g. ``1`` and ``\"1\"``) count once.

        Args:
            catalogs: Unused; present for :class:`BaseProvider` compatibility.

        Returns:
            The number of unique string forms among ``choices``.
        """
        return len(set(str(c) for c in self._choices))

    def enumerate_all(self, catalogs: Dict[str, Any]) -> List[Any] | None:
        """Return every distinct choice in first-seen order.

        Equivalent to ``list(dict.fromkeys(choices))`` over the configured
        sequence.

        Args:
            catalogs: Unused; present for :class:`BaseProvider` compatibility.

        Returns:
            Unique choice values in first-seen order.
        """
        return list(dict.fromkeys(self._choices))
