# HA-Hive-Local-Thermostat

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![Downloads][download-latest-shield]]()
[![HACS Installs][hacs-installs-shield]]()
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

Local Hive Thermostat MQTT integration for Home Assistant

_Please :star: this repo if you find it useful_  
_If you want to show your support please_

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/codechimp)

To use this integration your Hive thermostat receiver must be added to [Zigbee2MQTT](https://www.zigbee2mqtt.io/supported-devices/#v=Hive) and a MQTT broker and the MQTT integration within Home Assistant must be correctly configured.

Zigbee2MQTT will expose the native sensors but Hive requires specific message structures to be sent for setting modes and a combination of sensor values to determine the modes, this integration creates controls and sensors that correctly interface with the native Hive values/methods.

SLR1x, SLR2x and OTR1 thermostats are supported, this has been tested with an SLR2c, SLR1c and OTR1. If you have thoroughly tested a different model please let me know and I'll add it to the list of confirmed devices. As long as you have one of these receivers this integration will work with either the Hive mini or regular controller.

Once you have the thermostat receiver added to Zigbee2MQTT, add a device via this integration and specify a friendly name, the Zigbee2MQTT topic which should look something like this `zigbee2mqtt/HiveReceiver` (note this is case sensitive).

The new device created will have new sensors/controls available that will accurately show/send status changes.

You can optionally hide/disable the native Hive device created by Zigbee2MQTT within HomeAssistant.

The integration supports native boost and native schedules. With schedules you can switch on/off schedule mode but you cannot modify the schedule details via the integration. You can of course ignore the schedule mode and setup automations within Home Assistant to control when heating/water is on or off and set a temperature for heating.

The numeric entities allow you to set defaults for boost times, heating boost temperature and also frost protection. Frost protection should be set to match what you have set on the Hive thermostat for an accurate display.

Two actions are provided to natively boost the Heating `hive_local_thermostat.boost_heating` and Water `hive_local_thermostat.boost_water` (SLR2 only), these can optionally take a duration and temperature (heating only), these actions allow you to make custom buttons/scripts/automations to add additional control over the default boost buttons.

![Hive Screenshot](https://raw.githubusercontent.com/andrew-codechimp/HA-Hive-Local-Thermostat/main/images/screenshot.png "Hive Controls")

This project is not endorsed by, directly affiliated with, maintained, authorized, or sponsored by Hive.

## Installation

### HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=andrew-codechimp&repository=HA-Hive-Local-Thermostat&category=Integration)

Restart Home Assistant

In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Hive Local Thermostat"

### Manual Installation

<details>
<summary>Show detailed instructions</summary>

Installation via HACS is recommended, but a manual setup is supported.

1. Manually copy custom_components/hive_local_thermostat folder from latest release to custom_components folder in your config folder.
1. Restart Home Assistant.
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Hive Local Thermostat"

</details>

## FAQ's

- My boost remaining sensors are not counting down

  By default Zigbee2MQTT will not send frequent updates to track boosts by the minute, they will update but this is typically every 10 minutes.

  To change this within Zigbee2MQTT go into the receiver's reporting settings and change the following;  
  Min Rep Change of any tempSetpointHoldDuration to 1  
  If you have heat and water you will have two values under different Endpoints, with heat only you will have one.

- How do I get beta versions with HACS
  - Within Home Assistant go to Settings -> Integrations -> HACS
  - Select Services
  - Select Hive Local Thermostat
  - In the Diagnostics panel select the +1 entity not shown
  - Select Pre-release
  - Select the cog icon
  - Select Enable
  - Select Update and wait for the entity to be enabled
  - Turn on the Pre-release toggle
  - HACS will now show updates available for pre-releases if there are any

[commits-shield]: https://img.shields.io/github/commit-activity/y/andrew-codechimp/HA-Hive-Local-Thermostat.svg?style=for-the-badge
[commits]: https://github.com/andrew-codechimp/HA-Hive-Local-Thermostat/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge
[exampleimg]: example.png
[license-shield]: https://img.shields.io/github/license/andrew-codechimp/HA-Hive-Local-Thermostat.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/andrew-codechimp/HA-Hive-Local-Thermostat.svg?style=for-the-badge
[releases]: https://github.com/andrew-codechimp/HA-Hive-Local-Thermostat/releases
[download-latest-shield]: https://img.shields.io/github/downloads/andrew-codechimp/HA-Hive-Local-Thermostat/latest/total?style=for-the-badge
[hacs-installs-shield]: https://img.shields.io/endpoint.svg?url=https%3A%2F%2Flauwbier.nl%2Fhacs%2Fhive_local_thermostat&style=for-the-badge
