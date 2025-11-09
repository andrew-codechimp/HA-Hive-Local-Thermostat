"""Binary Sensor platform for hive_local_thermostat."""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    Platform,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .const import (
    DOMAIN,
    CONF_MODEL,
    MODEL_SLR2,
    CONF_MQTT_TOPIC,
)
from .entity import HiveEntity, HiveEntityDescription


@dataclass(frozen=True, kw_only=True)
class HiveBinarySensorEntityDescription(
    HiveEntityDescription,
    BinarySensorEntityDescription,
):
    """Class describing Hive binary sensor entities."""

    value_fn: Callable[[dict[str, Any]], bool | None]
    running_state: bool = False


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""

    if config_entry.options[CONF_MODEL] == MODEL_SLR2:
        entity_descriptions = [
            HiveBinarySensorEntityDescription(
                key="heat_boost",
                translation_key="heat_boost",
                icon="mdi:rocket-launch",
                name=config_entry.title,
                value_fn=lambda js: js["system_mode_heat"] == "emergency_heating",
                topic=config_entry.options[CONF_MQTT_TOPIC],
                entry_id=config_entry.entry_id,
                model=config_entry.options[CONF_MODEL],
                running_state=True,
            ),
            HiveBinarySensorEntityDescription(
                key="water_boost",
                translation_key="water_boost",
                icon="mdi:rocket-launch",
                name=config_entry.title,
                value_fn=lambda js: js["system_mode_water"] == "emergency_heating",
                topic=config_entry.options[CONF_MQTT_TOPIC],
                entry_id=config_entry.entry_id,
                model=config_entry.options[CONF_MODEL],
                running_state=True,
            ),
        ]
    else:
        entity_descriptions = [
            HiveBinarySensorEntityDescription(
                key="heat_boost",
                translation_key="heat_boost",
                icon="mdi:rocket-launch",
                name=config_entry.title,
                value_fn=lambda js: js["system_mode"] == "emergency_heating",
                topic=config_entry.options[CONF_MQTT_TOPIC],
                entry_id=config_entry.entry_id,
                model=config_entry.options[CONF_MODEL],
                running_state=True,
            ),
        ]

    _entities = [
        HiveBinarySensor(
            entity_description=entity_description,
        )
        for entity_description in entity_descriptions
    ]

    async_add_entities(sensorEntity for sensorEntity in _entities)

    hass.data[DOMAIN][config_entry.entry_id][Platform.BINARY_SENSOR] = _entities


class HiveBinarySensor(HiveEntity, BinarySensorEntity):
    """hive_local_thermostat Binary Sensor class."""

    entity_description: HiveBinarySensorEntityDescription

    def __init__(
        self,
        entity_description: HiveBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor class."""

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
            new_value = None

        self._attr_is_on = new_value

        if (
            self.hass is not None
        ):  # this is a hack to get around the fact that the entity is not yet initialized at first
            self.async_schedule_update_ha_state()
