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

Early scaffolding — repo structure, manifest, and file layout are in place;
config flow, the coordinator, and statistics import are not yet
implemented.

The HACS validation workflow's `brands` check is expected to fail until this
is submitted to the [home-assistant/brands](https://github.com/home-assistant/brands)
repository — that's only required for listing in the HACS default store, not
for installing via HACS as a custom repository.

## Requirements

A running [smartmeter-fetch](https://github.com/welworx/smartmeter-fetch)
instance reachable from Home Assistant.

## Installation (once implemented)

Via [HACS](https://hacs.xyz/) as a custom repository, or by copying
`custom_components/smartmeter` into your Home Assistant `custom_components`
directory.
