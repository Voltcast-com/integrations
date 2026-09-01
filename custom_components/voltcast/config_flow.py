"""Config flow: API key + bidding zone, validated against the live API."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    BASE_URL,
    CONF_API_KEY,
    CONF_DURATION_MINUTES,
    CONF_GRID_FEE_EUR_KWH,
    CONF_OBJECTIVE,
    CONF_SUPPLIER_MARKUP_EUR_KWH,
    CONF_VAT_PERCENT,
    CONF_ZONE,
    DEFAULT_DURATION_MINUTES,
    DEFAULT_GRID_FEE_EUR_KWH,
    DEFAULT_OBJECTIVE,
    DEFAULT_SUPPLIER_MARKUP_EUR_KWH,
    DEFAULT_VAT_PERCENT,
    DOMAIN,
)


def _action_settings_schema(defaults: dict[str, Any]) -> dict[Any, Any]:
    return {
        vol.Optional(
            CONF_DURATION_MINUTES,
            default=defaults.get(CONF_DURATION_MINUTES, DEFAULT_DURATION_MINUTES),
        ): vol.All(vol.Coerce(int), vol.Range(min=15, max=1440)),
        vol.Optional(
            CONF_OBJECTIVE,
            default=defaults.get(CONF_OBJECTIVE, DEFAULT_OBJECTIVE),
        ): vol.In(["cost", "carbon", "balanced"]),
        vol.Optional(
            CONF_GRID_FEE_EUR_KWH,
            default=defaults.get(
                CONF_GRID_FEE_EUR_KWH, DEFAULT_GRID_FEE_EUR_KWH
            ),
        ): vol.All(vol.Coerce(float), vol.Range(min=0, max=2)),
        vol.Optional(
            CONF_SUPPLIER_MARKUP_EUR_KWH,
            default=defaults.get(
                CONF_SUPPLIER_MARKUP_EUR_KWH, DEFAULT_SUPPLIER_MARKUP_EUR_KWH
            ),
        ): vol.All(vol.Coerce(float), vol.Range(min=0, max=2)),
        vol.Optional(
            CONF_VAT_PERCENT,
            default=defaults.get(CONF_VAT_PERCENT, DEFAULT_VAT_PERCENT),
        ): vol.All(vol.Coerce(float), vol.Range(min=0, max=50)),
    }


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
                    data={
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_ZONE: zone,
                        **{
                            key: user_input[key]
                            for key in (
                                CONF_DURATION_MINUTES,
                                CONF_OBJECTIVE,
                                CONF_GRID_FEE_EUR_KWH,
                                CONF_SUPPLIER_MARKUP_EUR_KWH,
                                CONF_VAT_PERCENT,
                            )
                        },
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Required(CONF_ZONE, default="DE-LU"): str,
                    **_action_settings_schema(user_input or {}),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return VoltcastOptionsFlow(config_entry)


class VoltcastOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        defaults = dict(self._config_entry.data) | dict(self._config_entry.options)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(_action_settings_schema(defaults)),
        )
