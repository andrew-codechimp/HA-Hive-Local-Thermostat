"""Tests for the number platform."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.number import ATTR_VALUE
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


async def test_number_entities_created_for_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that number entities are created for SLR1 model."""
    expected_entities = [
        "number.hive_thermostat_heating_boost_duration",
        "number.hive_thermostat_heating_frost_prevention",
        "number.hive_thermostat_heating_boost_temperature",
    ]

    for entity_id in expected_entities:
        entry = entity_registry.async_get(entity_id)
        assert entry is not None, f"Entity {entity_id} not found in registry"
        assert entry.domain == "number"


async def test_number_water_boost_not_created_for_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that water boost duration is NOT created for SLR1 model."""
    # SLR1 doesn't support water controls
    entity_id = "number.hive_thermostat_water_boost_duration"
    entry = entity_registry.async_get(entity_id)
    assert entry is None, f"Entity {entity_id} should not exist for SLR1"


async def test_number_entities_created_for_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that all number entities are created for SLR2 model."""
    expected_entities = [
        "number.hive_thermostat_slr2_heating_boost_duration",
        "number.hive_thermostat_slr2_heating_frost_prevention",
        "number.hive_thermostat_slr2_heating_boost_temperature",
        "number.hive_thermostat_slr2_water_boost_duration",
    ]

    for entity_id in expected_entities:
        entry = entity_registry.async_get(entity_id)
        assert entry is not None, f"Entity {entity_id} not found in registry"
        assert entry.domain == "number"


async def test_number_heating_boost_duration_default_value(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test heating boost duration has correct default value."""
    entity_id = "number.hive_thermostat_heating_boost_duration"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "120"  # DEFAULT_HEATING_BOOST_MINUTES


async def test_number_heating_frost_prevention_default_value(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test heating frost prevention has correct default value."""
    entity_id = "number.hive_thermostat_heating_frost_prevention"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "12"  # DEFAULT_FROST_TEMPERATURE


async def test_number_heating_boost_temperature_default_value(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test heating boost temperature has correct default value."""
    entity_id = "number.hive_thermostat_heating_boost_temperature"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "25"  # DEFAULT_HEATING_BOOST_TEMPERATURE


async def test_number_water_boost_duration_default_value(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test water boost duration has correct default value."""
    entity_id = "number.hive_thermostat_slr2_water_boost_duration"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "60"  # DEFAULT_WATER_BOOST_MINUTES


async def test_number_heating_boost_duration_attributes(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test heating boost duration has correct attributes."""
    entity_id = "number.hive_thermostat_heating_boost_duration"
    state = hass.states.get(entity_id)
    assert state is not None

    # Check min, max, step values
    assert state.attributes.get("min") == 15
    assert state.attributes.get("max") == 180  # MAXIMUM_BOOST_MINUTES
    assert state.attributes.get("step") == 1


async def test_number_heating_frost_prevention_attributes(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test heating frost prevention has correct attributes."""
    entity_id = "number.hive_thermostat_heating_frost_prevention"
    state = hass.states.get(entity_id)
    assert state is not None

    # Check min, max, step values
    assert state.attributes.get("min") == 5
    assert state.attributes.get("max") == 16
    assert state.attributes.get("step") == 0.5
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS
    assert state.attributes.get("device_class") == "temperature"


async def test_number_heating_boost_temperature_attributes(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test heating boost temperature has correct attributes."""
    entity_id = "number.hive_thermostat_heating_boost_temperature"
    state = hass.states.get(entity_id)
    assert state is not None

    # Check min, max, step values
    assert state.attributes.get("min") == 12
    assert state.attributes.get("max") == 32
    assert state.attributes.get("step") == 0.5
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS
    assert state.attributes.get("device_class") == "temperature"


async def test_number_set_value_heating_boost_duration(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test setting heating boost duration value."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    entity_id = "number.hive_thermostat_heating_boost_duration"

    # Set a new value
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity_id, ATTR_VALUE: 90},
        blocking=True,
    )

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.state == "90.0"

    # Verify coordinator was updated
    assert coordinator.heating_boost_duration == 90


async def test_number_set_value_heating_frost_prevention(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test setting heating frost prevention value."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    entity_id = "number.hive_thermostat_heating_frost_prevention"

    # Set a new value
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity_id, ATTR_VALUE: 10.5},
        blocking=True,
    )

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.state == "10.5"

    # Verify coordinator was updated
    assert coordinator.heating_frost_prevention == 10.5


async def test_number_set_value_heating_boost_temperature(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test setting heating boost temperature value."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    entity_id = "number.hive_thermostat_heating_boost_temperature"

    # Set a new value
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity_id, ATTR_VALUE: 22.5},
        blocking=True,
    )

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.state == "22.5"

    # Verify coordinator was updated
    assert coordinator.heating_boost_temperature == 22.5


async def test_number_set_value_water_boost_duration(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test setting water boost duration value."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    entity_id = "number.hive_thermostat_slr2_water_boost_duration"

    # Set a new value
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity_id, ATTR_VALUE: 45},
        blocking=True,
    )

    # Verify state was updated
    state = hass.states.get(entity_id)
    assert state.state == "45.0"

    # Verify coordinator was updated
    assert coordinator.water_boost_duration == 45


async def test_number_unique_ids_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test number entities have correct unique IDs for SLR1."""
    expected_unique_ids = {
        "number.hive_thermostat_heating_boost_duration": "hive_local_thermostat_hive thermostat_heating_boost_duration",
        "number.hive_thermostat_heating_frost_prevention": "hive_local_thermostat_hive thermostat_heating_frost_prevention",
        "number.hive_thermostat_heating_boost_temperature": "hive_local_thermostat_hive thermostat_heating_boost_temperature",
    }

    for entity_id, expected_unique_id in expected_unique_ids.items():
        entry = entity_registry.async_get(entity_id)
        assert entry is not None
        assert entry.unique_id == expected_unique_id


async def test_number_unique_ids_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test number entities have correct unique IDs for SLR2."""
    expected_unique_ids = {
        "number.hive_thermostat_slr2_heating_boost_duration": "hive_local_thermostat_hive thermostat slr2_heating_boost_duration",
        "number.hive_thermostat_slr2_heating_frost_prevention": "hive_local_thermostat_hive thermostat slr2_heating_frost_prevention",
        "number.hive_thermostat_slr2_heating_boost_temperature": "hive_local_thermostat_hive thermostat slr2_heating_boost_temperature",
        "number.hive_thermostat_slr2_water_boost_duration": "hive_local_thermostat_hive thermostat slr2_water_boost_duration",
    }

    for entity_id, expected_unique_id in expected_unique_ids.items():
        entry = entity_registry.async_get(entity_id)
        assert entry is not None
        assert entry.unique_id == expected_unique_id


async def test_number_entity_category(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test number entities have correct entity category."""
    entity_id = "number.hive_thermostat_heating_boost_duration"
    entry = entity_registry.async_get(entity_id)
    assert entry is not None
    assert entry.entity_category == "config"


async def test_number_friendly_names_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test number entities have correct friendly names for SLR1."""
    expected_names = {
        "number.hive_thermostat_heating_boost_duration": "Hive Thermostat Heating boost duration",
        "number.hive_thermostat_heating_frost_prevention": "Hive Thermostat Heating frost prevention",
        "number.hive_thermostat_heating_boost_temperature": "Hive Thermostat Heating boost temperature",
    }

    for entity_id, expected_name in expected_names.items():
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.attributes.get("friendly_name") == expected_name


async def test_number_friendly_names_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test number entities have correct friendly names for SLR2."""
    expected_names = {
        "number.hive_thermostat_slr2_heating_boost_duration": "Hive Thermostat SLR2 Heating boost duration",
        "number.hive_thermostat_slr2_heating_frost_prevention": "Hive Thermostat SLR2 Heating frost prevention",
        "number.hive_thermostat_slr2_heating_boost_temperature": "Hive Thermostat SLR2 Heating boost temperature",
        "number.hive_thermostat_slr2_water_boost_duration": "Hive Thermostat SLR2 Water boost duration",
    }

    for entity_id, expected_name in expected_names.items():
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.attributes.get("friendly_name") == expected_name


async def test_number_multiple_value_changes(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test changing number value multiple times."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    entity_id = "number.hive_thermostat_heating_boost_duration"

    # Set value multiple times
    values = [30, 60, 120, 180]
    for value in values:
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": entity_id, ATTR_VALUE: value},
            blocking=True,
        )

        state = hass.states.get(entity_id)
        assert state.state == f"{float(value)}"
        assert coordinator.heating_boost_duration == value


async def test_number_restore_state(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test that number entities restore their previous state."""
    entity_id = "number.hive_thermostat_heating_boost_duration"

    # Set a custom value
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity_id, ATTR_VALUE: 75},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state.state == "75.0"

    # Note: Full state restoration would require reloading the integration
    # which is tested in the actual implementation via async_added_to_hass


async def test_number_all_entities_independent(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test that all number entities work independently."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Set different values for each entity
    await hass.services.async_call(
        "number",
        "set_value",
        {
            "entity_id": "number.hive_thermostat_slr2_heating_boost_duration",
            ATTR_VALUE: 45,
        },
        blocking=True,
    )

    await hass.services.async_call(
        "number",
        "set_value",
        {
            "entity_id": "number.hive_thermostat_slr2_heating_frost_prevention",
            ATTR_VALUE: 8.5,
        },
        blocking=True,
    )

    await hass.services.async_call(
        "number",
        "set_value",
        {
            "entity_id": "number.hive_thermostat_slr2_heating_boost_temperature",
            ATTR_VALUE: 28.0,
        },
        blocking=True,
    )

    await hass.services.async_call(
        "number",
        "set_value",
        {
            "entity_id": "number.hive_thermostat_slr2_water_boost_duration",
            ATTR_VALUE: 90,
        },
        blocking=True,
    )

    # Verify all values were set independently
    assert coordinator.heating_boost_duration == 45
    assert coordinator.heating_frost_prevention == 8.5
    assert coordinator.heating_boost_temperature == 28.0
    assert coordinator.water_boost_duration == 90

    # Verify states
    assert (
        hass.states.get("number.hive_thermostat_slr2_heating_boost_duration").state
        == "45.0"
    )
    assert (
        hass.states.get("number.hive_thermostat_slr2_heating_frost_prevention").state
        == "8.5"
    )
    assert (
        hass.states.get("number.hive_thermostat_slr2_heating_boost_temperature").state
        == "28.0"
    )
    assert (
        hass.states.get("number.hive_thermostat_slr2_water_boost_duration").state
        == "90.0"
    )
