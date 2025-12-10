"""Streamlit dashboard that reuses mqtt_monitor settings to show live Pico sensor values."""
import json
import threading
import time
from datetime import datetime

import paho.mqtt.client as mqtt
import streamlit as st

from mqtt_monitor import HOST, PORT, TOPICS, ensure_host_resolvable

# Print MQTT messages to terminal for debugging. Set to False to silence.
VERBOSE_LOG = True

# Shared state guarded by a lock so the Streamlit thread can read safely.
latest = {
    "co2_ppm": None,
    "radar": None,
    "environment": None,
    "last_topic": None,
    "last_payload": None,
    "last_updated": None,
    "status": "disconnected",
}
state_lock = threading.Lock()


def _update_state(**kwargs):
    with state_lock:
        latest.update(kwargs)
        latest["last_updated"] = time.time()


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        _update_state(status="connected")
        for topic, qos in TOPICS:
            client.subscribe(topic, qos)
    else:
        _update_state(status=f"connect failed rc={rc}")


def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8", errors="replace")
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        data = payload

    if VERBOSE_LOG:
        print(f"MQTT {msg.topic}: {data}")

    if msg.topic == "sensors/pico/mtp40f/co2" and isinstance(data, dict):
        _update_state(
            co2_ppm=data.get("co2_ppm"),
            last_topic=msg.topic,
            last_payload=data,
        )
    elif msg.topic == "sensors/pico/air_mmwave" and isinstance(data, dict):
        _update_state(
            radar=data.get("radar"),
            environment=data.get("environment"),
            last_topic=msg.topic,
            last_payload=data,
        )
    else:
        _update_state(last_topic=msg.topic, last_payload=data)


def mqtt_thread():
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
            _update_state(status=f"disconnected: {exc}")
            time.sleep(2)


def format_ts(ts: float | None) -> str:
    if not ts:
        return "—"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def main():
    st.set_page_config(page_title="Pico MQTT Monitor", layout="wide")
    st.title("Pico MQTT Monitor")
    st.caption("Live view of CO₂ and mmWave sensor data via MQTT")

    if not ensure_host_resolvable(HOST):
        st.error(f"Cannot resolve MQTT host {HOST}")
        return

    # Start MQTT listener once per Streamlit session.
    if "mqtt_thread" not in st.session_state:
        t = threading.Thread(target=mqtt_thread, daemon=True)
        t.start()
        st.session_state["mqtt_thread"] = t

    status_placeholder = st.empty()
    table_placeholder = st.empty()
    raw_placeholder = st.expander("Last raw payload", expanded=False)

    # Poll the shared state once per second and update placeholders.
    while True:
        with state_lock:
            snapshot = latest.copy()

        status = snapshot.get("status", "unknown")
        last_updated = format_ts(snapshot.get("last_updated"))
        co2_ppm = snapshot.get("co2_ppm")
        radar = snapshot.get("radar") or {}
        env = snapshot.get("environment") or {}
        target_count = None
        if isinstance(radar, dict):
            target_count = radar.get("target_count")
            if target_count is None and isinstance(radar.get("targets"), list):
                target_count = len(radar.get("targets"))

        status_placeholder.write(f"Status: `{status}` · Last update: `{last_updated}`")

        table_rows = [
            {"metric": "CO2 ppm", "value": co2_ppm if co2_ppm is not None else "—"},
            {"metric": "People (radar)", "value": target_count if target_count is not None else "—"},
            {
                "metric": "Temperature (°C)",
                "value": env.get("temperature_c", "—") if isinstance(env, dict) else "—",
            },
            {
                "metric": "Humidity (%)",
                "value": env.get("humidity_pct", "—") if isinstance(env, dict) else "—",
            },
            {
                "metric": "Pressure (hPa)",
                "value": env.get("pressure_hpa", "—") if isinstance(env, dict) else "—",
            },
            {
                "metric": "Gas (kΩ)",
                "value": env.get("gas_kohms", "—") if isinstance(env, dict) else "—",
            },
        ]

        table_placeholder.table(table_rows)

        with raw_placeholder:
            raw = snapshot.get("last_payload")
            if isinstance(raw, (dict, list)):
                st.json(raw)
            else:
                st.write(raw if raw is not None else "No payload yet")

        time.sleep(1)


if __name__ == "__main__":
    main()
