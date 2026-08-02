"""Tests for the Smartmeter coordinator."""

import aiohttp
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.smartmeter.const import CONF_BASE_URL, DOMAIN
from custom_components.smartmeter.coordinator import SmartmeterDataUpdateCoordinator

BASE_URL = "http://smartmeter.local:8080"


def _make_coordinator(hass) -> SmartmeterDataUpdateCoordinator:
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=DOMAIN, data={CONF_BASE_URL: BASE_URL}
    )
    entry.add_to_hass(hass)
    return SmartmeterDataUpdateCoordinator(hass, entry)


def _readings_call(aioclient_mock):
    return next(
        call for call in aioclient_mock.mock_calls if "/v1/readings" in str(call[1])
    )


async def test_first_refresh_omits_since(recorder_mock, hass, aioclient_mock):
    aioclient_mock.get(
        f"{BASE_URL}/v1/points", json=[{"provider": "evn", "id": "AT001"}]
    )
    aioclient_mock.get(
        f"{BASE_URL}/v1/readings",
        json=[{"timestamp": "2026-01-01T00:15:00Z", "value": 100.0}],
    )

    coordinator = _make_coordinator(hass)
    await coordinator.async_refresh()
    await async_wait_recording_done(hass)

    assert "since" not in _readings_call(aioclient_mock)[1].query
    assert coordinator.last_update_success is True
    assert "smartmeter:evn_at001" in coordinator.data
    assert coordinator.last_successful_fetch is not None


async def test_second_refresh_passes_since(recorder_mock, hass, aioclient_mock):
    aioclient_mock.get(
        f"{BASE_URL}/v1/points", json=[{"provider": "evn", "id": "AT001"}]
    )
    aioclient_mock.get(
        f"{BASE_URL}/v1/readings",
        json=[{"timestamp": "2026-01-01T00:15:00Z", "value": 100.0}],
    )

    coordinator = _make_coordinator(hass)
    await coordinator.async_refresh()
    await async_wait_recording_done(hass)
    aioclient_mock.clear_requests()

    aioclient_mock.get(
        f"{BASE_URL}/v1/points", json=[{"provider": "evn", "id": "AT001"}]
    )
    aioclient_mock.get(f"{BASE_URL}/v1/readings", json=[])

    await coordinator.async_refresh()

    assert _readings_call(aioclient_mock)[1].query["since"] == (
        "2026-01-01T00:00:00+00:00"
    )


async def test_one_point_failing_does_not_block_others(
    recorder_mock, hass, aioclient_mock
):
    aioclient_mock.get(
        f"{BASE_URL}/v1/points",
        json=[
            {"provider": "evn", "id": "AT001"},
            {"provider": "evn", "id": "AT002"},
        ],
    )
    aioclient_mock.get(
        f"{BASE_URL}/v1/readings?point=AT001",
        json=[{"timestamp": "2026-01-01T00:15:00Z", "value": 100.0}],
    )
    aioclient_mock.get(f"{BASE_URL}/v1/readings?point=AT002", exc=aiohttp.ClientError)

    coordinator = _make_coordinator(hass)
    await coordinator.async_refresh()
    await async_wait_recording_done(hass)

    assert coordinator.last_update_success is True
    assert "smartmeter:evn_at001" in coordinator.data
    assert "smartmeter:evn_at002" not in coordinator.data


async def test_points_failure_raises_update_failed(recorder_mock, hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/v1/points", exc=aiohttp.ClientError)

    coordinator = _make_coordinator(hass)
    await coordinator.async_refresh()

    assert coordinator.last_update_success is False
