"""DataUpdateCoordinator for Voltcast."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from aiovoltcast import (
    VoltcastAuthError,
    VoltcastClient,
    VoltcastConnectionError,
    VoltcastError,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

type VoltcastConfigEntry = ConfigEntry[VoltcastCoordinator]

UPDATE_INTERVAL = timedelta(minutes=15)


class VoltcastCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll prices + forecast; day-ahead data updates ~13:00 CET daily."""

    config_entry: VoltcastConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: VoltcastConfigEntry,
        client: VoltcastClient,
        zone: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self.zone = zone

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch prices and (best-effort) the forecast."""
        try:
            prices = await self.client.prices(self.zone)
        except VoltcastAuthError as err:
            raise ConfigEntryAuthFailed(err) from err
        except (VoltcastConnectionError, VoltcastError) as err:
            raise UpdateFailed(f"Voltcast API error: {err}") from err

        forecast: dict[str, Any] = {"data": []}
        try:
            forecast = await self.client.forecast(self.zone, horizon="48h")
        except (VoltcastConnectionError, VoltcastError):
            _LOGGER.debug("Forecast unavailable for %s; serving prices only", self.zone)

        return {"prices": prices, "forecast": forecast}
