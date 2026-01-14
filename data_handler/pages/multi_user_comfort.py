"""Render helpers for the Multi-User Comfort page."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from thermal_comfort_model.comfort_calc import (
    all_users_context,
    compute_comfort,
    parse_env_from_payload,
)


def render_multi_user_comfort(snapshot: dict, placeholder: st.empty | None = None) -> None:
    if not placeholder:
        return

    with placeholder.container():
        st.subheader("Adaptive Multi-User Comfort Tracking")
        st.info("This page calculates comfort metrics for all individuals who have provided feedback, using the current indoor sensor data.")

        # 1. Get current environmental reading
        env_reading = parse_env_from_payload(snapshot)
        if not env_reading:
            st.warning("Waiting for environment data from MQTT (BME680)...")
            return

        # 2. Get all unique user contexts
        users = all_users_context()
        if not users:
            st.warning("No user feedback context found in responses.csv.")
            return

        # 3. Calculate comfort for each user
        results = []
        for uid, user in users.items():
            comfort = compute_comfort(env_reading, user)
            results.append({
                "User ID": uid[:8],  # Show short UID
                "Activity": user.activity,
                "Clothing (Upper)": user.clothing_upper,
                "Clothing (Lower)": user.clothing_lower,
                "PMV": comfort["pmv"],
                "PPD (%)": comfort["ppd"],
                "UTCI (C)": comfort["utci"],
                "MET": comfort["met"],
                "CLO": comfort["clo"],
            })

        # 4. Display as a table
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)

        # 5. Summary statistics
        if results:
            st.divider()
            st.subheader("Group Summary")
            avg_pmv = sum(r["PMV"] for r in results) / len(results)
            avg_ppd = sum(r["PPD (%)"] for r in results) / len(results)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Average PMV", round(avg_pmv, 2))
            col2.metric("Average PPD", f"{round(avg_ppd, 1)}%")
            col3.metric("Total Occupants", len(results))

            # Actionable insight (simplified for now, eventually for LLM)
            st.info(f"**Insight:** The group average PMV is {round(avg_pmv, 2)}. "
                    f"{'Heating is recommended' if avg_pmv < -0.5 else 'Cooling is recommended' if avg_pmv > 0.5 else 'Current settings are optimal for the group.'}")
