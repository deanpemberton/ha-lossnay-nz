
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN

@config_entries.HANDLERS.register(DOMAIN)
class LossnayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLLING

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(
                step_id="user", 
                data_schema=vol.Schema({
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                    vol.Required("app_version", default="6.3.1918"): str,
                    vol.Required("unit_id"): str,
                    vol.Required("mqtt_broker"): str,
                    vol.Required("mqtt_port", default=1883): int,
                    vol.Optional("mqtt_user"): str,
                    vol.Optional("mqtt_password"): str
                })
            )
        
        return self.async_create_entry(title="Mitsubishi Lossnay", data=user_input)
