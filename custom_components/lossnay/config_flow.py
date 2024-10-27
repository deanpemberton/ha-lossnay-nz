
from homeassistant import config_entries
from .const import DOMAIN

@config_entries.HANDLERS.register(DOMAIN)
class LossnayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=vol.Schema({
                vol.Required("username"): str,
                vol.Required("password"): str,
                vol.Required("mqtt_broker"): str,
                vol.Required("mqtt_port"): int,
                vol.Optional("mqtt_user"): str,
                vol.Optional("mqtt_password"): str,
            }))

        return self.async_create_entry(title="Lossnay", data=user_input)
