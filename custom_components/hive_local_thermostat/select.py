"""Select platform for hive_local_thermostat."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_MODEL,
    CONF_MQTT_TOPIC,
    DEFAULT_WATER_BOOST_MINUTES,
    DOMAIN,
    LOGGER,
    MODEL_OTR1,
    MODEL_SLR1,
    WATER_MODES,
)
from .entity import HiveEntity, HiveEntityDescription


@dataclass(frozen=True, kw_only=True)
class HiveSelectEntityDescription(
    HiveEntityDescription,
    SelectEntityDescription,
):
    """Class describing Hive sensor entities."""


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
    ) -> None:
    """Set up the sensor platform."""

    if config_entry.options[CONF_MODEL] in [MODEL_SLR1, MODEL_OTR1]:
        return

    ENTITY_DESCRIPTIONS = (
        HiveSelectEntityDescription(
            key="system_mode_water",
            translation_key="system_mode_water",
            name=config_entry.title,
            icon="mdi:water-boiler",
            topic=config_entry.options[CONF_MQTT_TOPIC],
            entry_id=config_entry.entry_id,
            model=config_entry.options[CONF_MODEL],
            options=WATER_MODES,
        ),
    )

    _entities = [HiveSelect(entity_description=entity_description,) for entity_description in ENTITY_DESCRIPTIONS]

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

        if mqtt_data["system_mode_water"] == "heat" and mqtt_data["temperature_setpoint_hold_duration_water"] !=65535:
            new_value = "auto"
        if mqtt_data["system_mode_water"] == "emergency_heating":
            new_value = "boost"
        if mqtt_data["system_mode_water"] == "heat" and mqtt_data["temperature_setpoint_hold_duration_water"] ==65535:
            new_value = "heat"
        if mqtt_data["system_mode_water"] == "off":
            new_value = "off"

        if new_value not in self.options:
            raise ValueError(f"Invalid option for {self.entity_id}: {new_value}")

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
            raise ValueError(f"Invalid option for {self.entity_id}: {option}")

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
