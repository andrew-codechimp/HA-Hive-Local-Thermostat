"""Common definitions for Hive Local Thermostat integration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from .coordinator import HiveCoordinator


@dataclass
class HiveData:
    """Hive data type."""

    platforms: list[Platform]
    coordinator: HiveCoordinator


type HiveConfigEntry = ConfigEntry[HiveData]
