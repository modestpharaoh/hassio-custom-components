"""WordPress Daily Prayer Time integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import (
    PrayerTimeCoordinator,
    WordpressPrayerTimeConfigEntry,
)
from .const import CONF_ENDPOINT, CONF_API_PATH

PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: WordpressPrayerTimeConfigEntry,
) -> bool:
    """Set up WordPress Daily Prayer Time from a config entry."""

    @callback
    def update_unique_id(
        entity_entry: er.RegistryEntry,
    ) -> dict[str, str] | None:
        """Update unique ID of entity entry."""
        if not entity_entry.unique_id.startswith(f"{entry.entry_id}-"):
            new_unique_id = f"{entry.entry_id}-{entity_entry.unique_id}"
            return {"new_unique_id": new_unique_id}
        return None

    _LOGGER.debug("Setting up WordPress Daily Prayer Time with entry: %s", entry)
    endpoint: str = entry.options[CONF_ENDPOINT]
    api_path: str = entry.options[CONF_API_PATH]
    
    await er.async_migrate_entries(hass, entry.entry_id, update_unique_id)

    coordinator = PrayerTimeCoordinator(
        hass,
        config_entry=entry,
        endpoint=endpoint,
        api_path=api_path,
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(
        entry.add_update_listener(async_options_updated)
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(
    hass: HomeAssistant,
    entry: WordpressPrayerTimeConfigEntry
) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    ):
        coordinator = entry.runtime_data
        if coordinator.event_unsub:
            coordinator.event_unsub()
    return unload_ok

async def async_options_updated(
    hass: HomeAssistant,
    entry: WordpressPrayerTimeConfigEntry,
) -> None:
    """Handle an options update."""
    coordinator = entry.runtime_data
    if coordinator.event_unsub:
        coordinator.event_unsub()
    await coordinator.async_request_refresh()
