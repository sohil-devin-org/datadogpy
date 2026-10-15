# Unless explicitly stated otherwise all files in this repository are licensed under the BSD-3-Clause License.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2015-Present Datadog, Inc
import logging
import pytest
import sys
import unittest

from unittest.mock import patch

from datadog.util.compat import conditional_lru_cache

class TestConditionalLRUCache(unittest.TestCase):
    def test_normal_usage(self):
        @conditional_lru_cache
        def test_function(some_string, num1, num2, num3):
            return (some_string, num1 + num2 + num3)

        for idx in range(600):
            self.assertEqual(
                test_function("abc", idx, idx*2, idx *3),
                ("abc", idx + idx * 2 + idx *3),
            )

    def test_var_args(self):
        @conditional_lru_cache
        def test_function(*args):
            return sum(list(args))

        args = []
        for idx in range(100):
            args.append(idx)
            self.assertEqual(
                test_function(*args),
                sum(args),
            )

    # pylint: disable=no-self-use
    def test_debug_log(self):
        test_object_logger = logging.getLogger('datadog.util')
        with patch.object(test_object_logger, 'debug') as mock_debug:
            @conditional_lru_cache
            def test_function():
                pass

            test_function()

            mock_debug.assert_called_once()

def test_slow_imports(monkeypatch):
    # We should lazy load certain modules to avoid slowing down the startup
    # time when running in a serverless environment.  This test will fail if
    # any of those modules are imported during the import of datadogpy.

    blocklist = [
        'configparser',
        'email.mime.application',
        'email.mime.multipart',
        'importlib.metadata',
        'importlib_metadata',
        'logging.handlers',
        'multiprocessing',
        'urllib.request',
    ]

    class BlockListFinder:
        def find_spec(self, fullname, *args):
            for lib in blocklist:
                if fullname == lib:
                    raise ImportError('module %s was imported!' % fullname)
            return None

    monkeypatch.setattr('sys.meta_path', [BlockListFinder()] + sys.meta_path)

    for mod in sys.modules.copy():
        if mod in blocklist or mod.startswith('datadog'):
            del sys.modules[mod]

    import datadog


def test_backwards_compatible_aliases():
    # These names are kept as Python 3 aliases so that existing imports keep working.
    import builtins
    import collections
    import configparser
    import inspect
    import io
    import logging
    import time
    import typing
    import urllib.parse
    import urllib.request

    from datadog.util import compat

    assert compat.builtins is builtins
    assert compat.IterableUserDict is collections.UserDict
    assert compat.StringIO is io.StringIO
    assert compat.urlparse is urllib.parse.urlparse
    assert compat.url_lib.urlopen is urllib.request.urlopen
    assert compat.configparser.ConfigParser is configparser.ConfigParser
    assert isinstance(compat.ConfigParser(), configparser.ConfigParser)
    assert compat.imap is map
    assert compat.get_input is input
    assert compat.text is str
    assert list(compat.iteritems({"a": 1})) == [("a", 1)]
    assert compat.iternext(iter([1, 2])) == 1
    assert compat.iscoroutinefunction is inspect.iscoroutinefunction
    assert compat.NullHandler is logging.NullHandler
    assert compat.monotonic is time.monotonic
    assert compat.cast(int, "x") == "x"
    assert compat.cast is typing.cast
    assert compat.is_p3k() is True
    assert compat.is_higher_py32() is True
    assert compat.is_higher_py35() is True
    assert compat.is_pypy() is ("__pypy__" in sys.builtin_module_names)
    assert compat.log is logging.getLogger("datadog.util")
    assert isinstance(compat.LazyLoader("json"), compat.LazyLoader)
