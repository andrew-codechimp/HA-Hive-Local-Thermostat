"""Define services for the Hive Local Thermostat integration."""

import logging
from typing import cast

import voluptuous as vol
from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_MODEL,
    CONF_MQTT_TOPIC,
    DEFAULT_HEATING_BOOST_MINUTES,
    DEFAULT_HEATING_BOOST_TEMPERATURE,
    DEFAULT_WATER_BOOST_MINUTES,
    DOMAIN,
    LOGGER,
    MODEL_SLR2,
)

SERVICE_HEATING_BOOST = "boost_heating"
SERVICE_WATER_BOOST = "boost_water"

SERVICE_DATA_HEATING_BOOST_MINUTES = "minutes_to_boost"
SERVICE_DATA_HEATING_BOOST_TEMPERATURE = "temperature_to_boost"
SERVICE_DATA_WATER_BOOST_MINUTES = "minutes_to_boost"

ATTR_CONFIG_ENTRY_ID = "config_entry_id"

SERVICE_HEATING_BOOST_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
        vol.Optional(SERVICE_DATA_HEATING_BOOST_MINUTES): cv.positive_int,
        vol.Optional(SERVICE_DATA_HEATING_BOOST_TEMPERATURE): cv.positive_float,
    }
)

SERVICE_WATER_BOOST_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
        vol.Optional(SERVICE_DATA_WATER_BOOST_MINUTES): cv.positive_int,
    }
)


_LOGGER = logging.getLogger(__name__)

def async_get_entry(hass: HomeAssistant, config_entry_id: str) -> ConfigEntry:
    """Get the Hive Local Thermostat config entry."""
    if not (entry := hass.config_entries.async_get_entry(config_entry_id)):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="integration_not_found",
            translation_placeholders={"target": DOMAIN},
        )
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="not_loaded",
            translation_placeholders={"target": entry.title},
        )
    return entry

def get_entity_value(hass: HomeAssistant, entry_id: str, entity_key: str, default: float) -> float:
    """Get an entities value store in hass data."""
    if entry_id not in hass.data[DOMAIN]:
        return default

    return cast(float, hass.data[DOMAIN][entry_id].get(entity_key, default))


def setup_services(hass: HomeAssistant) -> None:
    """Set up the services used by Hive Local Thermostat component."""

    async def handle_heating_boost(call: ServiceCall) -> ServiceResponse:
        """Handle the service call."""
        entry = async_get_entry(hass, call.data[ATTR_CONFIG_ENTRY_ID])
        boost_minutes = cast(int, call.data.get(SERVICE_DATA_HEATING_BOOST_MINUTES,
            get_entity_value(hass, entry.entry_id, "heating_boost_duration", DEFAULT_HEATING_BOOST_MINUTES)
        ))

        boost_temperature = cast(float, call.data.get(SERVICE_DATA_HEATING_BOOST_TEMPERATURE,
            get_entity_value(hass, entry.entry_id, "heating_boost_temperature", DEFAULT_HEATING_BOOST_TEMPERATURE)
        ))

        model=entry.options[CONF_MODEL]
        mqtt_topic=entry.options[CONF_MQTT_TOPIC]

        if model == MODEL_SLR2:
            payload = (
                r'{"system_mode_heat":"emergency_heating","temperature_setpoint_hold_duration_heat":'
                + str(boost_minutes)
                + r',"temperature_setpoint_hold_heat":1,"occupied_heating_setpoint_heat":'
                + str(boost_temperature)
                + r"}"
            )
        else:
            payload = (
                r'{"system_mode":"emergency_heating","temperature_setpoint_hold_duration":'
                + str(boost_minutes)
                + r',"temperature_setpoint_hold":1,"occupied_heating_setpoint":'
                + str(boost_temperature)
                + r"}"
            )

        LOGGER.debug("Sending to %s/set message %s", mqtt_topic, payload)
        await mqtt_client.async_publish(hass, mqtt_topic + "/set", payload)

        return None

    async def handle_water_boost(call: ServiceCall) -> ServiceResponse:
        """Handle the service call."""
        entry = async_get_entry(hass, call.data[ATTR_CONFIG_ENTRY_ID])
        boost_minutes = cast(int, call.data.get(SERVICE_DATA_WATER_BOOST_MINUTES,
            get_entity_value(hass, entry.entry_id, "water_boost_duration", DEFAULT_WATER_BOOST_MINUTES)
        ))

        model=entry.options[CONF_MODEL]
        mqtt_topic=entry.options[CONF_MQTT_TOPIC]

        if model == MODEL_SLR2:
            payload = (
                r'{"system_mode_water":"emergency_heating","temperature_setpoint_hold_duration_water":'
                + str(boost_minutes)
                + r',"temperature_setpoint_hold_water":1}'
            )

            LOGGER.debug("Sending to %s/set message %s", mqtt_topic, payload)
            await mqtt_client.async_publish(hass, mqtt_topic + "/set", payload)
        else:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="wrong_model",
            )

        return None



    hass.services.async_register(
        DOMAIN,
        SERVICE_HEATING_BOOST,
        handle_heating_boost,
        schema=SERVICE_HEATING_BOOST_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_WATER_BOOST,
        handle_water_boost,
        schema=SERVICE_WATER_BOOST_SCHEMA,
    )
