# Unless explicitly stated otherwise all files in this repository are licensed under the BSD-3-Clause License.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2015-Present Datadog, Inc
"""
Decorator `timed` for coroutine methods.
"""
# stdlib
from functools import wraps
import time
from typing import Any, Callable  # noqa: F401


def _get_wrapped_co(self, func):
    # type: (Any, Callable[..., Any]) -> Callable[..., Any]
    """
    `timed` wrapper for coroutine methods.
    """
    @wraps(func)
    async def wrapped_co(*args, **kwargs):
        # type: (*Any, **Any) -> Any
        start = time.monotonic()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            self._send(start)
    return wrapped_co
