"""Streamlit dashboard that reuses mqtt_monitor settings to show live Pico sensor values."""
import csv
import json
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt
import streamlit as st
import requests

from mqtt_monitor import HOST, PORT, TOPICS, ensure_host_resolvable

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from thermal_comfort_model.comfort_calc import (  # noqa: E402
    compute_comfort,
    latest_user_context,
    parse_env_from_payload,
)

SENSOR_CSV = Path(__file__).resolve().parent / "live_metrics.csv"

# Print MQTT messages to terminal for debugging. Set to False to silence.
VERBOSE_LOG = True

# Shared state guarded by a lock so the Streamlit thread can read safely.
latest = {
    "co2_ppm": None,
    "radar": None,
    "environment": None,
    "comfort": None,
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


def snapshot_to_row(snapshot: dict) -> dict:
    radar = snapshot.get("radar") or {}
    env = snapshot.get("environment") or {}
    comfort = snapshot.get("comfort") or {}

    people = None
    if isinstance(radar, dict):
        people = radar.get("target_count")
        if people is None and isinstance(radar.get("targets"), list):
            people = len(radar.get("targets"))

    ts = snapshot.get("last_updated")
    iso_ts = datetime.fromtimestamp(ts).isoformat() if ts else ""

    return {
        "timestamp": iso_ts,
        "co2_ppm": snapshot.get("co2_ppm"),
        "people": people,
        "temperature_c": env.get("temperature_c") if isinstance(env, dict) else None,
        "humidity_pct": env.get("humidity_pct") if isinstance(env, dict) else None,
        "pressure_hpa": env.get("pressure_hpa") if isinstance(env, dict) else None,
        "gas_kohms": env.get("gas_kohms") if isinstance(env, dict) else None,
        "pmv": comfort.get("pmv") if isinstance(comfort, dict) else None,
        "ppd": comfort.get("ppd") if isinstance(comfort, dict) else None,
        "utci": comfort.get("utci") if isinstance(comfort, dict) else None,
    }


def append_snapshot_to_csv(snapshot: dict):
    row = snapshot_to_row(snapshot)
    if not row.get("timestamp"):
        return
    headers = [
        "timestamp",
        "co2_ppm",
        "people",
        "temperature_c",
        "humidity_pct",
        "pressure_hpa",
        "gas_kohms",
        "pmv",
        "ppd",
        "utci",
    ]
    exists = SENSOR_CSV.exists()
    with SENSOR_CSV.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def latest_sensor_row() -> dict | None:
    if not SENSOR_CSV.exists():
        return None
    with SENSOR_CSV.open("r", newline="") as f:
        reader = list(csv.DictReader(f))
        if not reader:
            return None
        return reader[-1]


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        _update_state(status="connected")
        for topic, qos in TOPICS:
            client.subscribe(topic, qos)
    else:
        _update_state(status=f"connect failed rc={rc}")

def call_github_llm(prompt: str) -> str:
    token = st.secrets.get("github_models_token")
    if not token:
        return "Missing github_models_token in .streamlit/secrets.toml"

    url = "https://models.github.ai/inference/chat/completions"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "openai/gpt-4.1",
        "messages": [
            {
                "role": "system",
                "content": "You are a concise HVAC/thermal comfort assistant. Use provided sensor and user context to interpret comfort and give actionable, brief advice.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        return msg.get("content", "No content returned")
    except Exception as exc:
        return f"LLM call failed: {exc}"


def build_prompt(snapshot: dict, user_ctx) -> str:
    radar = snapshot.get("radar") or {}
    env = snapshot.get("environment") or {}
    comfort = snapshot.get("comfort") or {}

    co2 = snapshot.get("co2_ppm")
    people = None
    if isinstance(radar, dict):
        people = radar.get("target_count")
        if people is None and isinstance(radar.get("targets"), list):
            people = len(radar.get("targets"))

    lines = [
        "Sensor snapshot:",
        f"- Temperature: {env.get('temperature_c', 'unknown')} C",
        f"- Humidity: {env.get('humidity_pct', 'unknown')} %",
        f"- Pressure: {env.get('pressure_hpa', 'unknown')} hPa",
        f"- Gas: {env.get('gas_kohms', 'unknown')} kOhms",
        f"- CO2: {co2 if co2 is not None else 'unknown'} ppm",
        f"- People (radar): {people if people is not None else 'unknown'}",
        f"- PMV: {comfort.get('pmv', 'unknown') if isinstance(comfort, dict) else 'unknown'}",
        f"- PPD: {comfort.get('ppd', 'unknown') if isinstance(comfort, dict) else 'unknown'}",
        f"- UTCI: {comfort.get('utci', 'unknown') if isinstance(comfort, dict) else 'unknown'} C",
    ]

    if user_ctx:
        lines.append("User context (latest CSV):")
        lines.append(f"- Activity: {user_ctx.activity}")
        lines.append(f"- Task: {user_ctx.main_task}")
        lines.append(f"- Clothing upper: {user_ctx.clothing_upper}")
        lines.append(f"- Clothing lower: {user_ctx.clothing_lower}")
    else:
        lines.append("No user CSV context available.")

    lines.append("\nProvide a short interpretation of thermal comfort and actionable adjustments.")
    return "\n".join(lines)


def build_prompt_from_csv(sensor_row: dict | None, user_ctx, question: str) -> str:
    lines = []
    if question:
        lines.append(f"User question: {question}")
    lines.append("Sensor snapshot (from stored CSV):")
    if sensor_row:
        lines.extend(
            [
                f"- Timestamp: {sensor_row.get('timestamp', 'unknown')}",
                f"- Temperature: {sensor_row.get('temperature_c', 'unknown')} C",
                f"- Humidity: {sensor_row.get('humidity_pct', 'unknown')} %",
                f"- Pressure: {sensor_row.get('pressure_hpa', 'unknown')} hPa",
                f"- Gas: {sensor_row.get('gas_kohms', 'unknown')} kOhms",
                f"- CO2: {sensor_row.get('co2_ppm', 'unknown')} ppm",
                f"- People (radar): {sensor_row.get('people', 'unknown')}",
                f"- PMV: {sensor_row.get('pmv', 'unknown')}",
                f"- PPD: {sensor_row.get('ppd', 'unknown')}",
                f"- UTCI: {sensor_row.get('utci', 'unknown')} C",
            ]
        )
    else:
        lines.append("- No sensor CSV data available yet.")

    if user_ctx:
        lines.append("User context (latest CSV):")
        lines.append(f"- Activity: {user_ctx.activity}")
        lines.append(f"- Task: {user_ctx.main_task}")
        lines.append(f"- Clothing upper: {user_ctx.clothing_upper}")
        lines.append(f"- Clothing lower: {user_ctx.clothing_lower}")
    else:
        lines.append("No user CSV context available.")

    lines.append("\nProvide a short interpretation of thermal comfort and actionable adjustments.")
    return "\n".join(lines)

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
        env_reading = parse_env_from_payload(data)
        comfort = None
        if env_reading:
            user_ctx = latest_user_context()
            comfort = compute_comfort(env_reading, user_ctx)
        _update_state(
            radar=data.get("radar"),
            environment=data.get("environment"),
            comfort=comfort,
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

    page = st.sidebar.radio("Navigation", ["Live Metrics", "LLM Assistant"], index=0)

    if not ensure_host_resolvable(HOST):
        st.error(f"Cannot resolve MQTT host {HOST}")
        return

    # Start MQTT listener once per Streamlit session.
    if "mqtt_thread" not in st.session_state:
        t = threading.Thread(target=mqtt_thread, daemon=True)
        t.start()
        st.session_state["mqtt_thread"] = t

    status_placeholder = st.empty()
    table_placeholder = raw_placeholder = None
    sensor_box = user_box = llm_status = llm_output = None
    question = ""
    ask_button = False

    if page == "Live Metrics":
        table_placeholder = st.empty()
        raw_placeholder = st.expander("Last raw payload", expanded=False)
    else:
        st.subheader("LLM comfort assistant")
        question = st.text_area(
            "Question to ask the model",
            value="Summarize current thermal comfort and suggest adjustments.",
            height=80,
            key="llm_question",
        )
        ask_button = st.button("Ask LLM", type="primary", key="ask_llm_button")
        sensor_box = st.empty()
        user_box = st.empty()
        llm_status = st.empty()
        llm_output = st.empty()

    # Poll the shared state once per second and update placeholders.
    while True:
        with state_lock:
            snapshot = latest.copy()

        status = snapshot.get("status", "unknown")
        last_updated = format_ts(snapshot.get("last_updated"))
        co2_ppm = snapshot.get("co2_ppm")
        radar = snapshot.get("radar") or {}
        env = snapshot.get("environment") or {}
        comfort = snapshot.get("comfort") or {}
        target_count = None
        if isinstance(radar, dict):
            target_count = radar.get("target_count")
            if target_count is None and isinstance(radar.get("targets"), list):
                target_count = len(radar.get("targets"))

        status_placeholder.write(f"Status: `{status}` · Last update: `{last_updated}`")

        # Persist snapshot to CSV when we see a new update
        if snapshot.get("last_updated") and st.session_state.get("last_write_ts") != snapshot.get("last_updated"):
            append_snapshot_to_csv(snapshot)
            st.session_state["last_write_ts"] = snapshot.get("last_updated")

        if page == "Live Metrics":
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
                {
                    "metric": "PMV",
                    "value": comfort.get("pmv", "—") if isinstance(comfort, dict) else "—",
                },
                {
                    "metric": "PPD (%)",
                    "value": comfort.get("ppd", "—") if isinstance(comfort, dict) else "—",
                },
                {
                    "metric": "UTCI (°C)",
                    "value": comfort.get("utci", "—") if isinstance(comfort, dict) else "—",
                },
            ]

            if table_placeholder:
                table_placeholder.table(table_rows)

            if raw_placeholder:
                with raw_placeholder:
                    raw = snapshot.get("last_payload")
                    if isinstance(raw, (dict, list)):
                        st.json(raw)
                    else:
                        st.write(raw if raw is not None else "No payload yet")

        else:  # LLM Assistant page
            sensor_row = latest_sensor_row()
            user_ctx = latest_user_context()

            if sensor_box:
                if sensor_row:
                    sensor_box.table([sensor_row])
                else:
                    sensor_box.info("No sensor CSV data yet. Waiting for first MQTT update...")

            if user_box:
                if user_ctx:
                    user_box.table(
                        [
                            {
                                "activity": user_ctx.activity,
                                "main_task": user_ctx.main_task,
                                "clothing_upper": user_ctx.clothing_upper,
                                "clothing_lower": user_ctx.clothing_lower,
                            }
                        ]
                    )
                else:
                    user_box.info("No user CSV context available yet.")

            if ask_button and not st.session_state.get("llm_called"):
                prompt = build_prompt_from_csv(sensor_row, user_ctx, question)
                answer = call_github_llm(prompt)
                st.session_state["llm_answer"] = answer
                st.session_state["llm_called"] = True
            if not ask_button:
                st.session_state["llm_called"] = False

            if "llm_answer" in st.session_state and llm_status and llm_output:
                llm_status.write("LLM result:")
                st.session_state["llm_render_counter"] = st.session_state.get("llm_render_counter", 0) + 1
                key = f"llm_resp_{st.session_state['llm_render_counter']}"
                llm_output.text_area(
                    "Response",
                    value=st.session_state["llm_answer"],
                    height=300,
                    key=key,
                )

        time.sleep(1)


if __name__ == "__main__":
    main()