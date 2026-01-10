"""Define services for the Hive Local Thermostat integration."""

import logging
from typing import cast

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    callback,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .common import HiveData
from .const import (
    DOMAIN,
    MODEL_SLR2,
)

SERVICE_HEATING_BOOST = "boost_heating"
SERVICE_WATER_BOOST = "boost_water"
SERVICE_HEATING_BOOST_CANCEL = "cancel_boost_heating"
SERVICE_WATER_BOOST_CANCEL = "cancel_boost_water"

SERVICE_DATA_HEATING_BOOST_MINUTES = "minutes_to_boost"
SERVICE_DATA_HEATING_BOOST_TEMPERATURE = "temperature_to_boost"
SERVICE_DATA_WATER_BOOST_MINUTES = "minutes_to_boost"

ATTR_CONFIG_ENTRY_ID = "config_entry_id"

SERVICE_BASE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
    }
)

SERVICE_HEATING_BOOST_SCHEMA = SERVICE_BASE_SCHEMA.extend(
    {
        vol.Optional(SERVICE_DATA_HEATING_BOOST_MINUTES): cv.positive_int,
        vol.Optional(SERVICE_DATA_HEATING_BOOST_TEMPERATURE): cv.positive_float,
    }
)

SERVICE_WATER_BOOST_SCHEMA = SERVICE_BASE_SCHEMA.extend(
    {
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


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the services for the hive_local_thermostat integration."""

    hass.services.async_register(
        DOMAIN,
        SERVICE_HEATING_BOOST,
        _async_heating_boost,
        schema=SERVICE_HEATING_BOOST_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_HEATING_BOOST_CANCEL,
        _async_heating_boost_cancel,
        schema=SERVICE_BASE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_WATER_BOOST,
        _async_water_boost,
        schema=SERVICE_WATER_BOOST_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_WATER_BOOST_CANCEL,
        _async_water_boost_cancel,
        schema=SERVICE_BASE_SCHEMA,
    )


async def _async_heating_boost(call: ServiceCall) -> ServiceResponse:
    """Handle the service call."""
    entry = async_get_entry(call.hass, call.data[ATTR_CONFIG_ENTRY_ID])
    coordinator = cast(HiveData, entry.runtime_data).coordinator

    boost_minutes = cast(
        int,
        call.data.get(
            SERVICE_DATA_HEATING_BOOST_MINUTES,
            coordinator.heating_boost_duration,
        ),
    )

    boost_temperature = cast(
        float,
        call.data.get(
            SERVICE_DATA_HEATING_BOOST_TEMPERATURE,
            coordinator.heating_boost_temperature,
        ),
    )

    await coordinator.async_heating_boost(boost_minutes, boost_temperature)

    return None


async def _async_heating_boost_cancel(call: ServiceCall) -> ServiceResponse:
    """Handle the service call to cancel heating boost."""
    entry = async_get_entry(call.hass, call.data[ATTR_CONFIG_ENTRY_ID])
    coordinator = cast(HiveData, entry.runtime_data).coordinator

    await coordinator.async_heating_boost_cancel()

    return None


async def _async_water_boost(call: ServiceCall) -> ServiceResponse:
    """Handle the service call."""
    entry = async_get_entry(call.hass, call.data[ATTR_CONFIG_ENTRY_ID])
    coordinator = cast(HiveData, entry.runtime_data).coordinator

    boost_minutes = cast(
        int,
        call.data.get(
            SERVICE_DATA_WATER_BOOST_MINUTES,
            coordinator.water_boost_duration,
        ),
    )

    if coordinator.model != MODEL_SLR2:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="wrong_model",
        )

    await coordinator.async_water_boost(boost_minutes)

    return None


async def _async_water_boost_cancel(call: ServiceCall) -> ServiceResponse:
    """Handle the service call to cancel water boost."""
    entry = async_get_entry(call.hass, call.data[ATTR_CONFIG_ENTRY_ID])
    coordinator = cast(HiveData, entry.runtime_data).coordinator

    if coordinator.model != MODEL_SLR2:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="wrong_model",
        )

    await coordinator.async_water_boost_cancel()

    return None
