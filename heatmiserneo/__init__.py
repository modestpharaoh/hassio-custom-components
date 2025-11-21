"""The Heatmiser Neo integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Heatmiser Neo from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Store the config entry data in hass.data if needed, or just proceed to setup platforms
    # For this integration, the climate platform handles the connection, so we just forward the entry.
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Clean up any data stored in hass.data if necessary
        pass

    return unload_ok
