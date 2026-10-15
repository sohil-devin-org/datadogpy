# Unless explicitly stated otherwise all files in this repository are licensed under the BSD-3-Clause License.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2015-Present Datadog, Inc
# flake8: noqa
"""
Python 3 aliases kept for backwards compatibility.

datadogpy used to support Python 2 and this module held the py2/py3 shims. Python 3.9+ is now
required, so every name below is a thin alias for its standard library equivalent. They remain
importable because existing code (inside and outside datadogpy) imports them; new code should use
the standard library directly.
"""
import builtins
import logging
import sys
from collections import UserDict as IterableUserDict
from functools import lru_cache
from inspect import iscoroutinefunction
from io import StringIO
from logging import NullHandler
from time import monotonic
from typing import Any, Callable, Dict, Iterator, Tuple, TYPE_CHECKING, TypeVar, cast
from urllib.parse import urlparse

if TYPE_CHECKING:
    from configparser import ConfigParser as ConfigParserType  # noqa: F401

K = TypeVar('K')
V = TypeVar('V')


# Logging
log = logging.getLogger("datadog.util")


class LazyLoader:
    def __init__(self, module_name: str) -> None:
        self.module_name = module_name

    def __getattr__(self, name: str) -> Any:
        # defer the importing of the module to when one of its attributes
        # is accessed
        import importlib
        mod = importlib.import_module(self.module_name)
        return getattr(mod, name)


# `urllib.request` and `configparser` are slow to import; keep them lazy so that
# `import datadog` stays cheap (e.g. in serverless environments).
url_lib = LazyLoader('urllib.request')
configparser = LazyLoader('configparser')


def ConfigParser() -> "ConfigParserType":
    return configparser.ConfigParser()


imap = map
get_input = input
text = str


def iteritems(d: Dict[K, V]) -> Iterator[Tuple[K, V]]:
    return iter(d.items())


def iternext(iter: Iterator[V]) -> V:
    return next(iter)


def is_p3k() -> bool:
    """
    Assert that Python is version 3 or higher. Always True on supported versions.
    """
    return True


def is_higher_py32() -> bool:
    """
    Assert that Python is version 3.2 or higher. Always True on supported versions.
    """
    return True


def is_higher_py35() -> bool:
    """
    Assert that Python is version 3.5 or higher. Always True on supported versions.
    """
    return True


def is_pypy() -> bool:
    """
    Assert that PyPy is being used.
    """
    return "__pypy__" in sys.builtin_module_names


def conditional_lru_cache(func: Callable[..., V]) -> Callable[..., V]:
    """
    Wrap `func` in a `functools.lru_cache` of size 512.

    The cache used to be conditional on Python >= 3.2; it is now always enabled.
    """
    log.debug("Enabling LRU cache for function %s", func.__name__)

    return lru_cache(maxsize=512)(func)
