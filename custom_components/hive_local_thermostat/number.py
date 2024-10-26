"""Number platform for hive_local_thermostat."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntityDescription,
    RestoreNumber,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    Platform,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.dt import utcnow

from .const import (
    CONF_MODEL,
    CONF_MQTT_TOPIC,
    DEFAULT_FROST_TEMPERATURE,
    DEFAULT_HEATING_BOOST_MINUTES,
    DEFAULT_HEATING_BOOST_TEMPERATURE,
    DEFAULT_HEATING_TEMPERATURE,
    DEFAULT_WATER_BOOST_MINUTES,
    DOMAIN,
    LOGGER,
    MODEL_SLR2,
)
from .entity import HiveEntity, HiveEntityDescription


@dataclass(frozen=True, kw_only=True)
class HiveNumberEntityDescription(
    HiveEntityDescription,
    NumberEntityDescription,
):
    """Class describing Hive number entities."""

    default_value: float | None = None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the sensor platform."""

    entity_descriptions = [
        HiveNumberEntityDescription(
            key="heating_boost_duration",
            translation_key="heating_boost_duration",
            name=config_entry.title,
            icon="mdi:timer",
            topic=config_entry.options[CONF_MQTT_TOPIC],
            entity_category=EntityCategory.CONFIG,
            native_min_value=30,
            native_max_value=180,
            native_step=1,
            default_value=DEFAULT_HEATING_BOOST_MINUTES,
            entry_id=config_entry.entry_id,
            model=config_entry.options[CONF_MODEL],
        ),
        HiveNumberEntityDescription(
            key="heating_frost_prevention",
            translation_key="heating_frost_prevention",
            name=config_entry.title,
            icon="mdi:snowflake-thermometer",
            topic=config_entry.options[CONF_MQTT_TOPIC],
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            native_min_value=5,
            native_max_value=16,
            native_step=0.5,
            default_value=DEFAULT_FROST_TEMPERATURE,
            entry_id=config_entry.entry_id,
            model=config_entry.options[CONF_MODEL],
        ),
        HiveNumberEntityDescription(
            key="heating_default_temperature",
            translation_key="heating_default_temperature",
            name=config_entry.title,
            icon="mdi:thermometer",
            topic=config_entry.options[CONF_MQTT_TOPIC],
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            native_min_value=16,
            native_max_value=22,
            native_step=0.5,
            default_value=DEFAULT_HEATING_TEMPERATURE,
            entry_id=config_entry.entry_id,
            model=config_entry.options[CONF_MODEL],
        ),
        HiveNumberEntityDescription(
            key="heating_boost_temperature",
            translation_key="heating_boost_temperature",
            name=config_entry.title,
            icon="mdi:thermometer",
            topic=config_entry.options[CONF_MQTT_TOPIC],
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            native_min_value=12,
            native_max_value=32,
            native_step=0.5,
            default_value=DEFAULT_HEATING_BOOST_TEMPERATURE,
            entry_id=config_entry.entry_id,
            model=config_entry.options[CONF_MODEL],
        ),
    ]

    if config_entry.options[CONF_MODEL] == MODEL_SLR2:
        entity_descriptions.append(
            HiveNumberEntityDescription(
                key="water_boost_duration",
                translation_key="water_boost_duration",
                name=config_entry.title,
                icon="mdi:timer",
                topic=config_entry.options[CONF_MQTT_TOPIC],
                entity_category=EntityCategory.CONFIG,
                native_min_value=30,
                native_max_value=180,
                native_step=1,
                default_value=DEFAULT_WATER_BOOST_MINUTES,
                entry_id=config_entry.entry_id,
                model=config_entry.options[CONF_MODEL],
            )
        )

    _entities = [
        HiveNumber(
            entity_description=entity_description,
        )
        for entity_description in entity_descriptions
    ]

    async_add_entities(sensorEntity for sensorEntity in _entities)

    hass.data[DOMAIN][config_entry.entry_id][Platform.NUMBER] = _entities


class HiveNumber(HiveEntity, RestoreNumber):
    """hive_local_thermostat Number class."""

    entity_description: HiveNumberEntityDescription
    _state: float | None

    def __init__(
        self,
        entity_description: HiveNumberEntityDescription,
    ) -> None:
        """Initialize the sensor class."""

        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{DOMAIN}_{entity_description.name}_{entity_description.key}".lower()
        )
        self._attr_has_entity_name = True
        self._topic = entity_description.topic
        self._state = None
        self._attributes = {}
        self._last_updated = None

        super().__init__(entity_description)

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

        if self.entity_description.entry_id not in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN][self.entity_description.entry_id] = []

        self.hass.data[DOMAIN][self.entity_description.entry_id][
            self.entity_description.key
        ] = self._state

        LOGGER.debug(f"Restored {self.entity_description.key} state: {self._state}")

    @property
    def native_value(self) -> float | None:
        """Return value of number."""
        return self._state

    async def async_set_native_value(self, value: float) -> None:
        """Set value."""
        self._state = value
        self._last_updated = utcnow()

        if self.entity_description.entry_id not in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN][self.entity_description.entry_id] = []

        self.hass.data[DOMAIN][self.entity_description.entry_id][
            self.entity_description.key
        ] = value

        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        """Attributes of the sensor."""
        return self._attributes

    def process_update(self, mqtt_data) -> None:
        """Update the state of the sensor."""
        if (
            self.hass is not None
        ):  # this is a hack to get around the fact that the entity is not yet initialized at first
            self.async_schedule_update_ha_state()
