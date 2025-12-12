"""Number platform for Hive Local Thermostat."""

from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
    UnitOfTemperature,
)
from homeassistant.util.dt import utcnow
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.number import (
    RestoreNumber,
    NumberDeviceClass,
    NumberEntityDescription,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    LOGGER,
    MODEL_SLR2,
    DEFAULT_FROST_TEMPERATURE,
    DEFAULT_WATER_BOOST_MINUTES,
    DEFAULT_HEATING_BOOST_MINUTES,
    DEFAULT_HEATING_BOOST_TEMPERATURE,
)
from .common import HiveConfigEntry
from .entity import HiveEntity, HiveEntityDescription
from .coordinator import HiveCoordinator


@dataclass(frozen=True, kw_only=True)
class HiveNumberEntityDescription(
    HiveEntityDescription,
    NumberEntityDescription,
):
    """Class describing Hive number entities."""

    default_value: float | None = None


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: HiveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    coordinator = config_entry.runtime_data.coordinator

    entity_descriptions = [
        HiveNumberEntityDescription(
            key="heating_boost_duration",
            translation_key="heating_boost_duration",
            name=config_entry.title,
            entity_category=EntityCategory.CONFIG,
            native_min_value=15,
            native_max_value=180,
            native_step=1,
            default_value=DEFAULT_HEATING_BOOST_MINUTES,
        ),
        HiveNumberEntityDescription(
            key="heating_frost_prevention",
            translation_key="heating_frost_prevention",
            name=config_entry.title,
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            native_min_value=5,
            native_max_value=16,
            native_step=0.5,
            default_value=DEFAULT_FROST_TEMPERATURE,
        ),
        HiveNumberEntityDescription(
            key="heating_boost_temperature",
            translation_key="heating_boost_temperature",
            name=config_entry.title,
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            native_min_value=12,
            native_max_value=32,
            native_step=0.5,
            default_value=DEFAULT_HEATING_BOOST_TEMPERATURE,
        ),
    ]

    if coordinator.model == MODEL_SLR2:
        entity_descriptions.append(
            HiveNumberEntityDescription(
                key="water_boost_duration",
                translation_key="water_boost_duration",
                name=config_entry.title,
                entity_category=EntityCategory.CONFIG,
                native_min_value=15,
                native_max_value=180,
                native_step=1,
                default_value=DEFAULT_WATER_BOOST_MINUTES,
            )
        )

    _entities = [
        HiveNumber(
            entity_description=entity_description,
            coordinator=coordinator,
        )
        for entity_description in entity_descriptions
    ]

    async_add_entities(sensorEntity for sensorEntity in _entities)


class HiveNumber(HiveEntity, RestoreNumber):
    """hive_local_thermostat Number class."""

    entity_description: HiveNumberEntityDescription
    _state: float | None
    _last_updated: datetime | None

    def __init__(
        self,
        entity_description: HiveNumberEntityDescription,
        coordinator: HiveCoordinator,
    ) -> None:
        """Initialize the sensor class."""

        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{DOMAIN}_{entity_description.name}_{entity_description.key}".lower()
        )
        self._attr_has_entity_name = True
        self._state = None
        self._last_updated = None

        super().__init__(entity_description, coordinator)

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()

        if (last_state := await self.async_get_last_state()) and (
            last_number_data := await self.async_get_last_number_data()
        ):
            if last_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                self._state = last_number_data.native_value
            else:
                self._state = self.entity_description.default_value
        else:
            self._state = self.entity_description.default_value

        # Store value in coordinator
        setattr(self.coordinator, self.entity_description.key, self._state)

        LOGGER.debug(f"Restored {self.entity_description.key} state: {self._state}")

    @property
    def native_value(self) -> float | None:
        """Return value of number."""
        return self._state

    async def async_set_native_value(self, value: float) -> None:
        """Set value."""
        self._state = value
        self._last_updated = utcnow()

        # Store value in coordinator
        setattr(self.coordinator, self.entity_description.key, value)

        self.async_write_ha_state()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Number entities don't need to process MQTT data updates
        # They only update through user input
        self.async_write_ha_state()
