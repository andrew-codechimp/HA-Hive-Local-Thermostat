"""Fixtures for Hive Local Thermostat integration tests."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from custom_components.hive_local_thermostat.const import (
    CONF_MODEL,
    CONF_MQTT_TOPIC,
    CONF_SHOW_HEAT_SCHEDULE_MODE,
    CONF_SHOW_WATER_SCHEDULE_MODE,
    DOMAIN,
    MODEL_SLR1,
    MODEL_SLR2,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.core import HomeAssistant

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations defined in the test dir."""
    return


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.hive_local_thermostat.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def fixture_path() -> Path:
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture(fixture_path: Path) -> Any:
    """Load a fixture file."""

    def _load_fixture(filename: str) -> str:
        """Load fixture from file."""
        path = fixture_path / filename
        return path.read_text()

    return _load_fixture


@pytest.fixture
def load_json_fixture(fixture_path: Path) -> Any:
    """Load a JSON fixture file."""

    def _load_json_fixture(filename: str) -> dict[str, Any]:
        """Load JSON fixture from file."""
        path = fixture_path / filename
        return json.loads(path.read_text())

    return _load_json_fixture


@pytest.fixture
def mock_mqtt_message(load_json_fixture: Any) -> Any:
    """Create a mock MQTT message from a fixture file."""

    def _create_message(
        fixture_file: str, topic: str = "hive/thermostat"
    ) -> ReceiveMessage:
        """Create a ReceiveMessage object from fixture."""
        data = load_json_fixture(fixture_file)
        message = Mock(spec=ReceiveMessage)
        message.topic = topic
        message.payload = json.dumps(data)
        return message

    return _create_message


@pytest.fixture
async def mock_config_entry_slr1() -> MockConfigEntry:
    """Return a mock config entry for SLR1 model."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Hive Thermostat",
        data={},
        options={
            CONF_MQTT_TOPIC: "hive/thermostat",
            CONF_MODEL: MODEL_SLR1,
            CONF_SHOW_HEAT_SCHEDULE_MODE: True,
            CONF_SHOW_WATER_SCHEDULE_MODE: False,
        },
        unique_id="test_thermostat_slr1",
    )


@pytest.fixture
async def mock_config_entry_slr2() -> MockConfigEntry:
    """Return a mock config entry for SLR2 model."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Hive Thermostat SLR2",
        data={},
        options={
            CONF_MQTT_TOPIC: "hive/thermostat",
            CONF_MODEL: MODEL_SLR2,
            CONF_SHOW_HEAT_SCHEDULE_MODE: True,
            CONF_SHOW_WATER_SCHEDULE_MODE: True,
        },
        unique_id="test_thermostat_slr2",
    )


@pytest.fixture
async def setup_integration_slr1(
    hass: HomeAssistant, mock_config_entry_slr1: MockConfigEntry
) -> AsyncGenerator[MockConfigEntry]:
    """Set up the Hive Local Thermostat integration with SLR1."""
    mock_config_entry_slr1.add_to_hass(hass)

    with (
        patch(
            "custom_components.hive_local_thermostat.coordinator.mqtt_client.async_subscribe"
        ) as mock_subscribe,
        patch(
            "custom_components.hive_local_thermostat.mqtt_client.async_publish"
        ) as mock_publish,
    ):
        mock_subscribe.return_value = AsyncMock()
        mock_publish.return_value = None
        await hass.config_entries.async_setup(mock_config_entry_slr1.entry_id)
        await hass.async_block_till_done()

    return mock_config_entry_slr1


@pytest.fixture
async def setup_integration_slr2(
    hass: HomeAssistant, mock_config_entry_slr2: MockConfigEntry
) -> AsyncGenerator[MockConfigEntry]:
    """Set up the Hive Local Thermostat integration with SLR2."""
    mock_config_entry_slr2.add_to_hass(hass)

    with (
        patch(
            "custom_components.hive_local_thermostat.coordinator.mqtt_client.async_subscribe"
        ) as mock_subscribe,
        patch(
            "custom_components.hive_local_thermostat.mqtt_client.async_publish"
        ) as mock_publish,
    ):
        mock_subscribe.return_value = AsyncMock()
        mock_publish.return_value = None
        await hass.config_entries.async_setup(mock_config_entry_slr2.entry_id)
        await hass.async_block_till_done()

    return mock_config_entry_slr2
