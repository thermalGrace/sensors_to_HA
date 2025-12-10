"""Simple MQTT monitor for both Pico 2W devices."""
import json
import socket
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt

HOST = "192.168.50.176"
PORT = 1883

TOPICS = [
    ("sensors/pico/mtp40f/co2", 0),
    ("sensors/pico/air_mmwave", 0),
]

CLIENT_ID = "pico-data-monitor"
RECONNECT_DELAY_SEC = 2


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Connected to MQTT {HOST}:{PORT}")
        for topic, qos in TOPICS:
            client.subscribe(topic, qos)
            print(f"Subscribed to {topic} (QoS={qos})")
    else:
        print(f"MQTT connect failed with code {rc}")


def format_message(topic, payload_bytes):
    payload = payload_bytes.decode("utf-8", errors="replace")
    data = None
    try:
        data = json.loads(payload)
        pretty = json.dumps(data, ensure_ascii=False)
    except json.JSONDecodeError:
        pretty = payload
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if topic == "sensors/pico/mtp40f/co2":
        co2 = data.get("co2_ppm") if isinstance(data, dict) else None
        return f"[{timestamp}] CO2 → topic={topic}, co2_ppm={co2}, raw={pretty}"

    if topic == "sensors/pico/air_mmwave":
        radar = data.get("radar") if isinstance(data, dict) else None
        env = data.get("environment") if isinstance(data, dict) else None
        target_count = radar.get("target_count") if isinstance(radar, dict) else None
        return (
            f"[{timestamp}] MMWave → topic={topic}, targets={target_count}, env={env}, raw={pretty}"
        )

    return f"[{timestamp}] topic={topic}, payload={pretty}"


def on_message(client, userdata, msg):
    print(format_message(msg.topic, msg.payload))


def ensure_host_resolvable(host):
    try:
        socket.gethostbyname(host)
        return True
    except socket.gaierror:
        return False


def main():
    if not ensure_host_resolvable(HOST):
        print(f"Cannot resolve MQTT host {HOST}")
        sys.exit(1)

    # Stick to MQTT 3.1.1 protocol; callback matches v5 signature via properties=None.
    client = mqtt.Client(
        client_id=CLIENT_ID,
        protocol=mqtt.MQTTv311,
        callback_api_version=getattr(mqtt.CallbackAPIVersion, "VERSION2", None),
    )
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(HOST, PORT)
            client.loop_forever()
        except Exception as exc:
            print("MQTT disconnected:", exc)
            time.sleep(RECONNECT_DELAY_SEC)


if __name__ == "__main__":
    main()
