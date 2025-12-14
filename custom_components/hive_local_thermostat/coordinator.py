"""Coordinator for Hive Local Thermostat integration."""

from __future__ import annotations

import json
from typing import Any
from asyncio import sleep

from homeassistant.core import HomeAssistant, callback
from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.components.climate.const import HVACMode
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    LOGGER,
    MODEL_SLR2,
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

        self.pre_boost_hvac_mode: HVACMode | None = None
        self.pre_boost_occupied_heating_setpoint_heat: float | None = None

        # Number entity values
        self.heating_boost_duration: float = DEFAULT_HEATING_BOOST_MINUTES
        self.heating_boost_temperature: float = DEFAULT_HEATING_BOOST_TEMPERATURE
        self.heating_frost_prevention: float = DEFAULT_FROST_TEMPERATURE
        self.water_boost_duration: float = DEFAULT_WATER_BOOST_MINUTES

    @property
    def topic_get(self) -> str:
        """Return the topic getter."""
        return self.topic + "/get"

    @property
    def topic_set(self) -> str:
        """Return the topic setter."""
        return self.topic + "/set"

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

    async def _async_publish_set(self, payload: str) -> None:
        """Publish MQTT set message."""
        LOGGER.debug("Sending to %s message %s", self.topic_set, payload)
        await mqtt_client.async_publish(self.hass, self.topic_set, payload)

    async def async_water_boost(
        self, boost_duration_minutes: int | None = None
    ) -> None:
        """Send water boost command."""

        duration = str(boost_duration_minutes or self.water_boost_duration)
        payload = (
            r'{"system_mode_water":"emergency_heating","temperature_setpoint_hold_duration_water":'
            + duration
            + r',"temperature_setpoint_hold_water":1}'
        )

        await self._async_publish_set(payload)

    async def async_water_scheduled(self) -> None:
        """Send water scheduled command."""

        payload = r'{"system_mode_water":"heat","temperature_setpoint_hold_water":"0","temperature_setpoint_hold_duration_water":"0"}'
        await self._async_publish_set(payload)

    async def async_water_always_on(self) -> None:
        """Send water always on command."""

        payload = r'{"system_mode_water":"heat","temperature_setpoint_hold_water":1}'
        await self._async_publish_set(payload)

    async def async_water_always_off(self) -> None:
        """Send water always off command."""

        payload = r'{"system_mode_water":"off","temperature_setpoint_hold_water":0}'
        await self._async_publish_set(payload)

    async def async_heating_boost(
        self,
        boost_duration_minutes: int | None = None,
        boost_temperature: float | None = None,
    ) -> None:
        """Send heating boost command."""

        duration = str(int(boost_duration_minutes or self.heating_boost_duration))
        temperature = str(boost_temperature or self.heating_boost_temperature)

        if self.model == MODEL_SLR2:
            payload = (
                r'{"system_mode_heat":"emergency_heating","temperature_setpoint_hold_duration_heat":'
                + duration
                + r',"temperature_setpoint_hold_heat":1,"occupied_heating_setpoint_heat":'
                + temperature
                + r"}"
            )
        else:
            payload = (
                r'{"system_mode":"emergency_heating","temperature_setpoint_hold_duration":'
                + duration
                + r',"temperature_setpoint_hold":1,"occupied_heating_setpoint":'
                + temperature
                + r"}"
            )

        await self._async_publish_set(payload)

    async def async_set_temperature(self, temperature: float) -> None:
        """Set temperature."""

        if self.model == MODEL_SLR2:
            payload = r'{"occupied_heating_setpoint_heat":' + str(temperature) + r"}"
        else:
            payload = r'{"occupied_heating_setpoint":' + str(temperature) + r"}"

        await self._async_publish_set(payload)

    async def async_set_hvac_mode_off(self) -> None:
        """Set HVAC mode to off."""

        if self.model == MODEL_SLR2:
            payload = r'{"system_mode_heat":"off","temperature_setpoint_hold_heat":"0"}'
        else:
            payload = r'{"system_mode":"off","temperature_setpoint_hold":"0"}'

        await self._async_publish_set(payload)

        await sleep(0.5)

        if self.model == MODEL_SLR2:
            payload = (
                r'{"occupied_heating_setpoint_heat":'
                + str(self.heating_frost_prevention)
                + r',"temperature_setpoint_hold_heat":"1","temperature_setpoint_hold_duration_heat:"65535"}'
            )
        else:
            payload = (
                r'{"occupied_heating_setpoint":'
                + str(self.heating_frost_prevention)
                + r',"temperature_setpoint_hold":"1","temperature_setpoint_hold_duration:"65535"}'
            )

        await self._async_publish_set(payload)

    async def async_set_hvac_mode_auto(self) -> None:
        """Set HVAC mode to auto."""

        if self.model == MODEL_SLR2:
            payload = r'{"system_mode_heat":"heat","temperature_setpoint_hold_heat":"0","temperature_setpoint_hold_duration_heat":"0"}'
        else:
            payload = r'{"system_mode":"heat","temperature_setpoint_hold":"0","temperature_setpoint_hold_duration":"0"}'

        await self._async_publish_set(payload)

    async def async_set_hvac_mode_heat(
        self,
        temperature: float,
        set_from_temperature: bool,  # noqa: FBT001
    ) -> None:
        """Set HVAC mode to heat."""

        if self.model == MODEL_SLR2:
            payload = (
                r'{"system_mode_heat":"heat","occupied_heating_setpoint_heat":'
                + str(temperature)
                + r',"temperature_setpoint_hold_heat":"1","temperature_setpoint_hold_duration_heat":"0"}'
            )

            payload_heating_setpoint = (
                r'{"system_mode_heat":"heat","occupied_heating_setpoint_heat":'
                + str(temperature)
                + r"}"
            )
        else:
            payload = (
                r'{"system_mode":"heat","occupied_heating_setpoint":'
                + str(temperature)
                + r',"temperature_setpoint_hold":"1","temperature_setpoint_hold_duration":"0"}'
            )

            payload_heating_setpoint = (
                r'{"system_mode":"heat","occupied_heating_setpoint":'
                + str(temperature)
                + r"}"
            )

        await self._async_publish_set(payload)

        if not set_from_temperature:
            await sleep(0.5)
            await self._async_publish_set(payload_heating_setpoint)
