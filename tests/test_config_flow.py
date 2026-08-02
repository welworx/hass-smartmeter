"""Tests for the Smartmeter config flow."""

import aiohttp
import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.smartmeter.config_flow import (
    CannotConnect,
    NoPointsFound,
    _validate,
)
from custom_components.smartmeter.const import CONF_BASE_URL, DOMAIN

BASE_URL = "http://smartmeter.local:8080"


async def test_validate_success(hass, enable_custom_integrations, aioclient_mock):
    aioclient_mock.get(
        f"{BASE_URL}/v1/points",
        json=[{"id": "normal", "name": "Consumption"}],
    )

    points = await _validate(hass, BASE_URL)

    assert points == [{"id": "normal", "name": "Consumption"}]


async def test_validate_strips_trailing_slash(
    hass, enable_custom_integrations, aioclient_mock
):
    aioclient_mock.get(
        f"{BASE_URL}/v1/points",
        json=[{"id": "normal", "name": "Consumption"}],
    )

    points = await _validate(hass, f"{BASE_URL}/")

    assert points == [{"id": "normal", "name": "Consumption"}]


async def test_validate_no_points_found(
    hass, enable_custom_integrations, aioclient_mock
):
    aioclient_mock.get(f"{BASE_URL}/v1/points", json=[])

    with pytest.raises(NoPointsFound):
        await _validate(hass, BASE_URL)


async def test_validate_cannot_connect_on_client_error(
    hass, enable_custom_integrations, aioclient_mock
):
    aioclient_mock.get(f"{BASE_URL}/v1/points", exc=aiohttp.ClientError)

    with pytest.raises(CannotConnect):
        await _validate(hass, BASE_URL)


async def test_validate_cannot_connect_on_non_2xx(
    hass, enable_custom_integrations, aioclient_mock
):
    aioclient_mock.get(f"{BASE_URL}/v1/points", status=500)

    with pytest.raises(CannotConnect):
        await _validate(hass, BASE_URL)


async def test_user_flow_shows_form(recorder_mock, hass, enable_custom_integrations):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_user_flow_success(
    recorder_mock, hass, enable_custom_integrations, aioclient_mock
):
    aioclient_mock.get(
        f"{BASE_URL}/v1/points", json=[{"id": "normal", "name": "Consumption"}]
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_BASE_URL: BASE_URL}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_BASE_URL: BASE_URL}


async def test_user_flow_cannot_connect(
    recorder_mock, hass, enable_custom_integrations, aioclient_mock
):
    aioclient_mock.get(f"{BASE_URL}/v1/points", exc=aiohttp.ClientError)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_BASE_URL: BASE_URL}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_no_points_found(
    recorder_mock, hass, enable_custom_integrations, aioclient_mock
):
    aioclient_mock.get(f"{BASE_URL}/v1/points", json=[])

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_BASE_URL: BASE_URL}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_points_found"}


async def test_user_flow_already_configured(
    recorder_mock, hass, enable_custom_integrations, aioclient_mock
):
    MockConfigEntry(
        domain=DOMAIN, unique_id=DOMAIN, data={CONF_BASE_URL: BASE_URL}
    ).add_to_hass(hass)
    aioclient_mock.get(
        f"{BASE_URL}/v1/points", json=[{"id": "normal", "name": "Consumption"}]
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_BASE_URL: BASE_URL}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure_flow_updates_base_url(
    recorder_mock, hass, enable_custom_integrations, aioclient_mock
):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=DOMAIN, data={CONF_BASE_URL: BASE_URL}
    )
    entry.add_to_hass(hass)

    new_url = "http://smartmeter.local:9090"
    aioclient_mock.get(
        f"{new_url}/v1/points", json=[{"id": "normal", "name": "Consumption"}]
    )

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_BASE_URL: new_url}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == {CONF_BASE_URL: new_url}


async def test_reconfigure_flow_cannot_connect(
    recorder_mock, hass, enable_custom_integrations, aioclient_mock
):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=DOMAIN, data={CONF_BASE_URL: BASE_URL}
    )
    entry.add_to_hass(hass)
    aioclient_mock.get(f"{BASE_URL}/v1/points", exc=aiohttp.ClientError)

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_BASE_URL: BASE_URL}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert entry.data == {CONF_BASE_URL: BASE_URL}
