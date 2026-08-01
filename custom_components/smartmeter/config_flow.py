"""Config flow for the Smartmeter integration.

Asks for the base URL of a running smartmeter-fetch instance and validates
it by calling GET /v1/points. Only one instance is supported at a time.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_BASE_URL, DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigFlowResult

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


STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_BASE_URL): str})


class SmartmeterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smartmeter."""

    VERSION = 1

    async def _validate_and_finish(
        self, user_input: dict[str, Any], *, reconfigure: bool
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        try:
            await _validate(self.hass, user_input[CONF_BASE_URL])
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except NoPointsFound:
            errors["base"] = "no_points_found"
        except Exception:  # noqa: BLE001 — anything unanticipated maps to "unknown"
            _LOGGER.exception(
                "Unexpected error validating smartmeter-fetch connection"
            )
            errors["base"] = "unknown"

        if errors:
            step_id = "reconfigure" if reconfigure else "user"
            return self.async_show_form(
                step_id=step_id, data_schema=STEP_USER_DATA_SCHEMA, errors=errors
            )

        data = {CONF_BASE_URL: user_input[CONF_BASE_URL].rstrip("/")}

        if reconfigure:
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(), data=data
            )

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="Smartmeter", data=data)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )
        return await self._validate_and_finish(user_input, reconfigure=False)
