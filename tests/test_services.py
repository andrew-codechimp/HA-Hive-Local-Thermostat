"""Tests for the services."""

from unittest.mock import AsyncMock

import pytest
from custom_components.hive_local_thermostat.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError


async def test_service_boost_heating_with_defaults(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test boost_heating service with default values."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_heating_boost = AsyncMock()

    # Call the service
    await hass.services.async_call(
        DOMAIN,
        "boost_heating",
        {"config_entry_id": config_entry.entry_id},
        blocking=True,
    )

    # Verify the coordinator method was called with defaults
    coordinator.async_heating_boost.assert_called_once_with(
        coordinator.heating_boost_duration,
        coordinator.heating_boost_temperature,
    )


async def test_service_boost_heating_with_custom_values(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test boost_heating service with custom values."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_heating_boost = AsyncMock()

    # Call the service with custom values
    await hass.services.async_call(
        DOMAIN,
        "boost_heating",
        {
            "config_entry_id": config_entry.entry_id,
            "minutes_to_boost": 60,
            "temperature_to_boost": 28.5,
        },
        blocking=True,
    )

    # Verify the coordinator method was called with custom values
    coordinator.async_heating_boost.assert_called_once_with(60, 28.5)


async def test_service_boost_heating_with_minutes_only(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test boost_heating service with only minutes specified."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_heating_boost = AsyncMock()

    # Call the service with only minutes
    await hass.services.async_call(
        DOMAIN,
        "boost_heating",
        {
            "config_entry_id": config_entry.entry_id,
            "minutes_to_boost": 45,
        },
        blocking=True,
    )

    # Verify the coordinator method was called with custom minutes and default temperature
    coordinator.async_heating_boost.assert_called_once_with(
        45,
        coordinator.heating_boost_temperature,
    )


async def test_service_boost_heating_with_temperature_only(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test boost_heating service with only temperature specified."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_heating_boost = AsyncMock()

    # Call the service with only temperature
    await hass.services.async_call(
        DOMAIN,
        "boost_heating",
        {
            "config_entry_id": config_entry.entry_id,
            "temperature_to_boost": 30.0,
        },
        blocking=True,
    )

    # Verify the coordinator method was called with default minutes and custom temperature
    coordinator.async_heating_boost.assert_called_once_with(
        coordinator.heating_boost_duration,
        30.0,
    )


async def test_service_cancel_boost_heating(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test cancel_boost_heating service."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_heating_boost_cancel = AsyncMock()

    # Call the service
    await hass.services.async_call(
        DOMAIN,
        "cancel_boost_heating",
        {"config_entry_id": config_entry.entry_id},
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_heating_boost_cancel.assert_called_once()


async def test_service_boost_water_with_defaults_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test boost_water service with default values for SLR2."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_water_boost = AsyncMock()

    # Call the service
    await hass.services.async_call(
        DOMAIN,
        "boost_water",
        {"config_entry_id": config_entry.entry_id},
        blocking=True,
    )

    # Verify the coordinator method was called with defaults
    coordinator.async_water_boost.assert_called_once_with(
        coordinator.water_boost_duration,
    )


async def test_service_boost_water_with_custom_minutes_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test boost_water service with custom minutes for SLR2."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_water_boost = AsyncMock()

    # Call the service with custom minutes
    await hass.services.async_call(
        DOMAIN,
        "boost_water",
        {
            "config_entry_id": config_entry.entry_id,
            "minutes_to_boost": 90,
        },
        blocking=True,
    )

    # Verify the coordinator method was called with custom minutes
    coordinator.async_water_boost.assert_called_once_with(90)


async def test_service_boost_water_fails_for_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test boost_water service fails for SLR1 model."""
    config_entry = setup_integration_slr1

    # Call the service should raise an error for SLR1
    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "boost_water",
            {"config_entry_id": config_entry.entry_id},
            blocking=True,
        )

    assert exc_info.value.translation_key == "wrong_model"


async def test_service_cancel_boost_water_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test cancel_boost_water service for SLR2."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_water_boost_cancel = AsyncMock()

    # Call the service
    await hass.services.async_call(
        DOMAIN,
        "cancel_boost_water",
        {"config_entry_id": config_entry.entry_id},
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_water_boost_cancel.assert_called_once()


async def test_service_cancel_boost_water_fails_for_slr1(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test cancel_boost_water service fails for SLR1 model."""
    config_entry = setup_integration_slr1

    # Call the service should raise an error for SLR1
    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "cancel_boost_water",
            {"config_entry_id": config_entry.entry_id},
            blocking=True,
        )

    assert exc_info.value.translation_key == "wrong_model"


async def test_service_invalid_config_entry_id(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test services fail with invalid config entry ID."""
    # Call the service with invalid config entry ID
    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "boost_heating",
            {"config_entry_id": "invalid_entry_id"},
            blocking=True,
        )

    assert exc_info.value.translation_key == "integration_not_found"


async def test_service_boost_heating_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test boost_heating service works for SLR2 model."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_heating_boost = AsyncMock()

    # Call the service
    await hass.services.async_call(
        DOMAIN,
        "boost_heating",
        {
            "config_entry_id": config_entry.entry_id,
            "minutes_to_boost": 75,
            "temperature_to_boost": 26.0,
        },
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_heating_boost.assert_called_once_with(75, 26.0)


async def test_service_cancel_boost_heating_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test cancel_boost_heating service works for SLR2 model."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_heating_boost_cancel = AsyncMock()

    # Call the service
    await hass.services.async_call(
        DOMAIN,
        "cancel_boost_heating",
        {"config_entry_id": config_entry.entry_id},
        blocking=True,
    )

    # Verify the coordinator method was called
    coordinator.async_heating_boost_cancel.assert_called_once()


async def test_services_registered(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test that all services are registered."""
    # Verify all services are registered
    assert hass.services.has_service(DOMAIN, "boost_heating")
    assert hass.services.has_service(DOMAIN, "cancel_boost_heating")
    assert hass.services.has_service(DOMAIN, "boost_water")
    assert hass.services.has_service(DOMAIN, "cancel_boost_water")


async def test_service_boost_heating_multiple_calls(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
) -> None:
    """Test boost_heating service can be called multiple times."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_heating_boost = AsyncMock()

    # Call the service multiple times with different values
    await hass.services.async_call(
        DOMAIN,
        "boost_heating",
        {
            "config_entry_id": config_entry.entry_id,
            "minutes_to_boost": 30,
            "temperature_to_boost": 22.0,
        },
        blocking=True,
    )

    await hass.services.async_call(
        DOMAIN,
        "boost_heating",
        {
            "config_entry_id": config_entry.entry_id,
            "minutes_to_boost": 60,
            "temperature_to_boost": 24.0,
        },
        blocking=True,
    )

    await hass.services.async_call(
        DOMAIN,
        "boost_heating",
        {
            "config_entry_id": config_entry.entry_id,
            "minutes_to_boost": 90,
            "temperature_to_boost": 26.0,
        },
        blocking=True,
    )

    # Verify the coordinator method was called three times
    assert coordinator.async_heating_boost.call_count == 3


async def test_service_boost_water_multiple_calls_slr2(
    hass: HomeAssistant,
    setup_integration_slr2: MockConfigEntry,
) -> None:
    """Test boost_water service can be called multiple times for SLR2."""
    config_entry = setup_integration_slr2
    coordinator = config_entry.runtime_data.coordinator

    # Mock the coordinator method
    coordinator.async_water_boost = AsyncMock()

    # Call the service multiple times with different values
    await hass.services.async_call(
        DOMAIN,
        "boost_water",
        {
            "config_entry_id": config_entry.entry_id,
            "minutes_to_boost": 30,
        },
        blocking=True,
    )

    await hass.services.async_call(
        DOMAIN,
        "boost_water",
        {
            "config_entry_id": config_entry.entry_id,
            "minutes_to_boost": 60,
        },
        blocking=True,
    )

    # Verify the coordinator method was called twice
    assert coordinator.async_water_boost.call_count == 2
