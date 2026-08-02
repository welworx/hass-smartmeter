"""Tests for setting up the Smartmeter config entry (coordinator + sensor)."""

from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.smartmeter.const import CONF_BASE_URL, DOMAIN

BASE_URL = "http://smartmeter.local:8080"


async def test_setup_entry_creates_last_update_sensor(
    recorder_mock, hass, enable_custom_integrations, aioclient_mock
):
    aioclient_mock.get(
        f"{BASE_URL}/v1/points", json=[{"provider": "evn", "id": "AT001"}]
    )
    aioclient_mock.get(
        f"{BASE_URL}/v1/readings",
        json=[{"timestamp": "2026-01-01T00:15:00Z", "value": 100.0}],
    )
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=DOMAIN, data={CONF_BASE_URL: BASE_URL}
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_last_update"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state != "unknown"


async def test_unload_entry(
    recorder_mock, hass, enable_custom_integrations, aioclient_mock
):
    aioclient_mock.get(f"{BASE_URL}/v1/points", json=[])
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=DOMAIN, data={CONF_BASE_URL: BASE_URL}
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
