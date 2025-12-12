"""HiveLocalThermostatEntity class."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HiveCoordinator


@dataclass(frozen=True, kw_only=True)
class HiveEntityDescription(EntityDescription):
    """Defines a base Hive entity description."""

    entity_id: str | None = None


class HiveEntity(CoordinatorEntity[HiveCoordinator]):
    """HiveEntity class."""

    entity_description: HiveEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        description: HiveEntityDescription,
        coordinator: HiveCoordinator,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry_id)},
            name=self.entity_description.name
            if isinstance(self.entity_description.name, str)
            else None,
            model=coordinator.model,
            manufacturer="Hive",
        )
        self.entity_description = description
        if description.entity_id:
            self.entity_id = description.entity_id
