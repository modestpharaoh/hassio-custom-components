"""DataUpdateCoordinator for Heatmiser Neo."""
import logging
import socket
import json
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

class HeatmiserNeoCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Heatmiser Neo data."""

    def __init__(self, hass: HomeAssistant, host: str, port: int):
        """Initialize."""
        self.host = host
        self.port = port
        self.hub = HeatmiserNeoHub(host, port)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            return await self.hass.async_add_executor_job(self.hub.update)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

class HeatmiserNeoHub:
    """Heatmiser Neo Hub API."""

    def __init__(self, host, port):
        """Initialize."""
        self._host = host
        self._port = port

    def update(self):
        """Get the latest data."""
        response = self.json_request({"INFO": 0})
        if not response:
            return None
        
        # We also need engineers data for some attributes
        eng_response = self.json_request({"ENGINEERS_DATA": 0})
        
        # Merge data or structure it nicely
        # The current climate implementation expects a list of devices from INFO
        # and then looks up engineers data.
        # Let's return a dictionary keyed by device name for easier access
        
        data = {}
        if response and 'devices' in response:
            for device in response['devices']:
                name = device['device']
                data[name] = device
                # Add engineers data if available
                if eng_response and name in eng_response:
                    data[name]['engineers_data'] = eng_response[name]
        
        return data

    def json_request(self, request):
        """Communicate with the json server."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        try:
            sock.connect((self._host, self._port))
        except OSError:
            sock.close()
            return None

        sock.send(bytearray(json.dumps(request) + "\0\r", "utf-8"))
        try:
            buf = sock.recv(4096)
        except socket.timeout:
            sock.close()
            return None

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
        return json.loads(response, strict=False)
