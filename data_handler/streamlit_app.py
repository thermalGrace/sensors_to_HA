"""Streamlit launcher that wires together MQTT state, Live Metrics, and the LLM page."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import streamlit as st

from mqtt_monitor import HOST, ensure_host_resolvable

# Allow running via `streamlit run streamlit_app.py` without installing as a package.
PKG_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PKG_ROOT.parent
for entry in (PKG_ROOT, REPO_ROOT):
    if str(entry) not in sys.path:
        sys.path.append(str(entry))

from mqtt_service import ensure_mqtt_thread  # noqa: E402
from weather_service import ensure_weather_thread  # noqa: E402
from uicomponents.live_metrics import render_live_metrics  # noqa: E402
from uicomponents.llm_assistant import render_llm_assistant  # noqa: E402
from uicomponents.multi_user_comfort import render_multi_user_comfort  # noqa: E402
from state import append_snapshot_to_csv, format_ts, get_snapshot  # noqa: E402


def main():
    st.set_page_config(page_title="Pico MQTT Monitor", layout="wide")
    st.title("Thermal Grace - Perceived Thermal Comfort App")
    st.caption("Comfort-as-a-Service: Live view of CO₂ and mmWave sensor data via MQTT")

    page = st.sidebar.radio("Navigation", ["Live Metrics", "Adaptive Multi-User", "LLM Assistant"], index=0)

    if not ensure_host_resolvable(HOST):
        st.error(f"Cannot resolve MQTT host {HOST}")
        return

    ensure_mqtt_thread(st.session_state)
    ensure_weather_thread(st.session_state)

    status_placeholder = st.empty()
    table_placeholder = raw_placeholder = None
    sensor_box = user_box = llm_status = llm_output = None
    question = ""
    ask_button = False

    multi_user_placeholder = None
    if page == "Live Metrics":
        table_placeholder = st.empty()
        raw_placeholder = st.expander("Last raw payload", expanded=False)
    elif page == "Adaptive Multi-User":
        multi_user_placeholder = st.empty()
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

    # Simple heartbeat loop; Streamlit reruns the script so we poll state and render.
    while True:
        snapshot = get_snapshot()

        status = snapshot.get("status", "unknown")
        last_updated = format_ts(snapshot.get("last_updated"))
        status_placeholder.write(f"Status: `{status}` · Last update: `{last_updated}`")

        # Persist to CSV only when we observe a new MQTT message.
        if snapshot.get("last_updated") and st.session_state.get("last_write_ts") != snapshot.get("last_updated"):
            append_snapshot_to_csv(snapshot)
            st.session_state["last_write_ts"] = snapshot.get("last_updated")

        if page == "Live Metrics":
            render_live_metrics(snapshot, table_placeholder, raw_placeholder)
        elif page == "Adaptive Multi-User":
            render_multi_user_comfort(snapshot, multi_user_placeholder)
        else:
            render_llm_assistant(question, ask_button, sensor_box, user_box, llm_status, llm_output)

        time.sleep(1)


if __name__ == "__main__":
    main()