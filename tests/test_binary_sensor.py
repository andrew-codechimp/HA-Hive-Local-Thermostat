"""Tests for the binary_sensor platform."""

from typing import Any

import pytest
from custom_components.hive_local_thermostat.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


@pytest.mark.parametrize(
    ("fixture_name", "expected_states"),
    [
        (
            "mqtt_slr1_heating.json",
            {
                "heating_boost": STATE_OFF,
            },
        ),
        (
            "mqtt_slr1_boost.json",
            {
                "heating_boost": STATE_ON,
            },
        ),
        (
            "mqtt_slr1_idle.json",
            {
                "heating_boost": STATE_OFF,
            },
        ),
        (
            "mqtt_slr1_off.json",
            {
                "heating_boost": STATE_OFF,
            },
        ),
    ],
)
async def test_binary_sensor_slr1_states(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    mock_mqtt_message: Any,
    fixture_name: str,
    expected_states: dict[str, str],
) -> None:
    """Test SLR1 binary sensor states with different MQTT messages."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Process the MQTT message
    message = mock_mqtt_message(fixture_name, "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # Verify binary sensor states
    for entity_key, expected_state in expected_states.items():
        entity_id = f"binary_sensor.hive_thermostat_{entity_key}"
        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        assert state.state == expected_state, (
            f"Expected {entity_id} to be {expected_state}, got {state.state}"
        )


@pytest.mark.parametrize(
    ("fixture_name", "expected_states"),
    [
        (
            "mqtt_slr2_heating.json",
            {
                "heating_boost": STATE_OFF,
                "water_boost": STATE_OFF,
            },
        ),
        (
            "mqtt_slr2_boost.json",
            {
                "heating_boost": STATE_ON,
                "water_boost": STATE_OFF,
            },
        ),
        (
            "mqtt_slr2_idle.json",
            {
                "heating_boost": STATE_OFF,
                "water_boost": STATE_OFF,
            },
        ),
        (
            "mqtt_slr2_water_boost.json",
            {
                "heating_boost": STATE_OFF,
                "water_boost": STATE_ON,
            },
        ),
    ],
)
async def test_binary_sensor_slr2_states(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    mock_mqtt_message: Any,
    fixture_name: str,
    expected_states: dict[str, str],
) -> None:
    """Test SLR2 binary sensor states with different MQTT messages."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Process the MQTT message
    message = mock_mqtt_message(fixture_name, "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # Verify binary sensor states
    for entity_key, expected_state in expected_states.items():
        entity_id = f"binary_sensor.hive_thermostat_slr2_{entity_key}"
        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        assert state.state == expected_state, (
            f"Expected {entity_id} to be {expected_state}, got {state.state}"
        )


async def test_binary_sensor_entity_registry_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test that SLR1 binary sensors are properly registered."""
    entity_registry = er.async_get(hass)

    # Check heating boost binary sensor
    entry = entity_registry.async_get("binary_sensor.hive_thermostat_heating_boost")
    assert entry
    assert entry.unique_id == f"{DOMAIN}_hive thermostat_heat_boost"
    assert entry.original_name == "Heating boost"


async def test_binary_sensor_entity_registry_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test that SLR2 binary sensors are properly registered."""
    entity_registry = er.async_get(hass)

    # Check heating boost binary sensor
    entry = entity_registry.async_get(
        "binary_sensor.hive_thermostat_slr2_heating_boost"
    )
    assert entry
    assert entry.unique_id == f"{DOMAIN}_hive thermostat slr2_heat_boost"
    assert entry.original_name == "Heating boost"

    # Check water boost binary sensor
    entry = entity_registry.async_get("binary_sensor.hive_thermostat_slr2_water_boost")
    assert entry
    assert entry.unique_id == f"{DOMAIN}_hive thermostat slr2_water_boost"
    assert entry.original_name == "Water boost"


async def test_binary_sensor_slr1_snapshot(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    mock_mqtt_message: Any,
    snapshot,
) -> None:
    """Test SLR1 binary sensor snapshot."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Process the MQTT message
    message = mock_mqtt_message("mqtt_slr1_heating.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    binary_sensor_states = {}
    for entity_id in [
        "binary_sensor.hive_thermostat_heating_boost",
    ]:
        state = hass.states.get(entity_id)
        if state:
            binary_sensor_states[entity_id] = {
                "state": state.state,
                "attributes": dict(state.attributes),
            }

    assert binary_sensor_states == snapshot


async def test_binary_sensor_slr2_snapshot(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    mock_mqtt_message: Any,
    snapshot,
) -> None:
    """Test SLR2 binary sensor snapshot."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Process the MQTT message
    message = mock_mqtt_message("mqtt_slr2_heating.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    binary_sensor_states = {}
    for entity_id in [
        "binary_sensor.hive_thermostat_slr2_heating_boost",
        "binary_sensor.hive_thermostat_slr2_water_boost",
    ]:
        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        binary_sensor_states[entity_id] = {
            "state": state.state,
            "attributes": dict(state.attributes),
        }

    assert binary_sensor_states == snapshot


async def test_binary_sensor_slr1_boost_snapshot(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    mock_mqtt_message: Any,
    snapshot,
) -> None:
    """Test SLR1 binary sensor snapshot during boost."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Process the MQTT message
    message = mock_mqtt_message("mqtt_slr1_boost.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    binary_sensor_states = {}
    for entity_id in [
        "binary_sensor.hive_thermostat_heating_boost",
    ]:
        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        binary_sensor_states[entity_id] = {
            "state": state.state,
            "attributes": dict(state.attributes),
        }

    assert binary_sensor_states == snapshot


async def test_binary_sensor_slr2_boost_snapshot(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    mock_mqtt_message: Any,
    snapshot,
) -> None:
    """Test SLR2 binary sensor snapshot during boost."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Process the MQTT message
    message = mock_mqtt_message("mqtt_slr2_water_boost.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    binary_sensor_states = {}
    for entity_id in [
        "binary_sensor.hive_thermostat_slr2_heating_boost",
        "binary_sensor.hive_thermostat_slr2_water_boost",
    ]:
        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        binary_sensor_states[entity_id] = {
            "state": state.state,
            "attributes": dict(state.attributes),
        }

    assert binary_sensor_states == snapshot


async def test_binary_sensor_boost_transitions_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    mock_mqtt_message: Any,
) -> None:
    """Test SLR1 binary sensor transitions between boost states."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Start with idle state
    message = mock_mqtt_message("mqtt_slr1_idle.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    entity_id = "binary_sensor.hive_thermostat_heating_boost"
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF

    # Transition to boost
    message = mock_mqtt_message("mqtt_slr1_boost.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    # Transition back to idle
    message = mock_mqtt_message("mqtt_slr1_idle.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF


async def test_binary_sensor_boost_transitions_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    mock_mqtt_message: Any,
) -> None:
    """Test SLR2 binary sensor transitions between boost states."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Start with idle state
    message = mock_mqtt_message("mqtt_slr2_idle.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    heating_boost_id = "binary_sensor.hive_thermostat_slr2_heating_boost"
    water_boost_id = "binary_sensor.hive_thermostat_slr2_water_boost"

    assert hass.states.get(heating_boost_id).state == STATE_OFF
    assert hass.states.get(water_boost_id).state == STATE_OFF

    # Transition to heating boost
    message = mock_mqtt_message("mqtt_slr2_boost.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    assert hass.states.get(heating_boost_id).state == STATE_ON
    assert hass.states.get(water_boost_id).state == STATE_OFF

    # Transition to water boost
    message = mock_mqtt_message("mqtt_slr2_water_boost.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    assert hass.states.get(heating_boost_id).state == STATE_OFF
    assert hass.states.get(water_boost_id).state == STATE_ON

    # Transition back to idle
    message = mock_mqtt_message("mqtt_slr2_idle.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    assert hass.states.get(heating_boost_id).state == STATE_OFF
    assert hass.states.get(water_boost_id).state == STATE_OFF
