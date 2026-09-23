# End-to-end testing against Datadog

Unit and integration tests never talk to Datadog (integration tests replay VCR cassettes).
This is the manual flow for proving the client works against a real org: run the Agent in
Docker, send a metric through `datadog.statsd`, post an event through `datadog.api`, then
confirm both in the API and in the Datadog UI.

Everything below was verified on Python 3.12 with Agent 7 and the demo org (`datadoghq.com`).

## Prerequisites

| Env var | Purpose |
| --- | --- |
| `DD_API_KEY` | Agent intake + `api.Event.create` |
| `DD_APP_KEY` | `api.Event.get` / `api.Metric.query` read-back |
| `DD_SITE` | optional, default `datadoghq.com` |

Docker must be available. The Agent image is `gcr.io/datadoghq/agent:7` (~1 GB, cached after first pull).

## 1. Start the Agent

```sh
docker run -d --name dd-agent \
  -e DD_API_KEY="$DD_API_KEY" \
  -e DD_SITE=datadoghq.com \
  -e DD_HOSTNAME=devin-datadogpy-e2e \
  -e DD_DOGSTATSD_NON_LOCAL_TRAFFIC=true \
  -p 8125:8125/udp \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /proc/:/host/proc/:ro \
  -v /sys/fs/cgroup/:/host/sys/fs/cgroup:ro \
  gcr.io/datadoghq/agent:7
```

`DD_HOSTNAME` pins the host the metric is reported under (otherwise the Agent uses the container id).
`-p 8125:8125/udp` exposes DogStatsD to the host so `datadog.statsd` can reach it at `127.0.0.1:8125`.

Wait ~30 s, then confirm the key was accepted:

```sh
docker exec dd-agent agent status | grep -A2 "API Keys status"
#   API key ending with xxxx: API Key valid
```

## 2. Send a metric and an event

`scripts/e2e_smoke.py` does the whole round trip and exits non-zero on failure:

```sh
.venv/bin/python scripts/e2e_smoke.py
```

It

1. tags everything with a fresh `run_id:<hex>` so runs never collide,
2. sends `datadogpy.e2e.smoke` (gauge, value 42) and `datadogpy.e2e.smoke.count` (counter) via `statsd` to the Agent,
3. posts an event titled `datadogpy e2e smoke <run_id>` via `api.Event.create`,
4. polls `api.Event.get` and `api.Metric.query` until both are visible (events index in seconds,
   metrics take 1–2 minutes; bounded by `E2E_QUERY_TIMEOUT`, default 240 s),
5. prints Metric Explorer / Event Explorer / Infrastructure URLs for that `run_id`.

Typical output:

```
run_id=2bfcf396 hostname=devin-datadogpy-e2e site=datadoghq.com
sent gauge datadogpy.e2e.smoke=42 and counter datadogpy.e2e.smoke.count via DogStatsD
posted event id=8822925208839464509 title='datadogpy e2e smoke 2bfcf396'
waiting (event=False metric=False)...
event readback OK
metric readback OK: 1 point(s), last=[1790150180000.0, 42.0]

Verify in the UI:
  metric : https://app.datadoghq.com/metric/explorer?exp_metric=datadogpy.e2e.smoke&exp_scope=run_id:2bfcf396&exp_agg=avg
  event  : https://app.datadoghq.com/event/explorer?query=tags:run_id:2bfcf396
  host   : https://app.datadoghq.com/infrastructure?host=devin-datadogpy-e2e
```

The same thing by hand, if you want to poke at a single call:

```python
from datadog import initialize, statsd, api
initialize(api_key=..., app_key=..., statsd_host="127.0.0.1", statsd_port=8125)
statsd.gauge("datadogpy.e2e.smoke", 42, tags=["source:manual"])
statsd.flush()
api.Event.create(title="hello from datadogpy", text="manual test", tags=["source:manual"])
```

## 3. Verify in the Datadog UI

Log in to <https://app.datadoghq.com> as `sohil.kshirsagar+bot@cognition.ai` (password in the
`DATADOG_UI_PASSWORD` secret; the Devin browser profile is normally already logged in).

* **Metric** – open the `metric :` URL printed by the script (Metrics → Explorer). You should see a
  flat line at 42 for `datadogpy.e2e.smoke` scoped to the run's `run_id` tag. Alternatively
  Metrics → Summary, search `datadogpy.e2e.smoke`.
* **Event** – open the `event :` URL (Events → Explorer). One event titled
  `datadogpy e2e smoke <run_id>` with tags `source:datadogpy-e2e`, `run_id:<run_id>`, host
  `devin-datadogpy-e2e`. Widen the time picker to "Past 1 Hour" if the default window is too narrow.
* **Host** – Infrastructure → Host Map / Infrastructure List shows `devin-datadogpy-e2e` while the
  Agent is running (disappears a few hours after it stops).

## Troubleshooting

* `API Key invalid` in `agent status` – wrong `DD_API_KEY` or wrong `DD_SITE`.
* Metric never becomes queryable – check `docker exec dd-agent agent status | grep -A20 DogStatsD`
  for `Udp Packets` increasing; if not, DogStatsD is not reachable from the host (missing
  `-p 8125:8125/udp` or `DD_DOGSTATSD_NON_LOCAL_TRAFFIC`).
* `api.Event.get` returns `No event matches that event_id` right after creation – normal for a few
  seconds; the script retries.
* Event visible in API but not in Explorer – widen the time range; Explorer defaults to a short window.

## Cleanup

```sh
docker rm -f dd-agent
```
