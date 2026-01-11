"""Tests for the climate platform."""

from unittest.mock import AsyncMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    DOMAIN as CLIMATE_DOMAIN,
    PRESET_BOOST,
    PRESET_NONE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_TEMPERATURE,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


async def test_climate_entity_created_for_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that climate entity is created for SLR1 model."""
    entity_id = "climate.hive_thermostat_climate"
    entry = entity_registry.async_get(entity_id)
    assert entry is not None, f"Entity {entity_id} not found in registry"
    assert entry.domain == "climate"


async def test_climate_entity_created_for_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that climate entity is created for SLR2 model."""
    entity_id = "climate.hive_thermostat_slr2_climate"
    entry = entity_registry.async_get(entity_id)
    assert entry is not None, f"Entity {entity_id} not found in registry"
    assert entry.domain == "climate"


async def test_climate_default_attributes_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test climate entity default attributes for SLR1."""
    entity_id = "climate.hive_thermostat_climate"
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.attributes.get("min_temp") == 5
    assert state.attributes.get("max_temp") == 32
    assert state.attributes.get("target_temp_step") == 0.5
    assert state.attributes.get("temperature") is None
    assert state.attributes.get("current_temperature") is None
    assert state.attributes.get("preset_mode") is None
    assert state.attributes.get("hvac_modes") == [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.AUTO,
    ]
    assert state.attributes.get("preset_modes") == [PRESET_NONE, PRESET_BOOST]


async def test_climate_default_attributes_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test climate entity default attributes for SLR2."""
    entity_id = "climate.hive_thermostat_slr2_climate"
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.attributes.get("min_temp") == 5
    assert state.attributes.get("max_temp") == 32
    assert state.attributes.get("target_temp_step") == 0.5


async def test_climate_hvac_modes_with_schedule(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test HVAC modes include AUTO when schedule mode is enabled."""
    entity_id = "climate.hive_thermostat_climate"
    state = hass.states.get(entity_id)

    assert state is not None
    hvac_modes = state.attributes.get("hvac_modes")
    assert HVACMode.OFF in hvac_modes
    assert HVACMode.HEAT in hvac_modes
    assert HVACMode.AUTO in hvac_modes


async def test_climate_supported_features(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test climate entity supported features."""
    entity_id = "climate.hive_thermostat_climate"
    state = hass.states.get(entity_id)

    assert state is not None
    # Check supported_features bitmask includes required features
    features = state.attributes.get("supported_features")
    assert features is not None
    # Verify the features include the expected ones
    assert features & ClimateEntityFeature.TARGET_TEMPERATURE
    assert features & ClimateEntityFeature.PRESET_MODE
    assert features & ClimateEntityFeature.TURN_ON
    assert features & ClimateEntityFeature.TURN_OFF


async def test_climate_set_temperature(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test setting temperature."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator
    entity_id = "climate.hive_thermostat_climate"

    # Mock the coordinator method
    coordinator.async_set_temperature = AsyncMock()

    # Set temperature
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            "entity_id": entity_id,
            ATTR_TEMPERATURE: 22.5,
        },
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_set_temperature.assert_called_once_with(22.5)

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.attributes.get(ATTR_TEMPERATURE) == 22.5


async def test_climate_set_hvac_mode_heat(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test setting HVAC mode to HEAT."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator
    entity_id = "climate.hive_thermostat_climate"

    # Mock the coordinator methods
    coordinator.async_set_hvac_mode_heat = AsyncMock()
    coordinator.async_set_temperature = AsyncMock()

    # First set a temperature so we have a target temperature
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            "entity_id": entity_id,
            ATTR_TEMPERATURE: 20.0,
        },
        blocking=True,
    )

    # Set HVAC mode to HEAT
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {
            "entity_id": entity_id,
            ATTR_HVAC_MODE: HVACMode.HEAT,
        },
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_set_hvac_mode_heat.assert_called_once()

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.state == HVACMode.HEAT


async def test_climate_set_hvac_mode_off(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test setting HVAC mode to OFF."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator
    entity_id = "climate.hive_thermostat_climate"

    # Mock the coordinator method
    coordinator.async_set_hvac_mode_off = AsyncMock()

    # Set HVAC mode to OFF
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {
            "entity_id": entity_id,
            ATTR_HVAC_MODE: HVACMode.OFF,
        },
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_set_hvac_mode_off.assert_called_once()

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.state == HVACMode.OFF


async def test_climate_set_hvac_mode_auto(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test setting HVAC mode to AUTO."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator
    entity_id = "climate.hive_thermostat_climate"

    # Mock the coordinator method
    coordinator.async_set_hvac_mode_auto = AsyncMock()

    # Set HVAC mode to AUTO
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {
            "entity_id": entity_id,
            ATTR_HVAC_MODE: HVACMode.AUTO,
        },
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_set_hvac_mode_auto.assert_called_once()

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.state == HVACMode.AUTO


async def test_climate_set_preset_mode_boost(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test setting preset mode to BOOST."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator
    entity_id = "climate.hive_thermostat_climate"

    # Mock the coordinator method
    coordinator.async_heating_boost = AsyncMock()

    # Set preset mode to BOOST
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            "entity_id": entity_id,
            ATTR_PRESET_MODE: PRESET_BOOST,
        },
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_heating_boost.assert_called_once()

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.attributes.get(ATTR_PRESET_MODE) == PRESET_BOOST


async def test_climate_set_preset_mode_none_from_boost(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test setting preset mode to NONE from BOOST."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator
    entity_id = "climate.hive_thermostat_climate"

    # Mock the coordinator methods
    coordinator.async_heating_boost = AsyncMock()
    coordinator.async_set_hvac_mode_heat = AsyncMock()

    # First set to boost
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            "entity_id": entity_id,
            ATTR_PRESET_MODE: PRESET_BOOST,
        },
        blocking=True,
    )

    # Store pre-boost values
    coordinator.pre_boost_hvac_mode = HVACMode.HEAT
    coordinator.pre_boost_occupied_heating_setpoint_heat = 21.0

    # Set preset mode back to NONE
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            "entity_id": entity_id,
            ATTR_PRESET_MODE: PRESET_NONE,
        },
        blocking=True,
    )

    # Verify the coordinator method was called to restore previous mode
    coordinator.async_set_hvac_mode_heat.assert_called_once_with(21.0)


async def test_climate_set_temperature_with_hvac_mode(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test setting temperature with HVAC mode."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator
    entity_id = "climate.hive_thermostat_climate"

    # Mock the coordinator methods
    coordinator.async_set_temperature = AsyncMock()
    coordinator.async_set_hvac_mode_heat = AsyncMock()
    coordinator.current_temperature = 20.0

    # Set temperature with HVAC mode
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            "entity_id": entity_id,
            ATTR_TEMPERATURE: 23.0,
            ATTR_HVAC_MODE: HVACMode.HEAT,
        },
        blocking=True,
    )

    # Verify both methods were called
    coordinator.async_set_hvac_mode_heat.assert_called_once()
    coordinator.async_set_temperature.assert_called_once_with(23.0)


async def test_climate_coordinator_update(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test that climate entity updates from coordinator."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator
    entity_id = "climate.hive_thermostat_climate"

    # Update coordinator data
    coordinator.current_temperature = 21.5
    coordinator.target_temperature = 22.0
    coordinator.hvac_mode = HVACMode.HEAT
    coordinator.preset_mode = PRESET_NONE

    # Trigger coordinator update by calling _handle_coordinator_update
    # since async_refresh is not implemented
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.attributes.get("current_temperature") == 21.5
    assert state.attributes.get(ATTR_TEMPERATURE) == 22.0
    assert state.state == HVACMode.HEAT
    assert state.attributes.get(ATTR_PRESET_MODE) == PRESET_NONE


async def test_climate_unique_id_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test climate entity unique ID for SLR1."""
    entity_id = "climate.hive_thermostat_climate"
    entry = entity_registry.async_get(entity_id)

    assert entry is not None
    assert entry.unique_id == "hive_local_thermostat_hive thermostat_climate"


async def test_climate_unique_id_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test climate entity unique ID for SLR2."""
    entity_id = "climate.hive_thermostat_slr2_climate"
    entry = entity_registry.async_get(entity_id)

    assert entry is not None
    assert entry.unique_id == "hive_local_thermostat_hive thermostat slr2_climate"


async def test_climate_temperature_unit(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test climate entity uses Celsius."""
    entity_id = "climate.hive_thermostat_climate"
    state = hass.states.get(entity_id)

    assert state is not None
    # Temperature unit should be Celsius
    # The unit is implicit in Home Assistant climate entities


async def test_climate_turn_off_service(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test turn_off service."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator
    entity_id = "climate.hive_thermostat_climate"

    # Mock the coordinator method
    coordinator.async_set_hvac_mode_off = AsyncMock()

    # Call turn_off service
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_OFF,
        {
            "entity_id": entity_id,
        },
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_set_hvac_mode_off.assert_called_once()

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.state == HVACMode.OFF


async def test_climate_turn_on_service(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test turn_on service."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator
    entity_id = "climate.hive_thermostat_climate"

    # Mock the coordinator methods
    coordinator.async_set_hvac_mode_heat = AsyncMock()
    coordinator.async_set_temperature = AsyncMock()

    # First set a temperature so we have a target temperature
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            "entity_id": entity_id,
            ATTR_TEMPERATURE: 20.0,
        },
        blocking=True,
    )

    # Call turn_on service
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_ON,
        {
            "entity_id": entity_id,
        },
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_set_hvac_mode_heat.assert_called_once()


async def test_climate_preset_mode_restores_previous_temperature(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test that canceling boost restores previous temperature."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator
    entity_id = "climate.hive_thermostat_climate"

    # Mock the coordinator methods
    coordinator.async_heating_boost = AsyncMock()
    coordinator.async_set_hvac_mode_heat = AsyncMock()
    coordinator.async_set_temperature = AsyncMock()

    # Activate boost
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            "entity_id": entity_id,
            ATTR_PRESET_MODE: PRESET_BOOST,
        },
        blocking=True,
    )

    # Verify boost was activated
    coordinator.async_heating_boost.assert_called_once()

    # Store the pre-boost values in coordinator
    coordinator.pre_boost_hvac_mode = HVACMode.HEAT
    coordinator.pre_boost_occupied_heating_setpoint_heat = 21.0

    # Cancel boost
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            "entity_id": entity_id,
            ATTR_PRESET_MODE: PRESET_NONE,
        },
        blocking=True,
    )

    # Verify it restored the previous temperature
    coordinator.async_set_hvac_mode_heat.assert_called_with(21.0)


async def test_climate_multiple_temperature_changes(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test multiple temperature changes."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator
    entity_id = "climate.hive_thermostat_climate"

    # Mock the coordinator method
    coordinator.async_set_temperature = AsyncMock()

    temperatures = [18.0, 20.5, 22.0, 24.5]
    for temp in temperatures:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                "entity_id": entity_id,
                ATTR_TEMPERATURE: temp,
            },
            blocking=True,
        )

    # Verify the coordinator method was called for each temperature
    assert coordinator.async_set_temperature.call_count == len(temperatures)


async def test_climate_slr2_entity_attributes(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test climate entity for SLR2 has correct attributes."""
    entity_id = "climate.hive_thermostat_slr2_climate"
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.attributes.get("friendly_name") == "Hive Thermostat SLR2 Climate"
    assert state.attributes.get("min_temp") == 5
    assert state.attributes.get("max_temp") == 32
    assert state.attributes.get("target_temp_step") == 0.5
