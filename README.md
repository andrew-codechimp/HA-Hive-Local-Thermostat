# HA-Hive-MQTT-Orchestrator
Local Hive Thermostat MQTT integration Home Assistant

Early dev, nothing to see yet

To use this integration your Hive thermostat receiver must be added to [Zigbee2MQTT](https://www.zigbee2mqtt.io/supported-devices/#v=Hive).

Zigbee2MQTT will expose the native sensors but Hive requires specific message structures to be sent for setting modes and a combination of sensor values to determine the modes, this integration creates controls and sensors that correctly interface with the native hive values/methods.

SLR1x and SLR2x thermostats are supported, though this has only been tested with an SLR2c.

Once you have the thermostat receiver added to Zigbee2MQTT, add a device via this integration and specify a friendly name, the Zibee2MQTT topic which should look something like this `zigbee2mqtt/HiveReceiver` (note this is case sensitive).

The new device created will have new sensors/controls available that will accurately show/send status changes.

You can optionally hide/disable the native Hive device created by Zigbee2MQTT within HomeAssistant.

The integration supports native boost and native schedules. With schedules you can switch on/off schedule mode but you cannot modify the schedule details via the integration. You can of course ignore the schedule mode and setup automations within Home Assistant to control when heating/water is on or off and what temperature for heating.

The numeric entities allow you to set defaults for boost times, temperatures and also frost protection. Frost protection should be set to match what you have set on the Hive thermostat for an accurate display.


Example received json from zigbee2mqtt/Z2mHiveReceiver
```
{
    "last_seen": "2024-04-04T09:18:37+01:00",
    "linkquality": 109,
    "local_temperature_heat": 20.28,
    "local_temperature_water": 21,
    "occupied_heating_setpoint_heat": 19,
    "occupied_heating_setpoint_water": 22,
    "running_state_heat": "idle",
    "running_state_water": "idle",
    "system_mode_heat": "heat",
    "system_mode_water": "heat",
    "temperature_setpoint_hold_duration_heat": 0,
    "temperature_setpoint_hold_duration_water": 0,
    "temperature_setpoint_hold_heat": false,
    "temperature_setpoint_hold_water": false,
    "weekly_schedule_heat": {
        "days": [
            "saturday"
        ],
        "transitions": [
            {
                "heating_setpoint": 20,
                "time": 420
            },
            {
                "heating_setpoint": 19,
                "time": 540
            },
            {
                "heating_setpoint": 20,
                "time": 1020
            },
            {
                "heating_setpoint": 1,
                "time": 1380
            },
            {
                "heating_setpoint": 1,
                "time": 1380
            },
            {
                "heating_setpoint": 1,
                "time": 1380
            }
        ]
    },
    "weekly_schedule_water": {
        "days": [
            "saturday"
        ],
        "transitions": [
            {
                "heating_setpoint": 99,
                "time": 1200
            },
            {
                "heating_setpoint": 0,
                "time": 1320
            },
            {
                "heating_setpoint": 0,
                "time": 1320
            },
            {
                "heating_setpoint": 0,
                "time": 1320
            },
            {
                "heating_setpoint": 0,
                "time": 1320
            },
            {
                "heating_setpoint": 0,
                "time": 1320
            }
        ]
    }
}
```
