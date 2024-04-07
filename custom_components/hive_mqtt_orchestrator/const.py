"""Constants for hive_mqtt_orchestrator."""

import json
from logging import Logger, getLogger
from pathlib import Path

LOGGER: Logger = getLogger(__package__)

MIN_HA_VERSION = "2024.3"

manifestfile = Path(__file__).parent / "manifest.json"
with open(file=manifestfile, encoding="UTF-8") as json_file:
    manifest_data = json.load(json_file)

DOMAIN = manifest_data.get("domain")
NAME = manifest_data.get("name")
VERSION = manifest_data.get("version")
ISSUEURL = manifest_data.get("issue_tracker")
MANUFACTURER = "@Andrew-CodeChimp"
CONFIG_VERSION = 1

CONF_MQTT_TOPIC = "mqtt_topic"

HIVE_BOOST = "emergency_heat"

DEFAULT_HEATING_TEMPERATURE = 20
DEFAULT_FROST_TEMPERATURE = 12
DEFAULT_HEATING_BOOST_MINUTES = 120
DEFAULT_WATER_BOOST_MINUTES = 60