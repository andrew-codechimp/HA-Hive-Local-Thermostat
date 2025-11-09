"""Type definitions for Hive Local Thermostat integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntry


@dataclass
class HiveData:
    """Hive data type."""

    platforms: list[Platform]
    entities: dict[Platform, list] = None
    entity_values: dict[str, float] = None

    def __post_init__(self):
        """Initialize mutable default values."""
        if self.entities is None:
            self.entities = {}
        if self.entity_values is None:
            self.entity_values = {}


type HiveConfigEntry = ConfigEntry[HiveData]
