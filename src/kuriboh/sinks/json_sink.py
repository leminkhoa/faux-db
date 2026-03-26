from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any
from collections.abc import Iterable

from .base import BaseSink


def _json_default(obj: Any) -> Any:
    """Convert non-JSON-serializable types for json.dumps."""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class JsonSink(BaseSink):
    def __init__(self, output_path: Path):
        self._output_path = output_path

    def write_rows(self, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure each row has keys in fieldnames order; filter to fieldnames only
        data = [{k: row.get(k) for k in fieldnames} for row in rows]
        with self._output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=_json_default)
