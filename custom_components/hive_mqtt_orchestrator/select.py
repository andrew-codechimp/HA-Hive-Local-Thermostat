"""Select platform for hive_mqtt_orchestrator."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import callback
from homeassistant.util import slugify
from homeassistant.const import (
    Platform,
    UnitOfInformation,
    CONF_NAME,
    CONF_ENTITIES,
)

from .entity import HiveEntity, HiveEntityDescription

from .const import (
    DOMAIN,
    LOGGER,
    CONF_MQTT_TOPIC
)

@dataclass
class HiveSensorEntityDescription(
    HiveEntityDescription,
    SelectEntityDescription,
):
    """Class describing Hive sensor entities."""


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
    ):
    """Set up the sensor platform."""

    ENTITY_DESCRIPTIONS = (
        HiveSensorEntityDescription(
            key="system_mode_water",
            translation_key="system_mode_water",
            icon="mdi:water-boiler",
            func=lambda js: js["system_mode_water"],
            topic=config_entry.options[CONF_MQTT_TOPIC]
        ),
    )

    _entities = {}

    _entities = [HiveSelect(entity_description=entity_description,) for entity_description in ENTITY_DESCRIPTIONS]

    async_add_entities(
        [sensorEntity for sensorEntity in _entities],
    )

    hass.data[DOMAIN][config_entry.entry_id][Platform.SELECT] = _entities

class HiveSelect(HiveEntity, SelectEntity):
    """hive_mqtt_orchestrator Select class."""

    def __init__(
        self,
        entity_description: HiveSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(entity_description)

        self.entity_description = entity_description
        self._attr_unique_id = f"{DOMAIN}_{entity_description.key}".lower()
        self._attr_has_entity_name = True
        self._func = entity_description.func
        self._topic = entity_description.topic

    def process_update(self, mqtt_data) -> None:
        """Update the state of the sensor."""
        new_value = self._func(mqtt_data)
        # if (self._ignore_zero_values and new_value == 0):
        #     LOGGER.debug("Ignored new value of %s on %s.", new_value, self._attr_unique_id)
        #     return
        self._attr_native_value = new_value
        if (self.hass is not None): # this is a hack to get around the fact that the entity is not yet initialized at first
            self.async_schedule_update_ha_state()

    @property
    def options(self):
        "Return the list of possible options."
        return self._option_dps.values(self._device)

    @property
    def current_option(self):
        "Return the currently selected option"
        return self._option_dps.get_value(self._device)

    async def async_select_option(self, option):
        "Set the option"
        await self._option_dps.async_set_value(self._device, option)