"""Button platform for Hive Local Thermostat."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    LOGGER,
    MODEL_SLR2,
)
from .common import HiveConfigEntry
from .entity import HiveEntity, HiveEntityDescription
from .coordinator import HiveCoordinator


@dataclass(frozen=True, kw_only=True)
class HiveButtonEntityDescription(
    HiveEntityDescription,
    ButtonEntityDescription,
):
    """Class describing Hive sensor entities."""


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: HiveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    coordinator = config_entry.runtime_data.coordinator

    entity_descriptions = [
        HiveButtonEntityDescription(
            key="boost_heating",
            translation_key="boost_heating",
            name=config_entry.title,
        ),
    ]

    if coordinator.model == MODEL_SLR2:
        entity_descriptions.append(
            HiveButtonEntityDescription(
                key="boost_water",
                translation_key="boost_water",
                name=config_entry.title,
            )
        )

    _entities = [
        HiveButton(
            entity_description=entity_description,
            coordinator=coordinator,
        )
        for entity_description in entity_descriptions
    ]

    async_add_entities(sensorEntity for sensorEntity in _entities)


class HiveButton(HiveEntity, ButtonEntity):
    """hive_local_thermostat Button class."""

    entity_description: HiveButtonEntityDescription

    def __init__(
        self,
        entity_description: HiveButtonEntityDescription,
        coordinator: HiveCoordinator,
    ) -> None:
        """Initialize the button class."""

        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{DOMAIN}_{entity_description.name}_{entity_description.key}".lower()
        )
        self._attr_has_entity_name = True

        super().__init__(entity_description, coordinator)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Button entities don't need to process MQTT data updates
        self.async_write_ha_state()

    async def async_press(self) -> None:
        """Press the button."""
        if self.entity_description.key == "boost_water":
            payload = (
                r'{"system_mode_water":"emergency_heating","temperature_setpoint_hold_duration_water":'
                + str(self.coordinator.water_boost_duration)
                + r',"temperature_setpoint_hold_water":1}'
            )
        elif self.entity_description.key == "boost_heating":
            if self.coordinator.model == MODEL_SLR2:
                payload = (
                    r'{"system_mode_heat":"emergency_heating","temperature_setpoint_hold_duration_heat":'
                    + str(int(self.coordinator.heating_boost_duration))
                    + r',"temperature_setpoint_hold_heat":1,"occupied_heating_setpoint_heat":'
                    + str(self.coordinator.heating_boost_temperature)
                    + r"}"
                )
            else:
                payload = (
                    r'{"system_mode":"emergency_heating","temperature_setpoint_hold_duration":'
                    + str(int(self.coordinator.heating_boost_duration))
                    + r',"temperature_setpoint_hold":1,"occupied_heating_setpoint":'
                    + str(self.coordinator.heating_boost_temperature)
                    + r"}"
                )

        LOGGER.debug("Sending to %s message %s", self.coordinator.topic_set, payload)
        await mqtt_client.async_publish(self.hass, self.coordinator.topic_set, payload)
