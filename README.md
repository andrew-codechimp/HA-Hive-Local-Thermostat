# HA-Hive-Local-Thermostat
Local Hive Thermostat MQTT integration Home Assistant

**Early beta**

To use this integration your Hive thermostat receiver must be added to [Zigbee2MQTT](https://www.zigbee2mqtt.io/supported-devices/#v=Hive) and a MQTT broker and the MQTT integration within Home Assistant must be correctly configured.

Zigbee2MQTT will expose the native sensors but Hive requires specific message structures to be sent for setting modes and a combination of sensor values to determine the modes, this integration creates controls and sensors that correctly interface with the native Hive values/methods.

SLR1x and SLR2x thermostats are supported, though this has only been tested with an SLR2c.

Once you have the thermostat receiver added to Zigbee2MQTT, add a device via this integration and specify a friendly name, the Zibee2MQTT topic which should look something like this `zigbee2mqtt/HiveReceiver` (note this is case sensitive).

The new device created will have new sensors/controls available that will accurately show/send status changes.

You can optionally hide/disable the native Hive device created by Zigbee2MQTT within HomeAssistant.

The integration supports native boost and native schedules. With schedules you can switch on/off schedule mode but you cannot modify the schedule details via the integration. You can of course ignore the schedule mode and setup automations within Home Assistant to control when heating/water is on or off and set a temperature for heating.

The numeric entities allow you to set defaults for boost times, temperatures and also frost protection. Frost protection should be set to match what you have set on the Hive thermostat for an accurate display.

