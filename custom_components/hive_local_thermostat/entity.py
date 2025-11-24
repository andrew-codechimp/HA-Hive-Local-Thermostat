"""HiveLocalThermostatEntity class."""

from __future__ import annotations

import abc
from typing import Any, cast
from dataclasses import dataclass

from homeassistant.helpers.entity import Entity, DeviceInfo, EntityDescription
from homeassistant.components.mqtt import client as mqtt_client

from .const import DOMAIN, LOGGER
from .common import HiveData


@dataclass(frozen=True, kw_only=True)
class HiveEntityDescription(EntityDescription):
    """Defines a base Hive entity description."""

    entity_id: str | None = None
    topic: str
    entry_id: str
    model: str | None = None


class HiveEntity(Entity):
    """HiveEntity class."""

    entity_description: HiveEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        description: HiveEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.entity_description.entry_id)},
            name=self.entity_description.name
            if isinstance(self.entity_description.name, str)
            else None,
            model=self.entity_description.model,
            manufacturer="Hive",
        )
        self.entity_description = description
        if description.entity_id:
            self.entity_id = description.entity_id

    @abc.abstractmethod
    def process_update(self, mqtt_data: dict[str, Any]) -> float | None:
        """To be implemented by entities to process updates from MQTT."""
        raise NotImplementedError(
            "users must define process_update to use this base class"  # noqa: EM101
        )

    def get_entity_value(self, entity_key: str, default: float) -> float:
        """Get an entities value store in runtime data."""
        # Get the config entry from hass
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.entry_id == self.entity_description.entry_id:
                return cast(HiveData, entry.runtime_data).entity_values.get(
                    entity_key, default
                )
        return default

    def add_diagnostic_mqtt_publish(self, topic: str, payload: str) -> None:
        """Add MQTT publish to diagnostic data."""
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.entry_id == self.entity_description.entry_id:
                diagnostic_msg = f"PUBLISH: {topic} - {payload}"
                cast(HiveData, entry.runtime_data).add_diagnostic_data(diagnostic_msg)
                break

    async def async_mqtt_publish(
        self, payload: str, topic_suffix: str = "/set"
    ) -> None:
        """Publish MQTT message with logging and diagnostics."""
        topic = self.entity_description.topic + topic_suffix
        LOGGER.debug("Sending to %s message %s", topic, payload)
        self.add_diagnostic_mqtt_publish(topic, payload)
        await mqtt_client.async_publish(self.hass, topic, payload)
