# hass-smartmeter

[![Validate](https://github.com/welworx/hass-smartmeter/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/welworx/hass-smartmeter/actions/workflows/validate.yml)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)

A Home Assistant custom integration that reads consumption and production
readings from a [smartmeter-fetch](https://github.com/welworx/smartmeter-fetch)
instance's `/v1` HTTP API and imports them into HA's Energy dashboard as
long-term statistics — one stream per metering point.

This integration never talks to a grid operator portal or a database
directly. It only ever calls smartmeter-fetch's versioned API, so it works
the same way regardless of which grid operator or storage backend
smartmeter-fetch is configured with.

> **Disclaimer:** Built for **personal, educational use only.** Not
> affiliated with, endorsed by, or supported by Home Assistant, Netz NÖ,
> EVN, or any other grid operator. Use at your own risk.

## Status

Config flow, the coordinator, and statistics import are implemented:
setting up the integration discovers metering points from a running
smartmeter-fetch instance and imports readings into the Energy dashboard
as long-term statistics, one stream per point.

Not in the HACS default store yet — install via HACS as a custom
repository, or manually (see Installation below). Two things are still
needed before a default-store submission:

- **A GitHub release.** HACS uses release tags to offer version selection;
  none has been cut yet.
- **Brand assets** (icon/logo) submitted to
  [home-assistant/brands](https://github.com/home-assistant/brands) —
  required for the default store, not for a custom-repository install.
  Until this lands, the HACS validation workflow's `brands` check stays
  disabled (`ignore: brands` in `.github/workflows/validate.yml`).

(The repository description, topics, and issue tracker HACS also checks
for are already in place.)

## Requirements

A running [smartmeter-fetch](https://github.com/welworx/smartmeter-fetch)
instance reachable from Home Assistant.

## Installation

**Via [HACS](https://hacs.xyz/) (custom repository):**

1. HACS → the "⋮" menu → **Custom repositories**
2. Add `https://github.com/welworx/hass-smartmeter`, category **Integration**
3. Find "Smartmeter" in HACS and install it, then restart Home Assistant

**Manually:** no `git clone` needed — download the repository as a ZIP
(GitHub's **Code → Download ZIP**, or a release archive once one exists)
and copy the `custom_components/smartmeter` folder into your Home
Assistant config's `custom_components/` directory (creating it if it
doesn't exist yet), then restart Home Assistant.

Either way, finish setup under **Settings → Devices & Services → Add
Integration → Smartmeter**, entering your smartmeter-fetch instance's base
URL.
