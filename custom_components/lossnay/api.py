
import requests
import json
import paho.mqtt.client as mqtt
import time
import logging

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

    def authenticate(self):
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
        response = requests.post(url, headers=headers, data=payload)
        
        if response.status_code == 200:
            auth_cookie = response.cookies.get('auth')
            return auth_cookie
        else:
            logging.error(f"Failed to authenticate: {response.status_code} - {response.text}")
            return None

    def get_unit_data(self, auth_cookie):
        url = "https://api.melview.net/api/unitcommand.aspx"
        payload = json.dumps({
            "unitid": self.unit_id,
            "v": 3
        })
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'auth={auth_cookie}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error("Failed to retrieve unit data")
            return None

    def publish_to_mqtt(self, data):
        client = mqtt.Client()
        client.username_pw_set(self.mqtt_user, self.mqtt_password)
        client.connect(self.mqtt_broker, self.mqtt_port, 60)
        client.loop_start()
        
        # Publish discovery configs for each sensor
        for key in data.keys():
            self.publish_discovery_config(client, key)

        # Publish sensor data
        for key, value in data.items():
            client.publish(f"homeassistant/sensor/Lossnay/{key}", value)
        
        client.loop_stop()
        client.disconnect()

    def publish_discovery_config(self, client, sensor_name):
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
        client.publish(f"homeassistant/sensor/Lossnay_{sensor_name}/config", json.dumps(config_payload), retain=True)
