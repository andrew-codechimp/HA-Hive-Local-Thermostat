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

To use this integration your Hive thermostat receiver must be added to [Zigbee2MQTT](https://www.zigbee2mqtt.io/supported-devices/#v=Hive) and an MQTT broker and the MQTT integration within Home Assistant must be correctly configured. It is important to follow the pairing steps within the Zigbee2MQTT documentation, the thermostat remote control must be paired directly to the thermostat receiver.

Zigbee2MQTT will expose the native sensors but Hive requires specific message structures to be sent for setting modes and a combination of sensor values to determine the modes, this integration creates controls and sensors that correctly interface with the native Hive values/methods.

SLR1x, SLR2x, SLT6b and OTR1 thermostats are supported, this has been tested with an SLR2d, SLR2c, SLR1c and OTR1. If you have thoroughly tested a different model please let me know and I'll add it to the list of confirmed devices. As long as you have one of these receivers this integration will work with either the Hive mini or regular controller.

Once you have the thermostat receiver added to Zigbee2MQTT, add a device via this integration and specify a friendly name, the Zigbee2MQTT topic which should look something like this `zigbee2mqtt/HiveReceiver` (note this is case sensitive).

The new device created will have new sensors/controls available that will accurately show/send status changes.

You can optionally hide/disable the native Hive device created by Zigbee2MQTT within HomeAssistant.

The integration supports native boost and native schedules (auto). With schedules you can switch on/off schedule mode but you cannot modify the schedule details via the integration. You can of course ignore the schedule mode and setup automations within Home Assistant to control when heating/water is on or off and set a temperature for heating.

The numeric entities allow you to set defaults for boost times, heating boost temperature and also frost protection. Frost protection should be set to match what you have set on the Hive thermostat for an accurate display.

Actions are provided to natively boost the Heating `hive_local_thermostat.boost_heating` and Water `hive_local_thermostat.boost_water` (SLR2 only), these can optionally take a duration and temperature (heating only), these actions allow you to make custom buttons/scripts/automations to add additional control over the default boost buttons.

There are also matching actions to cancel the native boost for Heating `hive_local_thermostat.cancel_boost_heating` and Water `hive_local_thermostat.cancel_boost_water` (SLR2 only), these actions will return the heating/water back to the state they were before the boost.

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

## Climate Control Operation

Ensure that you are using the climate control created by this integration, not the one that Zigbee2MQTT creates, otherwise your commands will not work correctly (to tell them apart, this integration has a preset selector for None and Boost).

The climate control provides 3 modes

- Off - turns the Hive off, it will only ever heat if the temperature is below the Hive thermostats preset frost protection temperature. No schedules you have on the Hive thermostat will activate.
- Heat - turns the Hive on and will heat to the temperature specified and maintain that temperature.
- Auto - turns the Hive to its inbuilt schedule mode, the schedules created on the Hive thermostat will be active, you can adjust the temperature either within this integration or via the Hive thermostat and it will override the temperature until the next scheduled temperature.

The presets provide the facility to boost the heating. Selecting Boost will trigger your predefined boost temperature and duration specified in this integrations device configuration section, selecting None will cancel any active boost.

## FAQ's

- What are running states

  Running states are whether your boiler is actually active, you can see in the above screenshot that my thermostat is on Auto (schedule on the Hive thermostat), the current temperature is above my target temperature therefore the running state is idle. This will change to heating when the current temperature goes below my target and the boiler is triggered to heat.

- My boost remaining sensors are not counting down

  By default Zigbee2MQTT will not send frequent updates to track boosts by the minute, they will update but this is typically every 10 minutes.

  To change this within Zigbee2MQTT go into the receiver's reporting settings and change the following;

  Min Rep Change of any tempSetpointHoldDuration to 1  
  
  If you have heat and water you will have two values under different Endpoints, with heat only you will have one.

- I have changed thermostat settings within Zigbee2MQTT but it does not work properly.

  Zigbee2MQTT's UI exposes the current state of each value in a generic way, it does not have the logic to correctly send/interpret the values required to control the Hive thermostat, the documentation for each thermostat within Zigbee2MQTT explains the messages required to change things, this integration provides a wrapper around all this complexity for you but there is nothing stopping you from creating your own MQTT messages to do this.

- Can this be used with ZHA?

  No, this integration requires sending/receiving messages via MQTT to the Hive thermostat, ZHA does not work like this.

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
