from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from kuriboh.cli import cli
from kuriboh.core.validation import ValidationSummary, validate_project


def test_schema_generate_file_dispatches_to_run_generation(monkeypatch, tmp_path):
    runner = CliRunner()
    schema = tmp_path / "users.yml"
    schema.write_text("users: {}\n", encoding="utf-8")
    called = {}

    monkeypatch.setattr(
        "kuriboh.cli.commands.common.run_generation",
        lambda path: called.setdefault("path", path),
    )
    monkeypatch.setattr(
        "kuriboh.cli.commands.common.run_domain",
        lambda path: called.setdefault("unexpected", path),
    )

    result = runner.invoke(cli, ["schema", "generate", str(schema)])

    assert result.exit_code == 0, result.output
    assert called == {"path": schema}


def test_schema_generate_directory_dispatches_to_run_domain(monkeypatch, tmp_path):
    runner = CliRunner()
    domain = tmp_path / "ecommerce"
    domain.mkdir()
    called = {}

    monkeypatch.setattr(
        "kuriboh.cli.commands.common.run_generation",
        lambda path: called.setdefault("unexpected", path),
    )
    monkeypatch.setattr(
        "kuriboh.cli.commands.common.run_domain",
        lambda path: called.setdefault("path", path),
    )

    result = runner.invoke(cli, ["schema", "generate", str(domain)])

    assert result.exit_code == 0, result.output
    assert called == {"path": domain}


def test_generate_alias_dispatches_to_run_generation(monkeypatch, tmp_path):
    runner = CliRunner()
    schema = tmp_path / "users.yml"
    schema.write_text("users: {}\n", encoding="utf-8")
    called = {}

    monkeypatch.setattr(
        "kuriboh.cli.commands.common.run_generation",
        lambda path: called.setdefault("path", path),
    )
    monkeypatch.setattr(
        "kuriboh.cli.commands.common.run_domain",
        lambda path: called.setdefault("unexpected", path),
    )

    result = runner.invoke(cli, ["generate", str(schema)])

    assert result.exit_code == 0, result.output
    assert called == {"path": schema}


def test_schema_generate_missing_path_reports_error(tmp_path):
    runner = CliRunner()
    missing = tmp_path / "missing"

    result = runner.invoke(cli, ["schema", "generate", str(missing)])

    assert result.exit_code != 0
    assert "Not a file or directory" in result.output


def test_config_validate_dispatches_to_project_validation(monkeypatch, tmp_path):
    runner = CliRunner()
    called = {}

    def fake_validate_project(path: Path):
        called["path"] = path
        return ValidationSummary(
            base_dir=path,
            schema_count=2,
            domain_count=1,
            provider_count=3,
            catalog_count=4,
        )

    monkeypatch.setattr("kuriboh.cli.commands.config.validate_project", fake_validate_project)

    result = runner.invoke(cli, ["config", "validate", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert called == {"path": tmp_path}
    assert "Validated configuration" in result.output
    assert "Schema files" in result.output


def test_init_creates_starter_project(tmp_path):
    runner = CliRunner()

    result = runner.invoke(cli, ["init", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "schemas").is_dir()
    assert (tmp_path / "providers").is_dir()
    assert (tmp_path / "catalogs").is_dir()
    assert (tmp_path / "seeds").is_dir()
    assert (tmp_path / "outputs").is_dir()
    assert (tmp_path / "functions").is_dir()
    assert (tmp_path / "functions" / "__init__.py").exists()
    assert (tmp_path / "schemas" / "example" / "users.yml").exists()
    assert (tmp_path / "providers" / "example.yml").exists()
    assert (tmp_path / "catalogs" / "demo.yml").exists()
    assert "Initialized Kuriboh project" in result.output


def test_init_starter_project_is_valid(tmp_path):
    runner = CliRunner()

    result = runner.invoke(cli, ["init", str(tmp_path)])

    assert result.exit_code == 0, result.output

    summary = validate_project(tmp_path)

    assert summary.schema_count == 1
    assert summary.domain_count == 1
    assert summary.provider_count == 2
    assert summary.catalog_count == 1


def test_root_help_includes_common_patterns():
    runner = CliRunner()

    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0, result.output
    assert "Common patterns:" in result.output
    assert "kuriboh init" in result.output
    assert "kuriboh schema generate schemas/example/users.yml" in result.output


def test_config_help_includes_detailed_guides():
    runner = CliRunner()

    result = runner.invoke(cli, ["config", "--help"])

    assert result.exit_code == 0, result.output
    assert "Validation includes:" in result.output
    assert "kuriboh config validate ./demo-project" in result.output
    assert "Examples:\n  kuriboh config validate\n  kuriboh config validate ./demo-project" in result.output


def test_schema_generate_help_includes_examples():
    runner = CliRunner()

    result = runner.invoke(cli, ["schema", "generate", "--help"])

    assert result.exit_code == 0, result.output
    assert "Examples:" in result.output
    assert "kuriboh schema generate schemas/example" in result.output
