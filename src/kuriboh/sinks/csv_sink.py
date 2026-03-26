from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
from collections.abc import Iterable

from .base import BaseSink


class CsvSink(BaseSink):
    def __init__(self, output_path: Path):
        self._output_path = output_path

    def write_rows(self, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        with self._output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
