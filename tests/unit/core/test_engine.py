from __future__ import annotations

from types import SimpleNamespace

import pytest
from faker import Faker

from faux.core.context import GenerationContext
from faux.core.engine import run_domain, run_generation


def test_run_generation_uses_existing_context_and_base_dir(monkeypatch, tmp_path):
    schema_path = tmp_path / "schemas" / "shop" / "users.yml"
    schema_path.parent.mkdir(parents=True)
    schema_path.write_text("users: {}\n", encoding="utf-8")
    context = GenerationContext(faker=Faker(), catalogs={"colors": {}})
    observed = {}

    class _FakeGenerator:
        def __init__(self, schema_path_arg, base_dir_arg, context_arg):
            observed["schema_path"] = schema_path_arg
            observed["base_dir"] = base_dir_arg
            observed["context"] = context_arg

        def plan(self):
            observed["planned"] = True
            return "PLAN"

        def execute(self, plan):
            observed["executed_with"] = plan

    monkeypatch.setattr("faux.core.engine.TableGenerator", _FakeGenerator)

    run_generation(schema_path, context=context, base_dir=tmp_path)

    assert observed == {
        "schema_path": schema_path,
        "base_dir": tmp_path,
        "context": context,
        "planned": True,
        "executed_with": "PLAN",
    }


def test_run_generation_builds_default_context_from_catalogs(monkeypatch, tmp_path):
    schema_path = tmp_path / "schemas" / "shop" / "users.yml"
    schema_path.parent.mkdir(parents=True)
    schema_path.write_text("users: {}\n", encoding="utf-8")
    observed = {}

    class _FakeGenerator:
        def __init__(self, schema_path_arg, base_dir_arg, context_arg):
            observed["schema_path"] = schema_path_arg
            observed["base_dir"] = base_dir_arg
            observed["context"] = context_arg

        def plan(self):
            return "PLAN"

        def execute(self, plan):
            observed["plan"] = plan

    monkeypatch.setattr("faux.core.engine.load_catalogs", lambda base_dir: {"catalog": {"a": 1}})
    monkeypatch.setattr("faux.core.engine.TableGenerator", _FakeGenerator)

    run_generation(schema_path)

    assert observed["base_dir"] == schema_path.parent.parent
    assert isinstance(observed["context"], GenerationContext)
    assert observed["context"].catalogs == {"catalog": {"a": 1}}
    assert observed["plan"] == "PLAN"


def test_run_domain_raises_when_no_schema_files(tmp_path):
    with pytest.raises(ValueError, match="No .yml schema files"):
        run_domain(tmp_path)


def test_run_domain_rejects_duplicate_table_names(monkeypatch, tmp_path):
    domain = tmp_path / "schemas" / "shop"
    domain.mkdir(parents=True)
    (domain / "a.yml").write_text("a: {}\n", encoding="utf-8")
    (domain / "b.yml").write_text("b: {}\n", encoding="utf-8")

    monkeypatch.setattr("faux.core.engine.load_schema", lambda path: {"raw": path.name})
    monkeypatch.setattr(
        "faux.core.engine.validate_schema",
        lambda raw: SimpleNamespace(table_name="users"),
    )

    with pytest.raises(ValueError, match="Duplicate table name 'users'"):
        run_domain(domain)


def test_run_domain_executes_tables_in_topological_order_with_shared_context(monkeypatch, tmp_path):
    domain = tmp_path / "schemas" / "shop"
    domain.mkdir(parents=True)
    users = domain / "users.yml"
    orders = domain / "orders.yml"
    users.write_text("users: {}\n", encoding="utf-8")
    orders.write_text("orders: {}\n", encoding="utf-8")
    schema_map = {
        users: SimpleNamespace(table_name="users"),
        orders: SimpleNamespace(table_name="orders"),
    }
    calls = []

    monkeypatch.setattr("faux.core.engine.load_schema", lambda path: {"path": path})
    monkeypatch.setattr(
        "faux.core.engine.validate_schema",
        lambda raw: schema_map[raw["path"]],
    )
    monkeypatch.setattr("faux.core.engine.build_table_dag", lambda schemas: ["users", "orders"])
    monkeypatch.setattr("faux.core.engine.load_catalogs", lambda base_dir: {"catalog": {}})

    def _record_run_generation(schema_path, context=None, base_dir=None):
        calls.append((schema_path.name, context, base_dir))

    monkeypatch.setattr("faux.core.engine.run_generation", _record_run_generation)

    run_domain(domain)

    assert [name for name, _, _ in calls] == ["users.yml", "orders.yml"]
    assert calls[0][1] is calls[1][1]
    assert isinstance(calls[0][1], GenerationContext)
    assert calls[0][2] == tmp_path
