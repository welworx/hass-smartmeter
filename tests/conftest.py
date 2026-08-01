"""Shared test fixtures for the Smartmeter integration."""

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow custom_components/smartmeter to be loaded during tests."""
    yield
