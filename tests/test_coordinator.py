"""Tests for Hive Local Thermostat coordinator."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from custom_components.hive_local_thermostat.const import DOMAIN, MODEL_SLR1, MODEL_SLR2
from custom_components.hive_local_thermostat.coordinator import (
    BOOST_ERROR,
    HiveCoordinator,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.util.dt import utcnow


@pytest.fixture
def coordinator_slr1(hass: HomeAssistant) -> HiveCoordinator:
    """Create a coordinator instance for SLR1 model."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    return HiveCoordinator(
        hass=hass,
        entry_id=entry.entry_id,
        model=MODEL_SLR1,
        topic="hive/thermostat",
        show_heat_schedule_mode=True,
        show_water_schedule_mode=False,
    )


@pytest.fixture
def coordinator_slr2(hass: HomeAssistant) -> HiveCoordinator:
    """Create a coordinator instance for SLR2 model."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    return HiveCoordinator(
        hass=hass,
        entry_id=entry.entry_id,
        model=MODEL_SLR2,
        topic="hive/thermostat",
        show_heat_schedule_mode=True,
        show_water_schedule_mode=True,
    )


async def test_correct_heat_boost_normal_value(
    hass: HomeAssistant,
    coordinator_slr1: HiveCoordinator,
) -> None:
    """Test correct_heat_boost with normal boost remaining value."""
    # Reported value is below BOOST_ERROR threshold
    reported_boost = 45
    reported_temperature = 22.0

    result = coordinator_slr1.correct_heat_boost(reported_boost, reported_temperature)

    # Should not trigger correction
    assert result is False
    # Should set heat_boost_remaining to reported value
    assert coordinator_slr1.heat_boost_remaining == reported_boost


async def test_correct_heat_boost_error_value_with_tracking(
    hass: HomeAssistant,
    coordinator_slr1: HiveCoordinator,
    freezer,
) -> None:
    """Test correct_heat_boost with error value when boost tracking is active."""
    # Set up boost tracking state
    boost_start_time = utcnow() - timedelta(minutes=15)  # Started 15 minutes ago
    coordinator_slr1.heat_boost_started = boost_start_time
    coordinator_slr1.heat_boost_started_duration = 60  # Originally 60 minutes
    reported_boost = 65535  # Error value > BOOST_ERROR
    reported_temperature = 22.0

    with patch.object(coordinator_slr1.hass, "async_create_task") as mock_create_task:
        result = coordinator_slr1.correct_heat_boost(
            reported_boost, reported_temperature
        )

        # Should trigger correction
        assert result is True
        # Should calculate remaining time: 60 - 15 = 45 minutes (±1 for test execution)
        assert 44 <= coordinator_slr1.heat_boost_remaining <= 45
        # Should create task to send corrected boost command
        mock_create_task.assert_called_once()


async def test_correct_heat_boost_error_value_without_tracking(
    hass: HomeAssistant,
    coordinator_slr1: HiveCoordinator,
) -> None:
    """Test correct_heat_boost with error value when boost tracking is not active."""
    # No boost tracking state set
    coordinator_slr1.heat_boost_started = None
    coordinator_slr1.heat_boost_started_duration = 0
    reported_boost = 65535  # Error value > BOOST_ERROR
    reported_temperature = 22.0

    with patch.object(coordinator_slr1.hass, "async_create_task") as mock_create_task:
        result = coordinator_slr1.correct_heat_boost(
            reported_boost, reported_temperature
        )

        # Should trigger correction
        assert result is True
        # Should set remaining to 0 when no tracking data
        assert coordinator_slr1.heat_boost_remaining == 0
        # Should create task to send corrected boost command
        mock_create_task.assert_called_once()


async def test_correct_heat_boost_error_value_boost_expired(
    hass: HomeAssistant,
    coordinator_slr1: HiveCoordinator,
) -> None:
    """Test correct_heat_boost with error value when boost has expired."""
    # Set up boost tracking state where boost has expired
    boost_start_time = utcnow() - timedelta(minutes=75)  # Started 75 minutes ago
    coordinator_slr1.heat_boost_started = boost_start_time
    coordinator_slr1.heat_boost_started_duration = 60  # Originally 60 minutes
    reported_boost = 65535  # Error value > BOOST_ERROR
    reported_temperature = 22.0

    with patch.object(coordinator_slr1.hass, "async_create_task") as mock_create_task:
        result = coordinator_slr1.correct_heat_boost(
            reported_boost, reported_temperature
        )

        # Should trigger correction
        assert result is True
        # Should calculate negative time but store as -15
        # (elapsed 75 - duration 60 = -15)
        assert coordinator_slr1.heat_boost_remaining == -15
        # Should create task to send corrected boost command
        mock_create_task.assert_called_once()


async def test_correct_heat_boost_at_error_threshold(
    hass: HomeAssistant,
    coordinator_slr1: HiveCoordinator,
) -> None:
    """Test correct_heat_boost exactly at BOOST_ERROR threshold."""
    # Reported value is exactly BOOST_ERROR
    reported_boost = BOOST_ERROR
    reported_temperature = 22.0

    result = coordinator_slr1.correct_heat_boost(reported_boost, reported_temperature)

    # Should not trigger correction (needs to be > BOOST_ERROR)
    assert result is False
    # Should set heat_boost_remaining to reported value
    assert coordinator_slr1.heat_boost_remaining == reported_boost


async def test_correct_heat_boost_just_above_threshold(
    hass: HomeAssistant,
    coordinator_slr1: HiveCoordinator,
) -> None:
    """Test correct_heat_boost just above BOOST_ERROR threshold."""
    # Set up boost tracking
    boost_start_time = utcnow() - timedelta(minutes=10)
    coordinator_slr1.heat_boost_started = boost_start_time
    coordinator_slr1.heat_boost_started_duration = 30
    # Reported value is just above BOOST_ERROR
    reported_boost = BOOST_ERROR + 1
    reported_temperature = 22.0

    with patch.object(coordinator_slr1.hass, "async_create_task") as mock_create_task:
        result = coordinator_slr1.correct_heat_boost(
            reported_boost, reported_temperature
        )

        # Should trigger correction
        assert result is True
        # Should calculate remaining time: 30 - 10 = 20 minutes (±1 for test execution)
        assert 19 <= coordinator_slr1.heat_boost_remaining <= 20
        # Should create task to send corrected boost command
        mock_create_task.assert_called_once()


async def test_correct_heat_boost_slr2_model(
    hass: HomeAssistant,
    coordinator_slr2: HiveCoordinator,
) -> None:
    """Test correct_heat_boost works correctly with SLR2 model."""
    # Set up boost tracking for SLR2
    boost_start_time = utcnow() - timedelta(minutes=20)
    coordinator_slr2.heat_boost_started = boost_start_time
    coordinator_slr2.heat_boost_started_duration = 120
    reported_boost = 65535  # Error value
    reported_temperature = 24.0

    with patch.object(coordinator_slr2.hass, "async_create_task") as mock_create_task:
        result = coordinator_slr2.correct_heat_boost(
            reported_boost, reported_temperature
        )

        # Should trigger correction
        assert result is True
        # Should calculate remaining time: 120 - 20 = 100 minutes (±1 for test execution)
        assert 99 <= coordinator_slr2.heat_boost_remaining <= 100
        # Should create task to send corrected boost command
        mock_create_task.assert_called_once()


async def test_correct_heat_boost_zero_value(
    hass: HomeAssistant,
    coordinator_slr1: HiveCoordinator,
) -> None:
    """Test correct_heat_boost with zero boost remaining."""
    reported_boost = 0
    reported_temperature = 22.0

    result = coordinator_slr1.correct_heat_boost(reported_boost, reported_temperature)

    # Should not trigger correction
    assert result is False
    # Should set heat_boost_remaining to 0
    assert coordinator_slr1.heat_boost_remaining == 0


async def test_correct_water_boost_normal_value(
    hass: HomeAssistant,
    coordinator_slr2: HiveCoordinator,
) -> None:
    """Test correct_water_boost with normal boost remaining value."""
    # Reported value is below BOOST_ERROR threshold
    reported_boost = 30

    result = coordinator_slr2.correct_water_boost(reported_boost)

    # Should not trigger correction
    assert result is False
    # Should set water_boost_remaining to reported value
    assert coordinator_slr2.water_boost_remaining == reported_boost


async def test_correct_water_boost_error_value_with_tracking(
    hass: HomeAssistant,
    coordinator_slr2: HiveCoordinator,
) -> None:
    """Test correct_water_boost with error value when boost tracking is active."""
    # Set up boost tracking state
    boost_start_time = utcnow() - timedelta(minutes=10)  # Started 10 minutes ago
    coordinator_slr2.water_boost_started = boost_start_time
    coordinator_slr2.water_boost_started_duration = 40  # Originally 40 minutes
    reported_boost = 65535  # Error value > BOOST_ERROR

    with patch.object(coordinator_slr2.hass, "async_create_task") as mock_create_task:
        result = coordinator_slr2.correct_water_boost(reported_boost)

        # Should trigger correction
        assert result is True
        # Should calculate remaining time: 40 - 10 = 30 minutes (±1 for test execution)
        assert 29 <= coordinator_slr2.water_boost_remaining <= 30
        # Should create task to send corrected boost command
        mock_create_task.assert_called_once()


async def test_correct_water_boost_error_value_without_tracking(
    hass: HomeAssistant,
    coordinator_slr2: HiveCoordinator,
) -> None:
    """Test correct_water_boost with error value when boost tracking is not active."""
    # No boost tracking state set
    coordinator_slr2.water_boost_started = None
    coordinator_slr2.water_boost_started_duration = 0
    reported_boost = 65535  # Error value > BOOST_ERROR

    with patch.object(coordinator_slr2.hass, "async_create_task") as mock_create_task:
        result = coordinator_slr2.correct_water_boost(reported_boost)

        # Should trigger correction
        assert result is True
        # Should set remaining to 0 when no tracking data
        assert coordinator_slr2.water_boost_remaining == 0
        # Should create task to send corrected boost command
        mock_create_task.assert_called_once()


async def test_correct_water_boost_error_value_boost_expired(
    hass: HomeAssistant,
    coordinator_slr2: HiveCoordinator,
) -> None:
    """Test correct_water_boost with error value when boost has expired."""
    # Set up boost tracking state where boost has expired
    boost_start_time = utcnow() - timedelta(minutes=50)  # Started 50 minutes ago
    coordinator_slr2.water_boost_started = boost_start_time
    coordinator_slr2.water_boost_started_duration = 40  # Originally 40 minutes
    reported_boost = 65535  # Error value > BOOST_ERROR

    with patch.object(coordinator_slr2.hass, "async_create_task") as mock_create_task:
        result = coordinator_slr2.correct_water_boost(reported_boost)

        # Should trigger correction
        assert result is True
        # Should calculate negative time but store as -10
        # (elapsed 50 - duration 40 = -10)
        assert coordinator_slr2.water_boost_remaining == -10
        # Should create task to send corrected boost command
        mock_create_task.assert_called_once()


async def test_correct_water_boost_at_error_threshold(
    hass: HomeAssistant,
    coordinator_slr2: HiveCoordinator,
) -> None:
    """Test correct_water_boost exactly at BOOST_ERROR threshold."""
    # Reported value is exactly BOOST_ERROR
    reported_boost = BOOST_ERROR

    result = coordinator_slr2.correct_water_boost(reported_boost)

    # Should not trigger correction (needs to be > BOOST_ERROR)
    assert result is False
    # Should set water_boost_remaining to reported value
    assert coordinator_slr2.water_boost_remaining == reported_boost


async def test_correct_water_boost_just_above_threshold(
    hass: HomeAssistant,
    coordinator_slr2: HiveCoordinator,
) -> None:
    """Test correct_water_boost just above BOOST_ERROR threshold."""
    # Set up boost tracking
    boost_start_time = utcnow() - timedelta(minutes=5)
    coordinator_slr2.water_boost_started = boost_start_time
    coordinator_slr2.water_boost_started_duration = 25
    # Reported value is just above BOOST_ERROR
    reported_boost = BOOST_ERROR + 1

    with patch.object(coordinator_slr2.hass, "async_create_task") as mock_create_task:
        result = coordinator_slr2.correct_water_boost(reported_boost)

        # Should trigger correction
        assert result is True
        # Should calculate remaining time: 25 - 5 = 20 minutes (±1 for test execution)
        assert 19 <= coordinator_slr2.water_boost_remaining <= 20
        # Should create task to send corrected boost command
        mock_create_task.assert_called_once()


async def test_correct_water_boost_zero_value(
    hass: HomeAssistant,
    coordinator_slr2: HiveCoordinator,
) -> None:
    """Test correct_water_boost with zero boost remaining."""
    reported_boost = 0

    result = coordinator_slr2.correct_water_boost(reported_boost)

    # Should not trigger correction
    assert result is False
    # Should set water_boost_remaining to 0
    assert coordinator_slr2.water_boost_remaining == 0
