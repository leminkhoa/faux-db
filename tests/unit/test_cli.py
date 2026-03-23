from __future__ import annotations

import sys

import pytest

from kuriboh import cli


def test_cli_generate_file_dispatches_to_run_generation(monkeypatch, tmp_path):
    schema = tmp_path / "users.yml"
    schema.write_text("users: {}\n", encoding="utf-8")
    called = {}

    monkeypatch.setattr(sys, "argv", ["kuriboh", "generate", str(schema)])
    monkeypatch.setattr("kuriboh.cli.run_generation", lambda path: called.setdefault("path", path))
    monkeypatch.setattr("kuriboh.cli.run_domain", lambda path: called.setdefault("unexpected", path))

    cli.main()

    assert called == {"path": schema}


def test_cli_generate_directory_dispatches_to_run_domain(monkeypatch, tmp_path):
    domain = tmp_path / "ecommerce"
    domain.mkdir()
    called = {}

    monkeypatch.setattr(sys, "argv", ["kuriboh", "generate", str(domain)])
    monkeypatch.setattr("kuriboh.cli.run_generation", lambda path: called.setdefault("unexpected", path))
    monkeypatch.setattr("kuriboh.cli.run_domain", lambda path: called.setdefault("path", path))

    cli.main()

    assert called == {"path": domain}


def test_cli_missing_path_raises_file_not_found(monkeypatch, tmp_path):
    missing = tmp_path / "missing"
    monkeypatch.setattr(sys, "argv", ["kuriboh", "generate", str(missing)])

    with pytest.raises(FileNotFoundError, match="Not a file or directory"):
        cli.main()
