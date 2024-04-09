"""Sensor platform for hive_local_thermostat."""

from __future__ import annotations

from typing import Any
from time import sleep

from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.const import (
    Platform,
)

from .entity import HiveEntity, HiveEntityDescription

from .const import (
    DOMAIN,
    LOGGER,
    CONF_MQTT_TOPIC,
    DEFAULT_WATER_BOOST_MINUTES,
    DEFAULT_HEATING_BOOST_MINUTES,
    DEFAULT_HEATING_BOOST_TEMPERATURE,
    DEFAULT_FROST_TEMPERATURE,
    CONF_MODEL,
    MODEL_SLR2,
)

@dataclass
class HiveSwitchEntityDescription(
    HiveEntityDescription,
    SwitchEntityDescription,
):
    """Class describing Hive sensor entities."""

async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
    ):
    """Set up the sensor platform."""

    entity_descriptions = [
        HiveSwitchEntityDescription(
            key="boost_heating",
            translation_key="boost_heating",
            icon="mdi:radiator",
            name=config_entry.title,
            func=lambda js: js["running_state_heat"],
            topic=config_entry.options[CONF_MQTT_TOPIC],
            entry_id=config_entry.entry_id,
            model=config_entry.options[CONF_MODEL],
        ),
    ]

    if config_entry.options[CONF_MODEL] == MODEL_SLR2:
        entity_descriptions.append(HiveSwitchEntityDescription(
            key="boost_water",
            translation_key="boost_water",
            icon="mdi:water-boiler",
            name=config_entry.title,
            func=lambda js: js["running_state_water"],
            topic=config_entry.options[CONF_MQTT_TOPIC],
            entry_id=config_entry.entry_id,
            model=config_entry.options[CONF_MODEL],
            )
        )

    _entities = {}

    _entities = [HiveSwitch(entity_description=entity_description,) for entity_description in entity_descriptions]

    async_add_entities(
        sensorEntity for sensorEntity in _entities
    )

    hass.data[DOMAIN][config_entry.entry_id][Platform.SWITCH] = _entities

class HiveSwitch(HiveEntity, SwitchEntity):
    """hive_local_thermostat Switch class."""

    def __init__(
        self,
        entity_description: HiveSwitchEntityDescription,
    ) -> None:
        """Initialize the switch class."""

        self.entity_description = entity_description
        self._attr_unique_id = f"{DOMAIN}_{entity_description.name}_{entity_description.key}".lower()
        self._attr_has_entity_name = True
        self._func = entity_description.func
        self._topic = entity_description.topic

        super().__init__(entity_description)

    def process_update(self, mqtt_data) -> None:
        """Update the state of the switch."""
        self._mqtt_data = mqtt_data

        self._attr_is_on = self._func(mqtt_data) == "emergency_heating"

        if (self.hass is not None): # this is a hack to get around the fact that the entity is not yet initialized at first
            self.async_schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        """If boost is on."""

        return self._attr_is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on boost."""

        self._pre_boost_mqtt_data = self._mqtt_data

        if self.entity_description.key == "boost_water":
            payload = (r'{"system_mode_water":"emergency_heating","temperature_setpoint_hold_duration_water":' +
                       str(self.get_entity_value("water_boost_duration", DEFAULT_WATER_BOOST_MINUTES)) +
                       r',"temperature_setpoint_hold_water":1}')
        elif self.entity_description.key == "boost_heating":
            payload = (r'{"system_mode_heat":"emergency_heating","temperature_setpoint_hold_duration_heat":' +
                       str(int(self.get_entity_value("heating_boost_duration", DEFAULT_HEATING_BOOST_MINUTES))) +
                       r',"temperature_setpoint_hold_heat":1,"occupied_heating_setpoint_heat":' +
                       str(self.get_entity_value("heating_boost_temperature", DEFAULT_HEATING_BOOST_TEMPERATURE)) + r'}')

        LOGGER.debug("Sending to {self._topic}/set message {payload}")
        await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)

        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off boost."""

        if self.entity_description.key == "boost_water":
            payload = None

            if self._pre_boost_mqtt_data["system_mode_water"] == "auto":
                payload = r'{"system_mode_water":"heat","temperature_setpoint_hold_water":"0","temperature_setpoint_hold_duration_water":"0"}'
            elif self._pre_boost_mqtt_data["system_mode_water"] == "heat":
                payload = r'{"system_mode_water":"heat","temperature_setpoint_hold_water":1}'
            elif self._pre_boost_mqtt_data["system_mode_water"] == "off":
                payload = r'{"system_mode_water":"off","temperature_setpoint_hold_water":0}'

            if payload:
                LOGGER.debug("Sending to {self._topic}/set message {payload}")
                await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)

        elif self.entity_description.key == "boost_heating":

            if self._pre_boost_mqtt_data["system_mode_heat"] == "off":
                payload = r'{"system_mode_heat":"off","temperature_setpoint_hold_heat":"0"}'
                LOGGER.debug("Sending to {self._topic}/set message {payload}")
                await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)

                sleep(0.5)

                payload = r'{"occupied_heating_setpoint_heat":' + str(self.get_entity_value("heating_frost_prevention", DEFAULT_FROST_TEMPERATURE)) + r',"temperature_setpoint_hold_heat":"1","temperature_setpoint_hold_duration_heat:"65535"}'
                LOGGER.debug("Sending to {self._topic}/set message {payload}")
                await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)
            else:
                payload = (r'{"system_mode_heat":"' +
                            self._pre_boost_mqtt_data["system_mode_heat"] +
                            r'","occupied_heating_setpoint_heat":' +
                            self._pre_boost_mqtt_data["occupied_heating_setpoint_heat"] +
                            r',"temperature_setpoint_hold_heat":' +
                            self._pre_boost_mqtt_data["temperature_setpoint_hold_heat"] +
                            r'","temperature_setpoint_hold_duration_heat":' +
                            self._pre_boost_mqtt_data["temperature_setpoint_hold_duration_heat"] + r'}')

                LOGGER.debug("Sending to {self._topic}/set message {payload}")
                await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)

        self._attr_is_on = False
        self.async_write_ha_state()
