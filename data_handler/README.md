# Data Handler / Dashboard

Streamlit dashboard that listens to MQTT topics from Pico 2W sensors, computes thermal comfort, and lets users ask an LLM for guidance. Sensor snapshots are persisted to CSV for later analysis and for the LLM prompt.

## Files and roles
- `streamlit_app.py` — Main Streamlit entry; sets up navigation, starts the MQTT listener thread, renders pages, and persists snapshots to `live_metrics.csv`.
- `mqtt_service.py` — MQTT consumer used by the dashboard; decodes payloads, computes comfort metrics, and updates shared state.
- `mqtt_monitor.py` — CLI-only monitor for the same topics, useful for quick debugging without the UI.
- `state.py` — Thread-safe shared state plus CSV helpers (`append_snapshot_to_csv`, `latest_sensor_row`, formatting utilities).
- `llm_utils.py` — Builds prompts from sensor/user context and calls the GitHub Models chat completions endpoint.
- `pages/live_metrics.py` — Renders the live metrics table and last raw payload view for the dashboard.
- `pages/llm_assistant.py` — Renders the LLM assistant page, wiring the question box, context tables, and one-shot LLM call.
- `thermal_comfort_model/comfort_calc.py` — Converts environment MQTT payloads into PMV/PPD/UTCI using pythermalcomfort, pulling latest user context from CSV.
- `thermal_comfort_model/test.py` — Tiny sanity check script for the comfort formulas.
- `user_feedback_app/app.py` — Streamlit survey that captures user comfort context (activity, clothing, etc.) into `user_feedback_app/responses.csv` for use by the model.
- `live_metrics.csv` — Appended by the dashboard when new MQTT data arrives; used by the LLM assistant for historical context.

## How pieces fit together
1. `streamlit_app.py` starts the UI and spawns `mqtt_service.ensure_mqtt_thread`, which subscribes to:
   - `sensors/pico/mtp40f/co2` (CO₂ ppm)
   - `sensors/pico/air_mmwave` (radar targets + environment)
2. Incoming payloads go through `mqtt_service.on_message`, which:
   - Updates shared state in `state.py`.
   - Derives comfort metrics via `thermal_comfort_model.compute_comfort` when environment data is present.
3. The Streamlit loop reads snapshots from `state.py` and:
   - Shows them on the **Live Metrics** page (`pages/live_metrics.py`).
   - Appends new snapshots to `live_metrics.csv` for persistence.
4. The **LLM Assistant** page (`pages/llm_assistant.py`) pulls the latest CSV row plus the most recent user context from `user_feedback_app/responses.csv`, builds a prompt with `llm_utils.build_prompt_from_csv`, and sends it via `llm_utils.call_github_llm`.
5. The standalone survey (`user_feedback_app/app.py`) provides the occupant context the comfort model and LLM rely on.
6. Optional: `mqtt_monitor.py` can be run separately to tail MQTT messages for debugging.

## Running
- Dashboard: `cd data_handler && streamlit run streamlit_app.py`
- User survey: `cd data_handler/user_feedback_app && streamlit run app.py`
- Comfort calculator CLI (logs comfort to stdout): `cd data_handler && python thermal_comfort_model/comfort_calc.py`
- MQTT CLI monitor: `cd data_handler && python mqtt_monitor.py`

Set `HOST`/`PORT` in `mqtt_monitor.py` and `mqtt_service.py` if your broker address changes. Provide `github_models_token` in `.streamlit/secrets.toml` for the LLM assistant.
