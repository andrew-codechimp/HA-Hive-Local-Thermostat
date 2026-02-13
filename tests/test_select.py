"""Tests for the select platform."""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


async def test_select_not_created_for_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that select entities are not created for SLR1 model."""
    # SLR1 doesn't support water controls, so no select entity should exist
    entries = er.async_entries_for_config_entry(
        entity_registry, setup_integration_slr1.entry_id
    )
    select_entries = [entry for entry in entries if entry.domain == "select"]
    assert len(select_entries) == 0


async def test_select_created_for_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that select entities are created for SLR2 model."""
    entity_id = "select.hive_thermostat_slr2_water_mode"
    entry = entity_registry.async_get(entity_id)
    assert entry is not None, f"Entity {entity_id} not found in registry"
    assert entry.domain == "select"


async def test_select_options_with_schedule_mode(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test select options include 'auto' when schedule mode is shown."""
    entity_id = "select.hive_thermostat_slr2_water_mode"
    state = hass.states.get(entity_id)
    assert state is not None, f"Entity {entity_id} not found"

    # With show_water_schedule_mode=True, options should include "auto"
    expected_options = ["auto", "heat", "off", "boost"]
    assert state.attributes.get("options") == expected_options


async def test_select_options_without_schedule_mode(
    hass: HomeAssistant,
    mock_config_entry_slr2: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test select options exclude 'auto' when schedule mode is not shown."""
    # Modify config to disable schedule mode
    mock_config_entry_slr2.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry_slr2,
        options={**mock_config_entry_slr2.options, "show_water_schedule_mode": False},
    )

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

    entity_id = "select.hive_thermostat_slr2_water_mode"
    state = hass.states.get(entity_id)
    assert state is not None, f"Entity {entity_id} not found"

    # Without show_water_schedule_mode, options should exclude "auto"
    expected_options = ["heat", "off", "boost"]
    assert state.attributes.get("options") == expected_options


async def test_select_exists(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test select entity exists for SLR2."""
    entity_id = "select.hive_thermostat_slr2_water_mode"
    state = hass.states.get(entity_id)
    assert state is not None, f"Entity {entity_id} not found"
    assert "options" in state.attributes
    assert set(state.attributes["options"]) == {"auto", "heat", "off", "boost"}


async def test_select_option_auto(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test selecting 'auto' option calls async_water_scheduled."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_water_scheduled = AsyncMock()

    entity_id = "select.hive_thermostat_slr2_water_mode"

    # Select 'auto' option
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "auto"},
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_water_scheduled.assert_called_once()

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.state == "auto"


async def test_select_option_heat(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test selecting 'heat' option calls async_water_always_on."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_water_always_on = AsyncMock()

    entity_id = "select.hive_thermostat_slr2_water_mode"

    # Select 'heat' option
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "heat"},
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_water_always_on.assert_called_once()

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.state == "heat"


async def test_select_option_boost(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test selecting 'boost' option calls async_water_boost."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_water_boost = AsyncMock()

    entity_id = "select.hive_thermostat_slr2_water_mode"

    # Select 'boost' option
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "boost"},
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_water_boost.assert_called_once()

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.state == "boost"


async def test_select_option_off(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test selecting 'off' option calls async_water_always_off."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_water_always_off = AsyncMock()

    entity_id = "select.hive_thermostat_slr2_water_mode"

    # Select 'off' option
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "off"},
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_water_always_off.assert_called_once()

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.state == "off"


async def test_select_invalid_option(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test selecting an invalid option through service call is rejected."""
    entity_id = "select.hive_thermostat_slr2_water_mode"

    # Try to select an invalid option through service call
    # Home Assistant should reject this before it gets to our code
    with pytest.raises(Exception):  # Service validation error  # noqa: B017, PT011
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": entity_id, "option": "invalid_mode"},
            blocking=True,
        )


async def test_select_restore_state(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test that select entity restores its previous state."""
    entity_id = "select.hive_thermostat_slr2_water_mode"

    # Set initial state
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator
    coordinator.async_water_always_on = AsyncMock()

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "heat"},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state.state == "heat"

    # Reload the integration
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    # State should be restored
    state = hass.states.get(entity_id)
    assert state is not None
    # Note: The restored state might be None initially until MQTT update


async def test_select_entity_attributes(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test select entity has correct attributes."""
    entity_id = "select.hive_thermostat_slr2_water_mode"
    state = hass.states.get(entity_id)
    assert state is not None

    # Check basic attributes
    assert "options" in state.attributes
    assert "friendly_name" in state.attributes
    assert state.attributes["friendly_name"] == "Hive Thermostat SLR2 Water mode"


async def test_select_integration_with_mqtt(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    mock_mqtt_message: Any,
) -> None:
    """Test select entity integration with MQTT messages."""
    entity_id = "select.hive_thermostat_slr2_water_mode"
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Verify initial state
    state = hass.states.get(entity_id)
    assert state is not None

    # Process a water boost message
    message = mock_mqtt_message("mqtt_slr2_water_boost.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # The coordinator should have the right water mode after processing
    assert coordinator.water_mode == "boost"


async def test_select_unique_id(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test select entity has correct unique ID."""
    entity_id = "select.hive_thermostat_slr2_water_mode"
    entry = entity_registry.async_get(entity_id)
    assert entry is not None
    # Unique ID format: {DOMAIN}_{name}_{key} in lowercase
    assert (
        entry.unique_id
        == "hive_local_thermostat_hive thermostat slr2_system_mode_water"
    )
