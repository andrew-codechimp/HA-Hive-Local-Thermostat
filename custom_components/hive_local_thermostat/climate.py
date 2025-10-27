"""Sensor platform for hive_local_thermostat."""

from __future__ import annotations

from math import floor
from asyncio import sleep
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_TEMPERATURE,
    Platform,
    UnitOfTemperature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.components.climate import (
    PRESET_NONE,
    PRESET_BOOST,
    ATTR_HVAC_MODE,
    HVACMode,
    HVACAction,
    ClimateEntity,
    ClimateEntityFeature,
    ClimateEntityDescription,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    LOGGER,
    CONF_MODEL,
    HIVE_BOOST,
    MODEL_SLR2,
    CONF_MQTT_TOPIC,
    DEFAULT_FROST_TEMPERATURE,
    CONF_SHOW_HEAT_SCHEDULE_MODE,
    DEFAULT_HEATING_BOOST_MINUTES,
    DEFAULT_HEATING_BOOST_TEMPERATURE,
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

    show_schedule_mode: bool = True


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
        show_schedule_mode=config_entry.options.get(CONF_SHOW_HEAT_SCHEDULE_MODE, True),
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

        if entity_description.show_schedule_mode:
            self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
        else:
            self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
        self._attr_hvac_mode = None
        self._attr_preset_modes = list(PRESET_MAP.keys())
        self._attr_preset_mode = None

        # Setting the new TURN_ON / TURN_OFF features isn't enough to make stop the
        # warning message about not setting them
        self._enable_turn_on_off_backwards_compatibility = False
        self._attr_supported_features = (
            ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
        )

        self._attr_max_temp = 32
        self._attr_min_temp = 5
        self._attr_target_temperature_step = 0.5

        self._pre_boost_hvac_mode: HVACMode | None = None
        self._pre_boost_occupied_heating_setpoint_heat: float | None = None
        self._hvac_mode_set_from_temperature = False

        super().__init__(entity_description)

    async def async_set_preset_mode(self, preset_mode):
        """Set the preset mode."""

        self._attr_preset_mode = preset_mode

        if preset_mode == "boost":
            self._pre_boost_hvac_mode = self._attr_hvac_mode
            self._pre_boost_occupied_heating_setpoint_heat = (
                self._attr_target_temperature
            )

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

            LOGGER.debug("Sending to %s/set message %s", self._topic, payload)
            await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)
        elif self._pre_boost_hvac_mode is not None:
            await self.async_set_hvac_mode(self._pre_boost_hvac_mode)
            self._pre_boost_hvac_mode = None
            self._pre_boost_occupied_heating_setpoint_heat = None

        # Write updated temperature to HA state to avoid flapping (MQTT confirmation is slow)
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):  # noqa: ANN003
        """Set the target temperature."""
        if temperature := kwargs.get(ATTR_TEMPERATURE):
            self._attr_target_temperature = temperature

        if hvac_mode := kwargs.get(ATTR_HVAC_MODE):
            self._hvac_mode_set_from_temperature = True
            await self.async_set_hvac_mode(hvac_mode)

        if temperature:
            if self.entity_description.model == MODEL_SLR2:
                payload = (
                    r'{"occupied_heating_setpoint_heat":' + str(temperature) + r"}"
                )
            else:
                payload = r'{"occupied_heating_setpoint":' + str(temperature) + r"}"

            LOGGER.debug("Sending to %s/set message %s", self._topic, payload)
            await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)

        # Write updated temperature to HA state to avoid flapping (MQTT confirmation is slow)
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):  # noqa: PLR0912, PLR0915
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

            LOGGER.debug("Sending to %s/set message %s", self._topic, payload)
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
                        + r"}"
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
                        + r"}"
                    )
            else:
                if not self._hvac_mode_set_from_temperature:  # noqa: SIM102
                    if self._attr_current_temperature:
                        # Get the current temperature and round down to nearest .5
                        self._attr_target_temperature = (
                            floor((self._attr_current_temperature) * 2) / 2
                        )
                if self.entity_description.model == MODEL_SLR2:
                    payload = (
                        r'{"system_mode_heat":"heat","occupied_heating_setpoint_heat":'
                        + str(self._attr_target_temperature)
                        + r',"temperature_setpoint_hold_heat":"1","temperature_setpoint_hold_duration_heat":"0"}'
                    )

                    payload_heating_setpoint = (
                        r'{"system_mode_heat":"heat","occupied_heating_setpoint_heat":'
                        + str(self._attr_target_temperature)
                        + r"}"
                    )
                else:
                    payload = (
                        r'{"system_mode":"heat","occupied_heating_setpoint":'
                        + str(self._attr_target_temperature)
                        + r',"temperature_setpoint_hold":"1","temperature_setpoint_hold_duration":"0"}'
                    )

                    payload_heating_setpoint = (
                        r'{"system_mode_heat":"heat","occupied_heating_setpoint":'
                        + str(self._attr_target_temperature)
                        + r"}"
                    )

            LOGGER.debug("Sending to %s/set message %s", self._topic, payload)
            await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)

            if not self._hvac_mode_set_from_temperature:
                await sleep(0.5)
                LOGGER.debug("Sending to %s/set message %s", self._topic, payload)
                await mqtt_client.async_publish(
                    self.hass, self._topic + "/set", payload_heating_setpoint
                )
        elif hvac_mode == HVACMode.OFF:
            if self.entity_description.model == MODEL_SLR2:
                payload = (
                    r'{"system_mode_heat":"off","temperature_setpoint_hold_heat":"0"}'
                )
            else:
                payload = r'{"system_mode":"off","temperature_setpoint_hold":"0"}'

            LOGGER.debug("Sending to %s/set message %s", self._topic, payload)
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

            LOGGER.debug("Sending to %s/set message %s", self._topic, payload)
            await mqtt_client.async_publish(self.hass, self._topic + "/set", payload)

        else:
            LOGGER.error("Unable to set hvac mode: %s", hvac_mode)

        self._hvac_mode_set_from_temperature = False

        # Write updated temperature to HA state to avoid flapping (MQTT confirmation is slow)
        self.async_write_ha_state()

    def _climate_preset(self, mode) -> str:
        """Get the current preset."""

        return next(
            (k for k, v in PRESET_MAP.items() if v == mode), PRESET_MAP[PRESET_NONE]
        )

    def process_update(self, mqtt_data):  # noqa: C901, PLR0912, PLR0915
        """Update the state of the sensor."""

        # Current Temperature
        if self.entity_description.model == MODEL_SLR2:
            if "local_temperature_heat" in mqtt_data:
                self._attr_current_temperature = mqtt_data["local_temperature_heat"]
        elif "local_temperature" in mqtt_data:
            self._attr_current_temperature = mqtt_data["local_temperature"]

        # Target Temperature
        if self.entity_description.model == MODEL_SLR2:
            if "occupied_heating_setpoint_heat" in mqtt_data:
                if mqtt_data["occupied_heating_setpoint_heat"] == 1:
                    self._attr_target_temperature = self.get_entity_value(
                        "heating_frost_prevention", DEFAULT_FROST_TEMPERATURE
                    )
                else:
                    self._attr_target_temperature = mqtt_data[
                        "occupied_heating_setpoint_heat"
                    ]
        elif "occupied_heating_setpoint" in mqtt_data:
            if mqtt_data["occupied_heating_setpoint"] == 1:
                self._attr_target_temperature = self.get_entity_value(
                    "heating_frost_prevention", DEFAULT_FROST_TEMPERATURE
                )
            else:
                self._attr_target_temperature = mqtt_data["occupied_heating_setpoint"]

        # Preset Mode
        self._attr_preset_mode = None
        if self.entity_description.model == MODEL_SLR2:
            if "system_mode_heat" in mqtt_data:
                self._attr_preset_mode = self._climate_preset(
                    mqtt_data["system_mode_heat"]
                )
        elif "system_mode" in mqtt_data:
            self._attr_preset_mode = self._climate_preset(mqtt_data["system_mode"])

        # HVAC Action
        self._attr_hvac_action = None
        if self.entity_description.model == MODEL_SLR2:
            if "running_state_heat" not in mqtt_data:
                self._attr_hvac_action = HVACAction.PREHEATING
            running_state_heat = mqtt_data["running_state_heat"]
        else:
            if "running_state" not in mqtt_data:
                self._attr_hvac_action = HVACAction.PREHEATING
            running_state_heat = mqtt_data["running_state"]

        if not self._attr_hvac_action:
            if running_state_heat == "idle":
                self._attr_hvac_action = HVACAction.IDLE
            if running_state_heat == "" or running_state_heat is None:
                self._attr_hvac_action = HVACAction.PREHEATING
            if running_state_heat == "heat":
                self._attr_hvac_action = HVACAction.HEATING
            if running_state_heat == "off":
                self._attr_hvac_action = HVACAction.OFF

        # HVAC Mode
        self._attr_hvac_mode = None
        if self.entity_description.model == MODEL_SLR2:
            if mqtt_data["system_mode_heat"] == "heat":
                if (
                    mqtt_data["temperature_setpoint_hold_heat"] is False
                    and self.entity_description.show_schedule_mode
                ):
                    self._attr_hvac_mode = HVACMode.AUTO
                else:
                    self._attr_hvac_mode = HVACMode.HEAT
            if mqtt_data["system_mode_heat"] == "emergency_heating":
                self._attr_hvac_mode = HVACMode.HEAT
            if mqtt_data["system_mode_heat"] == "off":
                self._attr_hvac_mode = HVACMode.OFF
        else:
            if mqtt_data["system_mode"] == "heat":
                if (
                    mqtt_data["temperature_setpoint_hold"] is False
                    and self.entity_description.show_schedule_mode
                ):
                    self._attr_hvac_mode = HVACMode.AUTO
                else:
                    self._attr_hvac_mode = HVACMode.HEAT
            if mqtt_data["system_mode"] == "emergency_heating":
                self._attr_hvac_mode = HVACMode.HEAT
            if mqtt_data["system_mode"] == "off":
                self._attr_hvac_mode = HVACMode.OFF

        # This is a hack to get around the fact that the entity is not yet initialized at first
        if self.hass is not None:
            self.async_schedule_update_ha_state()
