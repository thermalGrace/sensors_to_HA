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
