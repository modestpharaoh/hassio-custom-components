"""
homeassistant.components.number.heatmiserneo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Heatmiser NeoStat Number Entities
"""

import logging
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import UnitOfTemperature
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Heatmiser Neo Numbers from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    numbers = []

    if coordinator.data:
        for name, device in coordinator.data.items():
            if device['DEVICE_TYPE'] != 6:
                numbers.append(HeatmiserNeoFrostTempNumber(coordinator, name))

    async_add_entities(numbers, True)

class HeatmiserNeoFrostTempNumber(CoordinatorEntity, NumberEntity):
    """Represents a Heatmiser NeoStat Frost Temperature Number."""

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
        return f"{self.coordinator.host}-{self._name}-frost-temp"

    @property
    def name(self):
        """Return the name of the number."""
        return f"{self._name} Frost Temperature"

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
    def native_value(self):
        """Return the current value."""
        if self.data and 'engineers_data' in self.data:
            return float(self.data['engineers_data'].get("FROST TEMPERATURE"))
        return None

    @property
    def native_min_value(self):
        """Return the minimum value."""
        return 5.0

    @property
    def native_max_value(self):
        """Return the maximum value."""
        return 17.0

    @property
    def native_step(self):
        """Return the step value."""
        return 1.0

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:snowflake-thermometer"

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.hass.async_add_executor_job(
            lambda: self.coordinator.hub.json_request({"SET_FROST": [int(value), str(self._name)]})
        )
        await self.coordinator.async_request_refresh()
