"""Button platform for Hive Local Thermostat."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .common import HiveConfigEntry
from .const import (
    DOMAIN,
    MODEL_SLR2,
)
from .coordinator import HiveCoordinator
from .entity import HiveEntity, HiveEntityDescription


@dataclass(frozen=True, kw_only=True)
class HiveButtonEntityDescription(
    HiveEntityDescription,
    ButtonEntityDescription,
):
    """Class describing Hive sensor entities."""


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: HiveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    coordinator = config_entry.runtime_data.coordinator

    entity_descriptions = [
        HiveButtonEntityDescription(
            key="boost_heating",
            translation_key="boost_heating",
            name=config_entry.title,
        ),
    ]

    if coordinator.model == MODEL_SLR2:
        entity_descriptions.append(
            HiveButtonEntityDescription(
                key="boost_water",
                translation_key="boost_water",
                name=config_entry.title,
            )
        )

    _entities = [
        HiveButton(
            entity_description=entity_description,
            coordinator=coordinator,
        )
        for entity_description in entity_descriptions
    ]

    async_add_entities(sensorEntity for sensorEntity in _entities)


class HiveButton(HiveEntity, ButtonEntity):
    """hive_local_thermostat Button class."""

    entity_description: HiveButtonEntityDescription

    def __init__(
        self,
        entity_description: HiveButtonEntityDescription,
        coordinator: HiveCoordinator,
    ) -> None:
        """Initialize the button class."""

        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{DOMAIN}_{entity_description.name}_{entity_description.key}".lower()
        )
        self._attr_has_entity_name = True

        super().__init__(entity_description, coordinator)

    async def async_press(self) -> None:
        """Press the button."""
        if self.entity_description.key == "boost_water":
            await self.coordinator.async_water_boost()
        elif self.entity_description.key == "boost_heating":
            await self.coordinator.async_heating_boost()
