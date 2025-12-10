This directory contains code and notes for debugging, testing and integrating various sensors for perceived thermal comfort in Home Asssistant. 

## MQTT Monitor

Run `python data_handler/mqtt_monitor.py` on the Raspberry Pi to watch the incoming MQTT messages from both Pico 2 W devices:

- subscribes to `sensors/pico/mtp40f/co2` and `sensors/pico/air_mmwave`
- prints a timestamped summary of CO₂ ppm, radar target counts, and environment data

Install the dependency if it is not already available:

```bash
pip install paho-mqtt
```

## Streamlit dashboard

For a simple live dashboard powered by the same MQTT topics:

```bash
pip install streamlit paho-mqtt
streamlit run data_handler/streamlit_app.py
```

The app reuses the broker settings from `data_handler/mqtt_monitor.py`, starts an MQTT listener in a background thread, and refreshes the displayed values every second.
