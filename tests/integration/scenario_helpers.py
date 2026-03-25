"""
Helpers for integration scenarios that put a local ``functions/`` package on ``sys.path``.

Multiple scenarios reuse the top-level name ``functions``; the first import stays in
``sys.modules``. Call :func:`clear_cached_functions_packages` before ``syspath_prepend``
and generation so the correct scenario package loads.
"""

from __future__ import annotations

import sys


def clear_cached_functions_packages() -> None:
    for key in list(sys.modules.keys()):
        if key == "functions" or key.startswith("functions."):
            del sys.modules[key]
