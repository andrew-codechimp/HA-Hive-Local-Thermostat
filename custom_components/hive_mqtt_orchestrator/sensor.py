"""Sensor platform for hive_mqtt_orchestrator."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import callback
from homeassistant.util import slugify
from homeassistant.const import (
    Platform,
    UnitOfInformation,
    CONF_NAME,
    CONF_ENTITIES,
)

from .entity import HiveEntity, HiveEntityDescription

from .const import (
    DOMAIN,
    LOGGER,
    CONF_MQTT_TOPIC,
    ICON_UNKNOWN,
    CONF_MODEL,
    MODEL_SLR2,
)

@dataclass
class HiveSensorEntityDescription(
    HiveEntityDescription,
    SensorEntityDescription,
):
    """Class describing Hive sensor entities."""

async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
    ):
    """Set up the sensor platform."""

    entity_descriptions = [
        HiveSensorEntityDescription(
            key="running_state_heat",
            translation_key="running_state_heat",
            icon="mdi:radiator-disabled",
            icons_by_state = {
                "heat": "mdi:radiator",
                "idle": "mdi:radiator-off",
                "off": "mdi:radiator-off",
                "preheating": "mdi:radiator",
            },
            name=config_entry.title,
            func=lambda js: js["running_state_heat"],
            topic=config_entry.options[CONF_MQTT_TOPIC],
            entry_id=config_entry.entry_id,
            model=config_entry.options[CONF_MODEL],
        ),
    ]

    if config_entry.options[CONF_MODEL] == MODEL_SLR2:
        entity_descriptions.append(HiveSensorEntityDescription(
                key="running_state_water",
                translation_key="running_state_water",
                icon="mdi:water-boiler",
                icons_by_state = {
                    "heat": "mdi:water-boiler",
                    "idle": "mdi:water-boiler-off",
                    "off": "mdi:water-boiler-off",
                },
                name=config_entry.title,
                func=lambda js: js["running_state_water"],
                topic=config_entry.options[CONF_MQTT_TOPIC],
                entry_id=config_entry.entry_id,
                model=config_entry.options[CONF_MODEL],
            )
        )

    _entities = {}

    _entities = [HiveSensor(entity_description=entity_description,) for entity_description in entity_descriptions]

    async_add_entities(
        [sensorEntity for sensorEntity in _entities],
    )

    hass.data[DOMAIN][config_entry.entry_id][Platform.SENSOR] = _entities

class HiveSensor(HiveEntity, SensorEntity):
    """hive_mqtt_orchestrator Sensor class."""

    def __init__(
        self,
        entity_description: HiveSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""

        self.entity_description = entity_description
        self._attr_unique_id = f"{DOMAIN}_{entity_description.name}_{entity_description.key}".lower()
        self._attr_has_entity_name = True
        self._func = entity_description.func
        self._topic = entity_description.topic

        super().__init__(entity_description)

    def process_update(self, mqtt_data) -> None:
        """Update the state of the sensor."""
        new_value = self._func(mqtt_data)
        # if (self._ignore_zero_values and new_value == 0):
        #     LOGGER.debug("Ignored new value of %s on %s.", new_value, self._attr_unique_id)
        #     return

        if new_value == "":
            new_value = "preheating"

        self._attr_icon = self.entity_description.icons_by_state.get(new_value, ICON_UNKNOWN)

        self._attr_native_value = new_value
        if (self.hass is not None): # this is a hack to get around the fact that the entity is not yet initialized at first
            self.async_schedule_update_ha_state()

    # @property
    # def native_value(self) -> str:
    #     """Return the native value of the sensor."""
    #     if (
    #         self.coordinator.data
    #         and self.entity_description.key in self.coordinator.data
    #     ):
    #         return self.coordinator.data[self.entity_description.key]
    #     return None

    # @property
    # def extra_state_attributes(self):
    #     """Return the state attributes."""
    #     return {ATTR_DEVICE_ID: self._device_id}
