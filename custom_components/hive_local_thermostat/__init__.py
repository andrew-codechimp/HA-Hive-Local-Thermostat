"""Custom integration to integrate hive_local_thermostat with Home Assistant.

For more details about this integration, please refer to
https://github.com/andrew-codechimp/HA_Hive_Local_Thermostat
"""

from __future__ import annotations

from asyncio import sleep

from awesomeversion.awesomeversion import AwesomeVersion

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    Platform,
    __version__ as HA_VERSION,  # noqa: N812
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.mqtt import client as mqtt_client

from .const import (
    DOMAIN,
    LOGGER,
    CONF_MODEL,
    MODEL_SLR2,
    MIN_HA_VERSION,
    CONF_MQTT_TOPIC,
)
from .common import HiveData, HiveConfigEntry
from .services import async_setup_services
from .coordinator import HiveCoordinator

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

    platforms = get_platforms(entry.options[CONF_MODEL])

    coordinator = HiveCoordinator(
        hass,
        entry.entry_id,
        entry.options[CONF_MODEL],
        entry.options[CONF_MQTT_TOPIC],
    )

    entry.runtime_data = HiveData(
        platforms=platforms,
        coordinator=coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    topic = entry.options[CONF_MQTT_TOPIC]

    LOGGER.debug(
        "Subscribing to MQTT topic: %s, will parse platforms for %s",
        topic,
        entry.options[CONF_MODEL],
    )

    # Subscribe to MQTT and have the coordinator handle messages
    entry.async_on_unload(
        await mqtt_client.async_subscribe(
            hass, topic, coordinator.handle_mqtt_message, 1
        )
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
    return await hass.config_entries.async_unload_platforms(
        entry, entry.runtime_data.platforms
    )


async def config_entry_update_listener(
    hass: HomeAssistant, entry: HiveConfigEntry
) -> None:
    """Update listener, called when the config entry options are changed."""

    await hass.config_entries.async_reload(entry.entry_id)
