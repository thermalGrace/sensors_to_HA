"""Render helpers for the LLM Assistant page."""
from __future__ import annotations

import streamlit as st

from thermal_comfort_model.comfort_calc import (
    all_users_context,
    get_multi_user_results,
    latest_user_context,
    parse_env_from_payload,
)

from data_handler.llm_utils import build_multi_user_prompt, call_github_llm
from data_handler.state import get_snapshot, latest_sensor_row


def render_llm_assistant(question: str, ask_button: bool, sensor_box, user_box, llm_status, llm_output) -> None:
    sensor_row = latest_sensor_row()
    users = all_users_context()
    user_ctx = latest_user_context()  # still used for single user display if needed

    if sensor_box:
        if sensor_row:
            sensor_box.table([sensor_row])
        else:
            sensor_box.info("No sensor CSV data yet. Waiting for first MQTT update...")

    if user_box:
        if users:
            # Show a summary list of users found today
            display_users = []
            for uid, ctx in users.items():
                display_users.append({
                    "UID": uid[:8],
                    "Activity": ctx.activity,
                    "Clothing": f"{ctx.clothing_upper} / {ctx.clothing_lower}"
                })
            user_box.table(display_users)
        else:
            user_box.info("No user feedback submitted today. Submit feedback in the survey app to see personalized results.")

    # Fire the LLM call once per button press to avoid repeated API hits during reruns.
    if ask_button and not st.session_state.get("llm_called"):
        # Gather multi-user results for the prompt
        snapshot = get_snapshot()
        env_reading = parse_env_from_payload(snapshot)
        results = []
        if env_reading and users:
            results = get_multi_user_results(env_reading, users)
            
        prompt = build_multi_user_prompt(sensor_row, results, question)
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
