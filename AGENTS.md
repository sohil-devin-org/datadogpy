# Working in datadogpy

Python client for the Datadog API (`datadog.api`), DogStatsD (`datadog.dogstatsd`),
ThreadStats (`datadog.threadstats`) and the `dog`/`dogwrap`/`dogshell` CLIs.
Pure Python, no compiled extensions. Python 3.9+ only (`requires-python = ">=3.9"` in `pyproject.toml`);
do not add Python 2 shims, `sys.version_info` guards for versions below 3.9, `from __future__` imports,
or `u""` string prefixes.

## Setup

```sh
python3 -m venv .venv
.venv/bin/pip install -e . click freezegun mock pytest pytest-vcr python-dateutil vcrpy \
  flake8==7.1.2 mypy==1.14.1 -r doc/requirements.txt
```

## Verify before opening a PR

```sh
.venv/bin/flake8 datadog                              # max-line-length 120, config in tox.ini
.venv/bin/mypy --config-file mypy.ini datadog         # types are `# type:` comments today
.venv/bin/pytest -q tests/unit                        # ~90s
.venv/bin/pytest -q tests/integration -m "not admin_needed" --vcr-record=none   # replays cassettes, no creds
.venv/bin/sphinx-build -b html doc/source doc/_build/html
```

Scope re-runs to the file you touched (`pytest tests/unit/dogstatsd/test_statsd.py -k <name>`) while
iterating; run the full set once before pushing.

`tests/unit/dogstatsd/test_statsd.py::TestDogStatsd::test_dedicated_udp6_telemetry_dest` binds
`('localhost', 0)` on an AF_INET6 socket and fails on hosts where `localhost` has no `::1` entry
(GitHub runners are fine). It is not caused by your change unless you touched IPv6 handling.

## Rules

- Never delete or weaken a test to make CI pass. If a test is wrong, say so in the PR and fix the test explicitly.
- DogStatsD wire format (`metric:value|type|@rate|#tags|c:container`) and telemetry metric names are a
  protocol. Changes must be covered by a unit test asserting the exact bytes sent.
- `tests/integration` runs against recorded VCR cassettes in CI. Do not re-record cassettes; that needs
  live Datadog credentials and the `ci/integrations` label.
- Add a `changelog/*` label to every PR (`changelog/Fixed`, `changelog/Changed`, `changelog/Added`,
  `changelog/no-changelog`, ...). The `Ensure labels` check fails without one.
- Keep PRs to one package where possible: `datadog/api`, `datadog/dogstatsd`, `datadog/dogshell`,
  `datadog/threadstats`, `datadog/util`, `tests/`.

## CI

- `quick-check`: one Python 3.12 job with everything in "Verify" above (~3 min). Runs on every PR.
- `test`: lint + 7-interpreter matrix (3.9–3.14, pypy3.10). Runs on every PR.
- `CodeQL`: python analysis on PRs to `master`. All three `github/codeql-action/*` steps must be on
  the same major version.
- `Ensure labels`: requires a `changelog/*` label.
