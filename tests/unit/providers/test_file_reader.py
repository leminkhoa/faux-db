"""Tests for :class:`~kuriboh.providers.file_reader.FileReaderProvider`."""

from __future__ import annotations

from kuriboh.providers.file_reader import FileReaderProvider


def test_file_reader_cycles_rows():
    p = FileReaderProvider(
        [{"c": "a"}, {"c": "b"}],
        "c",
    )
    assert p.generate({}) == "a"
    assert p.generate({}) == "b"
    assert p.generate({}) == "a"


def test_file_reader_empty_returns_none():
    p = FileReaderProvider([], "c")
    assert p.generate({}) is None
