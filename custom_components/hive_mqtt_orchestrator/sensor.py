"""Sensor platform for andrews_arnold_quota."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.core import callback

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

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        if (
            self.coordinator.data
            and self.entity_description.key in self.coordinator.data
        ):
            return self.coordinator.data[self.entity_description.key]
        return None
