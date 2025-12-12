"""Select platform for Hive Local Thermostat."""  # noqa: A005

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    LOGGER,
    MODEL_OTR1,
    MODEL_SLR1,
    CONF_SHOW_WATER_SCHEDULE_MODE,
)
from .common import HiveConfigEntry
from .entity import HiveEntity, HiveEntityDescription
from .coordinator import HiveCoordinator


@dataclass(frozen=True, kw_only=True)
class HiveSelectEntityDescription(
    HiveEntityDescription,
    SelectEntityDescription,
):
    """Class describing Hive sensor entities."""

    show_schedule_mode: bool = True


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: HiveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    coordinator = config_entry.runtime_data.coordinator

    if coordinator.model in [MODEL_SLR1, MODEL_OTR1]:
        return

    if config_entry.options.get(CONF_SHOW_WATER_SCHEDULE_MODE, True):
        show_schedule_mode = True
        water_modes = ["auto", "heat", "off", "boost"]
    else:
        show_schedule_mode = False
        water_modes = ["heat", "off", "boost"]

    entity_descriptions = (
        HiveSelectEntityDescription(
            key="system_mode_water",
            translation_key="system_mode_water",
            name=config_entry.title,
            options=water_modes,
            show_schedule_mode=show_schedule_mode,
        ),
    )

    _entities = [
        HiveSelect(
            entity_description=entity_description,
            coordinator=coordinator,
        )
        for entity_description in entity_descriptions
    ]

    async_add_entities(sensorEntity for sensorEntity in _entities)


class HiveSelect(HiveEntity, SelectEntity, RestoreEntity):
    """hive_local_thermostat Select class."""

    entity_description: HiveSelectEntityDescription

    def __init__(
        self,
        entity_description: HiveSelectEntityDescription,
        coordinator: HiveCoordinator,
    ) -> None:
        """Initialize the sensor class."""

        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{DOMAIN}_{entity_description.name}_{entity_description.key}".lower()
        )
        self._attr_has_entity_name = True
        self._attr_current_option = None
        if entity_description.options:
            self._attr_options = entity_description.options

        super().__init__(entity_description, coordinator)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        mqtt_data = self.coordinator.data

        if mqtt_data["system_mode_water"] == "heat":
            if mqtt_data["temperature_setpoint_hold_water"] is False:
                if self.entity_description.show_schedule_mode:
                    new_value = "auto"
                else:
                    new_value = "heat"
            else:
                new_value = "heat"
        if mqtt_data["system_mode_water"] == "emergency_heating":
            new_value = "boost"
        if mqtt_data["system_mode_water"] == "off":
            new_value = "off"

        if new_value not in self.options:
            msg = f"Invalid option for {self.entity_id}: {new_value}"
            raise ValueError(msg)

        self._attr_current_option = new_value
        self.async_write_ha_state()

    @property
    def options(self) -> list[str]:
        """Return the list of possible options."""
        return self._attr_options

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        return self._attr_current_option

    async def async_added_to_hass(self) -> None:
        """Restore last state when added."""
        last_state = await self.async_get_last_state()
        if last_state:
            self._attr_current_option = last_state.state

    async def async_select_option(self, option: str) -> None:
        """Update the current selected option."""
        if option not in self.options:
            msg = f"Invalid option for {self.entity_id}: {option}"
            raise ValueError(msg)

        if option == "auto":
            payload = r'{"system_mode_water":"heat","temperature_setpoint_hold_water":"0","temperature_setpoint_hold_duration_water":"0"}'
        elif option == "heat":
            payload = (
                r'{"system_mode_water":"heat","temperature_setpoint_hold_water":1}'
            )
        elif option == "boost":
            payload = (
                r'{"system_mode_water":"emergency_heating","temperature_setpoint_hold_duration_water":'
                + str(self.coordinator.water_boost_duration)
                + r',"temperature_setpoint_hold_water":1}'
            )
        elif option == "off":
            payload = r'{"system_mode_water":"off","temperature_setpoint_hold_water":0}'

        LOGGER.debug("Sending to %s message %s", self.coordinator.topic_set, payload)
        await mqtt_client.async_publish(self.hass, self.coordinator.topic_set, payload)

        self._attr_current_option = option
        self.async_write_ha_state()
