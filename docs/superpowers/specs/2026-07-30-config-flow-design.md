# Config Flow Design

## Goal

Implement `custom_components/smartmeter/config_flow.py`: the setup UI that
lets a user point this integration at a running smartmeter-fetch instance.

## Scope

In scope:
- `config_flow.py` — user setup step, reconfigure step, connection
  validation.

Out of scope (separate, later designs):
- `coordinator.py` — polling `GET /v1/readings`.
- `statistics.py` — bucketing readings and calling
  `async_add_external_statistics`.
- Any UI for selecting a subset of metering points (all discovered points
  are imported automatically — see Data flow).

## Architecture

A single-step `ConfigFlow` (`SmartmeterConfigFlow(ConfigFlow, domain=DOMAIN)`)
asks for one field, `base_url`. On submit, it validates by calling
`GET {base_url}/v1/points` — this both confirms the instance is reachable
and gives the "no points found" error case something to check. On success it
creates one config entry with `unique_id=DOMAIN`, so a second setup attempt
aborts as already-configured (single smartmeter-fetch instance only, per
the current design). A `reconfigure` step lets the user change the base URL
later without removing and re-adding the integration.

The API has no authentication (local-network use, matching the current
README/CLAUDE.md), so the form has exactly one field.

Config entry data stores only `{base_url}` — never the discovered point
list. Points are rediscovered live by the coordinator on every refresh
(out of scope here); this keeps a point added later on the smartmeter-fetch
side (e.g. a second provider, or a new metering point on an existing
account) showing up in HA without the user touching config flow again.

## Components

- `custom_components/smartmeter/config_flow.py`:
  - `SmartmeterConfigFlow(ConfigFlow, domain=DOMAIN)`
  - `async_step_user(user_input)` — shows/validates the `base_url` form.
  - `async_step_reconfigure(user_input)` — same form/validation, updates
    the existing entry's data instead of creating a new one.
  - `_validate(hass, base_url) -> list[dict]` — shared helper: strips a
    trailing slash from `base_url`, does
    `GET {base_url}/v1/points` via
    `homeassistant.helpers.aiohttp_client.async_get_clientsession(hass)`
    with a 10s timeout, returns the parsed JSON array or raises one of:
    - `CannotConnect` — timeout, connection error, or non-2xx response.
    - `NoPointsFound` — request succeeded but the array is empty.
- No new runtime dependency: aiohttp is already provided by HA core, so
  `manifest.json`'s `requirements: []` is unchanged.

## Data flow

```
user submits base_url
  -> strip trailing slash
  -> GET {base_url}/v1/points  (10s timeout)
  -> non-empty list  -> async_set_unique_id(DOMAIN); abort if already configured
                     -> create_entry(data={CONF_BASE_URL: base_url})
  -> empty list      -> form error: no_points_found
  -> connection/timeout/non-2xx -> form error: cannot_connect
  -> any other exception -> form error: unknown (logged)
```

The reconfigure step runs the same validation, then calls
`async_update_reload_and_abort` with the new `base_url` instead of
`create_entry`.

## Error handling

Three form-level errors, shown on the `base_url` field:
- `cannot_connect` — network/timeout/non-2xx talking to `/v1/points`.
- `no_points_found` — reachable, but the smartmeter-fetch instance reports
  zero metering points (e.g. provider not configured yet on that side).
- `unknown` — anything else (logged with the exception for diagnosis).

These are the only three outcomes `_validate` can raise; no other error
branches exist.

## Testing

Add `pytest-homeassistant-custom-component` as a dev dependency (nothing is
configured yet in `pyproject.toml`). Use its `aioclient_mock` fixture to
simulate `GET /v1/points` returning: a non-empty point list, an empty list,
a connection error, and a timeout — asserting the resulting flow result
type and `errors` dict for each. No real smartmeter-fetch instance
involved. Also test the reconfigure step updates an existing entry's
`base_url` rather than creating a second entry.
