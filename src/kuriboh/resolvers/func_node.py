from __future__ import annotations

import difflib
import inspect
from importlib import import_module
from typing import Any
from collections.abc import Callable

from ..core.context import GenerationContext
from ..core.exceptions import FuncLoadError
from ..parsers.schema import COL_REF_PATTERN
from .base import BaseResolver


def _suggest_similar(name: str, candidates: list[str], cutoff: float = 0.6) -> str | None:
    """Return a 'Did you mean X?' suggestion if there is a close match."""
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=cutoff)
    if not matches:
        return None
    return f"Did you mean '{matches[0]}'?"


def _load_callable(path: str) -> Callable[..., Any]:
    """
    Import and return the callable at '<module>.<attr>'.

    Raises FuncLoadError with a clear message when the module is missing,
    the attribute does not exist, or the attribute is not callable.
    """
    if "." not in path:
        raise FuncLoadError(
            f"Invalid func path '{path}'.",
            path,
            suggestion="Use '<module>.<callable>' (e.g. 'test.country_of_origin').",
        )

    module_name, attr_name = path.rsplit(".", 1)

    try:
        module = import_module(module_name)
    except ModuleNotFoundError as e:
        raise FuncLoadError(
            f"Function '{path}' could not be loaded: module '{module_name}' does not exist.",
            path,
            suggestion="Check that the module path is correct (e.g. 'test.country_of_origin' for the 'test' module in the functions package).",
        ) from e

    try:
        obj = getattr(module, attr_name)
    except AttributeError:
        candidates = [x for x in dir(module) if not x.startswith("_")]
        raise FuncLoadError(
            f"Function '{path}' could not be loaded: '{attr_name}' does not exist in module '{module_name}'.",
            path,
            suggestion=_suggest_similar(attr_name, candidates),
        )

    if not callable(obj):
        raise FuncLoadError(
            f"Function '{path}' could not be loaded: '{attr_name}' in module '{module_name}' is not callable.",
            path,
            suggestion="Ensure the name refers to a function or class that can be called.",
        )

    return obj


def _resolve_col_refs(params: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    """
    Replace any column reference string values in params (template {{ col("name") }})
    with the live value from the current row.
    Called at generation time; the DAG guarantees referenced columns are already resolved.
    """
    resolved: dict[str, Any] = {}
    for k, v in params.items():
        if isinstance(v, str):
            m = COL_REF_PATTERN.fullmatch(v.strip())
            if m:
                col_name = m.group(1)
                if col_name not in row:
                    raise ValueError(
                        f"{{ col('{col_name}') }} referenced in func params "
                        f"but '{col_name}' has not been generated yet"
                    )
                resolved[k] = row[col_name]
                continue
        resolved[k] = v
    return resolved


def _call_with_supported_kwargs(
    func: Callable[..., Any],
    params: dict[str, Any],
    context: GenerationContext,
    row: dict[str, Any],
) -> Any:
    """
    Resolve column reference templates, then call func with resolved params.
    Injects context and row into kwargs only if the function signature accepts them.
    """
    kwargs = _resolve_col_refs(params, row)
    try:
        sig = inspect.signature(func)
    except ValueError:
        return func(**kwargs)
    names = set(sig.parameters)
    if "context" in names:
        kwargs["context"] = context
    if "row" in names:
        kwargs["row"] = row
    return func(**kwargs)


class FuncResolver(BaseResolver):
    """
    Resolver that calls a user-defined Python function for each value.

    Schema: type: "$func", func: "<module>.<callable>", params: { ... }.
    The callable is imported once at build time. Optional params "context"
    and "row" are injected at runtime if the function signature accepts them.
    """

    def __init__(
        self,
        func_path: str,
        params: dict[str, Any] | None = None,
        bind_to_col: str | None = None,
        unique: bool = False,
        pk_cache_key: str | None = None,
    ) -> None:
        super().__init__(
            bind_to_col=bind_to_col,
            cache_key=f"func.{func_path}",
            unique=unique,
            pk_cache_key=pk_cache_key,
        )
        self._func_path = func_path
        self._params = params or {}
        self._func = _load_callable(func_path)

    def _generate(self, context: GenerationContext, row: dict[str, Any]) -> Any:
        return _call_with_supported_kwargs(
            self._func, self._params, context, row
        )
