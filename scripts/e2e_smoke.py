#!/usr/bin/env python3
# Unless explicitly stated otherwise all files in this repository are licensed under the BSD-3-Clause License.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2015-Present Datadog, Inc
"""
End-to-end smoke test against a real Datadog org. See E2E_TESTING.md.

Sends one DogStatsD metric through a locally running Agent and posts one event
through the HTTP API, then reads both back through the API and prints the UI
URLs where they can be verified.

Environment:
  DD_API_KEY   required
  DD_APP_KEY   required (read-back + UI links)
  DD_SITE      default datadoghq.com
  DD_AGENT_HOST / DD_DOGSTATSD_PORT   default 127.0.0.1 / 8125
  E2E_HOSTNAME default devin-datadogpy-e2e (must match the Agent's DD_HOSTNAME)
"""
from __future__ import print_function

import os
import sys
import time
import uuid

from datadog import api, initialize, statsd

METRIC = "datadogpy.e2e.smoke"
EVENT_AGG_KEY = "datadogpy-e2e-smoke"
QUERY_TIMEOUT_S = int(os.environ.get("E2E_QUERY_TIMEOUT", "240"))


def main():
    api_key = os.environ.get("DD_API_KEY")
    app_key = os.environ.get("DD_APP_KEY")
    if not api_key or not app_key:
        print("DD_API_KEY and DD_APP_KEY must be set", file=sys.stderr)
        return 2

    site = os.environ.get("DD_SITE", "datadoghq.com")
    hostname = os.environ.get("E2E_HOSTNAME", "devin-datadogpy-e2e")
    run_id = uuid.uuid4().hex[:8]
    tags = ["source:datadogpy-e2e", "run_id:%s" % run_id]

    initialize(
        api_key=api_key,
        app_key=app_key,
        api_host="https://api.%s" % site,
        statsd_host=os.environ.get("DD_AGENT_HOST", "127.0.0.1"),
        statsd_port=int(os.environ.get("DD_DOGSTATSD_PORT", "8125")),
        host_name=hostname,
        hostname_from_config=False,
    )

    print("run_id=%s hostname=%s site=%s" % (run_id, hostname, site))

    # 1. DogStatsD -> Agent (UDP). Send a few points so the Agent flushes at least one.
    for i in range(3):
        statsd.gauge(METRIC, 42, tags=tags)
        statsd.increment(METRIC + ".count", tags=tags)
        time.sleep(1)
    statsd.flush()
    print("sent gauge %s=42 and counter %s.count via DogStatsD" % (METRIC, METRIC))

    # 2. Event -> HTTP API.
    title = "datadogpy e2e smoke %s" % run_id
    ev = api.Event.create(
        title=title,
        text="Posted by scripts/e2e_smoke.py via datadog.api",
        tags=tags,
        alert_type="info",
        aggregation_key=EVENT_AGG_KEY,
        host=hostname,
    )
    event_id = ev.get("event", {}).get("id")
    if not event_id:
        print("event create failed: %r" % (ev,), file=sys.stderr)
        return 1
    print("posted event id=%s title=%r" % (event_id, title))

    # 3. Read back through the API. Events index within seconds, metrics take ~1-2 minutes.
    query = "avg:%s{run_id:%s}" % (METRIC, run_id)
    deadline = time.time() + QUERY_TIMEOUT_S
    event_ok = metric_ok = False
    while time.time() < deadline and not (event_ok and metric_ok):
        if not event_ok:
            got = api.Event.get(event_id)
            event_ok = str(got.get("event", {}).get("id")) == str(event_id)
            if event_ok:
                print("event readback OK")
        if not metric_ok:
            now = int(time.time())
            res = api.Metric.query(start=now - 600, end=now, query=query)
            series = res.get("series") or []
            metric_ok = bool(series and series[0].get("pointlist"))
            if metric_ok:
                pts = series[0]["pointlist"]
                print("metric readback OK: %d point(s), last=%r" % (len(pts), pts[-1]))
        if not (event_ok and metric_ok):
            print("waiting (event=%s metric=%s)..." % (event_ok, metric_ok))
            time.sleep(15)
    if not (event_ok and metric_ok):
        print("readback incomplete after %ss (event=%s metric=%s)" % (QUERY_TIMEOUT_S, event_ok, metric_ok),
              file=sys.stderr)
        return 1

    app = "https://app.%s" % site
    print("\nVerify in the UI:")
    print("  metric : %s/metric/explorer?exp_metric=%s&exp_scope=run_id:%s&exp_agg=avg" % (app, METRIC, run_id))
    print("  event  : %s/event/explorer?query=tags:run_id:%s" % (app, run_id))
    print("  host   : %s/infrastructure?host=%s" % (app, hostname))
    return 0


if __name__ == "__main__":
    sys.exit(main())
