"""Custom integration to integrate hive_local_thermostat with Home Assistant.

For more details about this integration, please refer to
https://github.com/andrew-codechimp/HA_Hive_Local_Thermostat
"""

from __future__ import annotations

import json
from asyncio import sleep
from dataclasses import dataclass

from awesomeversion.awesomeversion import AwesomeVersion

from homeassistant.core import HomeAssistant, callback
from homeassistant.const import (
    CONF_ENTITIES,
    Platform,
    __version__ as HA_VERSION,  # noqa: N812
)
from homeassistant.helpers import config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.components.mqtt.models import ReceiveMessage

from .const import (
    DOMAIN,
    LOGGER,
    CONF_MODEL,
    MODEL_SLR2,
    MIN_HA_VERSION,
    CONF_MQTT_TOPIC,
)
from .services import async_setup_services

PLATFORMS_SLR1: list[Platform] = [
    Platform.SENSOR,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.BUTTON,
    Platform.BINARY_SENSOR,
]

PLATFORMS_SLR2: list[Platform] = [
    Platform.SENSOR,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.BINARY_SENSOR,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


@dataclass
class HiveData:
    """Hive data type."""

    platforms: list[Platform]


type HiveConfigEntry = ConfigEntry[HiveData]


def get_platforms(model: str) -> list[Platform]:
    """Return platforms for model."""
    return PLATFORMS_SLR2 if model == MODEL_SLR2 else PLATFORMS_SLR1


async def async_setup(
    hass: HomeAssistant,
    config: ConfigType,  # noqa: ARG001
) -> bool:
    """Integration setup."""

    if AwesomeVersion(HA_VERSION) < AwesomeVersion(MIN_HA_VERSION):  # pragma: no cover
        msg = (
            "This integration requires at least Home Assistant version "
            f" {MIN_HA_VERSION}, you are running version {HA_VERSION}."
            " Please upgrade Home Assistant to continue using this integration."
        )
        LOGGER.critical(msg)
        return False

    async_setup_services(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: HiveConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {}
    hass.data[DOMAIN][entry.entry_id][CONF_ENTITIES] = []

    platforms = get_platforms(entry.options[CONF_MODEL])

    entry.runtime_data = HiveData(platforms=platforms)

    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    @callback
    async def mqtt_message_received(message: ReceiveMessage) -> None:
        """Handle received MQTT message."""
        topic = message.topic
        payload = message.payload
        LOGGER.debug("Received message: %s", topic)
        LOGGER.debug("Payload: %s", payload)

        if not payload:
            LOGGER.error(
                "Received empty payload on topic %s, check that you have the correct topic name",
                topic,
            )
            return

        parsed_data = json.loads(payload)

        # if entry.options[CONF_MODEL] == MODEL_SLR2:
        #     if "system_mode_heat" not in parsed_data:
        #         LOGGER.error(
        #             "Received data does not contain 'system_mode_heat' for SLR2, check you have the correct model set"
        #         )
        #         return
        # else:
        #     if "system_mode_water" in parsed_data:
        #         LOGGER.error(
        #             "Received data contains 'system_mode_water' for SLR1/OTR1, check you have the correct model set"
        #         )
        #         return

        if entry.entry_id not in hass.data[DOMAIN]:
            return

        for platform in get_platforms(entry.options[CONF_MODEL]):
            for entity in hass.data[DOMAIN][entry.entry_id][platform]:
                entity.process_update(parsed_data)

    topic = entry.options[CONF_MQTT_TOPIC]

    LOGGER.debug(
        "Subscribing to MQTT topic: %s, will parse platforms for %s",
        topic,
        entry.options[CONF_MODEL],
    )

    entry.async_on_unload(
        await mqtt_client.async_subscribe(hass, topic, mqtt_message_received, 1)
    )

    # Send an initial message to get the current state
    await sleep(2)
    payload = r'{"system_mode":""}'
    LOGGER.debug("Sending to %s/get message %s", topic, payload)
    await mqtt_client.async_publish(hass, topic + "/get", payload)

    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: HiveConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(
        entry, entry.runtime_data.platforms
    ):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def config_entry_update_listener(
    hass: HomeAssistant, entry: HiveConfigEntry
) -> None:
    """Update listener, called when the config entry options are changed."""

    await hass.config_entries.async_reload(entry.entry_id)
