# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## What this is

A Home Assistant custom integration (HACS) that imports consumption and
production readings into the HA Energy dashboard. It is the *only* intended
consumer of [smartmeter-fetch](https://github.com/welworx/smartmeter-fetch)'s
`/v1` HTTP API.

## Critical constraint: no direct storage access

This repo must never talk to a database, JSON file, or grid operator portal
directly — only to smartmeter-fetch's `/v1` API
(`GET /v1/points`, `GET /v1/readings?point=<id>&since=<RFC3339>`). The whole
point of the split between the two repos is that storage backend and grid
operator are invisible here. If a task seems to require reading storage
directly, it belongs in smartmeter-fetch instead.

## Critical constraint: delayed data and statistics buckets

Upstream readings can arrive several days late. Always resume reads from
the last successfully imported statistic's timestamp (via
`recorder.statistics.get_last_statistics` or equivalent), never from a
fixed "yesterday" offset — otherwise late data for an already-processed day
gets silently skipped. When importing, use
`async_add_external_statistics` with the reading's own interval timestamp,
not the time the import ran, so a late-arriving Tuesday reading lands in
Tuesday's bucket even if fetched on Friday.

## Layout

- `custom_components/smartmeter/config_flow.py` — asks for the
  smartmeter-fetch base URL, discovers points via `GET /v1/points`.
- `custom_components/smartmeter/coordinator.py` — polls
  `GET /v1/readings`.
- `custom_components/smartmeter/statistics.py` — hourly-buckets readings
  and imports them as long-term statistics, one stream per metering point.

## Commands

```bash
ruff check .
```

## Disclaimer

Personal, educational-use tool. Not affiliated with or endorsed by Home
Assistant or any grid operator.
