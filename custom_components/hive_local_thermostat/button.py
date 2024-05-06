"""Button platform for hive_local_thermostat."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
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
    CONF_MODEL,
    MODEL_SLR2,
)


@dataclass
class HiveButtonEntityDescription(
    HiveEntityDescription,
    ButtonEntityDescription,
):
    """Class describing Hive sensor entities."""


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the sensor platform."""

    entity_descriptions = [
        HiveButtonEntityDescription(
            key="boost_heating",
            translation_key="boost_heating",
            icon="mdi:radiator",
            name=config_entry.title,
            topic=config_entry.options[CONF_MQTT_TOPIC],
            entry_id=config_entry.entry_id,
            model=config_entry.options[CONF_MODEL],
        ),
    ]

    if config_entry.options[CONF_MODEL] == MODEL_SLR2:
        entity_descriptions.append(
            HiveButtonEntityDescription(
                key="boost_water",
                translation_key="boost_water",
                icon="mdi:water-boiler",
                name=config_entry.title,
                topic=config_entry.options[CONF_MQTT_TOPIC],
                entry_id=config_entry.entry_id,
                model=config_entry.options[CONF_MODEL],
            )
        )

    _entities = {}

    _entities = [
        HiveButton(
            entity_description=entity_description,
        )
        for entity_description in entity_descriptions
    ]

    async_add_entities(sensorEntity for sensorEntity in _entities)

    hass.data[DOMAIN][config_entry.entry_id][Platform.BUTTON] = _entities


class HiveButton(HiveEntity, ButtonEntity):
    """hive_local_thermostat Button class."""

    def __init__(
        self,
        entity_description: HiveButtonEntityDescription,
    ) -> None:
        """Initialize the button class."""

        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{DOMAIN}_{entity_description.name}_{entity_description.key}".lower()
        )
        self._attr_has_entity_name = True
        self._topic = entity_description.topic

        super().__init__(entity_description)

    def process_update(self, mqtt_data) -> None:
        """Update the state of the switch."""
        if (
            self.hass is not None
        ):  # this is a hack to get around the fact that the entity is not yet initialized at first
            self.async_schedule_update_ha_state()

    async def async_press(self) -> None:
        """Press the button."""
        if self.entity_description.key == "boost_water":
            payload = (
                r'{"system_mode_water":"emergency_heating","temperature_setpoint_hold_duration_water":'
                + str(
                    self.get_entity_value(
                        "water_boost_duration", DEFAULT_WATER_BOOST_MINUTES
                    )
                )
                + r',"temperature_setpoint_hold_water":1}'
            )
        elif self.entity_description.key == "boost_heating":
            if self.entity_description.model == MODEL_SLR2:
                payload = (
                    r'{"system_mode_heat":"emergency_heating","temperature_setpoint_hold_duration_heat":'
                    + str(
                        int(
                            self.get_entity_value(
                                "heating_boost_duration", DEFAULT_HEATING_BOOST_MINUTES
                            )
                        )
                    )
                    + r',"temperature_setpoint_hold_heat":1,"occupied_heating_setpoint_heat":'
                    + str(
                        self.get_entity_value(
                            "heating_boost_temperature",
                            DEFAULT_HEATING_BOOST_TEMPERATURE,
                        )
                    )
                    + r"}"
                )
            else:
                payload = (
                    r'{"system_mode":"emergency_heating","temperature_setpoint_hold_duration":'
                    + str(
                        int(
                            self.get_entity_value(
                                "heating_boost_duration", DEFAULT_HEATING_BOOST_MINUTES
                            )
                        )
                    )
                    + r',"temperature_setpoint_hold":1,"occupied_heating_setpoint":'
                    + str(
                        self.get_entity_value(
                            "heating_boost_temperature",
                            DEFAULT_HEATING_BOOST_TEMPERATURE,
                        )
                    )
                    + r"}"
                )

        LOGGER.debug("Sending to {self._topic}/set message {payload}")
        await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)
