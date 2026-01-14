"""Utilities for building LLM prompts and calling the GitHub Models endpoint."""
from __future__ import annotations

import requests
import streamlit as st


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

    # Basic GitHub Models inference call; keep timeout short for UI responsiveness.
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        return msg.get("content", "No content returned")
    except Exception as exc:  # pragma: no cover - UI feedback only
        return f"LLM call failed: {exc}"


def build_prompt_from_snapshot(snapshot: dict, user_ctx) -> str:
    radar = snapshot.get("radar") or {}
    env = snapshot.get("environment") or {}
    comfort = snapshot.get("comfort") or {}
    weather = snapshot.get("weather") or {}
    weather_error = snapshot.get("weather_error")

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

    if weather:
        lines.append("Weather snapshot:")
        lines.extend(
            [
                f"- Condition: {weather.get('condition', 'unknown')}",
                f"- Temp: {weather.get('temperature_c', 'unknown')} C",
                f"- Feels like: {weather.get('feel_temperature_c', 'unknown')} C",
                f"- Humidity: {weather.get('humidity_pct', 'unknown')} %",
                f"- Pressure: {weather.get('pressure_hpa', 'unknown')} hPa",
                f"- Wind: {weather.get('wind_speed_ms', 'unknown')} m/s (gust {weather.get('wind_gust_ms', 'unknown')} m/s)",
                f"- Precip: {weather.get('precip_total_mm', 'unknown')} mm over {weather.get('precip_timeframe_min', 'unknown')} min",
                f"- Measured at: {weather.get('measured_iso', 'unknown')}",
            ]
        )
    elif weather_error:
        lines.append(f"Weather snapshot unavailable (error: {weather_error})")
    else:
        lines.append("Weather snapshot unavailable.")

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


def build_multi_user_prompt(sensor_row: dict | None, users_results: list, question: str) -> str:
    lines = []
    if question:
        lines.append(f"User question: {question}")
    
    lines.append("Environment Context:")
    if sensor_row:
        lines.extend([
            f"- Indoor Temp: {sensor_row.get('temperature_c', 'unknown')} C",
            f"- Indoor Humidity: {sensor_row.get('humidity_pct', 'unknown')} %",
            f"- CO2: {sensor_row.get('co2_ppm', 'unknown')} ppm",
            f"- People (radar): {sensor_row.get('people', 'unknown')}",
            f"- Weather: {sensor_row.get('weather_condition', 'unknown')}, {sensor_row.get('weather_temperature_c', 'unknown')} C (feels {sensor_row.get('weather_feel_temperature_c', 'unknown')} C)",
        ])
    else:
        lines.append("- No snapshot data available.")

    lines.append("\nIndividual Occupant Data:")
    if not users_results:
        lines.append("- No occupant feedback available.")
    else:
        for r in users_results:
            lines.append(f"- User {r['User ID']}:")
            lines.append(f"  * Activity: {r['Activity']}")
            lines.append(f"  * Clothing: {r['Clothing (Upper)']} / {r['Clothing (Lower)']}")
            lines.append(f"  * Current Comfort: PMV={r['PMV']}, PPD={r['PPD (%)']}%, UTCI={r['UTCI (C)']} C")

        # Averages
        avg_pmv = sum(r["PMV"] for r in users_results) / len(users_results)
        avg_ppd = sum(r["PPD (%)"] for r in users_results) / len(users_results)
        lines.append(f"\nGroup Averages:")
        lines.append(f"- Average PMV: {round(avg_pmv, 2)}")
        lines.append(f"- Average PPD: {round(avg_ppd, 1)}%")

    lines.append("\nTask:")
    lines.append("1. Provide precise, personalized recommendations for each user to improve their comfort (e.g., changing layers, moving location, adjusting personal fans).")
    lines.append("2. Provide a final summary for general HVAC/building-level adjustments (temperature, ventilation) that best balances the needs of all occupants.")
    lines.append("Be concise but specific.")
    
    return "\n".join(lines)
