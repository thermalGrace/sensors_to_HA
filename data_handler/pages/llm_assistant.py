"""Render helpers for the LLM Assistant page."""
from __future__ import annotations

import streamlit as st

from thermal_comfort_model.comfort_calc import latest_user_context

from data_handler.llm_utils import build_prompt_from_csv, call_github_llm
from data_handler.state import latest_sensor_row


def render_llm_assistant(question: str, ask_button: bool, sensor_box, user_box, llm_status, llm_output) -> None:
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

    # Fire the LLM call once per button press to avoid repeated API hits during reruns.
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
