
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lossnay from a config entry."""
    _LOGGER.info("Setting up Lossnay integration with entry: %s", entry.data)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward setup for the entities (for example, fan)
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "fan")
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Lossnay integration for entry: %s", entry.data)

    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "fan")
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
