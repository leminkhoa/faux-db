"""
Central exception types for faux-db.

Raising these (instead of generic ValueError/TypeError) lets callers handle
specific cases (e.g. invalid $func config) and gives users clear, actionable messages.
"""

from __future__ import annotations


class FauxError(Exception):
    """Base exception for all faux-db specific errors."""



class FuncLoadError(FauxError):
    """
    Raised when a $func column references a function that cannot be loaded.

    Typical causes:
    - Module in func path does not exist (e.g. typo in module name).
    - Callable name does not exist on the module (e.g. typo in function name).
    - Referenced name is not callable (e.g. a constant instead of a function).

    Use the configured func path (e.g. "test.country_of_origin") and the error
    message to fix the schema or the functions package.
    """

    def __init__(self, message: str, func_path: str, suggestion: str | None = None) -> None:
        self.func_path = func_path
        self.suggestion = suggestion
        full = message
        if suggestion:
            full = f"{message} {suggestion}"
        super().__init__(full)
