
DOMAIN = "lossnay"

async def async_setup_entry(hass, entry):
    hass.data[DOMAIN] = entry.data
    return True
