"""Common definitions for Hive Local Thermostat integration."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from collections import deque
from dataclasses import field, dataclass

from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.mqtt import client as mqtt_client

from .const import LOGGER, MAX_DIAGNOSTIC_ENTRIES

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


@dataclass
class HiveData:
    """Hive data type."""

    platforms: list[Platform]
    entities: dict[Platform, list]
    entity_values: dict[str, float]
    diagnostic_data: deque[str] = field(
        default_factory=lambda: deque(maxlen=MAX_DIAGNOSTIC_ENTRIES)
    )

    def __post_init__(self) -> None:
        """Initialize mutable default values."""
        if self.entities is None:
            self.entities = {}
        if self.entity_values is None:
            self.entity_values = {}

    def add_diagnostic_data(self, data: str | dict[str, Any]) -> None:
        """Add diagnostic data.

        Keeps recent entries in order received/sent.

        Args:
            data: String or dict to store. Dicts will be JSON serialized.

        """
        # Convert dict to JSON string if needed
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)

        self.diagnostic_data.append(data_str)


type HiveConfigEntry = ConfigEntry[HiveData]


async def async_mqtt_publish_with_diagnostics(
    hass: HomeAssistant,
    entry: HiveConfigEntry,
    topic: str,
    payload: str,
) -> None:
    """Publish MQTT message with logging and diagnostics.

    Args:
        hass: Home Assistant instance
        entry: Config entry for diagnostic logging
        topic: MQTT topic to publish to
        payload: MQTT payload to publish

    """
    LOGGER.debug("Sending to %s message %s", topic, payload)
    diagnostic_msg = f"PUBLISH: {topic} - {payload}"
    entry.runtime_data.add_diagnostic_data(diagnostic_msg)
    await mqtt_client.async_publish(hass, topic, payload)
