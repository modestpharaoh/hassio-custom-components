# Heatmiser Neo for Home Assistant

This integration provides support for Heatmiser Neo thermostats in Home Assistant.

## Features
- **Climate Entity**: Control temperature, hold mode, and frost protection.
- **Switch Entity**: Toggle Standby mode for each thermostat.
- **Sensors**: Monitor Hold Status and Hold Time remaining.
- **Config Flow**: Easy setup via the UI.
- **Reconfigure**: Change host/port via UI.
- **Services**: Custom services for advanced control (Hold, Frost, etc.) under the heatmiserneo domain.

## Installation
1. Copy the `heatmiserneo` folder to your `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration via Settings -> Devices & Services -> Add Integration -> Heatmiser Neo.

## Entities
For each thermostat, the following entities are created:
- `climate.<thermostat_name>`: The main thermostat control.
- `switch.<thermostat_name>_standby`: Switch to enable/disable Standby mode.
- `binary_sensor.<thermostat_name>_hold_status`: Indicates if Hold mode is active.
- `sensor.<thermostat_name>_hold_time`: Shows remaining Hold time (or 00:00).
- `number.<thermostat_name>_frost_temperature`: Configure Frost Temperature (5-17°C).
- `sensor.<thermostat_name>_current_temperature`: Current temperature reading.
- `sensor.<thermostat_name>_target_temperature`: Current target temperature.
- `sensor.<thermostat_name>_switching_differential`: Switching differential setting.
- `sensor.<thermostat_name>_output_delay`: Output delay setting.

## References

The code is largely taken from MindrustUK/Heatmiser-for-home-assistant project,
but I added the support for Heatmiser hold/standby features based on the hub API
docomentation in RJ/heatmiser-neohub.py

## Supported Features
* Only support heating profile.
* It includes the following parameters in the climate entity for each thermostat.
   * current_temperature: current temperature.
   * temperature: current set temperature.
   * hvac_action: current heating Operation (idle, heating)
   * on_hold: if the thermostat is on hold (off, on)
   * hold_temperature: current hold temperature.
   * on_frost: if the thermostat is on standby (off, on)
   * frost_temperature: current frost temperature.
   * output_delay: delay set on thermostat before it update.
* Supports hold/cancel the temperature of neostat thermostat to certain degree and time by custom services.
* Supports to activate/cancel the standby mode on the neostat thermostat by custom services.
* Supports force query of neo-hub by custom service.
