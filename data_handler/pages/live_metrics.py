"""Render helpers for the Live Metrics page."""
from __future__ import annotations

from typing import Any, Mapping

import streamlit as st


def render_live_metrics(snapshot: Mapping[str, Any], table_placeholder, raw_placeholder) -> None:
    radar = snapshot.get("radar") or {}
    env = snapshot.get("environment") or {}
    comfort = snapshot.get("comfort") or {}
    weather = snapshot.get("weather") or {}
    weather_error = snapshot.get("weather_error")
    co2_ppm = snapshot.get("co2_ppm")

    target_count = None
    if isinstance(radar, dict):
        target_count = radar.get("target_count")
        if target_count is None and isinstance(radar.get("targets"), list):
            target_count = len(radar.get("targets"))

    # Flatten nested dicts into a simple table for Streamlit display.
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
        {
            "metric": "Weather condition",
            "value": weather.get("condition", "—") if isinstance(weather, dict) else "—",
        },
        {
            "metric": "Weather temp (°C)",
            "value": weather.get("temperature_c", "—") if isinstance(weather, dict) else "—",
        },
        {
            "metric": "Feels like (°C)",
            "value": weather.get("feel_temperature_c", "—") if isinstance(weather, dict) else "—",
        },
        {
            "metric": "Weather humidity (%)",
            "value": weather.get("humidity_pct", "—") if isinstance(weather, dict) else "—",
        },
        {
            "metric": "Weather pressure (hPa)",
            "value": weather.get("pressure_hpa", "—") if isinstance(weather, dict) else "—",
        },
        {
            "metric": "Wind speed (m/s)",
            "value": weather.get("wind_speed_ms", "—") if isinstance(weather, dict) else "—",
        },
        {
            "metric": "Wind gust (m/s)",
            "value": weather.get("wind_gust_ms", "—") if isinstance(weather, dict) else "—",
        },
        {
            "metric": "Precip total (mm)",
            "value": weather.get("precip_total_mm", "—") if isinstance(weather, dict) else "—",
        },
        {
            "metric": "Precip window (min)",
            "value": weather.get("precip_timeframe_min", "—") if isinstance(weather, dict) else "—",
        },
        {
            "metric": "Weather status",
            "value": weather_error if weather_error else "ok" if weather else "—",
        },
    ]

    # Ensure consistent string values so Streamlit/Arrow don't attempt numeric casts on mixed columns.
    for row in table_rows:
        val = row.get("value")
        if val is None or val == "—":
            row["value"] = "—"
        elif isinstance(val, float):
            row["value"] = f"{val:.2f}"
        else:
            row["value"] = str(val)

    if table_placeholder:
        table_placeholder.table(table_rows)

    if raw_placeholder:
        with raw_placeholder:
            raw = snapshot.get("last_payload")
            if isinstance(raw, (dict, list)):
                st.json(raw)
            else:
                st.write(raw if raw is not None else "No payload yet")
