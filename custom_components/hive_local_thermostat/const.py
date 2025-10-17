"""Constants for hive_local_thermostat."""

import json
from logging import Logger, getLogger
from pathlib import Path

LOGGER: Logger = getLogger(__package__)

MIN_HA_VERSION = "2025.4"

manifestfile = Path(__file__).parent / "manifest.json"
with open(file=manifestfile, encoding="UTF-8") as json_file:
    manifest_data = json.load(json_file)

DOMAIN = manifest_data.get("domain")
NAME = manifest_data.get("name")
VERSION = manifest_data.get("version")
ISSUEURL = manifest_data.get("issue_tracker")
CONFIG_VERSION = 1

CONF_MQTT_TOPIC = "mqtt_topic"
CONF_MODEL = "model"
CONF_SHOW_HEAT_SCHEDULE_MODE = "show_heat_schedule_mode"
CONF_SHOW_WATER_SCHEDULE_MODE = "show_water_schedule_mode"

MODEL_OTR1 = "OTR1"
MODEL_SLR1 = "SLR1"
MODEL_SLR2 = "SLR2"

MODELS = [
    MODEL_OTR1,
    MODEL_SLR1,
    MODEL_SLR2,
]

HIVE_BOOST = "emergency_heat"

DEFAULT_FROST_TEMPERATURE = 12
DEFAULT_HEATING_BOOST_MINUTES = 120
DEFAULT_HEATING_BOOST_TEMPERATURE = 25
DEFAULT_WATER_BOOST_MINUTES = 60

ICON_UNKNOWN = "mdi:help"
