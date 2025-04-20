"""Config flow for WordPress Daily Prayer Time integration."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

import voluptuous as vol


from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    TextSelector,
)

from .const import CONF_ENDPOINT, CONF_API_PATH, DEFAULT_API_PATH, DOMAIN

_LOGGER = logging.getLogger(__name__)

class PrayerTimeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WordPress Daily Prayer Time."""

    VERSION = 1


    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            _LOGGER.debug("Entering async_step_user with user_input is None")
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_ENDPOINT,
                        ): TextSelector(),
                        vol.Required(
                            CONF_API_PATH,
                            default=DEFAULT_API_PATH,
                        ): TextSelector(),
                    }
                ),
                errors={"endpoint": "invalid_url"},
            )

        endpoint = user_input[CONF_ENDPOINT]
        _LOGGER.debug("Validating endpoint: %s", endpoint)
        endpoint_regex = r"^(https?://)([a-zA-Z0-9.-]+)(:\d+)?(/.*)?$"
        if not re.match(endpoint_regex, endpoint):
            _LOGGER.error("Invalid URL format: %s", endpoint)
            return self.async_abort(reason="invalid_url")
        _LOGGER.debug("Endpoint is valid: %s", endpoint)

        endpoint = user_input[CONF_ENDPOINT]
        parsed_url = urlparse(endpoint)
        website = parsed_url.netloc.split(":")[0]  # Remove port if present
        _LOGGER.debug("Naming the entry with website: %s", website)

        self._async_abort_entries_match(
            {
                CONF_ENDPOINT: user_input[CONF_ENDPOINT],
                CONF_API_PATH: user_input[CONF_API_PATH],
            },
        )
        return self.async_create_entry(
            title=website,
            data={},
            options={
                **user_input,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler()

class OptionsFlowHandler(OptionsFlow):
    """Handle options flow for WordPress Daily Prayer Time."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ENDPOINT,
                        default=self.config_entry.options[CONF_ENDPOINT]
                    ): TextSelector(),
                    vol.Required(
                        CONF_API_PATH,
                        default=self.config_entry.options[CONF_API_PATH]
                    ): TextSelector()
                }
            ),
        )
