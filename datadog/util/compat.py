# Unless explicitly stated otherwise all files in this repository are licensed under the BSD-3-Clause License.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2015-Present Datadog, Inc
# flake8: noqa
"""
Deprecated: Python 2/3 compatibility aliases, kept only for backwards compatibility.

datadogpy now requires Python 3.9+. New code should use the standard library directly;
every name below is a thin alias to its Python 3 equivalent.
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
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, Tuple, TypeVar, cast
from urllib.parse import urlparse

if TYPE_CHECKING:
    from configparser import ConfigParser as ConfigParserType  # noqa: F401

K = TypeVar("K")
V = TypeVar("V")

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


url_lib = LazyLoader("urllib.request")
configparser = LazyLoader("configparser")


def ConfigParser() -> "ConfigParserType":
    return configparser.ConfigParser()


imap = map
get_input = input
text = str


def iteritems(d: Dict[K, V]) -> Iterator[Tuple[K, V]]:
    return iter(d.items())


def iternext(iter: Iterator[V]) -> V:
    return next(iter)


def _is_py_version_higher_than(major: int, minor: int = 0) -> bool:
    """
    Assert that the Python version is higher than `$maj.$min`.
    """
    return sys.version_info >= (major, minor)


def is_p3k() -> bool:
    """
    Assert that Python is version 3 or higher.
    """
    return _is_py_version_higher_than(3)


def is_higher_py32() -> bool:
    """
    Assert that Python is version 3.2 or higher.
    """
    return _is_py_version_higher_than(3, 2)


def is_higher_py35() -> bool:
    """
    Assert that Python is version 3.5 or higher.
    """
    return _is_py_version_higher_than(3, 5)


def is_pypy() -> bool:
    """
    Assert that PyPy is being used
    """
    return "__pypy__" in sys.builtin_module_names


def conditional_lru_cache(func: Callable[..., V]) -> Callable[..., V]:
    """
    A decorator that enables a lru_cache of size 512.
    """
    log.debug("Enabling LRU cache for function %s", func.__name__)

    return lru_cache(maxsize=512)(func)
