"""Bihać Vodostaj integration."""
from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import WaterApi
from .const import DOMAIN
from .coordinator import WaterCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]
type WaterConfigEntry = ConfigEntry[WaterCoordinator]

async def async_setup_entry(hass: HomeAssistant, entry: WaterConfigEntry) -> bool:
    coordinator = WaterCoordinator(hass, entry, WaterApi(async_get_clientsession(hass)))
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True

async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: WaterConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
