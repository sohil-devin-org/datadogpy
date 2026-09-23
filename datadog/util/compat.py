# Unless explicitly stated otherwise all files in this repository are licensed under the BSD-3-Clause License.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2015-Present Datadog, Inc
# flake8: noqa
"""
Legacy Python 2/3 compatibility shims.

Every name here has a direct standard-library equivalent on Python 3.9+; callers
should import that instead. This module only exists so that packages that have not
been migrated yet keep importing.

`configparser` and `urllib.request` are deliberately imported lazily: importing them
eagerly slows down cold starts in serverless environments (see
`tests/unit/util/test_compat.py::test_slow_imports`).
"""
import builtins
import importlib
import logging
import sys
from collections import UserDict as IterableUserDict
from functools import lru_cache
from inspect import iscoroutinefunction
from io import StringIO
from logging import NullHandler
from time import monotonic
from typing import Any, Callable, Dict, Iterator, Tuple, Type, TypeVar, TYPE_CHECKING, cast
from urllib.parse import urlparse

if TYPE_CHECKING:
    from configparser import ConfigParser as ConfigParserType  # noqa: F401

K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T")

log = logging.getLogger("datadog.util")


class LazyLoader(object):
    def __init__(self, module_name):
        # type: (str) -> None
        self.module_name = module_name

    def __getattr__(self, name):
        # type: (str) -> Any
        # defer the importing of the module to when one of its attributes
        # is accessed
        mod = importlib.import_module(self.module_name)
        return getattr(mod, name)


url_lib = LazyLoader("urllib.request")
configparser = LazyLoader("configparser")


def ConfigParser():
    # type: () -> ConfigParserType
    return configparser.ConfigParser()


imap = map
get_input = input
text = str


def iteritems(d):
    # type: (Dict[K, V]) -> Iterator[Tuple[K, V]]
    return iter(d.items())


def iternext(iter):
    # type: (Iterator[V]) -> V
    return next(iter)


def is_p3k():
    # type: () -> bool
    return True


def is_higher_py32():
    # type: () -> bool
    return True


def is_higher_py35():
    # type: () -> bool
    return True


def is_pypy():
    # type: () -> bool
    """
    Assert that PyPy is being used.
    """
    return "__pypy__" in sys.builtin_module_names


def conditional_lru_cache(func):
    # type: (Callable[..., V]) -> Callable[..., V]
    log.debug("Enabling LRU cache for function %s", func.__name__)
    return lru_cache(maxsize=512)(func)
