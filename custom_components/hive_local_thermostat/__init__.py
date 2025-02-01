"""Custom integration to integrate hive_local_thermostat with Home Assistant.

For more details about this integration, please refer to
https://github.com/andrew-codechimp/HA_Hive_Local_Thermostat
"""

from __future__ import annotations

import json

from awesomeversion.awesomeversion import AwesomeVersion
from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITIES, Platform
from homeassistant.const import __version__ as HA_VERSION  # noqa: N812
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_MODEL,
    CONF_MQTT_TOPIC,
    DOMAIN,
    LOGGER,
    MIN_HA_VERSION,
    MODEL_SLR2,
)

PLATFORMS_SLR1: list[Platform] = [
    Platform.SENSOR, Platform.CLIMATE, Platform.NUMBER, Platform.BUTTON, Platform.BINARY_SENSOR
]

PLATFORMS_SLR2: list[Platform] = [
    Platform.SENSOR, Platform.CLIMATE, Platform.NUMBER, Platform.SELECT, Platform.BUTTON, Platform.BINARY_SENSOR
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

def get_platforms(model: str) -> list[Platform]:
    """Return platforms for model."""
    return PLATFORMS_SLR2 if model == MODEL_SLR2 else PLATFORMS_SLR1

async def async_setup(
    hass: HomeAssistant,  # pylint: disable=unused-argument
    config: ConfigType,  # pylint: disable=unused-argument
) -> bool:
    """Integration setup."""

    if AwesomeVersion(HA_VERSION) < AwesomeVersion(MIN_HA_VERSION):  # pragma: no cover
        msg = (
            "This integration requires at least HomeAssistant version "
            f" {MIN_HA_VERSION}, you are running version {HA_VERSION}."
            " Please upgrade HomeAssistant to continue use this integration."
        )
        LOGGER.critical(msg)
        return False

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {}
    hass.data[DOMAIN][entry.entry_id][CONF_ENTITIES] = []

    await hass.config_entries.async_forward_entry_setups(
        entry,
        get_platforms(entry.options[CONF_MODEL]))

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    @callback
    async def mqtt_message_received(message: ReceiveMessage) -> None:
        """Handle received MQTT message."""
        topic = message.topic
        payload = message.payload
        LOGGER.debug("Received message: %s", topic)
        LOGGER.debug("  Payload: %s", payload)

        parsed_data = json.loads(payload)

        if entry.entry_id not in hass.data[DOMAIN]:
            return

        for platform in get_platforms(entry.options[CONF_MODEL]):
            for entity in hass.data[DOMAIN][entry.entry_id][platform]:
                entity.process_update(parsed_data)

    topic=entry.options[CONF_MQTT_TOPIC]

    await mqtt_client.async_subscribe(
        hass, topic, mqtt_message_received, 1
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(
        entry,
        get_platforms(entry.options[CONF_MODEL])):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


@callback
async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)
