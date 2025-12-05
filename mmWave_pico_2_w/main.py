import json
import time
import network
import rp2
from simple import MQTTClient, MQTTException
from rd03d import RD03D

WIFI_SSID = "thermal_grace_iot_24"
WIFI_PASSWORD = "45_#_101_G."
# Set this to the broker on the same subnet as the Pico
MQTT_BROKER = "192.168.50.176"
MQTT_PORT = 1883
MQTT_USER = None
MQTT_PASSWORD = None
MQTT_CLIENT_ID = "pico-radar"
MQTT_TOPIC = b"sensors/radar/targets"
MQTT_KEEPALIVE = 60
PUBLISH_INTERVAL_MS = 100

rp2.country("NL")  # set your 2-letter country code

wlan = network.WLAN(network.STA_IF)

def connect_wifi(max_retries=20):
    # Handles hidden SSIDs too; will just attempt association with given SSID/key
    if wlan.isconnected():
        return True
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    retries = 0
    while not wlan.isconnected() and retries < max_retries:
        print("Wi-Fi: connecting... attempt", retries + 1, "status", wlan.status())
        time.sleep(0.5)
        retries += 1
    if wlan.isconnected():
        print("Wi-Fi: connected, IP:", wlan.ifconfig()[0])
    else:
        print("Wi-Fi: failed")
    return wlan.isconnected()


def ensure_wifi():
    if wlan.isconnected():
        return True
    print("Wi-Fi: not connected, reconnecting")
    return connect_wifi()

def ensure_mqtt_client():
    print("MQTT: connecting to", MQTT_BROKER, MQTT_PORT, "wlan status", wlan.status(), "ip", wlan.ifconfig()[0])
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
    return client

def targets_to_payload(targets):
    payload = {"timestamp_ms": time.ticks_ms(), "targets": []}
    for idx, t in enumerate(targets, start=1):
        payload["targets"].append(
            {
                "id": idx,
                "angle": round(t.angle, 2),
                "distance_mm": round(t.distance, 1),
                "speed_cms": round(t.speed, 2),
                "x_mm": t.x,
                "y_mm": t.y,
            }
        )
    return payload

def main():
    if not connect_wifi():
        print("Fatal: Wi-Fi connect failed")
        return

    radar = RD03D()
    mqtt_client = None
    last_publish = 0

    while True:
        try:
            if not ensure_wifi():
                print("Wi-Fi still down; skipping MQTT connect")
                time.sleep(1)
                continue

            if mqtt_client is None:
                mqtt_client = ensure_mqtt_client()

            if radar.update():
                now = time.ticks_ms()
                if time.ticks_diff(now, last_publish) >= PUBLISH_INTERVAL_MS:
                    payload = targets_to_payload(radar.targets)
                    mqtt_client.publish(MQTT_TOPIC, json.dumps(payload))
                    print("MQTT: published", payload)
                    last_publish = now
        except (OSError, MQTTException) as exc:
            print("Error:", exc)
            if mqtt_client:
                try:
                    mqtt_client.disconnect()
                except OSError:
                    pass
            mqtt_client = None
            time.sleep(2)
        except Exception as exc:
            print("Unexpected error:", exc)
            return
        time.sleep(0.02)

if __name__ == "__main__":
    main()