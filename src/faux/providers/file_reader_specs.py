"""
Typed spec dataclasses shared between
:mod:`~faux.providers.file_reader` and
:mod:`~faux.resolvers.file_reader_context`.

Keeping specs here (in the ``providers`` package) avoids a circular
import: ``FileReaderProvider`` can import from its own package, and
``file_reader_context`` (in ``resolvers``) can also import from ``providers``
without going in a cycle.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any


@dataclass
class FileReaderSampleSpec:
    column: str
    strategy: str
    rng: random.Random
    seq: list[int]          # mutable counter; intentionally not frozen
    shuffle_indices: list[int] | None


@dataclass(frozen=True)
class FileReaderLookupSpec:
    key_columns: tuple[str, ...]
    value_column: str
    key: tuple[Any, ...]
    on_missing: str
    default_value: Any


FileReaderSpec = FileReaderSampleSpec | FileReaderLookupSpec
