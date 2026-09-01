"""Voltcast integration: prices, forecasts, risk, and Home action windows."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]
UPDATE_INTERVAL = timedelta(minutes=15)


class VoltcastCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls prices + forecast; the recorder side updates ~13:00 CET daily."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            always_update=False,
        )
        settings = dict(entry.data) | dict(entry.options)
        self._session = async_get_clientsession(hass)
        self._headers = {
            "Authorization": f"Bearer {settings[CONF_API_KEY]}",
            "Accept": "application/json",
        }
        self.zone = settings[CONF_ZONE]
        self.duration_minutes = int(
            settings.get(CONF_DURATION_MINUTES, DEFAULT_DURATION_MINUTES)
        )
        self.objective = settings.get(CONF_OBJECTIVE, DEFAULT_OBJECTIVE)
        self.tariff = {
            "grid_fee_eur_kwh": float(
                settings.get(
                    CONF_GRID_FEE_EUR_KWH, DEFAULT_GRID_FEE_EUR_KWH
                )
            ),
            "supplier_markup_eur_kwh": float(
                settings.get(
                    CONF_SUPPLIER_MARKUP_EUR_KWH,
                    DEFAULT_SUPPLIER_MARKUP_EUR_KWH,
                )
            ),
            "vat_percent": float(
                settings.get(CONF_VAT_PERCENT, DEFAULT_VAT_PERCENT)
            ),
        }

    async def _fetch(
        self,
        path: str,
        *,
        method: str = "GET",
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async with self._session.request(
            method,
            f"{BASE_URL}{path}",
            headers=self._headers,
            json=json,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status >= 400:
                raise UpdateFailed(f"Voltcast API {response.status} for {path}")
            return await response.json()

    async def _optional(
        self,
        path: str,
        *,
        method: str = "GET",
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            return await self._fetch(path, method=method, json=json)
        except (UpdateFailed, aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.debug("Optional Voltcast surface unavailable: %s", err)
            return {"data": [], "meta": {"available": False}}

    async def _async_update_data(self) -> dict[str, Any]:
        prices, forecast, risk, optimization = await asyncio.gather(
            self._fetch(f"/v1/prices/{self.zone}"),
            self._optional(f"/v1/forecasts/{self.zone}?horizon=48h"),
            self._optional(f"/v1/risk/negative/{self.zone}?days=2"),
            self._optional(
                "/v1/optimize/cheapest-window",
                method="POST",
                json={
                    "zone": self.zone,
                    "duration_minutes": self.duration_minutes,
                    "count": 1,
                    "objective": self.objective,
                    "tariff": self.tariff,
                },
            ),
        )
        return {
            "prices": prices,
            "forecast": forecast,
            "risk": risk,
            "optimization": optimization,
        }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = VoltcastCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_options))

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


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
