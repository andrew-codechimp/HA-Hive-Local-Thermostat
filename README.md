# HA-Hive-Local-Thermostat

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![Downloads][download-latest-shield]](Downloads)
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]


Local Hive Thermostat MQTT integration for Home Assistant

*Please :star: this repo if you find it useful*  
*If you want to show your support please*

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/codechimp)

To use this integration your Hive thermostat receiver must be added to [Zigbee2MQTT](https://www.zigbee2mqtt.io/supported-devices/#v=Hive) and a MQTT broker and the MQTT integration within Home Assistant must be correctly configured.

Zigbee2MQTT will expose the native sensors but Hive requires specific message structures to be sent for setting modes and a combination of sensor values to determine the modes, this integration creates controls and sensors that correctly interface with the native Hive values/methods.

SLR1x and SLR2x thermostats are supported, this has been tested with an SLR2c and an SLR1c. If you have thoroughly tested a different model please let me know and I'll add it to the list of confirmed devices. As long as you have one of these receivers this integration will work with either the Hive mini or regular controller.

Once you have the thermostat receiver added to Zigbee2MQTT, add a device via this integration and specify a friendly name, the Zibee2MQTT topic which should look something like this `zigbee2mqtt/HiveReceiver` (note this is case sensitive).

The new device created will have new sensors/controls available that will accurately show/send status changes.

You can optionally hide/disable the native Hive device created by Zigbee2MQTT within HomeAssistant.

The integration supports native boost and native schedules. With schedules you can switch on/off schedule mode but you cannot modify the schedule details via the integration. You can of course ignore the schedule mode and setup automations within Home Assistant to control when heating/water is on or off and set a temperature for heating.

The numeric entities allow you to set defaults for boost times, temperatures and also frost protection. Frost protection should be set to match what you have set on the Hive thermostat for an accurate display.

![Hive Screenshot](https://github.com/andrew-codechimp/HA-Hive-Local-Thermostat/blob/main/images/screenshot.png "Hive Controls")

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

***

[commits-shield]: https://img.shields.io/github/commit-activity/y/andrew-codechimp/HA-Hive-Local-Thermostat.svg?style=for-the-badge
[commits]: https://github.com/andrew-codechimp/HA-Hive-Local-Thermostat/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[exampleimg]: example.png
[license-shield]: https://img.shields.io/github/license/andrew-codechimp/HA-Hive-Local-Thermostat.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/andrew-codechimp/HA-Hive-Local-Thermostat.svg?style=for-the-badge
[releases]: https://github.com/andrew-codechimp/HA-Hive-Local-Thermostat/releases
[download-latest-shield]: https://img.shields.io/github/downloads/andrew-codechimp/HA-Hive-Local-Thermostat/latest/total?style=for-the-badge
