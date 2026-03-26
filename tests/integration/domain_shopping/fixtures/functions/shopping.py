"""Scenario-local helpers for the shopping domain integration."""

from __future__ import annotations

from typing import Any

from faux.core.context import GenerationContext


def format_price_display(cents: int) -> str:
    return f"{int(cents) / 100:.2f}"


def line_subtotal_cents(
    qty: int,
    product_id: str,
    context: GenerationContext,
) -> int:
    rows: list[dict[str, Any]] = context.generated_tables.get("product", [])
    for row in rows:
        if str(row["id"]) == str(product_id):
            return int(qty) * int(row["unit_price_cents"])
    raise ValueError(f"unknown product_id {product_id!r}")
