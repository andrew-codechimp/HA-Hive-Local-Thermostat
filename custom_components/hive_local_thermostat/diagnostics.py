"""Diagnostics support for Hive Local Thermostat."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .common import HiveConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    hive_entry: HiveConfigEntry = entry

    # Get runtime data
    runtime_data = hive_entry.runtime_data

    # Convert diagnostic data deque to list
    diagnostic_data_list = list(runtime_data.diagnostic_data)

    return {
        "config_entry": {
            "title": entry.title,
            "version": entry.version,
            "minor_version": entry.minor_version,
            "data": dict(sorted(entry.data.items())),
            "options": dict(sorted(entry.options.items())),
        },
        "entity_values": dict(sorted(runtime_data.entity_values.items())),
        "diagnostic_data": diagnostic_data_list,
    }
