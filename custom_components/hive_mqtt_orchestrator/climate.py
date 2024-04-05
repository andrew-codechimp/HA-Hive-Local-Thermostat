"""Sensor platform for hive_mqtt_orchestrator."""

from __future__ import annotations

import logging

from dataclasses import dataclass

from homeassistant.const import (
    UnitOfTemperature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_NONE,
    ClimateEntity,
    HVACMode,
    ClimateEntityFeature,
    ClimateEntityDescription,
)

from homeassistant.const import (
    Platform
)

from .const import (
    DOMAIN,
    PRESET_MANUAL,
    # PRESET_SMART,
    # PRESET_TIMER,
    # COORDINATORS,
    # ATTR_TEMPERATURE_LOW,
    # ATTR_TEMPERATURE_HIGH,
    # ATTR_TEMPERATURE_AVERAGE,
    # TEMPERATURE_MODE_HIGH,
    # TEMPERATURE_MODE_LOW,
    # TEMPERATURE_MODE_AVERAGE,
)

PRESET_MAP = {
    PRESET_MANUAL: "Manual",
    PRESET_BOOST: "Boost",
}

from .entity import HiveEntity, HiveEntityDescription

from datetime import timedelta

@dataclass
class HiveClimateEntityDescription(
    HiveEntityDescription,
    ClimateEntityDescription,
):
    """Class describing Hive sensor entities."""

async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
    ):
    """Set up the sensor platform."""
    _sensors = {}

    hive_climate_entity_description = HiveClimateEntityDescription(
        key="climate",
        translation_key="climate",
        # icon="mdi:counter",
        # native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        func=None
    )

    _sensors = [HiveClimateEntity(entity_description=hive_climate_entity_description) ]

    async_add_entities(
        [sensorEntity for sensorEntity in _sensors],
    )

    hass.data[DOMAIN][config_entry.entry_id][Platform.CLIMATE] = _sensors

class HiveClimateEntity(HiveEntity, ClimateEntity):

    def __init__(
        self,
        entity_description: HiveClimateEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(entity_description)

        self._attr_unique_id = f"{DOMAIN}_{entity_description.key}".lower()
        self._attr_has_entity_name = True
        self._func = entity_description.func

        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]

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
        self._attr_icon = "mdi:water-boiler"
        self._attr_max_temp = 70
        self._attr_min_temp = 15
        self._attr_target_temperature_step = 5

        self._mqtt_data = None

    # async def async_update(self):
    #     await self._tsmart._async_get_status()

    @property
    def hvac_mode(self):
        # return HVACMode.HEAT if self._tsmart.power else HVACMode.OFF
        return HVACMode.OFF

    # async def async_set_hvac_mode(self, hvac_mode):
    #     await self._tsmart.async_control_set(
    #         hvac_mode == HVACMode.HEAT,
    #         PRESET_MAP[self.preset_mode],
    #         self.target_temperature,
    #     )
    #     await self.coordinator.async_request_refresh()

    @property
    def current_temperature(self):
        if not self._mqtt_data:
            return
        if "local_temperature_heat" in self._mqtt_data:
            return self._mqtt_data["local_temperature_heat"]

    @property
    def target_temperature(self):
        if not self._mqtt_data:
            return
        if "occupied_heating_setpoint_heat" in self._mqtt_data:
            return self._mqtt_data["occupied_heating_setpoint_heat"]

    # async def async_set_temperature(self, temperature, **kwargs):
    #     await self._tsmart.async_control_set(
    #         self.hvac_mode == HVACMode.HEAT, PRESET_MAP[self.preset_mode], temperature
    #     )
    #     await self.coordinator.async_request_refresh()

    # def _climate_preset(self, tsmart_mode):
    #     return next((k for k, v in PRESET_MAP.items() if v == tsmart_mode), None)

    # @property
    # def preset_mode(self):
    #     return self._climate_preset(self._tsmart.mode)

    # async def async_set_preset_mode(self, preset_mode):
    #     await self._tsmart.async_control_set(
    #         self.hvac_mode == HVACMode.HEAT,
    #         PRESET_MAP[preset_mode],
    #         self.target_temperature,
    #     )
    #     await self.coordinator.async_request_refresh()

    # @property
    # def extra_state_attributes(self) -> dict[str, str] | None:
    #     """Return the state attributes of the battery type."""

    #     # Temperature related attributes
    #     attrs = {
    #         ATTR_TEMPERATURE_LOW: self._tsmart.temperature_low,
    #         ATTR_TEMPERATURE_HIGH: self._tsmart.temperature_high,
    #         ATTR_TEMPERATURE_AVERAGE: self._tsmart.temperature_average,
    #     }

    #     super_attrs = super().extra_state_attributes
    #     if super_attrs:
    #         attrs.update(super_attrs)
    #     return attrs

    def process_update(self, mqtt_data) -> None:
        """Update the state of the sensor."""
        self._mqtt_data = mqtt_data
        if (self.hass is not None): # this is a hack to get around the fact that the entity is not yet initialized at first
            self.async_schedule_update_ha_state()