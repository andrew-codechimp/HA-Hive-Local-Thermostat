"""Sensor platform for Hive Local Thermostat."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Any

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    PRESET_BOOST,
    PRESET_NONE,
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .common import HiveConfigEntry
from .const import (
    DOMAIN,
    HIVE_BOOST,
    LOGGER,
)
from .coordinator import HiveCoordinator
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
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: HiveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    coordinator = config_entry.runtime_data.coordinator

    hive_climate_entity_description = HiveClimateEntityDescription(
        key="climate",
        translation_key="climate",
        name=config_entry.title,
    )

    _entities = [
        HiveClimateEntity(
            entity_description=hive_climate_entity_description, coordinator=coordinator
        )
    ]

    async_add_entities(climateEntity for climateEntity in _entities)


class HiveClimateEntity(HiveEntity, ClimateEntity):
    """hive_local_thermostat Climate class."""

    entity_description: HiveClimateEntityDescription

    def __init__(
        self,
        entity_description: HiveClimateEntityDescription,
        coordinator: HiveCoordinator,
    ) -> None:
        """Initialize the sensor class."""

        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{DOMAIN}_{entity_description.name}_{entity_description.key}".lower()
        )
        self._attr_has_entity_name = True

        self._attr_temperature_unit = UnitOfTemperature.CELSIUS

        if coordinator.show_heating_schedule_mode:
            self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
        else:
            self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
        self._attr_hvac_mode = None
        self._attr_preset_modes = list(PRESET_MAP.keys())
        self._attr_preset_mode = None

        self._attr_supported_features = (
            ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
        )

        self._attr_max_temp = 32
        self._attr_min_temp = 5
        self._attr_target_temperature_step = 0.5

        self._hvac_mode_set_from_temperature = False

        super().__init__(entity_description, coordinator)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode."""

        self._attr_preset_mode = preset_mode

        if preset_mode == "boost":
            self.coordinator.pre_boost_hvac_mode = self._attr_hvac_mode
            self.coordinator.pre_boost_occupied_heating_setpoint_heat = (
                self._attr_target_temperature
            )

            await self.coordinator.async_heating_boost()

        elif self.coordinator.pre_boost_hvac_mode is not None:
            if (
                self.coordinator.pre_boost_hvac_mode == HVACMode.HEAT
                and self.coordinator.pre_boost_occupied_heating_setpoint_heat
                is not None
            ):
                await self.coordinator.async_set_hvac_mode_heat(
                    self.coordinator.pre_boost_occupied_heating_setpoint_heat,
                )
            else:
                await self.async_set_hvac_mode(self.coordinator.pre_boost_hvac_mode)
            self.coordinator.pre_boost_hvac_mode = None
            self.coordinator.pre_boost_occupied_heating_setpoint_heat = None

        # Write updated temperature to HA state to avoid flapping (MQTT confirmation is slow)
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature."""
        """Set the target temperature."""
        if temperature := kwargs.get(ATTR_TEMPERATURE):
            self._attr_target_temperature = temperature

        if hvac_mode := kwargs.get(ATTR_HVAC_MODE):
            self._hvac_mode_set_from_temperature = True
            await self.async_set_hvac_mode(hvac_mode)
            return

        if temperature:
            await self.coordinator.async_set_temperature(temperature)

        # Write updated temperature to HA state to avoid flapping (MQTT confirmation is slow)
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the hvac mode."""

        if hvac_mode in self._attr_hvac_modes:
            self._attr_hvac_mode = hvac_mode
        else:
            LOGGER.error("Unrecognized hvac mode: %s", hvac_mode)
            return

        if hvac_mode == HVACMode.AUTO:
            await self.coordinator.async_set_hvac_mode_auto()
        if hvac_mode == HVACMode.HEAT:
            if self._hvac_mode_set_from_temperature:
                assert self._attr_target_temperature is not None
                await self.coordinator.async_set_hvac_mode_heat(
                    self._attr_target_temperature, self._hvac_mode_set_from_temperature
                )

                self._hvac_mode_set_from_temperature = False
                self.async_write_ha_state()
                return

            if self.coordinator.pre_boost_occupied_heating_setpoint_heat:
                await self.coordinator.async_set_hvac_mode_heat(
                    self.coordinator.pre_boost_occupied_heating_setpoint_heat,
                    self._hvac_mode_set_from_temperature,
                )
            else:
                if self._attr_current_temperature:
                    # Get the current temperature and round down to nearest .5
                    self._attr_target_temperature = (
                        floor((self._attr_current_temperature) * 2) / 2
                    )
                assert self._attr_target_temperature is not None
                await self.coordinator.async_set_hvac_mode_heat(
                    self._attr_target_temperature, self._hvac_mode_set_from_temperature
                )

        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_set_hvac_mode_off()

        self._hvac_mode_set_from_temperature = False

        # Write updated temperature to HA state to avoid flapping (MQTT confirmation is slow)
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Set the HVAC State to on."""
        assert self._attr_target_temperature is not None
        await self.coordinator.async_set_hvac_mode_heat(self._attr_target_temperature)

    async def async_turn_off(self) -> None:
        """Set the HVAC State to off."""
        await self.coordinator.async_set_hvac_mode_off()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._attr_current_temperature = self.coordinator.current_temperature
        self._attr_target_temperature = self.coordinator.target_temperature
        self._attr_preset_mode = self.coordinator.preset_mode
        self._attr_hvac_action = self.coordinator.hvac_action
        self._attr_hvac_mode = self.coordinator.hvac_mode

        # Update HA state
        self.async_write_ha_state()
