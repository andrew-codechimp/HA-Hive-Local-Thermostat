"""Tests for the button platform."""

from unittest.mock import AsyncMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


async def test_button_heating_boost_created_for_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that heating boost button is created for SLR1 model."""
    entity_id = "button.hive_thermostat_heating_boost"
    entry = entity_registry.async_get(entity_id)
    assert entry is not None, f"Entity {entity_id} not found in registry"
    assert entry.domain == "button"


async def test_button_water_boost_not_created_for_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that water boost button is NOT created for SLR1 model."""
    # SLR1 doesn't support water controls
    entity_id = "button.hive_thermostat_water_boost"
    entry = entity_registry.async_get(entity_id)
    assert entry is None, f"Entity {entity_id} should not exist for SLR1"


async def test_buttons_created_for_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that both boost buttons are created for SLR2 model."""
    heating_boost_id = "button.hive_thermostat_slr2_heating_boost"
    water_boost_id = "button.hive_thermostat_slr2_water_boost"

    heating_entry = entity_registry.async_get(heating_boost_id)
    assert heating_entry is not None, f"Entity {heating_boost_id} not found in registry"
    assert heating_entry.domain == "button"

    water_entry = entity_registry.async_get(water_boost_id)
    assert water_entry is not None, f"Entity {water_boost_id} not found in registry"
    assert water_entry.domain == "button"


async def test_button_heating_boost_press_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test pressing heating boost button calls coordinator method for SLR1."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_heating_boost = AsyncMock()

    entity_id = "button.hive_thermostat_heating_boost"

    # Press the button
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": entity_id},
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_heating_boost.assert_called_once()


async def test_button_heating_boost_press_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test pressing heating boost button calls coordinator method for SLR2."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_heating_boost = AsyncMock()

    entity_id = "button.hive_thermostat_slr2_heating_boost"

    # Press the button
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": entity_id},
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_heating_boost.assert_called_once()


async def test_button_water_boost_press_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test pressing water boost button calls coordinator method for SLR2."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_water_boost = AsyncMock()

    entity_id = "button.hive_thermostat_slr2_water_boost"

    # Press the button
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": entity_id},
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_water_boost.assert_called_once()


async def test_button_heating_boost_attributes_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test heating boost button has correct attributes for SLR1."""
    entity_id = "button.hive_thermostat_heating_boost"
    state = hass.states.get(entity_id)
    assert state is not None

    # Check basic attributes
    assert "friendly_name" in state.attributes
    assert state.attributes["friendly_name"] == "Hive Thermostat Heating boost"


async def test_button_attributes_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test buttons have correct attributes for SLR2."""
    heating_boost_id = "button.hive_thermostat_slr2_heating_boost"
    water_boost_id = "button.hive_thermostat_slr2_water_boost"

    # Check heating boost button
    heating_state = hass.states.get(heating_boost_id)
    assert heating_state is not None
    assert "friendly_name" in heating_state.attributes
    assert (
        heating_state.attributes["friendly_name"]
        == "Hive Thermostat SLR2 Heating boost"
    )

    # Check water boost button
    water_state = hass.states.get(water_boost_id)
    assert water_state is not None
    assert "friendly_name" in water_state.attributes
    assert water_state.attributes["friendly_name"] == "Hive Thermostat SLR2 Water boost"


async def test_button_heating_boost_unique_id_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test heating boost button has correct unique ID for SLR1."""
    entity_id = "button.hive_thermostat_heating_boost"
    entry = entity_registry.async_get(entity_id)
    assert entry is not None
    # Unique ID format: {DOMAIN}_{name}_{key} in lowercase
    assert entry.unique_id == "hive_local_thermostat_hive thermostat_boost_heating"


async def test_button_unique_ids_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test buttons have correct unique IDs for SLR2."""
    # Check heating boost button
    heating_boost_id = "button.hive_thermostat_slr2_heating_boost"
    heating_entry = entity_registry.async_get(heating_boost_id)
    assert heating_entry is not None
    assert (
        heating_entry.unique_id
        == "hive_local_thermostat_hive thermostat slr2_boost_heating"
    )

    # Check water boost button
    water_boost_id = "button.hive_thermostat_slr2_water_boost"
    water_entry = entity_registry.async_get(water_boost_id)
    assert water_entry is not None
    assert (
        water_entry.unique_id
        == "hive_local_thermostat_hive thermostat slr2_boost_water"
    )


async def test_button_entity_registry_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test SLR1 button is registered correctly in entity registry."""
    expected_entity = "button.hive_thermostat_heating_boost"

    entry = entity_registry.async_get(expected_entity)
    assert entry is not None, f"Entity {expected_entity} not found in registry"
    assert entry.domain == "button"
    assert entry.original_name == "Heating boost"


async def test_button_entity_registry_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test SLR2 buttons are registered correctly in entity registry."""
    expected_entities = [
        ("button.hive_thermostat_slr2_heating_boost", "Heating boost"),
        ("button.hive_thermostat_slr2_water_boost", "Water boost"),
    ]

    for entity_id, original_name in expected_entities:
        entry = entity_registry.async_get(entity_id)
        assert entry is not None, f"Entity {entity_id} not found in registry"
        assert entry.domain == "button"
        assert entry.original_name == original_name


async def test_button_multiple_presses(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test pressing button multiple times calls coordinator method each time."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_heating_boost = AsyncMock()

    entity_id = "button.hive_thermostat_slr2_heating_boost"

    # Press the button three times
    for _ in range(3):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": entity_id},
            blocking=True,
        )

    # Verify the coordinator method was called three times
    assert coordinator.async_heating_boost.call_count == 3


async def test_button_both_boost_buttons_independent(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test that heating and water boost buttons work independently."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Mock both coordinator methods
    coordinator.async_heating_boost = AsyncMock()
    coordinator.async_water_boost = AsyncMock()

    heating_boost_id = "button.hive_thermostat_slr2_heating_boost"
    water_boost_id = "button.hive_thermostat_slr2_water_boost"

    # Press heating boost button
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": heating_boost_id},
        blocking=True,
    )

    # Press water boost button
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": water_boost_id},
        blocking=True,
    )

    # Verify each method was called once
    coordinator.async_heating_boost.assert_called_once()
    coordinator.async_water_boost.assert_called_once()
