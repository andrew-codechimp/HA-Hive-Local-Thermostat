# Hive Local Thermostat Tests

This directory contains tests for the Hive Local Thermostat integration.

## Test Structure

```
tests/
├── __init__.py                # Tests package initialization
├── conftest.py                # Pytest fixtures and configuration
├── test_sensor.py             # Sensor platform tests
├── fixtures/                  # JSON fixtures for MQTT messages
│   ├── mqtt_slr1_heating.json
│   ├── mqtt_slr1_boost.json
│   ├── mqtt_slr1_idle.json
│   ├── mqtt_slr1_off.json
│   ├── mqtt_slr2_heating.json
│   ├── mqtt_slr2_boost.json
│   ├── mqtt_slr2_idle.json
│   └── mqtt_slr2_water_boost.json
└── __snapshots__/             # Snapshot test data (auto-generated)
```

## Running Tests

### VS Code Tasks

You can run tests directly from VS Code using these tasks:

- **Pytest**: Run all tests without coverage
- **Pytest (Coverage)**: Run tests with coverage report
- **Pytest (Sensors Only)**: Run only sensor platform tests
- **Pytest (Update Snapshots)**: Update snapshot files

Access these via `Terminal > Run Task...` or `Ctrl+Shift+P` → `Tasks: Run Task`

### Command Line

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov --cov-report=term --cov-report=html

# Run only sensor tests
pytest tests/test_sensor.py -v

# Update snapshots
pytest --snapshot-update

# Run specific test
pytest tests/test_sensor.py::test_sensor_slr1_states -v
```

## Test Fixtures

The tests use JSON fixtures to simulate MQTT messages. These fixtures are located in `tests/fixtures/` and cover various scenarios:

### SLR1 Model
- `mqtt_slr1_heating.json`: Normal heating mode
- `mqtt_slr1_boost.json`: Boost mode active
- `mqtt_slr1_idle.json`: Idle state (not heating)
- `mqtt_slr1_off.json`: System off

### SLR2 Model (with water control)
- `mqtt_slr2_heating.json`: Heating mode with water idle
- `mqtt_slr2_boost.json`: Both heating and water boost active
- `mqtt_slr2_idle.json`: Heating idle, water off
- `mqtt_slr2_water_boost.json`: Water boost only

## Snapshot Testing

The tests use [syrupy](https://github.com/tophat/syrupy) for snapshot testing. Snapshots capture the expected state of sensors and are stored in `tests/__snapshots__/`.

When sensor behavior changes intentionally:
1. Run `pytest --snapshot-update` to update snapshots
2. Review the changes in `__snapshots__/` directory
3. Commit the updated snapshots with your changes

## Writing New Tests

### Adding a New Fixture

1. Create a JSON file in `tests/fixtures/` with the MQTT payload
2. Use the `load_json_fixture` or `mock_mqtt_message` fixture in your test

Example:
```python
async def test_new_scenario(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    mock_mqtt_message: Any,
) -> None:
    """Test a new scenario."""
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator

    # Load and process the fixture
    message = mock_mqtt_message("mqtt_new_scenario.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # Assert sensor states
    state = hass.states.get("sensor.hive_thermostat_running_state_heat")
    assert state.state == "expected_value"
```

### Adding Snapshot Tests

```python
async def test_new_snapshot(
    hass: HomeAssistant,
    setup_integration_slr1: MockConfigEntry,
    mock_mqtt_message: Any,
    snapshot: SnapshotAssertion,
) -> None:
    """Test with snapshot assertion."""
    # Setup and process message
    config_entry = setup_integration_slr1
    coordinator = config_entry.runtime_data.coordinator
    message = mock_mqtt_message("mqtt_scenario.json", "hive/thermostat")
    coordinator.handle_mqtt_message(message)
    await hass.async_block_till_done()

    # Capture sensor states
    sensor_states = {}
    for entity_id in ["sensor.entity_1", "sensor.entity_2"]:
        state = hass.states.get(entity_id)
        if state:
            sensor_states[entity_id] = {
                "state": state.state,
                "attributes": dict(state.attributes),
            }

    # Compare with snapshot
    assert sensor_states == snapshot
```

## CI/CD Integration

Tests run automatically in GitHub Actions on:
- Push to main branch
- Pull requests
- Manual workflow dispatch

The workflow is defined in `.github/workflows/tests.yml` and includes:
- Running pytest with coverage
- Uploading coverage reports to Codecov
- Uploading HTML coverage reports as artifacts

## Dependencies

Test dependencies are defined in `pyproject.toml`:
- `pytest`: Test framework
- `pytest-asyncio`: Async test support
- `pytest-cov`: Coverage reporting
- `pytest-homeassistant-custom-component`: Home Assistant test utilities
- `syrupy`: Snapshot testing

Install all dependencies with:
```bash
uv sync --all-groups
```
