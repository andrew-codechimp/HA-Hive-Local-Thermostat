"""Binary Sensor platform for Hive Local Thermostat."""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .const import (
    DOMAIN,
    MODEL_SLR2,
)
from .common import HiveConfigEntry
from .entity import HiveEntity, HiveEntityDescription
from .coordinator import HiveCoordinator


@dataclass(frozen=True, kw_only=True)
class HiveBinarySensorEntityDescription(
    HiveEntityDescription,
    BinarySensorEntityDescription,
):
    """Class describing Hive binary sensor entities."""

    value_fn: Callable[[dict[str, Any]], bool | None]
    running_state: bool = False


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: HiveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""

    coordinator = config_entry.runtime_data.coordinator

    if coordinator.model == MODEL_SLR2:
        entity_descriptions = [
            HiveBinarySensorEntityDescription(
                key="heat_boost",
                translation_key="heat_boost",
                name=config_entry.title,
                value_fn=lambda js: js["system_mode_heat"] == "emergency_heating",
                running_state=True,
            ),
            HiveBinarySensorEntityDescription(
                key="water_boost",
                translation_key="water_boost",
                name=config_entry.title,
                value_fn=lambda js: js["system_mode_water"] == "emergency_heating",
                running_state=True,
            ),
        ]
    else:
        entity_descriptions = [
            HiveBinarySensorEntityDescription(
                key="heat_boost",
                translation_key="heat_boost",
                name=config_entry.title,
                value_fn=lambda js: js["system_mode"] == "emergency_heating",
                running_state=True,
            ),
        ]

    _entities = [
        HiveBinarySensor(
            entity_description=entity_description,
            coordinator=coordinator,
        )
        for entity_description in entity_descriptions
    ]

    async_add_entities(sensorEntity for sensorEntity in _entities)


class HiveBinarySensor(HiveEntity, BinarySensorEntity):
    """hive_local_thermostat Binary Sensor class."""

    entity_description: HiveBinarySensorEntityDescription

    def __init__(
        self,
        entity_description: HiveBinarySensorEntityDescription,
        coordinator: HiveCoordinator,
    ) -> None:
        """Initialize the binary sensor class."""

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
            new_value = None

        self._attr_is_on = new_value
        self.async_write_ha_state()
