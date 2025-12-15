"""Shared sensor state and CSV persistence helpers for the Streamlit app."""
from __future__ import annotations

import csv
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

SENSOR_CSV = Path(__file__).resolve().parent / "live_metrics.csv"

# Shared state guarded by a lock so the Streamlit thread can read safely.
# Shared dict mirrors the most recent MQTT payloads plus derived comfort metrics.
latest: Dict[str, Any] = {
    "co2_ppm": None,
    "radar": None,
    "environment": None,
    "comfort": None,
    "weather": None,
    "weather_error": None,
    "last_topic": None,
    "last_payload": None,
    "last_updated": None,
    "status": "disconnected",
}
state_lock = threading.Lock()


def update_state(**kwargs: Any) -> None:
    """Update shared state while keeping last_updated in sync."""
    with state_lock:
        latest.update(kwargs)
        latest["last_updated"] = time.time()


def get_snapshot() -> Dict[str, Any]:
    """Return a shallow copy of the latest state for safe reads."""
    with state_lock:
        return latest.copy()


def snapshot_to_row(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    radar = snapshot.get("radar") or {}
    env = snapshot.get("environment") or {}
    comfort = snapshot.get("comfort") or {}
    weather = snapshot.get("weather") or {}

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
        "weather_temperature_c": weather.get("temperature_c") if isinstance(weather, dict) else None,
        "weather_feel_temperature_c": weather.get("feel_temperature_c") if isinstance(weather, dict) else None,
        "weather_humidity_pct": weather.get("humidity_pct") if isinstance(weather, dict) else None,
        "weather_pressure_hpa": weather.get("pressure_hpa") if isinstance(weather, dict) else None,
        "weather_wind_speed_ms": weather.get("wind_speed_ms") if isinstance(weather, dict) else None,
        "weather_wind_gust_ms": weather.get("wind_gust_ms") if isinstance(weather, dict) else None,
        "weather_precip_total_mm": weather.get("precip_total_mm") if isinstance(weather, dict) else None,
        "weather_precip_timeframe_min": weather.get("precip_timeframe_min") if isinstance(weather, dict) else None,
        "weather_condition": weather.get("condition") if isinstance(weather, dict) else None,
        "weather_measured_iso": weather.get("measured_iso") if isinstance(weather, dict) else None,
    }


def append_snapshot_to_csv(snapshot: Dict[str, Any]) -> None:
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
        "weather_temperature_c",
        "weather_feel_temperature_c",
        "weather_humidity_pct",
        "weather_pressure_hpa",
        "weather_wind_speed_ms",
        "weather_wind_gust_ms",
        "weather_precip_total_mm",
        "weather_precip_timeframe_min",
        "weather_condition",
        "weather_measured_iso",
    ]
    exists = SENSOR_CSV.exists()
    with SENSOR_CSV.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def latest_sensor_row() -> Dict[str, Any] | None:
    if not SENSOR_CSV.exists():
        return None
    with SENSOR_CSV.open("r", newline="") as f:
        reader = list(csv.DictReader(f))
        if not reader:
            return None
        return reader[-1]


def format_ts(ts: float | None) -> str:
    if not ts:
        return "—"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
