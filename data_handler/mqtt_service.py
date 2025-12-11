"""MQTT listener that pushes sensor updates into shared state."""
from __future__ import annotations

import json
import threading
import time
from typing import MutableMapping

import paho.mqtt.client as mqtt

from mqtt_monitor import HOST, PORT, TOPICS
from thermal_comfort_model.comfort_calc import compute_comfort, latest_user_context, parse_env_from_payload

from state import update_state

# Print MQTT messages to terminal for debugging. Set to False to silence.
VERBOSE_LOG = True


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        update_state(status="connected")
        for topic, qos in TOPICS:
            client.subscribe(topic, qos)
    else:
        update_state(status=f"connect failed rc={rc}")


def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8", errors="replace")
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        data = payload

    if VERBOSE_LOG:
        print(f"MQTT {msg.topic}: {data}")

    if msg.topic == "sensors/pico/mtp40f/co2" and isinstance(data, dict):
        update_state(
            co2_ppm=data.get("co2_ppm"),
            last_topic=msg.topic,
            last_payload=data,
        )
    elif msg.topic == "sensors/pico/air_mmwave" and isinstance(data, dict):
        env_reading = parse_env_from_payload(data)
        comfort = None
        if env_reading:
            user_ctx = latest_user_context()
            comfort = compute_comfort(env_reading, user_ctx)
        update_state(
            radar=data.get("radar"),
            environment=data.get("environment"),
            comfort=comfort,
            last_topic=msg.topic,
            last_payload=data,
        )
    else:
        update_state(last_topic=msg.topic, last_payload=data)


def _mqtt_loop():
    client = mqtt.Client(
        client_id="pico-streamlit",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(HOST, PORT)
            client.loop_forever()
        except Exception as exc:  # keep retrying on disconnect or network error
            update_state(status=f"disconnected: {exc}")
            time.sleep(2)


def ensure_mqtt_thread(session_state: MutableMapping[str, object]) -> None:
    """Start the MQTT listener only once per Streamlit session."""
    if session_state.get("mqtt_thread"):
        return
    t = threading.Thread(target=_mqtt_loop, daemon=True)
    t.start()
    session_state["mqtt_thread"] = t
