"""Config flow: API key + bidding zone, validated against the live API."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import BASE_URL, CONF_API_KEY, CONF_ZONE, DOMAIN


class VoltcastConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            zone = user_input[CONF_ZONE].strip().upper()
            session = async_get_clientsession(self.hass)
            try:
                async with session.get(
                    f"{BASE_URL}/v1/prices/{zone}",
                    headers={"Authorization": f"Bearer {user_input[CONF_API_KEY]}"},
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as response:
                    if response.status == 401:
                        errors["base"] = "invalid_auth"
                    elif response.status == 403:
                        errors["base"] = "zone_not_in_plan"
                    elif response.status == 404:
                        errors["base"] = "unknown_zone"
                    elif response.status >= 400:
                        errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(f"voltcast_{zone}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Voltcast {zone}",
                    data={CONF_API_KEY: user_input[CONF_API_KEY], CONF_ZONE: zone},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_ZONE, default="DE-LU"): str,
            }),
            errors=errors,
        )
