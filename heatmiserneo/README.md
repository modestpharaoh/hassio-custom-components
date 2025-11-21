# Heatmiser Neo for Home Assistant

This integration provides support for Heatmiser Neo thermostats in Home Assistant.

## Features
- **Climate Entity**: Control temperature, hold mode, and frost protection.
- **Switch Entity**: Toggle Standby mode for each thermostat.
- **Sensors**: Monitor Hold Status and Hold Time remaining.
- **Config Flow**: Easy setup via the UI.
- **Reconfigure**: Change host/port via UI.
- **Services**: Custom services for advanced control (Hold, Frost, etc.).

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

## Installation

Navigate to the custom_components directory for Home Assistant
```
cd /config/custom_components
git clone https://github.com/modestpharaoh/HeatmiserNeo-HomeAssistant
mv HeatmiserNeo-HomeAssistant heatmiserneo
```

As per example_configuration.yaml, add the following to the configuration.yaml in your /config directory.

```yaml
climate:
  - platform: heatmiserneo
    host: <Insert IP Address / Hostname>
    port: 4242
```

## Custom Services Example
Check services.yaml for examples of the following custom services:
* heatmiser.activate_frost
* heatmiser.cancel_frost
* heatmiser.cancel_hold
* heatmiser.hold_temp
* heatmiser.neo_update
* heatmiser.set_frost_temp
