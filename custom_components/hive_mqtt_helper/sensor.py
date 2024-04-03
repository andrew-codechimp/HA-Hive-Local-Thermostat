"""Sensor platform for andrews_arnold_quota."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import (
    UnitOfInformation,
)

from .const import DOMAIN
from .coordinator import HiveDataUpdateCoordinator
from .entity import HiveEntity, HiveEntityDescription


@dataclass
class HiveSensorEntityDescription(
    HiveEntityDescription,
    SensorEntityDescription,
):
    """Class describing Hive sensor entities."""


ENTITY_DESCRIPTIONS = (
    HiveSensorEntityDescription(
        key="monthly_quota_gb",
        translation_key="monthly_quota",
        entity_id="sensor.andrews_arnold_monthly_quota",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        api_field="quota_monthly",
    ),
    HiveSensorEntityDescription(
        key="quota_remaining_gb",
        translation_key="quota_remaining",
        entity_id="sensor.andrews_arnold_quota_remaining",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        api_field="quota_remaining",
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        HiveSensor(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class HiveSensor(HiveEntity, SensorEntity):
    """andrews_arnold_quota Sensor class."""

    def __init__(
        self,
        coordinator: HiveDataUpdateCoordinator,
        entity_description: HiveSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(entity_description, coordinator)

        self.entity_description = entity_description
        self._attr_unique_id = f"andrews_arnold_quota_{entity_description.key}".lower()
        self._attr_has_entity_name = True

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        if (
            self.coordinator.data
            and "quota" in self.coordinator.data
            and self.entity_description.api_field in self.coordinator.data["quota"][0]
        ):
            return round(
                int(
                    self.coordinator.data["quota"][0][self.entity_description.api_field]
                )
                / 1000000000,
                1,
            )
        return None
