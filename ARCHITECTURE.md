# Architecture

## Overview

Hive Local Thermostat is a Home Assistant (HA) custom integration that wraps Hive thermostat behavior exposed by Zigbee2MQTT. It listens to MQTT state updates from the receiver and publishes specific MQTT payloads that Hive requires for mode changes, boosts, and setpoints. The integration presents a HA climate entity plus supporting sensors, numbers, selects, buttons, and services.

At runtime, a single coordinator instance owns the device state and MQTT message handling. Entities read from and write to the coordinator, which sends MQTT commands and updates entity state from incoming payloads.

## Key Components

- Integration entry setup
  - [custom_components/hive_local_thermostat/__init__.py](custom_components/hive_local_thermostat/__init__.py)
  - Validates HA version, registers services, and sets up the config entry.
  - Creates a HiveCoordinator and wires MQTT subscription to it.

- Coordinator (state + MQTT)
  - [custom_components/hive_local_thermostat/coordinator.py](custom_components/hive_local_thermostat/coordinator.py)
  - Parses MQTT payloads, derives HVAC mode, preset, running state, and boost states.
  - Sends MQTT commands for modes, setpoints, and boost operations.
  - Stores long-lived values (boost durations, frost prevention, defaults) used by number entities and services.

- Entities (presentation + control)
  - Climate: [custom_components/hive_local_thermostat/climate.py](custom_components/hive_local_thermostat/climate.py)
  - Sensors: [custom_components/hive_local_thermostat/sensor.py](custom_components/hive_local_thermostat/sensor.py)
  - Numbers: [custom_components/hive_local_thermostat/number.py](custom_components/hive_local_thermostat/number.py)
  - Select (water mode for SLR2): [custom_components/hive_local_thermostat/select.py](custom_components/hive_local_thermostat/select.py)
  - Buttons (boost): [custom_components/hive_local_thermostat/button.py](custom_components/hive_local_thermostat/button.py)
  - Binary sensors (boost active): [custom_components/hive_local_thermostat/binary_sensor.py](custom_components/hive_local_thermostat/binary_sensor.py)

- Config flow
  - [custom_components/hive_local_thermostat/config_flow.py](custom_components/hive_local_thermostat/config_flow.py)
  - Captures MQTT topic, model, and schedule-mode visibility via HA UI.

- Services
  - [custom_components/hive_local_thermostat/services.py](custom_components/hive_local_thermostat/services.py)
  - Exposes boost and cancel boost actions with optional duration/temperature inputs.

- Diagnostics
  - [custom_components/hive_local_thermostat/diagnostics.py](custom_components/hive_local_thermostat/diagnostics.py)
  - Reports config details, coordinator state, and the most recent MQTT payload.

## Models and Platform Matrix

The integration supports multiple Hive receiver models with slightly different MQTT payload schemas.

- SLR2: heating + hot water support; exposes select and water-related sensors
- SLR1 / OTR1: heating only; no water select or water sensors

Platform selection is driven by the model in config options.

## Data Flow

### 1) Startup and subscription

1. HA loads the config entry.
2. Integration creates a HiveCoordinator and registers all supported platforms.
3. Integration subscribes to the MQTT topic for the receiver and routes all incoming payloads to the coordinator.
4. Integration publishes an initial "get" payload to request current state.

### 2) MQTT -> Coordinator -> Entities

1. Zigbee2MQTT publishes a state payload on the configured topic.
2. Coordinator parses JSON, validates fields by model, and derives:
   - HVAC mode (off/heat/auto)
   - Preset (none/boost)
   - Temperatures and running state
   - Boost tracking info (remaining time and active flags)
3. Coordinator updates its internal fields and notifies all entities.
4. Entities pull state from the coordinator and update HA state.

### 3) HA entity control -> Coordinator -> MQTT

1. User changes climate mode, setpoint, boost, or water mode in HA.
2. Entity calls coordinator methods (for example, `async_set_hvac_mode_heat()`).
3. Coordinator builds the Hive-specific MQTT payload and publishes to the /set topic.
4. The integration optimistically updates HA state to avoid UI flapping while waiting for MQTT confirmation.

## MQTT Topics and Payloads

- Base topic: user-configured (example: `zigbee2mqtt/HiveReceiver`)
- Getter: `<topic>/get`
- Setter: `<topic>/set`

The coordinator uses different payload keys for SLR2 vs SLR1/OTR1. For example:

- SLR2 heating setpoint: `occupied_heating_setpoint_heat`
- SLR1/OTR1 heating setpoint: `occupied_heating_setpoint`

Boost commands are sent as `system_mode` or `system_mode_heat` set to `emergency_heating` with duration fields.

### Payload Field Legend

- `system_mode` / `system_mode_heat`: Hive heating mode (`off`, `heat`, `emergency_heating`)
- `system_mode_water`: Hive water mode (`off`, `heat`, `emergency_heating`)
- `occupied_heating_setpoint` / `occupied_heating_setpoint_heat`: target temperature
- `temperature_setpoint_hold` / `_heat` / `_water`: hold flag (`1` for hold, `0` for schedule)
- `temperature_setpoint_hold_duration` / `_heat` / `_water`: boost duration in minutes

## Boost and Schedule Logic

- Heating boost and water boost are tracked with start timestamps and remaining duration.
- If the device reports an invalid boost remaining value (greater than 65000), the coordinator recalculates remaining time and re-sends a corrected boost command.
- Schedule mode visibility is configurable. When enabled, `AUTO` maps to Hive schedule mode ("heat" plus `temperature_setpoint_hold = False`).

## Error Handling and Resilience

- MQTT payloads are validated for model mismatch before applying.
- JSON parse errors are logged and ignored.
- Entities avoid crashing on missing fields and set safe defaults.

## Mermaid Sequence (Detailed)

```mermaid
sequenceDiagram
  participant HA as Home Assistant
  participant INT as Hive Integration
  participant MQTT as MQTT Broker
  participant Z2M as Zigbee2MQTT

  HA->>INT: Load config entry
  INT->>MQTT: Subscribe to <topic>
  INT->>MQTT: Publish <topic>/get {"system_mode":""}
  Z2M-->>MQTT: Publish state payload
  MQTT-->>INT: Deliver payload
  INT->>INT: Parse payload, validate model
  INT->>INT: Derive modes, temps, boosts
  INT-->>HA: Entity state updates

  HA->>INT: User changes HVAC mode
  alt SLR2
    INT->>MQTT: Publish <topic>/set
    note right of MQTT: {"system_mode_heat":"heat","occupied_heating_setpoint_heat":21.0,
    "temperature_setpoint_hold_heat":"1","temperature_setpoint_hold_duration_heat":"0"}
  else SLR1/OTR1
    INT->>MQTT: Publish <topic>/set
    note right of MQTT: {"system_mode":"heat","occupied_heating_setpoint":21.0,
    "temperature_setpoint_hold":"1","temperature_setpoint_hold_duration":"0"}
  end
  Z2M-->>MQTT: Publish updated state
  MQTT-->>INT: Deliver payload
  INT-->>HA: Entity state updates
```

```mermaid
sequenceDiagram
  participant HA as Home Assistant
  participant INT as Hive Integration
  participant MQTT as MQTT Broker
  participant Z2M as Zigbee2MQTT

  HA->>INT: User triggers heating boost
  alt SLR2
    INT->>MQTT: Publish <topic>/set
    note right of MQTT: {"system_mode_heat":"emergency_heating",
    "temperature_setpoint_hold_duration_heat":120,
    "temperature_setpoint_hold_heat":1,
    "occupied_heating_setpoint_heat":25}
  else SLR1/OTR1
    INT->>MQTT: Publish <topic>/set
    note right of MQTT: {"system_mode":"emergency_heating",
    "temperature_setpoint_hold_duration":120,
    "temperature_setpoint_hold":1,
    "occupied_heating_setpoint":25}
  end

  Z2M-->>MQTT: Publish boost state
  MQTT-->>INT: Deliver payload
  INT->>INT: Track boost remaining
  INT-->>HA: Boost sensors update
```

```mermaid
sequenceDiagram
  participant HA as Home Assistant
  participant INT as Hive Integration
  participant MQTT as MQTT Broker
  participant Z2M as Zigbee2MQTT

  HA->>INT: User changes water mode (SLR2)
  alt Auto (schedule)
    INT->>MQTT: Publish <topic>/set
    note right of MQTT: {"system_mode_water":"heat",
    "temperature_setpoint_hold_water":"0",
    "temperature_setpoint_hold_duration_water":"0"}
  else Heat (always on)
    INT->>MQTT: Publish <topic>/set
    note right of MQTT: {"system_mode_water":"heat",
    "temperature_setpoint_hold_water":1}
  else Boost
    INT->>MQTT: Publish <topic>/set
    note right of MQTT: {"system_mode_water":"emergency_heating",
    "temperature_setpoint_hold_duration_water":60,
    "temperature_setpoint_hold_water":1}
  else Off
    INT->>MQTT: Publish <topic>/set
    note right of MQTT: {"system_mode_water":"off",
    "temperature_setpoint_hold_water":0}
  end

  Z2M-->>MQTT: Publish updated state
  MQTT-->>INT: Deliver payload
  INT-->>HA: Water entities update
```

## Configuration Inputs

- `mqtt_topic`: Zigbee2MQTT device topic
- `model`: SLR1, SLR2, or OTR1
- `show_heat_schedule_mode`: expose AUTO for heating
- `show_water_schedule_mode`: expose AUTO for water (SLR2 only)

## Extensibility Notes

- New Hive models likely require changes to the coordinator payload parsing and the MQTT payload formatters.
- Additional entities should map to coordinator fields and update from MQTT payloads to keep a single source of truth.
