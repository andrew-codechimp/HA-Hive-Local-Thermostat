"""AndrewsArnoldQuotaEntity class."""

from __future__ import annotations

import abc

from dataclasses import dataclass

from homeassistant.helpers.entity import DeviceInfo, EntityDescription

from .const import DOMAIN, NAME, VERSION, MANUFACTURER


@dataclass
class HiveEntityDescription(EntityDescription):
    """Defines a base Hive entity description."""

    entity_id: str | None = None
    func: any | None = None


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

    @abc.abstractmethod
    def process_update(self, mqtt_data) -> None:
        raise NotImplementedError('users must define process_update to use this base class')