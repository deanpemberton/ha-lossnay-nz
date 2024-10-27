
import logging
from homeassistant.components.fan import FanEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    lossnay_api = hass.data[DOMAIN]
    async_add_entities([LossnayFan(lossnay_api)])

class LossnayFan(FanEntity):
    def __init__(self, api):
        self._api = api
        self._is_on = False
        self._speed = None

    @property
    def name(self):
        return "Lossnay Fan"

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, speed: str = None, **kwargs):
        await self._api.turn_on()
        self._is_on = True

    async def async_turn_off(self, **kwargs):
        await self._api.turn_off()
        self._is_on = False

    async def async_update(self):
        data = await self._api.get_state()
        self._is_on = data['is_on']
        self._speed = data['speed']
