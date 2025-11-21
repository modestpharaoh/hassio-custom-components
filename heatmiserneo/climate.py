"""
homeassistant.components.climate.heatmiserneo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Heatmiser NeoStat control via Heatmiser Neo-hub
Code largely taken from MindrustUK/Heatmiser-for-home-assistant
and added custom services to support Heatmiser Neostat hold/standby features
"""

from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
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

from datetime import timedelta
import socket
import json
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

VERSION = '3.0.0'

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
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    thermostats = []

    # We need to run this in an executor because it does blocking I/O
    NeoHubJson = await hass.async_add_executor_job(
        lambda: HeatmiserNeostat(UnitOfTemperature.CELSIUS, False, host, port).json_request({"INFO": 0})
    )

    _LOGGER.debug(NeoHubJson)

    if not NeoHubJson:
        _LOGGER.error("Could not connect to Heatmiser Neo Hub")
        return

    for device in NeoHubJson['devices']:
        if device['DEVICE_TYPE'] != 6:
            name = device['device']
            tmptempfmt = device['TEMPERATURE_FORMAT']
            if (tmptempfmt == False) or (tmptempfmt.upper() == "C"):
                temperature_unit = UnitOfTemperature.CELSIUS
            else:
                temperature_unit = UnitOfTemperature.FAHRENHEIT # Corrected constant
            away = device['AWAY']
            current_temperature = device['CURRENT_TEMPERATURE']
            set_temperature = device['CURRENT_SET_TEMPERATURE']
            on_hold = device['TEMP_HOLD']

            _LOGGER.info("Thermostat Name: %s " % name)
            _LOGGER.info("Thermostat Away Mode: %s " % away)
            _LOGGER.info("Thermostat Current Temp: %s " % current_temperature)
            _LOGGER.info("Thermostat Set Temp: %s " % set_temperature)
            _LOGGER.info("Thermostat Unit Of Measurement: %s " % temperature_unit)
            _LOGGER.info("Thermostat is on hold: %r " % on_hold)

            if (('TIMECLOCK' in device['STAT_MODE']) and (ExcludeTimeClock == True)):
              _LOGGER.debug("Found a Neostat configured in timer mode named: %s skipping" % device['device'])
            else:
              thermostats.append(HeatmiserNeostat(temperature_unit, away, host, port, name))

        elif device['DEVICE_TYPE'] == 6:
            _LOGGER.debug("Found a Neoplug named: %s skipping" % device['device'])

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
            await async_handle_neo_update_service(hass, call, host, port)

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
        lambda: thermostat.json_request({"HOLD":[{"temp":hold_temperature, "id":"hass","hours":hold_hours,"minutes":hold_minutes}, str(thermostat.name)]})
    )
    
    # Force refresh
    await thermostat.async_update_ha_state(force_refresh=True)

async def async_handle_cancel_hold_service(hass, call):
    """Handle cancel hold service calls."""
    entity_id = call.data[ATTR_ENTITY_ID]
    thermostat = await get_thermostat(hass, entity_id)
    if not thermostat:
        return
        
    hold_temperature = float(thermostat.hold_temperature) if thermostat.hold_temperature else 20.0
    await hass.async_add_executor_job(
        lambda: thermostat.json_request({"HOLD":[{"temp":hold_temperature, "id":"hass","hours":0,"minutes":0}, str(thermostat.name)]})
    )
    
    # Force refresh
    await thermostat.async_update_ha_state(force_refresh=True)


async def async_handle_activate_frost_service(hass, call):
    """Handle activate frost service calls."""
    entity_id = call.data[ATTR_ENTITY_ID]
    thermostat = await get_thermostat(hass, entity_id)
    if not thermostat:
        return

    await hass.async_add_executor_job(
        lambda: thermostat.json_request({"FROST_ON": str(thermostat.name)})
    )
    
    # Force refresh
    await thermostat.async_update_ha_state(force_refresh=True)

async def async_handle_cancel_frost_service(hass, call):
    """Handle cancel frost service calls."""
    entity_id = call.data[ATTR_ENTITY_ID]
    thermostat = await get_thermostat(hass, entity_id)
    if not thermostat:
        return

    await hass.async_add_executor_job(
        lambda: thermostat.json_request({"FROST_OFF": str(thermostat.name)})
    )
    
    # Force refresh
    await thermostat.async_update_ha_state(force_refresh=True)

async def async_handle_set_frost_temp_service(hass, call):
    """Handle set frost temp service calls."""
    entity_id = call.data[ATTR_ENTITY_ID]
    thermostat = await get_thermostat(hass, entity_id)
    if not thermostat:
        return
        
    frost_temperature = float(call.data["frost_temperature"])
    await hass.async_add_executor_job(
        lambda: thermostat.json_request({"SET_FROST": [frost_temperature, str(thermostat.name)]})
    )
    
    # Force refresh
    await thermostat.async_update_ha_state(force_refresh=True)

async def async_handle_neo_update_service(hass, call, host, port):
    """Handle neo update service calls."""
    # This service seems to update the hub? Or just trigger an update?
    # The original code created a new HeatmiserNeostat object just to call update()
    # which calls INFO: 0.
    # This seems redundant if we have entities polling.
    # But let's keep it.
    hub = HeatmiserNeostat(UnitOfTemperature.CELSIUS, False, host, port)
    await hass.async_add_executor_job(hub.update)


class HeatmiserNeostat(ClimateEntity):
    """ Represents a Heatmiser Neostat thermostat. """
    def __init__(self, unit_of_measurement, away, host, port, name="Null"):
        self._name = name
        self._unit_of_measurement = unit_of_measurement
        self._away = away
        self._host = host
        self._port = port
        #self._type = type Neostat vs Neostat-e
        self._hvac_action = None
        self._hvac_mode = None
        self._current_temperature = None
        self._target_temperature = None
        self.update_without_throttle = False
        self._on_hold = None
        self._hold_temperature = None
        self._hold_time = None
        self._on_standby = None
        self._frost_temperature = None
        self._switching_differential = None
        self._output_delay = None
        self._hvac_modes = hvac_modes
        self._support_flags = SUPPORT_FLAGS
        self._support_flags = self._support_flags | ClimateEntityFeature.TARGET_TEMPERATURE
        self.update()

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        if DOMAIN not in self.hass.data:
            self.hass.data[DOMAIN] = {}
        if 'entities' not in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN]['entities'] = []
        self.hass.data[DOMAIN]['entities'].append(self)

    async def async_will_remove_from_hass(self):
        """Run when entity will be removed."""
        if DOMAIN in self.hass.data and 'entities' in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN]['entities'].remove(self)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._host}-{self._name}"

    @property
    def device_info(self):
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self._name,
            manufacturer="Heatmiser",
            model="NeoStat",
            via_device=(DOMAIN, self._host),
        )

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags

    @property
    def should_poll(self):
        """ No polling needed for a demo thermostat. """
        return True

    @property
    def name(self):
        """ Returns the name. """
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def current_temperature(self):
        """ Returns the current temperature. """
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._current_humidity

    @property
    def target_humidity(self):
        """Return the humidity we try to reach."""
        return self._target_humidity

    @property
    def hvac_action(self):
        """Return current activity ie. currently heating, cooling, idle."""
        return self._hvac_action

    @property
    def hvac_mode(self):
        """Return current operation mode ie. heat, cool, off."""
        return self._hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return self._hvac_modes

    @property
    def on_hold(self):
        """Return if Temp on hold."""
        return self._on_hold

    @property
    def hold_temperature(self):
        """Return hold temperature."""
        return self._hold_temperature

    @property
    def hold_time(self):
        """Return the current hold time."""
        return self._hold_time

    @property
    def on_standby(self):
        """Return if thermostat on standby."""
        return self._on_standby

    @property
    def frost_temperature(self):
        """Return frost temperature."""
        return self._frost_temperature
    @property
    def switching_differential(self):
        """Return Switching Differential."""
        return self._switching_differential

    @property
    def output_delay(self):
        """Return frost temperature."""
        return self._output_delay

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "on_hold": self._on_hold,
            "hold_temperature": self._hold_temperature,
            "hold_time": self._hold_time,
            "on_standby": self._on_standby,
            "frost_temperature": self._frost_temperature,
            "switching_differential": self._switching_differential,
            "output_delay": self._output_delay,
        }

    def set_temperature(self, **kwargs):
        """ Set new target temperature. """
        # This is legacy sync method, we should use async_set_temperature
        pass
        
    async def async_set_temperature(self, **kwargs):
        """ Set new target temperature. """
        response = await self.hass.async_add_executor_job(
            lambda: self.json_request({"SET_TEMP": [float(kwargs.get(ATTR_TEMPERATURE)), self._name]})
        )
        if response:
            _LOGGER.info("set_temperature response: %s " % response)
            # Need check for success here
            # {'result': 'temperature was set'}
            
        # Force refresh
        await self.async_update_ha_state(force_refresh=True)

    def set_temperature_e(self, **kwargs):
        """ Set new target temperature. """
        # This seems to be unused or legacy
        pass

    def update(self):
        """ Get Updated Info. """
        if self.update_without_throttle:
            self.update_without_throttle = False
        _LOGGER.debug("Entered update(self)")
        response = self.json_request({"INFO": 0})
        engResponse = self.json_request({"ENGINEERS_DATA": 0})
        if response:
            # Add handling for mulitple thermostats here
            _LOGGER.debug("update() json response: %s " % response)
            # self._name = device['device']
            for device in response['devices']:
              if self._name == device['device']:
                tmptempfmt = device["TEMPERATURE_FORMAT"]
                if (tmptempfmt == False) or (tmptempfmt.upper() == "C"):
                  self._temperature_unit = UnitOfTemperature.CELSIUS
                else:
                  self._temperature_unit = UnitOfTemperature.FAHRENHEIT
                self._away = device['AWAY']
                self._target_temperature =  round(float(device["CURRENT_SET_TEMPERATURE"]), 2)
                self._current_temperature = round(float(device["CURRENT_TEMPERATURE"]), 2)
                self._current_humidity = round(float(device["HUMIDITY"]), 2)
                if device["TEMP_HOLD"]:
                    self._on_hold = STATE_ON
                else:
                    self._on_hold = STATE_OFF
                self._hold_temperature = round(float(device["HOLD_TEMPERATURE"]), 2)
                self._hold_time = device["HOLD_TIME"]
                if device["STANDBY"]:
                    self._on_standby = STATE_ON
                else:
                    self._on_standby = STATE_OFF

                # Figure out the current mode based on whether cooling is enabled - should verify that this is correct
                if device["COOLING_ENABLED"] == True:
                    self._hvac_mode = HVACMode.COOL
                else:
                    self._hvac_mode = HVACMode.HEAT

                # Figure out current action based on Heating / Cooling flags
                if device["HEATING"] == True:
                    self._hvac_action = HVACAction.HEATING
                    _LOGGER.debug("Heating")
                elif device["COOLING"] == True:
                    self._hvac_action = HVACAction.COOLING
                    _LOGGER.debug("Cooling")
                else:
                    self._hvac_action = HVACAction.IDLE
                    _LOGGER.debug("Idle")
            if engResponse:
                _LOGGER.debug("update() json engResponse: %s " % engResponse)
                self._frost_temperature = round(float(engResponse[device["device"]]["FROST TEMPERATURE"]), 2)
                self._switching_differential = round(float(engResponse[device["device"]]["SWITCHING DIFFERENTIAL"]), 2)
                self._output_delay = round(float(engResponse[device["device"]]["OUTPUT DELAY"]), 2)


    def json_request(self, request=None, wait_for_response=False):
        """ Communicate with the json server. """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        try:
            sock.connect((self._host, self._port))
        except OSError:
            sock.close()
            return False

        if not request:
            # no communication needed, simple presence detection returns True
            sock.close()
            return True

        _LOGGER.debug("json_request: %s " % request)

        sock.send(bytearray(json.dumps(request) + "\0\r", "utf-8"))
        try:
            buf = sock.recv(4096)
        except socket.timeout:
            # something is wrong, assume it's offline
            sock.close()
            return False

        # read until a newline or timeout
        buffering = True
        while buffering:
            if "\n" in str(buf, "utf-8"):
                response = str(buf, "utf-8").split("\n")[0]
                buffering = False
            else:
                try:
                    more = sock.recv(4096)
                except socket.timeout:
                    more = None
                if not more:
                    buffering = False
                    response = str(buf, "utf-8")
                else:
                    buf += more

        sock.close()

        response = response.rstrip('\0')

        _LOGGER.debug("json_response: %s " % response)

        return json.loads(response, strict=False)
