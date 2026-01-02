"""Background task to poll Buienradar weather and push it into shared state."""
from __future__ import annotations

import threading
import time
from typing import MutableMapping

import requests

from buienradar_data.query_current_state import (
    DEFAULT_ADDRESS,
    fetch_current_state,
    geocode,
    weather_summary_from_state,
)
from state import update_state

POLL_SECONDS = 7 * 60  # refresh every 7 minutes
TIMEFRAME_MIN = 45  # precipitation lookahead window


def _weather_loop(address: str = DEFAULT_ADDRESS) -> None:
    session = requests.Session()
    latitude = longitude = None

    while True:
        try:
            if latitude is None or longitude is None:
                latitude, longitude = geocode(address, session)

            state = fetch_current_state(latitude, longitude, TIMEFRAME_MIN)
            summary = weather_summary_from_state(state)
            update_state(weather=summary, weather_error=None)
        except Exception as exc:  # keep running even if Buienradar/Nominatim hiccups
            update_state(weather_error=str(exc))

        time.sleep(POLL_SECONDS)


def ensure_weather_thread(session_state: MutableMapping[str, object], address: str = DEFAULT_ADDRESS) -> None:
    """Start the weather polling loop once per Streamlit session."""

    if session_state.get("weather_thread"):
        return

    t = threading.Thread(target=_weather_loop, kwargs={"address": address}, daemon=True)
    t.start()
    session_state["weather_thread"] = t
