"""Select platform for hive_local_thermostat."""  # noqa: A005

from __future__ import annotations

from typing import Any
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    Platform,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    LOGGER,
    CONF_MODEL,
    MODEL_OTR1,
    MODEL_SLR1,
    CONF_MQTT_TOPIC,
    DEFAULT_WATER_BOOST_MINUTES,
    CONF_SHOW_WATER_SCHEDULE_MODE,
)
from .entity import HiveEntity, HiveEntityDescription


@dataclass(frozen=True, kw_only=True)
class HiveSelectEntityDescription(
    HiveEntityDescription,
    SelectEntityDescription,
):
    """Class describing Hive sensor entities."""

    show_schedule_mode: bool = True


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
    ) -> None:
    """Set up the sensor platform."""

    if config_entry.options[CONF_MODEL] in [MODEL_SLR1, MODEL_OTR1]:
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
            icon="mdi:water-boiler",
            topic=config_entry.options[CONF_MQTT_TOPIC],
            entry_id=config_entry.entry_id,
            model=config_entry.options[CONF_MODEL],
            options=water_modes,
            show_schedule_mode=show_schedule_mode,
        ),
    )

    _entities = [HiveSelect(entity_description=entity_description,) for entity_description in entity_descriptions]

    async_add_entities(
        sensorEntity for sensorEntity in _entities
    )

    hass.data[DOMAIN][config_entry.entry_id][Platform.SELECT] = _entities

class HiveSelect(HiveEntity, SelectEntity, RestoreEntity):
    """hive_local_thermostat Select class."""

    entity_description: HiveSelectEntityDescription

    def __init__(
        self,
        entity_description: HiveSelectEntityDescription,
    ) -> None:
        """Initialize the sensor class."""

        self.entity_description = entity_description
        self._attr_unique_id = f"{DOMAIN}_{entity_description.name}_{entity_description.key}".lower()
        self._attr_has_entity_name = True
        self._topic = entity_description.topic
        self._attr_current_option = None
        if entity_description.options:
            self._attr_options = entity_description.options

        super().__init__(entity_description)

    def process_update(self, mqtt_data: dict[str, Any]) -> None:
        """Update the state of the sensor."""

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
            raise ValueError(f"Invalid option for {self.entity_id}: {new_value}")  # noqa: EM102

        self._attr_current_option = new_value
        self.async_write_ha_state()

        if (self.hass is not None): # this is a hack to get around the fact that the entity is not yet initialized at first
            self.async_schedule_update_ha_state()

    @property
    def options(self):
        """Return the list of possible options."""
        return self._attr_options

    @property
    def current_option(self):
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
            raise ValueError(f"Invalid option for {self.entity_id}: {option}")  # noqa: EM102

        if option == "auto":
            payload = r'{"system_mode_water":"heat","temperature_setpoint_hold_water":"0","temperature_setpoint_hold_duration_water":"0"}'
        elif option == "heat":
            payload = r'{"system_mode_water":"heat","temperature_setpoint_hold_water":1}'
        elif option == "emergency_heat":
            payload = r'{"system_mode_water":"emergency_heating","temperature_setpoint_hold_duration_water":' + str(self.get_entity_value("water_boost_duration", DEFAULT_WATER_BOOST_MINUTES)) + r',"temperature_setpoint_hold_water":1}'
        elif option == "off":
            payload = r'{"system_mode_water":"off","temperature_setpoint_hold_water":0}'

        LOGGER.debug("Sending to %s/set message %s", self._topic, payload)
        await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)

        self._attr_current_option = option
        self.async_write_ha_state()
