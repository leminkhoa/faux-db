"""Sink factory: creates the appropriate sink based on OutputConfig.format."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .base import BaseSink
from .csv_sink import CsvSink
from .json_sink import JsonSink

if TYPE_CHECKING:
    from ..parsers.schema import OutputConfig


_SINK_REGISTRY: dict[str, type[BaseSink]] = {
    "csv": CsvSink,
    "json": JsonSink,
}


def create_sink(output_cfg: "OutputConfig", base_dir: Path | None = None) -> BaseSink:
    """Create a sink for the given output configuration."""
    output_path = Path(output_cfg.filepath)
    # Relative paths would otherwise resolve against cwd; anchor them to the project root
    # so e.g. ./outputs/foo.csv lands under base_dir, not the shell working directory.
    if base_dir is not None and not output_path.is_absolute():
        output_path = (base_dir / output_path).resolve()
    sink_cls = _SINK_REGISTRY.get(output_cfg.format)
    if sink_cls is None:
        raise ValueError(f"Unknown output format: {output_cfg.format}")
    return sink_cls(output_path)
