
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN
from .api import LossnayAPI

_LOGGER = logging.getLogger(__name__)


class LossnayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lossnay."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                    vol.Required("app_version", default="6.3.1918"): str,
                    vol.Required("unit_id"): str,
                    vol.Required("mqtt_broker"): str,
                    vol.Required("mqtt_port", default=1883): cv.port,
                    vol.Optional("mqtt_user"): str,
                    vol.Optional("mqtt_password"): str,
                }),
            )

        # Attempt to authenticate to validate credentials
        errors = {}
        try:
            api = LossnayAPI(
                user_input["username"],
                user_input["password"],
                user_input["app_version"],
                user_input["unit_id"],
                user_input["mqtt_broker"],
                user_input["mqtt_port"],
                user_input.get("mqtt_user"),
                user_input.get("mqtt_password")
            )
            if not api.authenticate():
                errors["base"] = "auth"
        except Exception as e:
            _LOGGER.error("Unexpected error during setup: %s", str(e))
            errors["base"] = "unknown"

        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                    vol.Required("app_version", default="6.3.1918"): str,
                    vol.Required("unit_id"): str,
                    vol.Required("mqtt_broker"): str,
                    vol.Required("mqtt_port", default=1883): cv.port,
                    vol.Optional("mqtt_user"): str,
                    vol.Optional("mqtt_password"): str,
                }),
                errors=errors,
            )

        return self.async_create_entry(title="Mitsubishi Lossnay", data=user_input)
