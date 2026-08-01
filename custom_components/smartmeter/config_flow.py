"""Config flow for the Smartmeter integration.

Asks for the base URL of a running smartmeter-fetch instance and validates
it by calling GET /v1/points. Only one instance is supported at a time.
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """The smartmeter-fetch instance could not be reached."""


class NoPointsFound(HomeAssistantError):
    """The smartmeter-fetch instance reported no metering points."""


async def _validate(hass: HomeAssistant, base_url: str) -> list[dict[str, Any]]:
    """Fetch /v1/points to confirm base_url is a working smartmeter-fetch instance."""
    base_url = base_url.rstrip("/")
    session = async_get_clientsession(hass)
    try:
        async with session.get(
            f"{base_url}/v1/points", timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            response.raise_for_status()
            points = await response.json()
    except (aiohttp.ClientError, TimeoutError) as err:
        raise CannotConnect from err

    if not points:
        raise NoPointsFound

    return points
