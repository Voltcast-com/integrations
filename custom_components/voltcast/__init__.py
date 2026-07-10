"""Voltcast integration: 15-minute European power prices + forecasts."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import BASE_URL, CONF_API_KEY, CONF_ZONE, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]
UPDATE_INTERVAL = timedelta(minutes=15)


class VoltcastCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls prices + forecast; the recorder side updates ~13:00 CET daily."""

    def __init__(self, hass: HomeAssistant, api_key: str, zone: str) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        self._session = async_get_clientsession(hass)
        self._headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
        self.zone = zone

    async def _fetch(self, path: str) -> dict[str, Any]:
        async with self._session.get(
            f"{BASE_URL}{path}", headers=self._headers, timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status >= 400:
                raise UpdateFailed(f"Voltcast API {response.status} for {path}")
            return await response.json()

    async def _async_update_data(self) -> dict[str, Any]:
        prices = await self._fetch(f"/v1/prices/{self.zone}")
        try:
            forecast = await self._fetch(f"/v1/forecasts/{self.zone}?horizon=48h")
        except UpdateFailed:
            forecast = {"data": [], "meta": {}}
        return {"prices": prices, "forecast": forecast}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = VoltcastCoordinator(hass, entry.data[CONF_API_KEY], entry.data[CONF_ZONE])
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        return True
    return False
