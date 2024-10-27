
# Combined api.py and fan.py in a single file
import aiohttp
import json
import paho.mqtt.client as mqtt
import time
import logging
from homeassistant.components import mqtt as hass_mqtt
from homeassistant.helpers.entity import Entity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import async_get_current_platform

# Lossnay API Wrapper Class


class LossnayAPI:
    def __init__(self, username, password, app_version, unit_id, mqtt_broker, mqtt_port, mqtt_user, mqtt_password):
        self.username = username
        self.password = password
        self.app_version = app_version
        self.unit_id = unit_id
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password

    async def authenticate(self):
        url = "https://api.melview.net/api/login.aspx"
        payload = json.dumps({
            "user": self.username,
            "pass": self.password,
            "appversion": self.app_version
        })
        headers = {
            'Content-Type': 'text/plain',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                if response.status == 200:
                    cookies = response.cookies
                    auth_cookie = cookies.get(
                        'auth').value if 'auth' in cookies else None
                    return auth_cookie
                else:
                    logging.error(f"Failed to authenticate: {response.status} - {await response.text()}")
                    return None

    async def get_unit_data(self, auth_cookie):
        url = "https://api.melview.net/api/unitcommand.aspx"
        payload = json.dumps({
            "unitid": self.unit_id,
            "v": 4
        })
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'auth={auth_cookie}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.error("Failed to retrieve unit data")
                    return None

    async def set_power_state(self, auth_cookie, power_on):
        url = "https://api.melview.net/api/unitcommand.aspx"
        command = "PW1" if power_on else "PW0"
        payload = json.dumps({
            "unitid": self.unit_id,
            "v": 4,
            "commands": command
        })
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'auth={auth_cookie}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                if response.status == 200:
                    logging.info("Power state changed successfully")
                else:
                    logging.error(f"Failed to change power state: {response.status} - {await response.text()}")

    async def set_mode(self, auth_cookie, mode):
        url = "https://api.melview.net/api/unitcommand.aspx"
        if mode == "Lossnay":
            command = "MD1"
        elif mode == "Bypass":
            command = "MD7"
        elif mode == "Auto":
            command = "MD3"
        else:
            logging.error(f"Invalid mode specified: {mode}")
            return

        payload = json.dumps({
            "unitid": self.unit_id,
            "v": 4,
            "commands": command
        })
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'auth={auth_cookie}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                if response.status == 200:
                    logging.info(f"Mode changed to {mode} successfully")
                else:
                    logging.error(f"Failed to change mode: {response.status} - {await response.text()}")

    async def set_fan_speed(self, auth_cookie, fan_speed):
        url = "https://api.melview.net/api/unitcommand.aspx"
        valid_fan_speeds = ["FS0", "FS2", "FS3", "FS5", "FS6"]
        if fan_speed not in valid_fan_speeds:
            logging.error(f"Invalid fan speed specified: {fan_speed}")
            return

        payload = json.dumps({
            "unitid": self.unit_id,
            "v": 4,
            "commands": fan_speed
        })
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'auth={auth_cookie}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                if response.status == 200:
                    logging.info(f"Fan speed set to {fan_speed} successfully")
                else:
                    logging.error(f"Failed to set fan speed: {response.status} - {await response.text()}")

    def publish_to_mqtt(self, data):
        client = mqtt.Client()
        client.username_pw_set(self.mqtt_user, self.mqtt_password)
        client.connect(self.mqtt_broker, self.mqtt_port, 60)
        client.loop_start()

        # Publish discovery configs for each sensor
        sensor_types = {
            "power": "power",
            "standby": "standby",
            "setmode": "mode",
            "automode": "automode",
            "setfan": "fan",
            "settemp": "temperature",
            "roomtemp": "temperature",
            "outdoortemp": "temperature",
            "supplyfan": "fan",
            "supplytemp": "temperature",
            "exhausttemp": "temperature",
            "coreefficiency": "efficiency",
            "fault": "fault",
            "error": "status"
        }

        for key, value in data.items():
            sensor_type = sensor_types.get(key, None)
            unit_of_measurement = None
            if sensor_type == "temperature":
                unit_of_measurement = "°C"
            elif sensor_type == "fan":
                unit_of_measurement = "RPM"
            elif sensor_type == "efficiency":
                unit_of_measurement = "%"

            self.publish_discovery_config(
                client, key, sensor_type, unit_of_measurement)

        # Publish sensor data
        for key, value in data.items():
            client.publish(f"homeassistant/sensor/Lossnay/{key}", value)

        client.loop_stop()
        client.disconnect()

    def publish_discovery_config(self, client, sensor_name, sensor_type, unit_of_measurement=None):
        config_payload = {
            "name": f"Mitsubishi {sensor_name.capitalize()}",
            "state_topic": f"homeassistant/sensor/Lossnay/{sensor_name}",
            "unique_id": f"lossnay_{sensor_name}",
            "device": {
                "identifiers": ["lossnay_unit"],
                "name": "Mitsubishi Lossnay Ventilation Unit",
                "model": "Lossnay",
                "manufacturer": "Mitsubishi"
            }
        }
        if sensor_type is not None:
            config_payload["device_class"] = sensor_type
        if unit_of_measurement:
            config_payload["unit_of_measurement"] = unit_of_measurement

        client.publish(
            f"homeassistant/sensor/Lossnay_{sensor_name}/config", json.dumps(config_payload), retain=True)

# Fan Entity for Home Assistant Integration


class LossnayFanEntity(FanEntity):
    def __init__(self, api, name, auth_cookie):
        self._attr_supported_features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF | FanEntityFeature.SET_SPEED
        self._api = api
        self._name = name
        self._auth_cookie = auth_cookie
        self._state = None
        self._speed = None

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state == "on"

    @property
    def speed(self):
        return self._speed

    async def async_turn_on(self, **kwargs):
        await self._api.set_power_state(self._auth_cookie, True)
        self._state = "on"
        await self.async_update_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._api.set_power_state(self._auth_cookie, False)
        self._state = "off"
        await self.async_update_ha_state()

    async def async_set_speed(self, speed: str):
        valid_speeds = {
            "auto": "FS0",
            "low": "FS2",
            "medium": "FS3",
            "high": "FS5",
            "very_high": "FS6"
        }
        if speed in valid_speeds:
            await self._api.set_fan_speed(self._auth_cookie, valid_speeds[speed])
            self._speed = speed
            await self.async_update_ha_state()
        else:
            logging.error(f"Invalid fan speed: {speed}")

    async def async_update(self):
        unit_data = await self._api.get_unit_data(self._auth_cookie)
        if unit_data:
            self._state = "on" if unit_data.get("power") == 1 else "off"
            self._speed = unit_data.get("setfan")
