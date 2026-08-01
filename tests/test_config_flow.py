"""Tests for the Smartmeter config flow."""

import aiohttp
import pytest

from custom_components.smartmeter.config_flow import (
    CannotConnect,
    NoPointsFound,
    _validate,
)

BASE_URL = "http://smartmeter.local:8080"


async def test_validate_success(hass, aioclient_mock):
    aioclient_mock.get(
        f"{BASE_URL}/v1/points",
        json=[{"id": "normal", "name": "Consumption"}],
    )

    points = await _validate(hass, BASE_URL)

    assert points == [{"id": "normal", "name": "Consumption"}]


async def test_validate_strips_trailing_slash(hass, aioclient_mock):
    aioclient_mock.get(
        f"{BASE_URL}/v1/points",
        json=[{"id": "normal", "name": "Consumption"}],
    )

    points = await _validate(hass, f"{BASE_URL}/")

    assert points == [{"id": "normal", "name": "Consumption"}]


async def test_validate_no_points_found(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/v1/points", json=[])

    with pytest.raises(NoPointsFound):
        await _validate(hass, BASE_URL)


async def test_validate_cannot_connect_on_client_error(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/v1/points", exc=aiohttp.ClientError)

    with pytest.raises(CannotConnect):
        await _validate(hass, BASE_URL)


async def test_validate_cannot_connect_on_non_2xx(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/v1/points", status=500)

    with pytest.raises(CannotConnect):
        await _validate(hass, BASE_URL)
