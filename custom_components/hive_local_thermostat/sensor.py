"""Sensor platform for Hive Local Thermostat."""

from __future__ import annotations

from typing import Any, cast
from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    PRECISION_TENTHS,
    Platform,
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
    ICON_UNKNOWN,
    CONF_MQTT_TOPIC,
)
from .common import HiveConfigEntry
from .entity import HiveEntity, HiveEntityDescription

BOOST_REMAINING_ERROR_VALUE = 60000


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

    if config_entry.options[CONF_MODEL] == MODEL_SLR2:
        entity_descriptions = [
            HiveSensorEntityDescription(
                key="running_state_heat",
                translation_key="running_state_heat",
                icon="mdi:radiator-disabled",
                icons_by_state={
                    "heat": "mdi:radiator",
                    "idle": "mdi:radiator-off",
                    "off": "mdi:radiator-off",
                    "preheating": "mdi:radiator",
                },
                name=config_entry.title,
                value_fn=lambda js: js["running_state_heat"],
                topic=config_entry.options[CONF_MQTT_TOPIC],
                entry_id=config_entry.entry_id,
                model=config_entry.options[CONF_MODEL],
                running_state=True,
            ),
            HiveSensorEntityDescription(
                key="local_temperature_heat",
                translation_key="local_temperature_heat",
                icon="mdi:thermometer",
                name=config_entry.title,
                device_class=SensorDeviceClass.TEMPERATURE,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                suggested_display_precision=1,
                value_fn=lambda data: cast(float, data["local_temperature_heat"]),
                topic=config_entry.options[CONF_MQTT_TOPIC],
                entry_id=config_entry.entry_id,
                model=config_entry.options[CONF_MODEL],
            ),
            HiveSensorEntityDescription(
                key="running_state_water",
                translation_key="running_state_water",
                icon="mdi:water-boiler",
                icons_by_state={
                    "heat": "mdi:water-boiler",
                    "idle": "mdi:water-boiler-off",
                    "off": "mdi:water-boiler-off",
                },
                name=config_entry.title,
                value_fn=lambda data: cast(str, data["running_state_water"]),
                topic=config_entry.options[CONF_MQTT_TOPIC],
                entry_id=config_entry.entry_id,
                model=config_entry.options[CONF_MODEL],
                running_state=True,
            ),
            HiveSensorEntityDescription(
                key="boost_remaining_heat",
                translation_key="boost_remaining_heat",
                icon="mdi:timer-outline",
                name=config_entry.title,
                value_fn=lambda data: cast(
                    int,
                    0
                    if data["temperature_setpoint_hold_duration_heat"]
                    > BOOST_REMAINING_ERROR_VALUE
                    else (
                        data["temperature_setpoint_hold_duration_heat"]
                        if data["system_mode_heat"] == "emergency_heating"
                        else 0
                    ),
                ),
                topic=config_entry.options[CONF_MQTT_TOPIC],
                entry_id=config_entry.entry_id,
                model=config_entry.options[CONF_MODEL],
            ),
            HiveSensorEntityDescription(
                key="boost_remaining_water",
                translation_key="boost_remaining_water",
                icon="mdi:timer-outline",
                name=config_entry.title,
                value_fn=lambda data: cast(
                    int,
                    0
                    if data["temperature_setpoint_hold_duration_water"]
                    > BOOST_REMAINING_ERROR_VALUE
                    else (
                        data["temperature_setpoint_hold_duration_water"]
                        if data["system_mode_water"] == "emergency_heating"
                        else 0
                    ),
                ),
                topic=config_entry.options[CONF_MQTT_TOPIC],
                entry_id=config_entry.entry_id,
                model=config_entry.options[CONF_MODEL],
            ),
        ]
    else:
        entity_descriptions = [
            HiveSensorEntityDescription(
                key="running_state_heat",
                translation_key="running_state_heat",
                icon="mdi:radiator-disabled",
                icons_by_state={
                    "heat": "mdi:radiator",
                    "idle": "mdi:radiator-off",
                    "off": "mdi:radiator-off",
                    "preheating": "mdi:radiator",
                },
                name=config_entry.title,
                value_fn=lambda data: cast(str, data["running_state"]),
                topic=config_entry.options[CONF_MQTT_TOPIC],
                entry_id=config_entry.entry_id,
                model=config_entry.options[CONF_MODEL],
                running_state=True,
            ),
            HiveSensorEntityDescription(
                key="local_temperature_heat",
                translation_key="local_temperature_heat",
                icon="mdi:thermometer",
                name=config_entry.title,
                device_class=SensorDeviceClass.TEMPERATURE,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                suggested_display_precision=1,
                value_fn=lambda data: cast(float, data["local_temperature"]),
                topic=config_entry.options[CONF_MQTT_TOPIC],
                entry_id=config_entry.entry_id,
                model=config_entry.options[CONF_MODEL],
            ),
            HiveSensorEntityDescription(
                key="boost_remaining_heat",
                translation_key="boost_remaining_heat",
                icon="mdi:timer-outline",
                name=config_entry.title,
                suggested_display_precision=1,
                value_fn=lambda data: cast(
                    int,
                    0
                    if data["temperature_setpoint_hold_duration"]
                    > BOOST_REMAINING_ERROR_VALUE
                    else (
                        data["temperature_setpoint_hold_duration"]
                        if data["system_mode"] == "emergency_heating"
                        else 0
                    ),
                ),
                topic=config_entry.options[CONF_MQTT_TOPIC],
                entry_id=config_entry.entry_id,
                model=config_entry.options[CONF_MODEL],
            ),
        ]

    _entities = [
        HiveSensor(
            entity_description=entity_description,
        )
        for entity_description in entity_descriptions
    ]

    async_add_entities(sensorEntity for sensorEntity in _entities)

    config_entry.runtime_data.entities[Platform.SENSOR] = _entities


class HiveSensor(HiveEntity, SensorEntity):
    """hive_local_thermostat Sensor class."""

    entity_description: HiveSensorEntityDescription

    def __init__(
        self,
        entity_description: HiveSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""

        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{DOMAIN}_{entity_description.name}_{entity_description.key}".lower()
        )
        self._attr_has_entity_name = True
        self._func = entity_description.value_fn
        self._topic = entity_description.topic

        super().__init__(entity_description)

    def process_update(self, mqtt_data: dict[str, Any]) -> None:
        """Update the state of the sensor."""

        try:
            new_value = self._func(mqtt_data)
        except KeyError:
            if self.entity_description.device_class == SensorDeviceClass.TEMPERATURE:
                new_value = 0
            else:
                new_value = ""

        if self.entity_description.running_state:
            if new_value == "" or new_value is None:
                new_value = "preheating"
            if self.entity_description.icons_by_state:
                self._attr_icon = self.entity_description.icons_by_state.get(
                    cast(str, new_value), ICON_UNKNOWN
                )
            else:
                self._attr_icon = ICON_UNKNOWN

        if self.entity_description.device_class == SensorDeviceClass.TEMPERATURE:
            new_value = show_temp(
                self.hass,
                cast(float, new_value),
                self.entity_description.native_unit_of_measurement
                or UnitOfTemperature.CELSIUS,
                PRECISION_TENTHS,
            )

        self._attr_native_value = new_value
        if (
            self.hass is not None
        ):  # this is a hack to get around the fact that the entity is not yet initialized at first
            self.async_schedule_update_ha_state()
