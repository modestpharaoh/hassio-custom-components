"""
homeassistant.components.climate.heatmiserneo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Heatmiser NeoStat control via Heatmiser Neo-hub
Code largely taken from MindrustUK/Heatmiser-for-home-assistant
and added custom services to support Heatmiser Neostat hold/standby features
"""

from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import logging
import voluptuous as vol
from homeassistant.components.climate.const import (
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    HVAC_MODES,
)
from homeassistant.const import (ATTR_ATTRIBUTION,
                                 ATTR_ENTITY_ID,
                                 ATTR_TEMPERATURE,
                                 CONF_HOST,
                                 CONF_NAME,
                                 CONF_PORT,
                                 STATE_OFF,
                                 STATE_ON,
                                 UnitOfTemperature,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import DeviceInfo

import socket
import json
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = 0

ATTRIBUTION = "Data provided by Heatmiser Neo"

COMPONENT_DOMAIN = "heatmiserneo"
SERVICE_HOLD_TEMP = "hold_temp"

SERVICE_NEO_UPDATE = "neo_update"

# New
SERVICE_HOLD_TEMPERATURE = "hold_temperature"
SERVICE_HOLD_TEMPERATURE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_id,
    vol.Required("hold_temperature"): cv.string,
    vol.Required("hold_hours"): cv.string,
    vol.Required("hold_minutes"): cv.string,
    }
)

SERVICE_CANCEL_HOLD = "cancel_hold"
SERVICE_CANCEL_HOLD_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_id,
    }
)

SERVICE_ACTIVATE_FROST = "activate_frost"
SERVICE_ACTIVATE_FROST_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_id,
    }
)

SERVICE_CANCEL_FROST = "cancel_frost"
SERVICE_CANCEL_FROST_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_id,
    }
)

SERVICE_SET_FROST_TEMP = "set_frost_temperature"
SERVICE_SET_FROST_TEMP_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_id,
    vol.Required("frost_temperature"): cv.string,
    }
)

# End New


SERVICE_HOLD_TEMP_SCHEMA = vol.Schema(
    {vol.Required("hold_temperature"): cv.string,
    vol.Required("hold_hours"): cv.string,
    vol.Required("hold_minutes"): cv.string,
    vol.Required("thermostat"): cv.string,
    }
)





# Heatmiser does support all lots more stuff, but only heat for now.
# hvac_modes=[HVAC_MODE_HEAT_COOL, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_OFF]
# Heatmiser doesn't really have an off mode - standby is a preset - implement later
hvac_modes = [HVACMode.HEAT]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT): cv.port,
    }
)

# Fix this when I figure out why my config won't read in. Voluptuous schma thing.
# Excludes time clocks from being included if set to True
ExcludeTimeClock = False

def get_entity_from_domain(hass, domain, entity_id):
    component = hass.data.get(domain)
    if component is None:
        # raise HomeAssistantError("{} component not set up".format(domain))
        # With config entries, we might not have the component in hass.data in the same way
        # But let's try to find the entity from the entity registry or device registry if needed
        # For now, let's rely on the fact that the services are registered and should work
        pass

    # entity = component.get_entity(entity_id)
    # if entity is None:
    #     raise HomeAssistantError("{} not found".format(entity_id))

    # return entity
    # This helper was used to find the entity object to call methods on it.
    # In modern HA, we should use hass.data or pass the entity object if possible.
    # However, for service calls, we get the entity_id.
    # We can use hass.helpers.entity_component.EntityComponent.get_entity
    # But better yet, we should register services in async_setup_entry and use platform.entities
    
    # For now, to minimize breakage, let's try to find the entity in the list of entities we added
    # This is tricky without a global registry in this file.
    # We will refactor service handling to be method calls on the entity if possible, or use a global list.
    pass


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Heatmiser Neo from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    thermostats = []

    if coordinator.data:
        for name, device in coordinator.data.items():
            if device['DEVICE_TYPE'] != 6:
                if (('TIMECLOCK' in device['STAT_MODE']) and (ExcludeTimeClock == True)):
                    _LOGGER.debug("Found a Neostat configured in timer mode named: %s skipping" % name)
                else:
                    thermostats.append(HeatmiserNeostat(coordinator, name))

            elif device['DEVICE_TYPE'] == 6:
                _LOGGER.debug("Found a Neoplug named: %s skipping" % name)

    async_add_entities(thermostats, True)

    # Service registration
    # We should register services only once, so we can check if they are already registered
    if not hass.services.has_service(COMPONENT_DOMAIN, SERVICE_HOLD_TEMPERATURE):
        async def async_hold_temperature(call):
            """Call hold temperature service handler."""
            await async_handle_hold_temperature_service(hass, call)

        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_HOLD_TEMPERATURE, async_hold_temperature, schema=SERVICE_HOLD_TEMPERATURE_SCHEMA
        )

    if not hass.services.has_service(COMPONENT_DOMAIN, SERVICE_CANCEL_HOLD):
        async def async_cancel_hold(call):
            """Call cancel hold service handler."""
            await async_handle_cancel_hold_service(hass, call)

        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_CANCEL_HOLD, async_cancel_hold, schema=SERVICE_CANCEL_HOLD_SCHEMA
        )

    if not hass.services.has_service(COMPONENT_DOMAIN, SERVICE_ACTIVATE_FROST):
        async def async_activate_frost(call):
            """Call activate frost service handler."""
            await async_handle_activate_frost_service(hass, call)

        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_ACTIVATE_FROST, async_activate_frost, schema=SERVICE_ACTIVATE_FROST_SCHEMA
        )

    if not hass.services.has_service(COMPONENT_DOMAIN, SERVICE_CANCEL_FROST):
        async def async_cancel_frost(call):
            """Call cancel frost service handler."""
            await async_handle_cancel_frost_service(hass, call)

        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_CANCEL_FROST, async_cancel_frost, schema=SERVICE_CANCEL_FROST_SCHEMA
        )

    if not hass.services.has_service(COMPONENT_DOMAIN, SERVICE_SET_FROST_TEMP):
        async def async_set_frost_temp(call):
            """Call set frost temp service handler."""
            await async_handle_set_frost_temp_service(hass, call)

        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_SET_FROST_TEMP, async_set_frost_temp, schema=SERVICE_SET_FROST_TEMP_SCHEMA
        )

    if not hass.services.has_service(COMPONENT_DOMAIN, SERVICE_NEO_UPDATE):
        async def async_neo_update(call):
            """Call neo update service handler."""
            await async_handle_neo_update_service(hass, call)

        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_NEO_UPDATE, async_neo_update)


# Helper to find entity
def find_entity(hass, entity_id):
    for entity in hass.data[DOMAIN].get("entities", []): # We need to store entities in hass.data to find them easily
        if entity.entity_id == entity_id:
            return entity
    # Fallback to looking up in entity registry if possible, but we need the object instance
    # The original code used a helper that looked in hass.data[domain] but that was for the old component structure
    # For now, let's rely on the fact that we can iterate over all climate entities
    # But wait, we don't have easy access to all climate entities instances from here without storing them.
    pass

# We need to store the entities somewhere to access them in services
# Let's modify async_setup_entry to store them
# But wait, the service calls pass entity_id.
# The best way is to use platform.async_register_entity_service if these were entity services
# But they are defined as domain services in the original code.
# Let's try to implement them as entity services if possible, or keep them as domain services but find the entity.

async def get_thermostat(hass, entity_id):
    """Get thermostat entity."""
    # This is a bit hacky, but we need to find the entity object
    # In a proper implementation, we should use entity services
    # For now, let's try to find it in the state machine? No, we need the object.
    # We can use hass.data[DOMAIN]['entities'] if we populate it.
    
    # Let's populate hass.data[DOMAIN]['entities']
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if 'entities' not in hass.data[DOMAIN]:
        hass.data[DOMAIN]['entities'] = []
        
    for entity in hass.data[DOMAIN]['entities']:
        if entity.entity_id == entity_id:
            return entity
    return None

async def async_handle_hold_temperature_service(hass, call):
    """Handle hold temp service calls."""
    entity_id = call.data[ATTR_ENTITY_ID]
    hold_temperature = float(call.data["hold_temperature"])
    hold_hours = int(float(call.data["hold_hours"]))
    hold_minutes = int(float(call.data["hold_minutes"]))
    
    thermostat = await get_thermostat(hass, entity_id)
    if not thermostat:
        _LOGGER.warning("Thermostat %s not found", entity_id)
        return

    # We need to run network calls in executor
    await hass.async_add_executor_job(
        lambda: thermostat.coordinator.hub.json_request({"HOLD":[{"temp":hold_temperature, "id":"hass","hours":hold_hours,"minutes":hold_minutes}, str(thermostat.name)]})
    )
    
    # Force refresh
    await thermostat.coordinator.async_request_refresh()

async def async_handle_cancel_hold_service(hass, call):
    """Handle cancel hold service calls."""
    entity_id = call.data[ATTR_ENTITY_ID]
    thermostat = await get_thermostat(hass, entity_id)
    if not thermostat:
        return
        
    hold_temperature = float(thermostat.hold_temperature) if thermostat.hold_temperature else 20.0
    await hass.async_add_executor_job(
        lambda: thermostat.coordinator.hub.json_request({"HOLD":[{"temp":hold_temperature, "id":"hass","hours":0,"minutes":0}, str(thermostat.name)]})
    )
    
    # Force refresh
    await thermostat.coordinator.async_request_refresh()


async def async_handle_activate_frost_service(hass, call):
    """Handle activate frost service calls."""
    entity_id = call.data[ATTR_ENTITY_ID]
    thermostat = await get_thermostat(hass, entity_id)
    if not thermostat:
        return

    await hass.async_add_executor_job(
        lambda: thermostat.coordinator.hub.json_request({"FROST_ON": str(thermostat.name)})
    )
    
    # Force refresh
    await thermostat.coordinator.async_request_refresh()

async def async_handle_cancel_frost_service(hass, call):
    """Handle cancel frost service calls."""
    entity_id = call.data[ATTR_ENTITY_ID]
    thermostat = await get_thermostat(hass, entity_id)
    if not thermostat:
        return

    await hass.async_add_executor_job(
        lambda: thermostat.coordinator.hub.json_request({"FROST_OFF": str(thermostat.name)})
    )
    
    # Force refresh
    await thermostat.coordinator.async_request_refresh()

async def async_handle_set_frost_temp_service(hass, call):
    """Handle set frost temp service calls."""
    entity_id = call.data[ATTR_ENTITY_ID]
    thermostat = await get_thermostat(hass, entity_id)
    if not thermostat:
        return
        
    frost_temperature = float(call.data["frost_temperature"])
    await hass.async_add_executor_job(
        lambda: thermostat.coordinator.hub.json_request({"SET_FROST": [frost_temperature, str(thermostat.name)]})
    )
    
    # Force refresh
    await thermostat.coordinator.async_request_refresh()

async def async_handle_neo_update_service(hass, call):
    """Handle neo update service calls."""
    # Just trigger a refresh on all coordinators?
    # Or find the coordinator for the entity?
    # The service doesn't take entity_id in the original code, it was global?
    # Actually it was taking host/port from config.
    # Let's just refresh all coordinators we know about.
    if DOMAIN in hass.data:
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if isinstance(coordinator, CoordinatorEntity): # Wait, coordinator is not entity
                pass
            if hasattr(coordinator, 'async_request_refresh'):
                await coordinator.async_request_refresh()


class HeatmiserNeostat(CoordinatorEntity, ClimateEntity):
    """ Represents a Heatmiser Neostat thermostat. """
    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._name = name
        self._coordinator = coordinator
        self._hvac_modes = hvac_modes
        self._support_flags = SUPPORT_FLAGS
        self._support_flags = self._support_flags | ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def data(self):
        """Helper to get data for this device."""
        return self.coordinator.data.get(self._name)

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        if DOMAIN not in self.hass.data:
            self.hass.data[DOMAIN] = {}
        if 'entities' not in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN]['entities'] = []
        self.hass.data[DOMAIN]['entities'].append(self)

    async def async_will_remove_from_hass(self):
        """Run when entity will be removed."""
        await super().async_will_remove_from_hass()
        if DOMAIN in self.hass.data and 'entities' in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN]['entities'].remove(self)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.coordinator.host}-{self._name}"

    @property
    def device_info(self):
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self._name,
            manufacturer="Heatmiser",
            model="NeoStat",
            via_device=(DOMAIN, self.coordinator.host),
        )

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags

    @property
    def name(self):
        """ Returns the name. """
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        if self.data:
            tmptempfmt = self.data.get("TEMPERATURE_FORMAT")
            if (tmptempfmt == False) or (tmptempfmt.upper() == "C"):
                return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT

    @property
    def current_temperature(self):
        """ Returns the current temperature. """
        if self.data:
            return round(float(self.data.get("CURRENT_TEMPERATURE")), 2)
        return None

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.data:
            return round(float(self.data.get("CURRENT_SET_TEMPERATURE")), 2)
        return None

    @property
    def current_humidity(self):
        """Return the current humidity."""
        if self.data:
             return round(float(self.data.get("HUMIDITY")), 2)
        return None

    @property
    def hvac_action(self):
        """Return current activity ie. currently heating, cooling, idle."""
        if self.data:
            if self.data.get("HEATING") == True:
                return HVACAction.HEATING
            elif self.data.get("COOLING") == True:
                return HVACAction.COOLING
        return HVACAction.IDLE

    @property
    def hvac_mode(self):
        """Return current operation mode ie. heat, cool, off."""
        if self.data:
            if self.data.get("COOLING_ENABLED") == True:
                return HVACMode.COOL
        return HVACMode.HEAT

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return self._hvac_modes

    @property
    def on_hold(self):
        """Return if Temp on hold."""
        if self.data:
            return STATE_ON if self.data.get("TEMP_HOLD") else STATE_OFF
        return STATE_OFF

    @property
    def hold_temperature(self):
        """Return hold temperature."""
        if self.data:
            return round(float(self.data.get("HOLD_TEMPERATURE")), 2)
        return None

    @property
    def hold_time(self):
        """Return the current hold time."""
        if self.data:
            return self.data.get("HOLD_TIME")
        return None

    @property
    def on_standby(self):
        """Return if thermostat on standby."""
        if self.data:
            return STATE_ON if self.data.get("STANDBY") else STATE_OFF
        return STATE_OFF

    @property
    def frost_temperature(self):
        """Return frost temperature."""
        if self.data and 'engineers_data' in self.data:
            return round(float(self.data['engineers_data'].get("FROST TEMPERATURE")), 2)
        return None
        
    @property
    def switching_differential(self):
        """Return Switching Differential."""
        if self.data and 'engineers_data' in self.data:
            return round(float(self.data['engineers_data'].get("SWITCHING DIFFERENTIAL")), 2)
        return None

    @property
    def output_delay(self):
        """Return frost temperature."""
        if self.data and 'engineers_data' in self.data:
            return round(float(self.data['engineers_data'].get("OUTPUT DELAY")), 2)
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "on_hold": self.on_hold,
            "hold_temperature": self.hold_temperature,
            "hold_time": self.hold_time,
            "on_standby": self.on_standby,
            "frost_temperature": self.frost_temperature,
            "switching_differential": self.switching_differential,
            "output_delay": self.output_delay,
        }

    def set_temperature(self, **kwargs):
        """ Set new target temperature. """
        # This is legacy sync method, we should use async_set_temperature
        pass
        
    async def async_set_temperature(self, **kwargs):
        """ Set new target temperature. """
        await self.hass.async_add_executor_job(
            lambda: self.coordinator.hub.json_request({"SET_TEMP": [float(kwargs.get(ATTR_TEMPERATURE)), self._name]})
        )
            
        # Force refresh
        await self.coordinator.async_request_refresh()

    def set_temperature_e(self, **kwargs):
        """ Set new target temperature. """
        # This seems to be unused or legacy
        pass
