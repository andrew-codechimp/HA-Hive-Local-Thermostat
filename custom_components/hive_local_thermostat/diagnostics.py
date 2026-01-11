"""Diagnostics support for Hive Local Thermostat."""

from __future__ import annotations

from typing import Any, cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .common import HiveData
from .const import (
    CONF_MODEL,
    CONF_MQTT_TOPIC,
    CONF_SHOW_HEAT_SCHEDULE_MODE,
    CONF_SHOW_WATER_SCHEDULE_MODE,
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = cast(HiveData, entry.runtime_data).coordinator

    return {
        "config": {
            "model": entry.options.get(CONF_MODEL),
            "topic": entry.options.get(CONF_MQTT_TOPIC),
            "show_heat_schedule_mode": entry.options.get(CONF_SHOW_HEAT_SCHEDULE_MODE),
            "show_water_schedule_mode": entry.options.get(
                CONF_SHOW_WATER_SCHEDULE_MODE
            ),
            "entry_id": entry.entry_id,
            "title": entry.title,
        },
        "coordinator_state": {
            "current_temperature": coordinator.current_temperature,
            "target_temperature": coordinator.target_temperature,
            "preset_mode": coordinator.preset_mode,
            "hvac_mode": coordinator.hvac_mode,
            "running_state_heat": coordinator.running_state_heat,
            "running_state_water": coordinator.running_state_water,
            "heat_boost": coordinator.heat_boost,
            "heat_boost_remaining": coordinator.heat_boost_remaining,
            "heating_boost_duration": coordinator.heating_boost_duration,
            "heating_boost_temperature": coordinator.heating_boost_temperature,
            "pre_boost_hvac_mode": coordinator.pre_boost_hvac_mode,
            "pre_boost_occupied_heating_setpoint_heat": coordinator.pre_boost_occupied_heating_setpoint_heat,
            "heating_frost_prevention": coordinator.heating_frost_prevention,
            "water_mode": coordinator.water_mode,
            "water_boost": coordinator.water_boost,
            "water_boost_remaining": coordinator.water_boost_remaining,
            "water_boost_duration": coordinator.water_boost_duration,
            "pre_boost_water_mode": coordinator.pre_boost_water_mode,
        },
        "last_mqtt_payload": coordinator.last_mqtt_payload,
    }
