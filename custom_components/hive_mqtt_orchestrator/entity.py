"""AndrewsArnoldQuotaEntity class."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, VERSION, MANUFACTURER
from .coordinator import HiveDataUpdateCoordinator


@dataclass
class HiveEntityDescription(EntityDescription):
    """Defines a base Hive entity description."""

    entity_id: str | None = None


class HiveEntity():
    """HiveEntity class."""

    entity_description: HiveEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        description: HiveEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=NAME,
            model=VERSION,
            manufacturer=MANUFACTURER,
        )
        self.entity_description = description
        if description.entity_id:
            self.entity_id = description.entity_id
