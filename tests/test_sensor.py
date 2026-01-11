"""Tests for the Hive Local Thermostat sensor platform."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from syrupy import SnapshotAssertion

from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


@pytest.mark.parametrize(
    ("fixture_file", "expected_states"),
    [
        (
            "mqtt_slr1_heating.json",
            {
                "running_state_heat": "heat",
                "current_temperature": "20.5",
                "heating_boost_remaining": "0",
            },
        ),
        (
            "mqtt_slr1_boost.json",
            {
                "running_state_heat": "heat",
                "current_temperature": "18.5",
                "heating_boost_remaining": "30",
            },
        ),
        (
            "mqtt_slr1_idle.json",
            {
                "running_state_heat": "idle",
                "current_temperature": "21.0",
                "heating_boost_remaining": "0",
            },
        ),
        (
            "mqtt_slr1_off.json",
            {
                "running_state_heat": "off",
                "current_temperature": "19.5",
                "heating_boost_remaining": "0",
            },
        ),
    ],
)
async def test_sensor_slr1_states(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    mock_mqtt_message: Any,
    fixture_file: str,
    expected_states: dict[str, str],
) -> None:
    """Test SLR1 sensor states from different MQTT messages."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Process the MQTT message
    message = mock_mqtt_message(fixture_file, "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # Check each sensor state
    for sensor_key, expected_state in expected_states.items():
        entity_id = f"sensor.hive_thermostat_{sensor_key}"
        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        assert state.state == expected_state, (
            f"Expected {sensor_key} to be {expected_state}, got {state.state}"
        )


@pytest.mark.parametrize(
    ("fixture_file", "expected_states"),
    [
        (
            "mqtt_slr2_heating.json",
            {
                "running_state_heat": "heat",
                "current_temperature": "20.5",
                "running_state_water": "idle",
                "heating_boost_remaining": "0",
                "water_boost_remaining": "0",
            },
        ),
        (
            "mqtt_slr2_boost.json",
            {
                "running_state_heat": "heat",
                "current_temperature": "18.5",
                "running_state_water": "idle",
                "heating_boost_remaining": "30",
                "water_boost_remaining": "0",
            },
        ),
        (
            "mqtt_slr2_idle.json",
            {
                "running_state_heat": "idle",
                "current_temperature": "19.0",
                "running_state_water": "idle",
                "heating_boost_remaining": "0",
                "water_boost_remaining": "0",
            },
        ),
        (
            "mqtt_slr2_off.json",
            {
                "running_state_heat": "off",
                "current_temperature": "19.0",
                "running_state_water": "off",
                "heating_boost_remaining": "0",
                "water_boost_remaining": "0",
            },
        ),
        (
            "mqtt_slr2_water_boost.json",
            {
                "running_state_heat": "idle",
                "current_temperature": "20.0",
                "running_state_water": "heat",
                "heating_boost_remaining": "0",
                "water_boost_remaining": "45",
            },
        ),
    ],
)
async def test_sensor_slr2_states(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    mock_mqtt_message: Any,
    fixture_file: str,
    expected_states: dict[str, str],
) -> None:
    """Test SLR2 sensor states from different MQTT messages."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Process the MQTT message
    message = mock_mqtt_message(fixture_file, "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # Check each sensor state
    for sensor_key, expected_state in expected_states.items():
        entity_id = f"sensor.hive_thermostat_slr2_{sensor_key}"
        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        assert state.state == expected_state, (
            f"Expected {sensor_key} to be {expected_state}, got {state.state}"
        )


async def test_sensor_slr1_temperature_attributes(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    mock_mqtt_message: Any,
) -> None:
    """Test SLR1 temperature sensor attributes."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Process a heating message
    message = mock_mqtt_message("mqtt_slr1_heating.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # Check temperature sensor attributes
    entity_id = "sensor.hive_thermostat_current_temperature"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS
    assert state.attributes.get(ATTR_DEVICE_CLASS) == "temperature"


async def test_sensor_slr2_temperature_attributes(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    mock_mqtt_message: Any,
) -> None:
    """Test SLR2 temperature sensor attributes."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Process a heating message
    message = mock_mqtt_message("mqtt_slr2_heating.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # Check temperature sensor attributes
    entity_id = "sensor.hive_thermostat_slr2_current_temperature"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS
    assert state.attributes.get(ATTR_DEVICE_CLASS) == "temperature"


async def test_sensor_entity_registry_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test SLR1 sensors are registered correctly."""
    expected_entities = [
        "sensor.hive_thermostat_running_state_heat",
        "sensor.hive_thermostat_current_temperature",
        "sensor.hive_thermostat_heating_boost_remaining",
    ]

    for entity_id in expected_entities:
        entry = entity_registry.async_get(entity_id)
        assert entry is not None, f"Entity {entity_id} not found in registry"
        assert entry.domain == "sensor"


async def test_sensor_entity_registry_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test SLR2 sensors are registered correctly."""
    expected_entities = [
        "sensor.hive_thermostat_slr2_running_state_heat",
        "sensor.hive_thermostat_slr2_current_temperature",
        "sensor.hive_thermostat_slr2_running_state_water",
        "sensor.hive_thermostat_slr2_heating_boost_remaining",
        "sensor.hive_thermostat_slr2_water_boost_remaining",
    ]

    for entity_id in expected_entities:
        entry = entity_registry.async_get(entity_id)
        assert entry is not None, f"Entity {entity_id} not found in registry"
        assert entry.domain == "sensor"


async def test_sensor_slr1_snapshot(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    mock_mqtt_message: Any,
    snapshot: SnapshotAssertion,
) -> None:
    """Test SLR1 sensor states match snapshot."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Process a heating message
    message = mock_mqtt_message("mqtt_slr1_heating.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # Get all sensor states
    sensor_states = {}
    for entity_id in [
        "sensor.hive_thermostat_running_state_heat",
        "sensor.hive_thermostat_current_temperature",
        "sensor.hive_thermostat_heating_boost_remaining",
    ]:
        state = hass.states.get(entity_id)
        if state:
            sensor_states[entity_id] = {
                "state": state.state,
                "attributes": dict(state.attributes),
            }

    assert sensor_states == snapshot


async def test_sensor_slr2_snapshot(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    mock_mqtt_message: Any,
    snapshot: SnapshotAssertion,
) -> None:
    """Test SLR2 sensor states match snapshot."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Process a heating message
    message = mock_mqtt_message("mqtt_slr2_heating.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # Get all sensor states
    sensor_states = {}
    for entity_id in [
        "sensor.hive_thermostat_slr2_running_state_heat",
        "sensor.hive_thermostat_slr2_current_temperature",
        "sensor.hive_thermostat_slr2_running_state_water",
        "sensor.hive_thermostat_slr2_heating_boost_remaining",
        "sensor.hive_thermostat_slr2_water_boost_remaining",
    ]:
        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        sensor_states[entity_id] = {
            "state": state.state,
            "attributes": dict(state.attributes),
        }

    assert sensor_states == snapshot


async def test_sensor_slr1_boost_snapshot(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    mock_mqtt_message: Any,
    snapshot: SnapshotAssertion,
) -> None:
    """Test SLR1 sensor states during boost match snapshot."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Process a boost message
    message = mock_mqtt_message("mqtt_slr1_boost.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # Get all sensor states
    sensor_states = {}
    for entity_id in [
        "sensor.hive_thermostat_running_state_heat",
        "sensor.hive_thermostat_current_temperature",
        "sensor.hive_thermostat_heating_boost_remaining",
    ]:
        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        sensor_states[entity_id] = {
            "state": state.state,
            "attributes": dict(state.attributes),
        }

    assert sensor_states == snapshot


async def test_sensor_slr2_boost_snapshot(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    mock_mqtt_message: Any,
    snapshot: SnapshotAssertion,
) -> None:
    """Test SLR2 sensor states during boost match snapshot."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Process a boost message
    message = mock_mqtt_message("mqtt_slr2_boost.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # Get all sensor states
    sensor_states = {}
    for entity_id in [
        "sensor.hive_thermostat_slr2_running_state_heat",
        "sensor.hive_thermostat_slr2_current_temperature",
        "sensor.hive_thermostat_slr2_running_state_water",
        "sensor.hive_thermostat_slr2_heating_boost_remaining",
        "sensor.hive_thermostat_slr2_water_boost_remaining",
    ]:
        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        sensor_states[entity_id] = {
            "state": state.state,
            "attributes": dict(state.attributes),
        }

    assert sensor_states == snapshot


async def test_sensor_empty_mqtt_payload(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test handling of empty MQTT payload."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    message = Mock(spec=ReceiveMessage)
    message.topic = "hive/thermostat"
    message.payload = ""

    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # Check that error was logged
    assert "Received empty payload" in caplog.text


async def test_sensor_invalid_json_payload(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test handling of invalid JSON in MQTT payload."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Create a message with invalid JSON
    message = Mock(spec=ReceiveMessage)
    message.topic = "hive/thermostat"
    message.payload = "not valid json{{"

    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # Check that error was logged
    assert "Failed to parse JSON" in caplog.text
