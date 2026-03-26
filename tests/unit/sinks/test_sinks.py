from __future__ import annotations

import json
import uuid
from datetime import date
from pathlib import Path

import pytest

from kuriboh.parsers.schema import OutputConfig
from kuriboh.sinks.base import BaseSink
from kuriboh.sinks.csv_sink import CsvSink
from kuriboh.sinks.factory import create_sink
from kuriboh.sinks.json_sink import JsonSink, _json_default


class _SinkImpl(BaseSink):
    def write_rows(self, rows, fieldnames) -> None:
        self.rows = list(rows)
        self.fieldnames = list(fieldnames)


def test_base_sink_default_abstract_contract_can_be_subclassed():
    sink = _SinkImpl()
    sink.write_rows([{"id": 1}], ["id"])
    assert sink.rows == [{"id": 1}]
    assert sink.fieldnames == ["id"]


def test_csv_sink_writes_header_and_rows(tmp_path):
    out = tmp_path / "nested" / "rows.csv"
    sink = CsvSink(out)

    sink.write_rows([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}], ["id", "name"])

    assert out.read_text(encoding="utf-8").splitlines() == [
        "id,name",
        "1,Alice",
        "2,Bob",
    ]


def test_json_default_converts_uuid_and_date():
    assert _json_default(uuid.UUID("12345678-1234-5678-1234-567812345678")) == "12345678-1234-5678-1234-567812345678"
    assert _json_default(date(2024, 1, 2)) == "2024-01-02"


def test_json_default_rejects_unknown_type():
    with pytest.raises(TypeError, match="not JSON serializable"):
        _json_default(Path("/tmp/x"))


def test_json_sink_filters_and_orders_keys(tmp_path):
    out = tmp_path / "nested" / "rows.json"
    sink = JsonSink(out)

    sink.write_rows(
        [{"name": "Alice", "id": 1, "extra": "ignore"}],
        ["id", "name"],
    )

    assert json.loads(out.read_text(encoding="utf-8")) == [{"id": 1, "name": "Alice"}]


def test_create_sink_builds_csv_sink():
    sink = create_sink(OutputConfig(format="csv", filepath="./out.csv"))
    assert isinstance(sink, CsvSink)


def test_create_sink_resolves_relative_path_against_base_dir(tmp_path):
    base = tmp_path / "project"
    base.mkdir()
    sink = create_sink(OutputConfig(format="csv", filepath="./outputs/users.csv"), base_dir=base)
    assert isinstance(sink, CsvSink)
    assert sink._output_path == (base / "outputs" / "users.csv").resolve()


def test_create_sink_builds_json_sink():
    sink = create_sink(OutputConfig(format="json", filepath="./out.json"))
    assert isinstance(sink, JsonSink)


def test_create_sink_rejects_unknown_format():
    bad = OutputConfig.model_construct(format="xml", filepath="./out.xml")
    with pytest.raises(ValueError, match="Unknown output format"):
        create_sink(bad)
