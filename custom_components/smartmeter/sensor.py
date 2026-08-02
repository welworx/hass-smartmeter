"""Diagnostic sensor for the Smartmeter integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import SmartmeterDataUpdateCoordinator

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SmartmeterConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartmeterConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the last-update diagnostic sensor."""
    async_add_entities([SmartmeterLastUpdateSensor(entry.runtime_data)])


class SmartmeterLastUpdateSensor(
    CoordinatorEntity[SmartmeterDataUpdateCoordinator], SensorEntity
):
    """Shows when the coordinator last successfully polled smartmeter-fetch."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Smartmeter Last Update"

    def __init__(self, coordinator: SmartmeterDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_last_update"

    @property
    def native_value(self) -> datetime | None:
        """Return the last successful fetch time."""
        return self.coordinator.last_successful_fetch
