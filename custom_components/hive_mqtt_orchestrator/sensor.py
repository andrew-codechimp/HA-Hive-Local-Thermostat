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
    CONF_MQTT_TOPIC
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

    ENTITY_DESCRIPTIONS = (
        HiveSensorEntityDescription(
            key="running_state_water",
            translation_key="running_state_water",
            icon="mdi:water-boiler",
            # native_unit_of_measurement=UnitOfInformation.GIGABYTES,
            func=lambda js: js["running_state_water"],
            topic=config_entry.options[CONF_MQTT_TOPIC]
        ),
        HiveSensorEntityDescription(
            key="running_state_heat",
            translation_key="running_state_heat",
            icon="mdi:radiator",
            # native_unit_of_measurement=UnitOfInformation.GIGABYTES,
            func=lambda js: js["running_state_heat"],
            topic=config_entry.options[CONF_MQTT_TOPIC]
        ),
    )

    _entities = {}

    _entities = [HiveSensor(entity_description=entity_description,) for entity_description in ENTITY_DESCRIPTIONS]

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
        super().__init__(entity_description)

        # config = entry.options
        # self.config_entry = entry
        # self._attr_name: str = (
        #     entry.title
        #     if entry.title is not None
        #     else entry.options.get(CONF_NAME)
        # )

        self.entity_description = entity_description
        self._attr_unique_id = f"{DOMAIN}_{entity_description.key}".lower()
        self._attr_has_entity_name = True
        self._func = entity_description.func
        self._topic = entity_description.topic


    # def __init__(self, device_id, name, icon, device_class, unit_of_measurement, state_class, func, entity_category = EntityCategory.CONFIG, ignore_zero_values = False) -> None:
    #     """Initialize the sensor."""
    #     self._device_id = device_id
    #     self._ignore_zero_values = ignore_zero_values
    #     self._attr_name = name
    #     self._attr_unique_id = slugify(device_id + "_" + name)
    #     self._attr_icon = icon
    #     if (device_class):
    #       self._attr_device_class = device_class
    #     if (unit_of_measurement):
    #       self._attr_native_unit_of_measurement = unit_of_measurement
    #     if (state_class):
    #       self._attr_state_class = state_class
    #     self._attr_entity_category = entity_category
    #     self._attr_should_poll = False

    #     self._func = func
    #     self._attr_device_info = DeviceInfo(
    #         connections={("mac", device_id)},
    #         manufacturer="Hildebrand Technology Limited",
    #         model="Glow Smart Meter IHD",
    #         name=f"Glow Smart Meter {device_id}",
    #     )
    #     self._attr_native_value = None

    def process_update(self, mqtt_data) -> None:
        """Update the state of the sensor."""
        new_value = self._func(mqtt_data)
        # if (self._ignore_zero_values and new_value == 0):
        #     LOGGER.debug("Ignored new value of %s on %s.", new_value, self._attr_unique_id)
        #     return
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
