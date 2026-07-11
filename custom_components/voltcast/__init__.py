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

    async def report_flexibility(call) -> None:
        """Opt-in service: contribute an anonymized flexibility action to
        Voltcast's aggregate dataset (voltcast.com/docs#telemetry).

        No PII leaves Home Assistant — only zone, device type, the planned
        window, energy and the trigger. Aggregates are published above a
        25-reporter k-anonymity floor; contributors get early access to them.

        Example automation action:
          service: voltcast.report_flexibility
          data:
            device_type: ev
            planned_start: "{{ now() + timedelta(hours=2) }}"
            planned_end: "{{ now() + timedelta(hours=6) }}"
            energy_kwh: 40
            trigger_type: cheapest_window
        """
        payload = {
            "zone": coordinator.zone,
            "device_type": call.data.get("device_type", "other"),
            "planned_start": str(call.data["planned_start"]),
            "planned_end": str(call.data["planned_end"]),
            "energy_kwh": call.data.get("energy_kwh"),
            "trigger": call.data.get("trigger_type", "manual"),
        }
        async with coordinator._session.post(  # noqa: SLF001
            f"{BASE_URL}/v1/telemetry/flex",
            headers=coordinator._headers,  # noqa: SLF001
            json={k: v for k, v in payload.items() if v is not None},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status >= 400:
                _LOGGER.warning("Voltcast telemetry rejected: HTTP %s", response.status)

    hass.services.async_register(DOMAIN, "report_flexibility", report_flexibility)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        return True
    return False
