"""Coordinator for Hive Local Thermostat integration."""

from __future__ import annotations

import json
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    LOGGER,
    DEFAULT_FROST_TEMPERATURE,
    DEFAULT_WATER_BOOST_MINUTES,
    DEFAULT_HEATING_BOOST_MINUTES,
    DEFAULT_HEATING_BOOST_TEMPERATURE,
)


class HiveCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Hive data from MQTT."""

    def __init__(
        self, hass: HomeAssistant, entry_id: str, model: str, topic: str
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{entry_id}",
        )
        self.entry_id = entry_id
        self.model = model
        self.topic = topic
        self.data: dict[str, Any] = {}

        # Number entity values
        self.heating_boost_duration: float = DEFAULT_HEATING_BOOST_MINUTES
        self.heating_boost_temperature: float = DEFAULT_HEATING_BOOST_TEMPERATURE
        self.heating_frost_prevention: float = DEFAULT_FROST_TEMPERATURE
        self.water_boost_duration: float = DEFAULT_WATER_BOOST_MINUTES

    @callback
    def handle_mqtt_message(self, message: ReceiveMessage) -> None:
        """Handle received MQTT message."""
        topic = message.topic
        payload = message.payload
        LOGGER.debug("Coordinator received message: %s", topic)
        LOGGER.debug("Payload: %s", payload)

        if not payload:
            LOGGER.error(
                "Received empty payload on topic %s, check that you have the correct topic name",
                topic,
            )
            return

        try:
            parsed_data = json.loads(payload)

            # if self.model == MODEL_SLR2:
            #     if "system_mode_heat" not in parsed_data:
            #         LOGGER.error(
            #             "Received data does not contain 'system_mode_heat' for SLR2, check you have the correct model set"
            #         )
            #         return
            # elif "system_mode_water" in parsed_data:
            #     LOGGER.error(
            #         "Received data contains 'system_mode_water' for SLR1/OTR1, check you have the correct model set"
            #     )
            #     return

            # Update the coordinator data with the new MQTT data
            self.data.update(parsed_data)
            # Notify all listeners (entities) that data has been updated
            self.async_set_updated_data(self.data)
        except json.JSONDecodeError:
            LOGGER.error("Failed to parse JSON from MQTT payload: %s", payload)
        except Exception as err:  # noqa: BLE001
            LOGGER.error("Error handling MQTT message: %s", err)
