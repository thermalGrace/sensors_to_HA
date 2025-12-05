import json, time, network, rp2
from umqtt.simple import MQTTClient, MQTTException
from rd03d import RD03D

WIFI_SSID = "thermal_grace_iot_24"
WIFI_PASSWORD = "45_#_101_G."
MQTT_BROKER = "192.168.50.176"  # Pi/HA host IP
MQTT_PORT = 1883
MQTT_USER = None
MQTT_PASSWORD = None
MQTT_CLIENT_ID = "pico-radar"
MQTT_TOPIC = b"sensors/radar/targets"
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

def targets_to_payload(targets):
    return {
        "timestamp_ms": time.ticks_ms(),
        "targets": [
            {
                "id": i + 1,
                "angle": round(t.angle, 2),
                "distance_mm": round(t.distance, 1),
                "speed_cms": round(t.speed, 2),
                "x_mm": t.x,
                "y_mm": t.y,
            }
            for i, t in enumerate(targets)
        ],
    }

def main():
    if not connect_wifi():
        return
    radar = RD03D()
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
                    payload = targets_to_payload(radar.targets)
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