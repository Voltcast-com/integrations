"""The Voltcast integration: European electricity prices and forecasts."""

from __future__ import annotations

from aiovoltcast import VoltcastClient

from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_ZONE
from .coordinator import VoltcastConfigEntry, VoltcastCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: VoltcastConfigEntry) -> bool:
    """Set up Voltcast from a config entry."""
    client = VoltcastClient(
        entry.data[CONF_API_KEY], session=async_get_clientsession(hass)
    )
    coordinator = VoltcastCoordinator(hass, entry, client, entry.data[CONF_ZONE])
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VoltcastConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
