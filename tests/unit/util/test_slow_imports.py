# Unless explicitly stated otherwise all files in this repository are licensed under the BSD-3-Clause License.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2015-Present Datadog, Inc
import sys


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
