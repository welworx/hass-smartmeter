"""Shared test fixtures for the Smartmeter integration."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow custom_components/smartmeter to be loaded during tests."""
    yield


@pytest.fixture(autouse=True)
def patch_mock_config_entry_for_reconfigure():
    """Add start_reconfigure_flow to MockConfigEntry if not present."""
    if not hasattr(MockConfigEntry, "start_reconfigure_flow"):

        async def start_reconfigure_flow(self, hass):
            """Start a reconfigure flow for this entry."""
            return await hass.config_entries.flow.async_init(
                self.domain,
                context={
                    "source": "reconfigure",
                    "entry_id": self.entry_id,
                },
            )

        MockConfigEntry.start_reconfigure_flow = start_reconfigure_flow
    yield
