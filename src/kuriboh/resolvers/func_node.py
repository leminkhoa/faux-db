from __future__ import annotations

import difflib
import inspect
from importlib import import_module
from typing import Any, Callable, Dict

from ..core.context import GenerationContext
from ..core.exceptions import FuncLoadError
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
            suggestion=f"Check that the module path is correct (e.g. 'test.country_of_origin' for the 'test' module in the functions package).",
        ) from e

    try:
        obj = getattr(module, attr_name)
    except AttributeError:
        candidates = [x for x in dir(module) if not x.startswith("_")]
        suggestion = _suggest_similar(attr_name, candidates)
        if suggestion:
            msg = f"Function '{path}' could not be loaded: '{attr_name}' does not exist in module '{module_name}'."
        else:
            msg = f"Function '{path}' could not be loaded: '{attr_name}' does not exist in module '{module_name}'."
        raise FuncLoadError(msg, path, suggestion=suggestion)

    if not callable(obj):
        raise FuncLoadError(
            f"Function '{path}' could not be loaded: '{attr_name}' in module '{module_name}' is not callable.",
            path,
            suggestion="Ensure the name refers to a function or class that can be called.",
        )

    return obj


def _call_with_supported_kwargs(
    func: Callable[..., Any],
    params: Dict[str, Any],
    context: GenerationContext,
    row: Dict[str, Any],
) -> Any:
    """
    Call func with params plus optional context/row if the callable accepts them.
    Avoids TypeError when the user function does not declare context or row.
    """
    kwargs = dict(params)
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
        params: Dict[str, Any] | None = None,
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

    def _generate(self, context: GenerationContext, row: Dict[str, Any]) -> Any:
        return _call_with_supported_kwargs(
            self._func, self._params, context, row
        )
