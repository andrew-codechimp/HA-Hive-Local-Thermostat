"""Sensor platform for Hive Local Thermostat."""

from __future__ import annotations

from typing import Any, cast
from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    PRECISION_TENTHS,
    UnitOfTemperature,
)
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorEntityDescription,
)
from homeassistant.helpers.temperature import display_temp as show_temp
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_MODEL,
    MODEL_SLR2,
)
from .common import HiveConfigEntry
from .entity import HiveEntity, HiveEntityDescription
from .coordinator import HiveCoordinator


@dataclass(frozen=True, kw_only=True)
class HiveSensorEntityDescription(
    HiveEntityDescription,
    SensorEntityDescription,
):
    """Class describing Hive sensor entities."""

    icons_by_state: dict[str, str] | None = None
    value_fn: Callable[[dict[str, Any]], str | int | float | None]
    running_state: bool = False


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: HiveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    coordinator = config_entry.runtime_data.coordinator

    if config_entry.options[CONF_MODEL] == MODEL_SLR2:
        entity_descriptions = [
            HiveSensorEntityDescription(
                key="running_state_heat",
                translation_key="running_state_heat",
                name=config_entry.title,
                value_fn=lambda js: js["running_state_heat"],
                running_state=True,
            ),
            HiveSensorEntityDescription(
                key="local_temperature_heat",
                translation_key="local_temperature_heat",
                name=config_entry.title,
                device_class=SensorDeviceClass.TEMPERATURE,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                suggested_display_precision=1,
                value_fn=lambda data: cast(float, data["local_temperature_heat"]),
            ),
            HiveSensorEntityDescription(
                key="running_state_water",
                translation_key="running_state_water",
                name=config_entry.title,
                value_fn=lambda data: cast(str, data["running_state_water"]),
                running_state=True,
            ),
            HiveSensorEntityDescription(
                key="boost_remaining_heat",
                translation_key="boost_remaining_heat",
                name=config_entry.title,
                value_fn=lambda data: cast(
                    int,
                    data["temperature_setpoint_hold_duration_heat"]
                    if data["system_mode_heat"] == "emergency_heating"
                    else 0,
                ),
            ),
            HiveSensorEntityDescription(
                key="boost_remaining_water",
                translation_key="boost_remaining_water",
                name=config_entry.title,
                value_fn=lambda data: cast(
                    int,
                    data["temperature_setpoint_hold_duration_water"]
                    if data["system_mode_water"] == "emergency_heating"
                    else 0,
                ),
            ),
        ]
    else:
        entity_descriptions = [
            HiveSensorEntityDescription(
                key="running_state_heat",
                translation_key="running_state_heat",
                name=config_entry.title,
                value_fn=lambda data: cast(str, data["running_state"]),
                running_state=True,
            ),
            HiveSensorEntityDescription(
                key="local_temperature_heat",
                translation_key="local_temperature_heat",
                name=config_entry.title,
                device_class=SensorDeviceClass.TEMPERATURE,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                suggested_display_precision=1,
                value_fn=lambda data: cast(float, data["local_temperature"]),
            ),
            HiveSensorEntityDescription(
                key="boost_remaining_heat",
                translation_key="boost_remaining_heat",
                name=config_entry.title,
                suggested_display_precision=1,
                value_fn=lambda data: cast(
                    int,
                    data["temperature_setpoint_hold_duration"]
                    if data["system_mode"] == "emergency_heating"
                    else 0,
                ),
            ),
        ]

    _entities = [
        HiveSensor(
            entity_description=entity_description,
            coordinator=coordinator,
        )
        for entity_description in entity_descriptions
    ]

    async_add_entities(sensorEntity for sensorEntity in _entities)


class HiveSensor(HiveEntity, SensorEntity):
    """hive_local_thermostat Sensor class."""

    entity_description: HiveSensorEntityDescription

    def __init__(
        self,
        entity_description: HiveSensorEntityDescription,
        coordinator: HiveCoordinator,
    ) -> None:
        """Initialize the sensor class."""

        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{DOMAIN}_{entity_description.name}_{entity_description.key}".lower()
        )
        self._attr_has_entity_name = True
        self._func = entity_description.value_fn

        super().__init__(entity_description, coordinator)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        mqtt_data = self.coordinator.data

        try:
            new_value = self._func(mqtt_data)
        except KeyError:
            if self.entity_description.device_class == SensorDeviceClass.TEMPERATURE:
                new_value = 0
            else:
                new_value = ""

        if self.entity_description.running_state and (
            new_value == "" or new_value is None
        ):
            new_value = "preheating"

        if self.entity_description.device_class == SensorDeviceClass.TEMPERATURE:
            new_value = show_temp(
                self.hass,
                cast(float, new_value),
                self.entity_description.native_unit_of_measurement
                or UnitOfTemperature.CELSIUS,
                PRECISION_TENTHS,
            )

        self._attr_native_value = new_value
        self.async_write_ha_state()
