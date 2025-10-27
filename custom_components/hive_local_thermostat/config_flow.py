"""Adds config flow for hive_local_thermostat."""
from __future__ import annotations

from typing import Any, cast
from collections.abc import Mapping

import voluptuous as vol

from homeassistant.core import callback
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaFlowFormStep,
    SchemaFlowMenuStep,
    SchemaConfigFlowHandler,
    SchemaOptionsFlowHandler,
)

from . import const


def required(
    key: str, options: dict[str, Any], default: Any | None = None
) -> vol.Required:
    """Return vol.Required."""
    if isinstance(options, dict) and key in options:
        suggested_value = options[key]
    elif default is not None:
        suggested_value = default
    else:
        return vol.Required(key)
    return vol.Required(key, description={"suggested_value": suggested_value})


def optional(
    key: str, options: dict[str, Any], default: Any | None = None
) -> vol.Optional:
    """Return vol.Optional."""
    if isinstance(options, dict) and key in options:
        suggested_value = options[key]
    elif default is not None:
        suggested_value = default
    else:
        return vol.Optional(key)
    return vol.Optional(key, description={"suggested_value": suggested_value})


async def general_options_schema(
    handler: SchemaConfigFlowHandler | SchemaOptionsFlowHandler,
) -> vol.Schema:
    """Generate options schema."""
    return vol.Schema(
        {
            required(const.CONF_MQTT_TOPIC, handler.options): selector.TextSelector(),
            required(const.CONF_MODEL, handler.options): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=const.MODELS,
                        translation_key="model",
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    ),
                ),
            required(const.CONF_SHOW_HEAT_SCHEDULE_MODE, handler.options, default=True): selector.BooleanSelector(
                    selector.BooleanSelectorConfig(),
                ),
            required(const.CONF_SHOW_WATER_SCHEDULE_MODE, handler.options, default=True): selector.BooleanSelector(
                    selector.BooleanSelectorConfig(),
                ),
        }
    )


async def general_config_schema(
    handler: SchemaConfigFlowHandler | SchemaOptionsFlowHandler,
) -> vol.Schema:
    """Generate config schema."""
    return vol.Schema(
        {
            required(CONF_NAME, handler.options): selector.TextSelector(),
            required(const.CONF_MQTT_TOPIC, handler.options): selector.TextSelector(),
            required(const.CONF_MODEL, handler.options): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=const.MODELS,
                        translation_key="model",
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    ),
                ),
            required(const.CONF_SHOW_HEAT_SCHEDULE_MODE, handler.options, default=True): selector.BooleanSelector(
                    selector.BooleanSelectorConfig(),
                ),
            required(const.CONF_SHOW_WATER_SCHEDULE_MODE, handler.options, default=True): selector.BooleanSelector(
                    selector.BooleanSelectorConfig(),
                ),
        }
    )

CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "user": SchemaFlowFormStep(general_config_schema),
}
OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "init": SchemaFlowFormStep(general_options_schema),
}


# mypy: ignore-errors
class ConfigFlowHandler(SchemaConfigFlowHandler, domain=const.DOMAIN):
    """Handle a config or options flow for Holdays."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW
    VERSION = const.CONFIG_VERSION

    @callback
    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title.

        The options parameter contains config entry options, which is the union of user
        input from the config flow steps.
        """
        return cast("str", options["name"]) if "name" in options else ""
