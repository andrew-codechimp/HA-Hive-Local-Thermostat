"""Sensor platform for andrews_arnold_quota."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import slugify

from homeassistant.const import (
    UnitOfInformation,
    CONF_NAME,
)

from .coordinator import HiveDataUpdateCoordinator
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


ENTITY_DESCRIPTIONS = (
    HiveSensorEntityDescription(
        key="running_state_water",
        translation_key="running_state_water",
        # icon="mdi:counter",
        # native_unit_of_measurement=UnitOfInformation.GIGABYTES,
    ),
    HiveSensorEntityDescription(
        key="running_state_heat",
        translation_key="running_state_heat",
        # icon="mdi:counter",
        # native_unit_of_measurement=UnitOfInformation.GIGABYTES,
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the sensor platform."""
    deviceUpdateGroups = {}

    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        HiveSensor(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )

    @callback
    async def mqtt_message_received(message: ReceiveMessage):
        """Handle received MQTT message."""
        topic = message.topic
        payload = message.payload
        device_id = topic.split("/")[1]
        if (device_mac == '+' or device_id == device_mac):
            updateGroups = await async_get_device_groups(deviceUpdateGroups, async_add_entities, device_id)
            LOGGER.debug("Received message: %s", topic)
            LOGGER.debug("  Payload: %s", payload)
            for updateGroup in updateGroups:
                updateGroup.process_update(message)

    topic=entry.options[CONF_MQTT_TOPIC]

    await mqtt_client.async_subscribe(
        hass, topic, mqtt_message_received, 1
    )

async def async_get_device_groups(deviceUpdateGroups, async_add_entities, device_id):
    #add to update groups if not already there
    if device_id not in deviceUpdateGroups:
        LOGGER.debug("New device found: %s", device_id)
        groups = [
            HiveSensorUpdateGroup(device_id, "STATE", STATE_SENSORS),
            HiveSensorUpdateGroup(device_id, "electricitymeter", ELECTRICITY_SENSORS),
            HiveSensorUpdateGroup(device_id, "gasmeter", GAS_SENSORS)
        ]
        async_add_entities(
            [sensorEntity for updateGroup in groups for sensorEntity in updateGroup.all_sensors],
            #True
        )
        deviceUpdateGroups[device_id] = groups

    return deviceUpdateGroups[device_id]

class HiveSensorUpdateGroup:
    """Representation of Hive Sensors that all get updated together."""

    def __init__(self, device_id: str, topic_regex: str, meters: Iterable) -> None:
        """Initialize the sensor collection."""
        self._topic_regex = re.compile(topic_regex)
        self._sensors = [HiveSensor(device_id = device_id, **meter) for meter in meters]

    def process_update(self, message: ReceiveMessage) -> None:
        """Process an update from the MQTT broker."""
        topic = message.topic
        payload = message.payload
        if (self._topic_regex.search(topic)):
            LOGGER.debug("Matched on %s", self._topic_regex.pattern)
            parsed_data = json.loads(payload)
            for sensor in self._sensors:
                sensor.process_update(parsed_data)

    @property
    def all_sensors(self) -> Iterable[HiveSensor]:
        """Return all meters."""
        return self._sensors

class HiveSensor(HiveEntity, SensorEntity):
    """andrews_arnold_quota Sensor class."""

    def __init__(
        self,
        coordinator: HiveDataUpdateCoordinator,
        entity_description: HiveSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(entity_description, coordinator)

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


    def __init__(self, device_id, name, icon, device_class, unit_of_measurement, state_class, func, entity_category = EntityCategory.CONFIG, ignore_zero_values = False) -> None:
        """Initialize the sensor."""
        self._device_id = device_id
        self._ignore_zero_values = ignore_zero_values
        self._attr_name = name
        self._attr_unique_id = slugify(device_id + "_" + name)
        self._attr_icon = icon
        if (device_class):
          self._attr_device_class = device_class
        if (unit_of_measurement):
          self._attr_native_unit_of_measurement = unit_of_measurement
        if (state_class):
          self._attr_state_class = state_class
        self._attr_entity_category = entity_category
        self._attr_should_poll = False

        self._func = func
        self._attr_device_info = DeviceInfo(
            connections={("mac", device_id)},
            manufacturer="Hildebrand Technology Limited",
            model="Glow Smart Meter IHD",
            name=f"Glow Smart Meter {device_id}",
        )
        self._attr_native_value = None

    def process_update(self, mqtt_data) -> None:
        """Update the state of the sensor."""
        new_value = self._func(mqtt_data)
        if (self._ignore_zero_values and new_value == 0):
            LOGGER.debug("Ignored new value of %s on %s.", new_value, self._attr_unique_id)
            return
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
