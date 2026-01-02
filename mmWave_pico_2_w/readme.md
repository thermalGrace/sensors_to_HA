# mmWave Pico 2 W (RD03D) — experiments, MQTT, brokers, visualizers

This folder is a collection of **debugging + experimental code** used while bringing up an **RD03D mmWave radar** on a **Raspberry Pi Pico 2 W**.

The work started with **UART-only** (printing/plotting over serial), then evolved to publishing structured target data over **MQTT** so it could be visualized and integrated elsewhere.

## What’s in here

### MicroPython (runs on Pico 2 W)

- `rd03d.py`
	- MicroPython UART decoder for RD03D frames.
	- Supports up to **3 targets** (multi-target mode).

- `code.py`
	- Early bring-up / debugging script.
	- Reads the radar and prints target values to the serial console.

- `main_radar_initial.py`
	- Minimal “CSV-like” serial output (angles/distances/speeds) for quick plotting/inspection.

- `main.py`
	- “UART → MQTT” bridge: reads RD03D targets and publishes JSON over MQTT.
	- Topic: `sensors/radar/targets`
	- Includes a periodic **heartbeat** publish (empty targets) when no radar targets are detected.

- `wifi_mqtt_diag.py`
	- Wi‑Fi + broker reachability diagnostics.
	- Scans SSIDs, connects Wi‑Fi, tests TCP to the broker, then publishes to `test/pico`.

### MQTT client library (MicroPython)

- `umqtt/simple.py`
	- Bundled MicroPython MQTT client used by the Pico scripts.
	- `main.py` and `wifi_mqtt_diag.py` import it as `from umqtt.simple import MQTTClient`.

### Broker (runs on your computer / Pi)

- `local_mqtt_broker.py`
	- A minimal local broker for quick testing.
	- Requires Python package `amqtt`.

Alternatively you can run Mosquitto (system service) on a Pi/host on your LAN.

### Visualizers (runs on your computer)

- `processing_mqtt_visuals.pde`
	- Processing sketch that subscribes to MQTT and draws the radar fan + up to 3 targets.
	- Can parse both the legacy payload (`{"targets": [...]}`) and a nested payload (`{"radar": {"targets": [...]}}`).

- `radar_visualizer.py`
	- Python visualizer using `paho-mqtt` + `matplotlib` (polar plot).
	- Subscribes to `sensors/radar/targets`.

## Hardware / wiring (RD03D → Pico 2 W)

`rd03d.py` uses UART **id=0** by default:

- Pico TX (GP0) → RD03D RX
- Pico RX (GP1) ← RD03D TX
- Baudrate: **256000**

Power the RD03D module according to your specific board variant.

## MQTT setup (summary)

The Pico publisher (`main.py`) is configured (edit constants at top of file):

- Broker: `192.168.50.176:1883`
- Client ID: `pico-radar`
- Topic: `sensors/radar/targets`
- Publish interval: 100 ms (when radar data updates)
- Heartbeat: publishes an empty `targets: []` periodically if no targets

Payload shape:

```json
{
	"timestamp_ms": 123456,
	"targets": [
		{
			"id": 1,
			"angle": 12.34,
			"distance_mm": 1870.5,
			"speed_cms": -3.2,
			"x_mm": 400,
			"y_mm": 1827
		}
	]
}
```

## How to run

### 1) Broker

- Option A: Mosquitto (recommended for “real” use)
	- Ensure it listens on `0.0.0.0:1883` (LAN reachable) and allows connections per your environment.

- Option B: local test broker
	- Install dependencies: `pip install amqtt`
	- Run: `python local_mqtt_broker.py`

### 2) Pico publisher

Copy these to the Pico:

- `main.py`
- `rd03d.py`
- `umqtt/simple.py` (keep the folder structure)

Reboot and watch the serial console for:

- Wi‑Fi connect logs
- `MQTT: connected`
- `MQTT publish targets: ...`

### 3) Visualize

- Processing: open `processing_mqtt_visuals.pde`, set `BROKER` and `TOPIC`, run.
- Python: `pip install paho-mqtt matplotlib` then run `python radar_visualizer.py`.

## Notes

- `processing_mqtt_visuals.pde` currently defaults to topic `sensors/pico/air_mmwave` (comment shows it used to be `sensors/radar/targets`). Make sure the topic matches the Pico script you’re running.
- If MQTT isn’t working, run `wifi_mqtt_diag.py` first to confirm the broker is reachable from the Pico.