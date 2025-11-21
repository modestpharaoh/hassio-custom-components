"""
homeassistant.components.switch.heatmiserneo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Heatmiser NeoStat Standby Switch
"""

import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Heatmiser Neo Switch from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    switches = []

    if coordinator.data:
        for name, device in coordinator.data.items():
            if device['DEVICE_TYPE'] != 6:
                switches.append(HeatmiserNeoStandbySwitch(coordinator, name))

    async_add_entities(switches, True)

class HeatmiserNeoStandbySwitch(CoordinatorEntity, SwitchEntity):
    """Represents a Heatmiser NeoStat Standby Switch."""

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
        return f"{self.coordinator.host}-{self._name}-standby"

    @property
    def name(self):
        """Return the name of the switch."""
        return f"{self._name} Standby"

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
        """Return true if the switch is on (Standby Active)."""
        if self.data:
            return self.data.get("STANDBY")
        return False

    async def async_turn_on(self, **kwargs):
        """Turn the switch on (Activate Standby)."""
        await self.hass.async_add_executor_job(
            lambda: self.coordinator.hub.json_request({"FROST_ON": str(self._name)})
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off (Deactivate Standby)."""
        await self.hass.async_add_executor_job(
            lambda: self.coordinator.hub.json_request({"FROST_OFF": str(self._name)})
        )
        await self.coordinator.async_request_refresh()
