"""Sensor platform for hive_local_thermostat."""

from __future__ import annotations

from asyncio import sleep
from dataclasses import dataclass

from homeassistant.components.climate import (
    PRESET_BOOST,
    PRESET_NONE,
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    Platform,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_MODEL,
    CONF_MQTT_TOPIC,
    DEFAULT_FROST_TEMPERATURE,
    DEFAULT_HEATING_BOOST_MINUTES,
    DEFAULT_HEATING_BOOST_TEMPERATURE,
    DEFAULT_HEATING_TEMPERATURE,
    DOMAIN,
    HIVE_BOOST,
    LOGGER,
    MODEL_SLR2,
)
from .entity import HiveEntity, HiveEntityDescription

PRESET_MAP = {
    PRESET_NONE: "",
    PRESET_BOOST: HIVE_BOOST,
}


@dataclass(frozen=True, kw_only=True)
class HiveClimateEntityDescription(
    HiveEntityDescription,
    ClimateEntityDescription,
):
    """Class describing Hive sensor entities."""


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    hive_climate_entity_description = HiveClimateEntityDescription(
        key="climate",
        translation_key="climate",
        name=config_entry.title,
        topic=config_entry.options[CONF_MQTT_TOPIC],
        entry_id=config_entry.entry_id,
        model=config_entry.options[CONF_MODEL],
    )

    _entities = [HiveClimateEntity(entity_description=hive_climate_entity_description)]

    async_add_entities(climateEntity for climateEntity in _entities)

    hass.data[DOMAIN][config_entry.entry_id][Platform.CLIMATE] = _entities


class HiveClimateEntity(HiveEntity, ClimateEntity):
    """hive_local_thermostat Climate class."""

    entity_description: HiveClimateEntityDescription

    def __init__(
        self,
        entity_description: HiveClimateEntityDescription,
    ) -> None:
        """Initialize the sensor class."""

        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{DOMAIN}_{entity_description.name}_{entity_description.key}".lower()
        )
        self._attr_has_entity_name = True
        self._topic = entity_description.topic

        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]

        # Setting the new TURN_ON / TURN_OFF features isn't enough to make stop the
        # warning message about not setting them
        self._enable_turn_on_off_backwards_compatibility = False
        self._attr_supported_features = (
            ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
        )
        self._attr_preset_modes = list(PRESET_MAP.keys())
        self._attr_max_temp = 32
        self._attr_min_temp = 15
        self._attr_target_temperature_step = 0.5

        self._mqtt_data = None
        self._pre_boost_hvac_mode = None
        self._pre_boost_occupied_heating_setpoint_heat = None

        super().__init__(entity_description)

    @property
    def hvac_mode(self):
        """Get the current hvac mode."""

        if not self._mqtt_data:
            return

        if self.entity_description.model == MODEL_SLR2:
            if (
                self._mqtt_data["system_mode_heat"] == "heat"
                and self._mqtt_data["temperature_setpoint_hold_duration_heat"] != 65535
            ):
                return HVACMode.AUTO
            if self._mqtt_data["system_mode_heat"] == "emergency_heating":
                return HVACMode.HEAT
            if (
                self._mqtt_data["system_mode_heat"] == "heat"
                and self._mqtt_data["temperature_setpoint_hold_duration_heat"] == 65535
            ):
                return HVACMode.HEAT
            if self._mqtt_data["system_mode_heat"] == "off":
                return HVACMode.OFF
        else:
            if (
                self._mqtt_data["system_mode"] == "heat"
                and self._mqtt_data["temperature_setpoint_hold_duration"] != 65535
            ):
                return HVACMode.AUTO
            if self._mqtt_data["system_mode"] == "emergency_heating":
                return HVACMode.HEAT
            if (
                self._mqtt_data["system_mode"] == "heat"
                and self._mqtt_data["temperature_setpoint_hold_duration"] == 65535
            ):
                return HVACMode.HEAT
            if self._mqtt_data["system_mode"] == "off":
                return HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the hvac mode."""

        if hvac_mode in self._attr_hvac_modes:
            self._attr_hvac_mode = hvac_mode
        else:
            LOGGER.error("Unrecognized hvac mode: %s", hvac_mode)
            return

        if hvac_mode == HVACMode.AUTO:
            if self.entity_description.model == MODEL_SLR2:
                payload = r'{"system_mode_heat":"heat","temperature_setpoint_hold_heat":"0","temperature_setpoint_hold_duration_heat":"0"}'
            else:
                payload = r'{"system_mode":"heat","temperature_setpoint_hold":"0","temperature_setpoint_hold_duration":"0"}'

            LOGGER.debug("Sending to {self._topic}/set message {payload}")
            await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)
        elif hvac_mode == HVACMode.HEAT:
            if self._pre_boost_occupied_heating_setpoint_heat:
                if self.entity_description.model == MODEL_SLR2:
                    payload = (
                        r'{"system_mode_heat":"heat","occupied_heating_setpoint_heat":'
                        + str(self._pre_boost_occupied_heating_setpoint_heat)
                        + r',"temperature_setpoint_hold_heat":"1","temperature_setpoint_hold_duration_heat":"0"}'
                    )

                    payload_heating_setpoint = (
                        r'{"system_mode_heat":"heat","occupied_heating_setpoint_heat":'
                        + str(self._pre_boost_occupied_heating_setpoint_heat)
                        + r'}'
                    )
                else:
                    payload = (
                        r'{"system_mode":"heat","occupied_heating_setpoint":'
                        + str(self._pre_boost_occupied_heating_setpoint_heat)
                        + r',"temperature_setpoint_hold":"1","temperature_setpoint_hold_duration":"0"}'
                    )

                    payload_heating_setpoint = (
                        r'{"system_mode_heat":"heat","occupied_heating_setpoint":'
                        + str(self._pre_boost_occupied_heating_setpoint_heat)
                        + r'}'
                    )
            else:
                heating_default_temperature = str(
                            self.get_entity_value(
                                "heating_default_temperature",
                                DEFAULT_HEATING_TEMPERATURE,
                            )
                        )
                if self.entity_description.model == MODEL_SLR2:
                    payload = (
                        r'{"system_mode_heat":"heat","occupied_heating_setpoint_heat":'
                        + heating_default_temperature
                        + r',"temperature_setpoint_hold_heat":"1","temperature_setpoint_hold_duration_heat":"0"}'
                    )

                    payload_heating_setpoint = (
                        r'{"system_mode_heat":"heat","occupied_heating_setpoint":'
                        + heating_default_temperature
                        + r'}'
                    )
                else:
                    payload = (
                        r'{"system_mode":"heat","occupied_heating_setpoint":'
                        + heating_default_temperature
                        + r',"temperature_setpoint_hold":"1","temperature_setpoint_hold_duration":"0"}'
                    )

                    payload_heating_setpoint = (
                        r'{"system_mode_heat":"heat","occupied_heating_setpoint":'
                        + heating_default_temperature
                        + r'}'
                    )

            LOGGER.debug("Sending to {self._topic}/set message {payload}")
            await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)
            await sleep(0.5)
            LOGGER.debug("Sending to {self._topic}/set message {payload_heating_setpoint}")
            await mqtt_client.async_publish(self.hass, self._topic + "/set", payload_heating_setpoint)
        elif hvac_mode == HVACMode.OFF:
            if self.entity_description.model == MODEL_SLR2:
                payload = (
                    r'{"system_mode_heat":"off","temperature_setpoint_hold_heat":"0"}'
                )
            else:
                payload = r'{"system_mode":"off","temperature_setpoint_hold":"0"}'

            LOGGER.debug("Sending to {self._topic}/set message {payload}")
            await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)

            await sleep(0.5)

            if self.entity_description.model == MODEL_SLR2:
                payload = (
                    r'{"occupied_heating_setpoint_heat":'
                    + str(
                        self.get_entity_value(
                            "heating_frost_prevention", DEFAULT_FROST_TEMPERATURE
                        )
                    )
                    + r',"temperature_setpoint_hold_heat":"1","temperature_setpoint_hold_duration_heat:"65535"}'
                )
            else:
                payload = (
                    r'{"occupied_heating_setpoint":'
                    + str(
                        self.get_entity_value(
                            "heating_frost_prevention", DEFAULT_FROST_TEMPERATURE
                        )
                    )
                    + r',"temperature_setpoint_hold":"1","temperature_setpoint_hold_duration:"65535"}'
                )

            LOGGER.debug("Sending to {self._topic}/set message {payload}")
            await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)

        else:
            LOGGER.error("Unable to set hvac mode: %s", hvac_mode)
            return

    @property
    def hvac_action(self):
        """Get the current action."""

        if not self._mqtt_data:
            return

        if self.entity_description.model == MODEL_SLR2:
            if "running_state_heat" not in self._mqtt_data:
                return HVACAction.PREHEATING
            running_state_heat = self._mqtt_data["running_state_heat"]
        else:
            if "running_state" not in self._mqtt_data:
                return HVACAction.PREHEATING
            running_state_heat = self._mqtt_data["running_state"]

        if running_state_heat == "idle":
            return HVACAction.IDLE
        if running_state_heat == "" or running_state_heat is None:
            return HVACAction.PREHEATING
        if running_state_heat == "heat":
            return HVACAction.HEATING
        if running_state_heat == "off":
            return HVACAction.OFF

    @property
    def current_temperature(self):
        """Get the current temperature."""

        if not self._mqtt_data:
            return
        if self.entity_description.model == MODEL_SLR2:
            if "local_temperature_heat" in self._mqtt_data:
                return self._mqtt_data["local_temperature_heat"]
        else:
            if "local_temperature" in self._mqtt_data:
                return self._mqtt_data["local_temperature"]

    @property
    def target_temperature(self):
        """Get the target temperature."""

        if not self._mqtt_data:
            return

        if self.entity_description.model == MODEL_SLR2:
            if "occupied_heating_setpoint_heat" in self._mqtt_data:
                if self._mqtt_data["occupied_heating_setpoint_heat"] == 1:
                    return self.get_entity_value("heating_frost_prevention", DEFAULT_FROST_TEMPERATURE)
                return self._mqtt_data["occupied_heating_setpoint_heat"]
        else:
            if "occupied_heating_setpoint" in self._mqtt_data:
                if self._mqtt_data["occupied_heating_setpoint"] == 1:
                    return self.get_entity_value("heating_frost_prevention", DEFAULT_FROST_TEMPERATURE)
                return self._mqtt_data["occupied_heating_setpoint"]

    async def async_set_temperature(self, **kwargs):
        """Set the target temperature."""

        temperature = kwargs.get(ATTR_TEMPERATURE)

        if self.entity_description.model == MODEL_SLR2:
            payload = r'{"occupied_heating_setpoint_heat":' + str(temperature) + r"}"
        else:
            payload = r'{"occupied_heating_setpoint":' + str(temperature) + r"}"

        LOGGER.debug("Sending to {self._topic}/set message {payload}")
        await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)

    def _climate_preset(self, mode):
        """Get the current preset."""

        return next(
            (k for k, v in PRESET_MAP.items() if v == mode), PRESET_MAP[PRESET_NONE]
        )

    @property
    def preset_mode(self):
        """Get the preset mode."""

        if not self._mqtt_data:
            return

        if self.entity_description.model == MODEL_SLR2:
            if "system_mode_heat" in self._mqtt_data:
                return self._climate_preset(self._mqtt_data["system_mode_heat"])
        else:
            if "system_mode" in self._mqtt_data:
                return self._climate_preset(self._mqtt_data["system_mode"])

    async def async_set_preset_mode(self, preset_mode):
        """Set the preset mode."""

        if preset_mode == "boost":
            self._pre_boost_hvac_mode = self.hvac_mode
            self._pre_boost_occupied_heating_setpoint_heat = self.target_temperature

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
        else:
            if self._pre_boost_hvac_mode is not None:
                await self.async_set_hvac_mode(self._pre_boost_hvac_mode)
                self._pre_boost_hvac_mode = None
                self._pre_boost_occupied_heating_setpoint_heat = None

    def process_update(self, mqtt_data) -> None:
        """Update the state of the sensor."""

        self._mqtt_data = mqtt_data
        if (
            self.hass is not None
        ):  # this is a hack to get around the fact that the entity is not yet initialized at first
            self.async_schedule_update_ha_state()
