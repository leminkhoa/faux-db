"""
Integration: retail-style domain (stores, customers, products, orders, line items).

ERD-style ``$rel`` graph::

    store ◄───────┐
                  │        transaction ◄── customer
                  │              │
                  ▼              ▼
               product    transaction_orders
                              ▲
                              │
                         (fan-in: txn + product)

Exercises: ``$faker`` (uuid, email, ints, pystr, ``date_between``), ``$rel`` (random / sequential),
``$provider`` (random_choice, template_choice, file_reader sample + lookup),
``$func`` (with ``context``), ``bind_to`` (e.g. email and title keyed by ``id``), ``unique``, and catalogs.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from kuriboh.core.dag import build_table_dag
from kuriboh.parsers.loader import load_schema
from kuriboh.parsers.schema import SchemaFile, validate_schema

EXPECTED_ROWS = 30

EXPECTED_HEADERS = {
    "customer": [
        "id",
        "email",
        "segment",
        "welcome_line",
        "service_tier",
        "created_at",
    ],
    "store": ["id", "store_code", "region", "tagline", "created_at"],
    "product": [
        "id",
        "store_id",
        "sku",
        "category",
        "unit_price_cents",
        "price_display",
        "title",
        "shelf_label",
        "line_tag",
        "brand_swatch",
        "created_at",
    ],
    "transaction": [
        "id",
        "customer_id",
        "store_id",
        "channel",
        "order_status",
        "status_stamp",
        "carrier_hint",
        "receipt_line",
        "created_at",
    ],
    "transaction_orders": [
        "id",
        "transaction_id",
        "product_id",
        "qty",
        "line_subtotal_cents",
        "created_at",
    ],
}


def _load_domain_schemas(domain_path: Path) -> dict[str, SchemaFile]:
    schemas: dict[str, SchemaFile] = {}
    for schema_file in sorted(domain_path.glob("*.yml")):
        raw = load_schema(schema_file)
        model = validate_schema(raw)
        schemas[model.table_name] = model
    return schemas


def _read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _col_values(csv_path: Path, column: str) -> list[str]:
    return [row[column] for row in _read_rows(csv_path)]


def test_domain_shopping_build_table_dag_order(domain_shopping_domain_path: Path) -> None:
    schemas = _load_domain_schemas(domain_shopping_domain_path)
    assert build_table_dag(schemas) == [
        "customer",
        "store",
        "product",
        "transaction",
        "transaction_orders",
    ]


def test_domain_shopping_all_schema_files_validate(domain_shopping_domain_path: Path) -> None:
    """Every YAML in the domain loads and passes :func:`validate_schema` (catches bad refs early)."""
    for schema_file in sorted(domain_shopping_domain_path.glob("*.yml")):
        raw = load_schema(schema_file)
        validate_schema(raw)


def test_domain_shopping_csv_headers_and_row_counts(
    domain_shopping_outputs: dict[str, Path],
) -> None:
    for key, path in domain_shopping_outputs.items():
        if key == "root":
            continue
        rows = _read_rows(path)
        assert len(rows) == EXPECTED_ROWS, f"{key}: expected {EXPECTED_ROWS} rows"
        assert list(rows[0].keys()) == EXPECTED_HEADERS[key], f"{key}: unexpected CSV header order"


def test_domain_shopping_referential_integrity_and_line_totals(
    domain_shopping_outputs: dict[str, Path],
) -> None:
    paths = {k: v for k, v in domain_shopping_outputs.items() if k != "root"}

    ids_customer = set(_col_values(paths["customer"], "id"))
    ids_store = set(_col_values(paths["store"], "id"))
    ids_product = set(_col_values(paths["product"], "id"))
    ids_transaction = set(_col_values(paths["transaction"], "id"))

    assert len(ids_customer) == EXPECTED_ROWS
    assert len(ids_store) == EXPECTED_ROWS
    assert len(ids_product) == EXPECTED_ROWS
    assert len(ids_transaction) == EXPECTED_ROWS

    rows_customer = _read_rows(paths["customer"])
    by_id_email = {r["id"]: r["email"] for r in rows_customer}
    assert len(by_id_email) == EXPECTED_ROWS
    assert all(r["email"] == by_id_email[r["id"]] for r in rows_customer)

    emails = _col_values(paths["customer"], "email")
    assert len(emails) == len(set(emails))

    rows_product = _read_rows(paths["product"])
    by_id_title = {r["id"]: r["title"] for r in rows_product}
    assert len(by_id_title) == EXPECTED_ROWS
    assert all(r["title"] == by_id_title[r["id"]] for r in rows_product)

    sku = _col_values(paths["product"], "sku")
    assert len(sku) == len(set(sku))

    for cid in _col_values(paths["transaction"], "customer_id"):
        assert cid in ids_customer
    for sid in _col_values(paths["transaction"], "store_id"):
        assert sid in ids_store

    carrier_hint = {
        "pending": "defer",
        "paid": "standard",
        "fulfilled": "express",
    }
    for row in _read_rows(paths["transaction"]):
        assert carrier_hint[row["order_status"]] == row["carrier_hint"]

    product_price = {r["id"]: int(r["unit_price_cents"]) for r in _read_rows(paths["product"])}
    order_rows = _read_rows(paths["transaction_orders"])
    assert len(order_rows) == EXPECTED_ROWS
    for row in order_rows:
        assert row["transaction_id"] in ids_transaction
        assert row["product_id"] in ids_product
        expected = int(row["qty"]) * product_price[row["product_id"]]
        assert int(row["line_subtotal_cents"]) == expected


def test_domain_shopping_product_price_display_matches_cents(
    domain_shopping_outputs: dict[str, Path],
) -> None:
    for row in _read_rows(domain_shopping_outputs["product"]):
        cents = int(row["unit_price_cents"])
        assert row["price_display"] == f"{cents / 100:.2f}"


def test_domain_shopping_bind_to_order_status_status_stamp(
    domain_shopping_outputs: dict[str, Path],
) -> None:
    """``status_stamp`` binds to ``order_status``: same status always maps to the same stamp."""
    stamp_by_status: dict[str, str] = {}
    for row in _read_rows(domain_shopping_outputs["transaction"]):
        status = row["order_status"]
        stamp = row["status_stamp"]
        if status in stamp_by_status:
            assert stamp_by_status[status] == stamp
        else:
            stamp_by_status[status] = stamp


def test_domain_shopping_bind_to_store_id_shelf_and_line_tag(
    domain_shopping_outputs: dict[str, Path],
) -> None:
    """``shelf_label`` and ``line_tag`` bind to ``store_id``: repeated store gets consistent values."""
    by_store: dict[str, tuple[str, str]] = {}
    for row in _read_rows(domain_shopping_outputs["product"]):
        sid = row["store_id"]
        pair = (row["shelf_label"], row["line_tag"])
        if sid in by_store:
            assert by_store[sid] == pair
        else:
            by_store[sid] = pair


def test_domain_shopping_product_store_fk_and_transaction_store_fk(
    domain_shopping_outputs: dict[str, Path],
) -> None:
    ids_store = set(_col_values(domain_shopping_outputs["store"], "id"))
    for row in _read_rows(domain_shopping_outputs["product"]):
        assert row["store_id"] in ids_store
    for row in _read_rows(domain_shopping_outputs["transaction"]):
        assert row["store_id"] in ids_store


def test_domain_shopping_store_code_format_and_uniqueness(
    domain_shopping_outputs: dict[str, Path],
) -> None:
    pattern = re.compile(r"^ST-\d{8}$")
    codes = _col_values(domain_shopping_outputs["store"], "store_code")
    assert len(codes) == len(set(codes))
    for c in codes:
        assert pattern.match(c), f"unexpected store_code shape: {c!r}"


def test_domain_shopping_created_at_nonempty(
    domain_shopping_outputs: dict[str, Path],
) -> None:
    for key in ("customer", "store", "product", "transaction", "transaction_orders"):
        for row in _read_rows(domain_shopping_outputs[key]):
            assert row["created_at"].strip(), f"{key}: empty created_at"


def test_domain_shopping_transaction_orders_qty_and_price_bounds(
    domain_shopping_outputs: dict[str, Path],
) -> None:
    for row in _read_rows(domain_shopping_outputs["transaction_orders"]):
        q = int(row["qty"])
        assert 1 <= q <= 4
    for row in _read_rows(domain_shopping_outputs["product"]):
        cents = int(row["unit_price_cents"])
        assert 99 <= cents <= 4999


def test_domain_shopping_provider_value_subsets(
    domain_shopping_outputs: dict[str, Path],
) -> None:
    """Spot-check catalog / seed–backed columns stay within expected vocabularies."""
    allowed_segment = {"b2c", "b2b", "wholesale"}
    allowed_channel = {"web", "pos", "mobile"}
    allowed_status = {"pending", "paid", "fulfilled"}
    allowed_brands = {"Acme Co", "Globex", "Initech", "Umbrella"}

    for row in _read_rows(domain_shopping_outputs["customer"]):
        assert row["segment"] in allowed_segment
    for row in _read_rows(domain_shopping_outputs["transaction"]):
        assert row["channel"] in allowed_channel
        assert row["order_status"] in allowed_status
    for row in _read_rows(domain_shopping_outputs["product"]):
        assert row["brand_swatch"] in allowed_brands


def test_domain_shopping_receipt_line_prefix(
    domain_shopping_outputs: dict[str, Path],
) -> None:
    for row in _read_rows(domain_shopping_outputs["transaction"]):
        assert row["receipt_line"].startswith("rcpt-")
