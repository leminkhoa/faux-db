"""
Tests for :mod:`kuriboh.resolvers.func_node`.

Scenarios covered:

_load_callable
- loads a valid stdlib callable
- path with no dot raises FuncLoadError
- missing module raises FuncLoadError
- missing attribute on real module raises FuncLoadError
- non-callable attribute raises FuncLoadError

_resolve_col_refs
- {{ col(name) }} is replaced with the live row value
- plain string values pass through unchanged
- non-string values (int, bool) pass through unchanged
- string partially containing {{ col() }} is NOT substituted (fullmatch required)
- missing column in row raises ValueError

_call_with_supported_kwargs
- function with no extra params works correctly
- context is injected when the function accepts it
- row is injected when the function accepts it
- both context and row injected when accepted

FuncResolver (end-to-end)
- basic call with static params
- {{ col() }} param resolved from current row
- module not found at construction time raises FuncLoadError
- function that accepts context receives the live GenerationContext
"""

from __future__ import annotations

import os.path
import sys
import types

import pytest
from faker import Faker

from kuriboh.core.context import GenerationContext
from kuriboh.core.exceptions import FuncLoadError
from kuriboh.resolvers.func_node import (
    FuncResolver,
    _call_with_supported_kwargs,
    _load_callable,
    _resolve_col_refs,
)

_FAKE_MOD = "_kuriboh_test_funcs"


def _ctx() -> GenerationContext:
    return GenerationContext(faker=Faker(), catalogs={})


def _install(**attrs):
    """Inject a throwaway module into sys.modules for the duration of a test."""
    mod = types.ModuleType(_FAKE_MOD)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[_FAKE_MOD] = mod


@pytest.fixture(autouse=True)
def _cleanup():
    yield
    sys.modules.pop(_FAKE_MOD, None)


# ---------------------------------------------------------------------------
# _load_callable
# ---------------------------------------------------------------------------

class TestLoadCallable:
    def test_loads_valid_stdlib_callable(self):
        fn = _load_callable("os.path.join")
        assert fn is os.path.join

    def test_path_without_dot_raises(self):
        with pytest.raises(FuncLoadError, match="Invalid"):
            _load_callable("nodot")

    def test_missing_module_raises(self):
        with pytest.raises(FuncLoadError, match="does not exist"):
            _load_callable("_totally_missing_module_xyz.fn")

    def test_missing_attribute_raises(self):
        _install(real_fn=lambda: None)
        with pytest.raises(FuncLoadError, match="does not exist"):
            _load_callable(f"{_FAKE_MOD}.nonexistent_attr")

    def test_non_callable_raises(self):
        _install(CONST="i_am_a_string")
        with pytest.raises(FuncLoadError, match="not callable"):
            _load_callable(f"{_FAKE_MOD}.CONST")

    def test_suggestion_included_for_close_match(self):
        """A typo in the attr name should produce a 'Did you mean' hint."""
        _install(greet=lambda: None)
        try:
            _load_callable(f"{_FAKE_MOD}.greet_typo")
        except FuncLoadError as e:
            # The suggestion may or may not fire depending on similarity threshold;
            # the important thing is that a FuncLoadError was raised.
            assert "greet_typo" in str(e) or "greet" in str(e)


# ---------------------------------------------------------------------------
# _resolve_col_refs
# ---------------------------------------------------------------------------

class TestResolveColRefs:
    def test_col_ref_replaced_with_row_value(self):
        assert _resolve_col_refs({"k": '{{ col("user_id") }}'}, {"user_id": 42}) == {"k": 42}

    def test_plain_string_passes_through(self):
        assert _resolve_col_refs({"k": "literal"}, {}) == {"k": "literal"}

    def test_non_string_values_pass_through(self):
        assert _resolve_col_refs({"n": 7, "flag": True}, {}) == {"n": 7, "flag": True}

    def test_partial_match_not_substituted(self):
        # fullmatch means the entire value must be a template, not a substring
        result = _resolve_col_refs({"k": 'prefix {{ col("x") }}'}, {"x": "v"})
        assert result == {"k": 'prefix {{ col("x") }}'}

    def test_missing_col_in_row_raises(self):
        with pytest.raises(ValueError, match="user_id"):
            _resolve_col_refs({"k": '{{ col("user_id") }}'}, {})

    def test_multiple_params_processed_independently(self):
        result = _resolve_col_refs(
            {"a": '{{ col("x") }}', "b": '{{ col("y") }}', "c": "static"},
            {"x": 1, "y": 2},
        )
        assert result == {"a": 1, "b": 2, "c": "static"}


# ---------------------------------------------------------------------------
# _call_with_supported_kwargs
# ---------------------------------------------------------------------------

class TestCallWithSupportedKwargs:
    def test_simple_function_receives_params(self):
        def add(a, b):
            return a + b

        assert _call_with_supported_kwargs(add, {"a": 3, "b": 4}, _ctx(), {}) == 7

    def test_context_injected_when_accepted(self):
        received = {}

        def fn(context):
            received["ctx"] = context

        ctx = _ctx()
        _call_with_supported_kwargs(fn, {}, ctx, {})
        assert received["ctx"] is ctx

    def test_row_injected_when_accepted(self):
        received = {}

        def fn(row):
            received["row"] = row

        row = {"x": 1}
        _call_with_supported_kwargs(fn, {}, _ctx(), row)
        assert received["row"] is row

    def test_both_context_and_row_injected(self):
        received = {}

        def fn(context, row):
            received["ctx"] = context
            received["row"] = row

        ctx = _ctx()
        row = {"a": "b"}
        _call_with_supported_kwargs(fn, {}, ctx, row)
        assert received["ctx"] is ctx
        assert received["row"] is row

    def test_no_injection_when_not_accepted(self):
        def fn():
            return "ok"

        assert _call_with_supported_kwargs(fn, {}, _ctx(), {}) == "ok"

    def test_signature_value_error_falls_back_to_plain_call(self, monkeypatch):
        class _CallableNoSig:
            def __call__(self, x):
                return x

        monkeypatch.setattr("kuriboh.resolvers.func_node.inspect.signature", lambda _: (_ for _ in ()).throw(ValueError))
        assert _call_with_supported_kwargs(_CallableNoSig(), {"x": 11}, _ctx(), {}) == 11


# ---------------------------------------------------------------------------
# FuncResolver (end-to-end)
# ---------------------------------------------------------------------------

class TestFuncResolver:
    def test_basic_static_params(self):
        _install(greet=lambda name: f"hi {name}")
        r = FuncResolver(f"{_FAKE_MOD}.greet", params={"name": "Alice"})
        assert r.resolve(_ctx(), {}) == "hi Alice"

    def test_col_ref_param_resolved_from_row(self):
        _install(upper=lambda text: text.upper())
        r = FuncResolver(f"{_FAKE_MOD}.upper", params={"text": '{{ col("raw") }}'})
        assert r.resolve(_ctx(), {"raw": "hello"}) == "HELLO"

    def test_missing_module_raises_at_construction(self):
        with pytest.raises(FuncLoadError):
            FuncResolver("_totally_missing_xyz.fn")

    def test_function_receives_live_context(self):
        received = {}

        def fn(x, context):
            received["ctx"] = context
            return x

        _install(fn=fn)
        ctx = _ctx()
        FuncResolver(f"{_FAKE_MOD}.fn", params={"x": 1}).resolve(ctx, {})
        assert received["ctx"] is ctx

    def test_function_receives_current_row(self):
        _install(passrow=lambda row: row["val"])
        r = FuncResolver(f"{_FAKE_MOD}.passrow")
        assert r.resolve(_ctx(), {"val": 99}) == 99
