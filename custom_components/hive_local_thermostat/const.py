"""Constants for hive_local_thermostat."""

import json
from logging import Logger, getLogger
from pathlib import Path
from typing import Final

LOGGER: Logger = getLogger(__package__)

MIN_HA_VERSION = "2024.12"

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

MODEL_SLR1 = "SLR1"
MODEL_SLR2 = "SLR2"

MODELS = [
    MODEL_SLR1,
    MODEL_SLR2,
]

HIVE_BOOST = "emergency_heat"

DEFAULT_FROST_TEMPERATURE = 12
DEFAULT_HEATING_BOOST_MINUTES = 120
DEFAULT_HEATING_BOOST_TEMPERATURE = 25
DEFAULT_WATER_BOOST_MINUTES = 60

WATER_MODES: Final = ["auto", "heat", "off", "boost"]

ICON_UNKNOWN = "mdi:help"
