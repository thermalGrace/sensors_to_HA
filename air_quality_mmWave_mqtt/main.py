import json
import time
import network
import rp2
from machine import I2C, Pin
from umqtt.simple import MQTTClient, MQTTException
from rd03d import RD03D
from bme680 import BME680_I2C

WIFI_SSID = "thermal_grace_iot_24"
WIFI_PASSWORD = "45_#_101_G."
MQTT_BROKER = "192.168.50.176"
MQTT_PORT = 1883
MQTT_USER = None
MQTT_PASSWORD = None
MQTT_CLIENT_ID = "pico-mmwave-air"
MQTT_TOPIC = b"sensors/pico/air_mmwave"
MQTT_KEEPALIVE = 60
PUBLISH_INTERVAL_MS = 100

rp2.country("NL")
wlan = network.WLAN(network.STA_IF)

def connect_wifi(max_retries=30):
	if wlan.isconnected():
		return True
	wlan.active(True)
	wlan.connect(WIFI_SSID, WIFI_PASSWORD)
	for _ in range(max_retries):
		if wlan.isconnected():
			break
		time.sleep(0.5)
	if wlan.isconnected():
		print("Wi-Fi:", wlan.ifconfig())
	else:
		print("Wi-Fi failed")
	return wlan.isconnected()

def build_radar_payload(targets):
	return [
		{
			"id": i + 1,
			"angle": round(t.angle, 2),
			"distance_mm": round(t.distance, 1),
			"speed_cms": round(t.speed, 2),
			"x_mm": t.x,
			"y_mm": t.y,
		}
		for i, t in enumerate(targets)
	]

def read_bme_sensor(bme):
	try:
		return {
			"temperature_c": round(bme.temperature, 2),
			"temperature_f": round((bme.temperature) * (9 / 5) + 32, 2),
			"humidity_pct": round(bme.humidity, 2),
			"pressure_hpa": round(bme.pressure, 2),
			"gas_kohms": round(bme.gas / 1000, 2),
		}
	except OSError:
		print("BME680: read failed")
		return None

def main():
	if not connect_wifi():
		return
	radar = RD03D()
	i2c = I2C(id=0, scl=Pin(5), sda=Pin(4))
	bme = BME680_I2C(i2c=i2c)
	client = None
	last_pub = 0
	while True:
		try:
			if not wlan.isconnected():
				print("Wi-Fi dropped, reconnecting...")
				connect_wifi()
				client = None
			if client is None:
				print("MQTT: connecting...")
				client = MQTTClient(
					MQTT_CLIENT_ID,
					MQTT_BROKER,
					port=MQTT_PORT,
					user=MQTT_USER,
					password=MQTT_PASSWORD,
					keepalive=MQTT_KEEPALIVE,
				)
				client.connect()
				print("MQTT: connected")
			if radar.update():
				now = time.ticks_ms()
				if time.ticks_diff(now, last_pub) >= PUBLISH_INTERVAL_MS:
					payload = {
						"timestamp_ms": now,
						"radar": {
							"target_count": len(radar.targets),
							"targets": build_radar_payload(radar.targets),
						},
						"environment": read_bme_sensor(bme),
					}
					client.publish(MQTT_TOPIC, json.dumps(payload))
					last_pub = now
		except (OSError, MQTTException) as exc:
			print("MQTT/Wi-Fi error:", exc)
			try:
				if client:
					client.disconnect()
			except OSError:
				pass
			client = None
			time.sleep(2)
		time.sleep(0.02)

if __name__ == "__main__":
	main()
