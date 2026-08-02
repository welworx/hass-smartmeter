"""The Smartmeter integration.

Reads consumption/production readings from a smartmeter-fetch instance's
/v1 HTTP API and imports them into Home Assistant. Provider- and
storage-backend-agnostic by design: this integration only ever talks to
smartmeter-fetch's versioned API, never to whatever is behind it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform

from .coordinator import SmartmeterDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .coordinator import SmartmeterConfigEntry

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: SmartmeterConfigEntry) -> bool:
    """Set up Smartmeter from a config entry."""
    coordinator = SmartmeterDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SmartmeterConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
