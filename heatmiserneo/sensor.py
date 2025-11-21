"""
homeassistant.components.sensor.heatmiserneo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Heatmiser NeoStat Sensors
"""

import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Heatmiser Neo Sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = []

    if coordinator.data:
        for name, device in coordinator.data.items():
            if device['DEVICE_TYPE'] != 6:
                sensors.append(HeatmiserNeoHoldSensor(coordinator, name))
                sensors.append(HeatmiserNeoHoldTimeSensor(coordinator, name))
                sensors.append(HeatmiserNeoTemperatureSensor(coordinator, name))
                sensors.append(HeatmiserNeoTargetTemperatureSensor(coordinator, name))
                sensors.append(HeatmiserNeoSwitchingDifferentialSensor(coordinator, name))
                sensors.append(HeatmiserNeoOutputDelaySensor(coordinator, name))

    async_add_entities(sensors, True)

class HeatmiserNeoHoldSensor(CoordinatorEntity, BinarySensorEntity):
    """Represents a Heatmiser NeoStat Hold Sensor."""

    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._name = name
        self._coordinator = coordinator

    @property
    def data(self):
        """Helper to get data for this device."""
        return self.coordinator.data.get(self._name)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.coordinator.host}-{self._name}-hold-status"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name} Hold Status"

    @property
    def device_info(self):
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.host}-{self._name}")},
            name=self._name,
            manufacturer="Heatmiser",
            model="NeoStat",
            via_device=(DOMAIN, self.coordinator.host),
        )

    @property
    def is_on(self):
        """Return true if the thermostat is on hold."""
        if self.data:
            return self.data.get("TEMP_HOLD")
        return False

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:car-brake-hold"

class HeatmiserNeoHoldTimeSensor(CoordinatorEntity, SensorEntity):
    """Represents a Heatmiser NeoStat Hold Time Sensor."""

    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._name = name
        self._coordinator = coordinator

    @property
    def data(self):
        """Helper to get data for this device."""
        return self.coordinator.data.get(self._name)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.coordinator.host}-{self._name}-hold-time"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name} Hold Time"

    @property
    def device_info(self):
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.host}-{self._name}")},
            name=self._name,
            manufacturer="Heatmiser",
            model="NeoStat",
            via_device=(DOMAIN, self.coordinator.host),
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.data:
            if self.data.get("TEMP_HOLD"):
                return self.data.get("HOLD_TIME")
            else:
                return "00:00"
        return None
    
    @property
    def icon(self):
        return "mdi:clock-outline"

class HeatmiserNeoTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Represents a Heatmiser NeoStat Current Temperature Sensor."""

    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._name = name
        self._coordinator = coordinator

    @property
    def data(self):
        """Helper to get data for this device."""
        return self.coordinator.data.get(self._name)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.coordinator.host}-{self._name}-current-temperature"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name} Current Temperature"

    @property
    def device_info(self):
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.host}-{self._name}")},
            name=self._name,
            manufacturer="Heatmiser",
            model="NeoStat",
            via_device=(DOMAIN, self.coordinator.host),
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.data:
            return round(float(self.data.get("CURRENT_TEMPERATURE")), 2)
        return None
    
    @property
    def unit_of_measurement(self):
        return "°C"
        
    @property
    def icon(self):
        return "mdi:thermometer"

class HeatmiserNeoTargetTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Represents a Heatmiser NeoStat Target Temperature Sensor."""

    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._name = name
        self._coordinator = coordinator

    @property
    def data(self):
        """Helper to get data for this device."""
        return self.coordinator.data.get(self._name)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.coordinator.host}-{self._name}-target-temperature"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name} Target Temperature"

    @property
    def device_info(self):
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.host}-{self._name}")},
            name=self._name,
            manufacturer="Heatmiser",
            model="NeoStat",
            via_device=(DOMAIN, self.coordinator.host),
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.data:
            return round(float(self.data.get("CURRENT_SET_TEMPERATURE")), 2)
        return None
    
    @property
    def unit_of_measurement(self):
        return "°C"
        
    @property
    def icon(self):
        return "mdi:thermometer-check"

class HeatmiserNeoSwitchingDifferentialSensor(CoordinatorEntity, SensorEntity):
    """Represents a Heatmiser NeoStat Switching Differential Sensor."""

    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._name = name
        self._coordinator = coordinator

    @property
    def data(self):
        """Helper to get data for this device."""
        return self.coordinator.data.get(self._name)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.coordinator.host}-{self._name}-switching-differential"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name} Switching Differential"

    @property
    def device_info(self):
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.host}-{self._name}")},
            name=self._name,
            manufacturer="Heatmiser",
            model="NeoStat",
            via_device=(DOMAIN, self.coordinator.host),
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.data and 'engineers_data' in self.data:
            return round(float(self.data['engineers_data'].get("SWITCHING DIFFERENTIAL")), 2)
        return None
    
    @property
    def unit_of_measurement(self):
        return "°C"
        
    @property
    def icon(self):
        return "mdi:thermometer-lines"

class HeatmiserNeoOutputDelaySensor(CoordinatorEntity, SensorEntity):
    """Represents a Heatmiser NeoStat Output Delay Sensor."""

    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._name = name
        self._coordinator = coordinator

    @property
    def data(self):
        """Helper to get data for this device."""
        return self.coordinator.data.get(self._name)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.coordinator.host}-{self._name}-output-delay"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name} Output Delay"

    @property
    def device_info(self):
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.host}-{self._name}")},
            name=self._name,
            manufacturer="Heatmiser",
            model="NeoStat",
            via_device=(DOMAIN, self.coordinator.host),
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.data and 'engineers_data' in self.data:
            return round(float(self.data['engineers_data'].get("OUTPUT DELAY")), 2)
        return None
    
    @property
    def unit_of_measurement(self):
        return "min"
        
    @property
    def icon(self):
        return "mdi:timer-sand"
