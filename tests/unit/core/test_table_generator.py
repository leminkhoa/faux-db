from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from faker import Faker

from faux.core.context import GenerationContext
from faux.core.table_generator import TableGenerator, TablePlan
from faux.parsers.schema import ColumnConfig, OutputConfig
from faux.sinks.base import BaseSink


class _RecordingSink(BaseSink):
    def __init__(self) -> None:
        self.rows = None
        self.fieldnames = None

    def write_rows(self, rows, fieldnames) -> None:
        self.rows = list(rows)
        self.fieldnames = list(fieldnames)


class _FakeResolver:
    def __init__(self, *, unique: bool = False, cardinality_value=None, generator=None) -> None:
        self._unique = unique
        self._cardinality_value = cardinality_value
        self._generator = generator or (lambda context, row: None)
        self.pre_init_calls = 0

    def resolve(self, context, row):
        return self._generator(context, row)

    def cardinality(self, catalogs):
        return self._cardinality_value

    def pre_init_pool(self, context):
        self.pre_init_calls += 1


def _ctx() -> GenerationContext:
    return GenerationContext(faker=Faker(), catalogs={})


def test_apply_cardinality_guard_caps_to_smallest_unique_cardinality(capsys):
    gen = TableGenerator(Path("/tmp/schema.yml"), Path("/tmp"), _ctx())
    resolvers = {
        "id": _FakeResolver(unique=True, cardinality_value=3),
        "name": _FakeResolver(unique=True, cardinality_value=5),
        "note": _FakeResolver(unique=False, cardinality_value=1),
    }

    assert gen._apply_cardinality_guard("users", 10, resolvers) == 3
    assert "Reducing rows to 3" in capsys.readouterr().out


def test_apply_cardinality_guard_leaves_rows_when_no_unique_cap():
    gen = TableGenerator(Path("/tmp/schema.yml"), Path("/tmp"), _ctx())
    resolvers = {
        "id": _FakeResolver(unique=False, cardinality_value=3),
        "name": _FakeResolver(unique=True, cardinality_value=None),
    }

    assert gen._apply_cardinality_guard("users", 10, resolvers) == 10


def test_execute_generates_rows_in_column_order_and_writes_sink():
    sink = _RecordingSink()
    context = _ctx()
    gen = TableGenerator(Path("/tmp/schema.yml"), Path("/tmp"), context)
    id_counter = {"value": 0}

    plan = TablePlan(
        table_name="users",
        rows_count=2,
        column_order=["id", "label"],
        resolvers={
            "id": _FakeResolver(
                generator=lambda context, row: id_counter.__setitem__("value", id_counter["value"] + 1)
                or id_counter["value"]
            ),
            "label": _FakeResolver(generator=lambda context, row: f"user-{row['id']}"),
        },
        fieldnames=["id", "label"],
        sink=sink,
    )

    rows = gen.execute(plan)

    assert rows == [{"id": 1, "label": "user-1"}, {"id": 2, "label": "user-2"}]
    assert context.generated_tables["users"] == rows
    assert sink.rows == rows
    assert sink.fieldnames == ["id", "label"]


def test_plan_builds_plan_and_preinits_resolvers(monkeypatch):
    context = _ctx()
    gen = TableGenerator(Path("/tmp/users.yml"), Path("/tmp/base"), context)
    output = OutputConfig(format="csv", filepath="./out.csv")
    columns_cfg = {"id": ColumnConfig(type="faker", method="uuid4")}
    schema_model = SimpleNamespace(
        table_name="users",
        table=SimpleNamespace(rows=4, columns=columns_cfg, output=output),
    )
    r1 = _FakeResolver()
    r2 = _FakeResolver(unique=True, cardinality_value=10)
    sink = _RecordingSink()

    monkeypatch.setattr("faux.core.table_generator.load_schema", lambda path: {"raw": True})
    monkeypatch.setattr("faux.core.table_generator.validate_schema", lambda raw: schema_model)
    monkeypatch.setattr("faux.core.table_generator.load_providers", lambda base_dir: {"P": {}})
    monkeypatch.setattr("faux.core.table_generator.build_registry", lambda base_dir, providers: "registry")
    monkeypatch.setattr(
        "faux.core.table_generator.validate_provider_columns_for_plan",
        lambda registry, columns: None,
    )
    monkeypatch.setattr("faux.core.table_generator.build_dag", lambda columns: ["id"])
    monkeypatch.setattr("faux.core.table_generator.compute_effective_unique", lambda columns: {"id": False})
    monkeypatch.setattr(
        "faux.core.table_generator.build_resolvers",
        lambda table_name, columns, effective_unique, faker, registry: {"id": r1, "other": r2},
    )
    monkeypatch.setattr(
        "faux.core.table_generator.create_sink",
        lambda output_cfg, base_dir=None: sink,
    )

    plan = gen.plan()

    assert plan.table_name == "users"
    assert plan.rows_count == 4
    assert plan.column_order == ["id"]
    assert plan.fieldnames == ["id"]
    assert plan.sink is sink
    assert r1.pre_init_calls == 1
    assert r2.pre_init_calls == 1
