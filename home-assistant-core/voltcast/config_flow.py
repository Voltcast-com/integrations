"""Config flow for the Voltcast integration."""

from __future__ import annotations

import logging
from typing import Any

from aiovoltcast import VoltcastAuthError, VoltcastClient, VoltcastConnectionError, VoltcastError
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_ZONE, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_ZONE, default="DE-LU"): str,
    }
)


class VoltcastConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Voltcast."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: API key + bidding zone."""
        errors: dict[str, str] = {}

        if user_input is not None:
            zone = user_input[CONF_ZONE].strip().upper()
            client = VoltcastClient(
                user_input[CONF_API_KEY], session=async_get_clientsession(self.hass)
            )
            try:
                await client.validate_key(zone)
            except VoltcastAuthError:
                errors["base"] = "invalid_auth"
            except VoltcastConnectionError:
                errors["base"] = "cannot_connect"
            except VoltcastError as err:
                errors["base"] = "invalid_zone" if err.code == "zone_not_found" else "unknown"
                if errors["base"] == "unknown":
                    _LOGGER.exception("Unexpected Voltcast API error")
            else:
                await self.async_set_unique_id(zone)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Voltcast {zone}",
                    data={CONF_API_KEY: user_input[CONF_API_KEY], CONF_ZONE: zone},
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
