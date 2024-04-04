# HA-Hive-MQTT-Orchestrator
Hive MQTT Orchestrator for Home Assistant

Early dev, nothing to see yet


Example received json
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
