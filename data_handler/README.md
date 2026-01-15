# Data Handler / Dashboard

Streamlit dashboard that listens to MQTT topics from Pico 2W sensors, pulls outdoor weather from Buienradar, computes thermal comfort, and lets users ask an LLM for guidance. Sensor snapshots (including weather) are persisted to CSV for later analysis and for the LLM prompt.

## Files and roles
- `streamlit_app.py` — Main Streamlit entry; sets up navigation, starts the MQTT listener thread, renders pages, and persists snapshots to `live_metrics.csv`.
- `mqtt_service.py` — MQTT consumer used by the dashboard; decodes payloads, computes comfort metrics, and updates shared state.
- `mqtt_monitor.py` — CLI-only monitor for the same topics, useful for quick debugging without the UI.
- `state.py` — Thread-safe shared state plus CSV helpers (`append_snapshot_to_csv`, `latest_sensor_row`, formatting utilities).
- `llm_utils.py` — Builds prompts from sensor/user context (including multi-user data) and calls the GitHub Models chat completions endpoint.
- `uicomponents/live_metrics.py` — Renders the live metrics table and last raw payload view for the dashboard.
- `uicomponents/multi_user_comfort.py` — Renders the Adaptive Multi-User page, showing per-occupant comfort and group averages.
- `uicomponents/llm_assistant.py` — Renders the LLM assistant page, wiring the multi-user context and one-shot LLM call.
- `thermal_comfort_model/comfort_calc.py` — Converts environment MQTT payloads into PMV/PPD/UTCI. Includes logic for multi-user aggregation and result grouping.
- `thermal_comfort_model/test.py` — Tiny sanity check script for the comfort formulas.
- `user_feedback_app/app.py` — Streamlit survey that captures user comfort context (activity, clothing, etc.) into `user_feedback_app/responses.csv` for use by the model.
- `buienradar_data/query_current_state.py` — Buienradar fetch + parsing helpers, including a `weather_summary_from_state` helper.
- `weather_service.py` — Background thread that refreshes Buienradar weather every 7 minutes and pushes it into shared state.
- `live_metrics.csv` — Appended by the dashboard when new MQTT data arrives; includes outdoor weather columns and feeds the LLM assistant.

## How pieces fit together
1. `streamlit_app.py` starts the UI and spawns `mqtt_service.ensure_mqtt_thread`, which subscribes to:
   - `sensors/pico/mtp40f/co2` (CO₂ ppm)
   - `sensors/pico/air_mmwave` (radar targets + environment)
2. Incoming payloads go through `mqtt_service.on_message`, which:
   - Updates shared state in `state.py`.
   - Derives comfort metrics via `thermal_comfort_model.compute_comfort` when environment data is present.
3. In parallel, `weather_service` polls Buienradar every 7 minutes for the configured address and stores a compact weather snapshot in shared state.
3. The Streamlit loop reads snapshots from `state.py` and:
   - Shows them on the **Live Metrics** page (`pages/live_metrics.py`), grouped into Indoor, Comfort, and Weather sections.
   - Shows occupant-specific metrics and group averages on the **Adaptive Multi-User** page (`pages/multi_user_comfort.py`).
   - Appends new snapshots (including weather fields) to `live_metrics.csv` for persistence.
4. The **LLM Assistant** page (`pages/llm_assistant.py`) pulls the latest sensor data plus the collection of user feedback, builds a comprehensive multi-user prompt with `llm_utils.build_multi_user_prompt`, and sends it via `llm_utils.call_github_llm`.
5. The LLM provides **personalized recommendations** for each occupant and a **general summary** for building-level HVAC adjustments.
6. The standalone survey (`user_feedback_app/app.py`) provides the occupant context the comfort model and LLM rely on.
6. Optional: `mqtt_monitor.py` can be run separately to tail MQTT messages for debugging.

## Running
- Dashboard: `cd data_handler && streamlit run streamlit_app.py`
- User survey: `cd data_handler/user_feedback_app && streamlit run app.py`
- Comfort calculator CLI (logs comfort to stdout): `cd data_handler && python thermal_comfort_model/comfort_calc.py`
- MQTT CLI monitor: `cd data_handler && python mqtt_monitor.py`

Tip: if you run both Streamlit apps at the same time, give one of them a different port, e.g.:

- `streamlit run streamlit_app.py --server.port 8501`
- `streamlit run user_feedback_app/app.py --server.port 8502`

## Dependencies
This folder is a regular Python app (not MicroPython). You’ll typically want:

- `streamlit`
- `paho-mqtt`
- `requests`
- `buienradar`
- `pythermalcomfort`

Example install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install streamlit paho-mqtt requests buienradar pythermalcomfort
```

Weather fetch depends on the `buienradar` package (`pip install buienradar`). Configure the address and poll interval inside `weather_service.py` if needed. If `live_metrics.csv` pre-exists without headers, the app will rewrite it once to add the expected header row (including weather columns).

Set `HOST`/`PORT` in `mqtt_monitor.py` and `mqtt_service.py` if your broker address changes. Provide `github_models_token` in `.streamlit/secrets.toml` for the LLM assistant.

## Configuration notes

### MQTT

The MQTT broker host/port and topics are defined in `mqtt_monitor.py` and imported by `mqtt_service.py`.
If your broker changes, edit:

- `HOST`, `PORT` and `TOPICS` in `mqtt_monitor.py`

Current topics consumed by the dashboard:

- `sensors/pico/mtp40f/co2`
- `sensors/pico/air_mmwave`

### Weather (Buienradar)

- Poll interval is controlled by `POLL_SECONDS` in `weather_service.py`.
- The default address is `DEFAULT_ADDRESS` in `buienradar_data/query_current_state.py`.
   - If you want a different location, edit `DEFAULT_ADDRESS` or pass a custom `address=` into `ensure_weather_thread(...)`.

### LLM assistant (GitHub Models)

The assistant uses GitHub Models via `llm_utils.call_github_llm()` and expects a token in Streamlit secrets.
Create:

- `.streamlit/secrets.toml`

With:

```toml
github_models_token = "YOUR_TOKEN_HERE"
```

The model configured in code is currently `openai/gpt-4.1`.
