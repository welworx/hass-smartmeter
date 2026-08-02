"""DataUpdateCoordinator for the Smartmeter integration.

Polls GET /v1/readings?point=<id>&since=<last statistic timestamp> on the
configured smartmeter-fetch instance, resuming from the last successfully
imported statistic rather than from a fixed "yesterday" offset — upstream
grid operator portals can publish data several days late.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import CONF_BASE_URL, DOMAIN
from .statistics import (
    PointRef,
    Reading,
    async_import_statistics,
    async_last_reading_timestamp,
    statistic_id_for,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)

type SmartmeterConfigEntry = ConfigEntry[SmartmeterDataUpdateCoordinator]
type SmartmeterData = dict[str, tuple[PointRef, list[Reading]]]


class SmartmeterDataUpdateCoordinator(DataUpdateCoordinator[SmartmeterData]):
    """Polls a smartmeter-fetch instance and imports readings as statistics."""

    config_entry: SmartmeterConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: SmartmeterConfigEntry
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(hours=6),
        )
        self.base_url = config_entry.data[CONF_BASE_URL]
        self.last_successful_fetch: datetime | None = None

    async def _async_update_data(self) -> SmartmeterData:
        """Fetch points and readings, then import them as statistics."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                f"{self.base_url}/v1/points", timeout=REQUEST_TIMEOUT
            ) as response:
                response.raise_for_status()
                points: list[PointRef] = await response.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Could not reach {self.base_url}: {err}") from err

        data: SmartmeterData = {}
        for point in points:
            statistic_id = statistic_id_for(point)
            since = await async_last_reading_timestamp(self.hass, statistic_id)
            try:
                readings = await self._async_get_readings(point, since)
            except (aiohttp.ClientError, TimeoutError) as err:
                _LOGGER.warning(
                    "Skipping point %s (%s) this cycle: %s",
                    point["id"],
                    point["provider"],
                    err,
                )
                continue
            data[statistic_id] = (point, readings)

        await async_import_statistics(self.hass, data)
        self.last_successful_fetch = dt_util.utcnow()
        return data

    async def _async_get_readings(
        self, point: PointRef, since: datetime | None
    ) -> list[Reading]:
        """Fetch readings for one metering point."""
        params = {"point": point["id"]}
        if since is not None:
            params["since"] = since.isoformat()

        session = async_get_clientsession(self.hass)
        async with session.get(
            f"{self.base_url}/v1/readings", params=params, timeout=REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            return await response.json()
