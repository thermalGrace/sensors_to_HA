# Pi Pico 2 W: 2× I2C sensors → MQTT (MicroPython)

This folder contains a MicroPython app for **Raspberry Pi Pico 2 W** that reads two sensors on **I2C**:

- **BME680** (temperature, humidity, pressure, gas resistance)
- **Second I2C sensor** (on the same bus, with its own I2C address)

…and publishes a combined JSON payload to an MQTT broker at a fixed interval.

## Files

- `main.py` – connects Wi‑Fi + MQTT, reads sensors, publishes JSON
- `bme680.py` – lightweight BME680 driver (derived from Adafruit, trimmed for MicroPython)
- `simple.py` – MQTT client library (MicroPython `umqtt.simple`-compatible)
- `rd03d.py` – legacy UART-based RD03D decoder (only needed if you still use that module)

## Hardware / wiring

### I2C bus (Pico I2C0)
`main.py` uses I2C **id=0** with:

- SDA: **GP4**
- SCL: **GP5**

Connect **both I2C sensors** to the same SDA/SCL lines (plus **3V3** and **GND**).

Notes:
- The driver defaults to I2C address **0x77** (`BME680_I2C(..., address=0x77)`)
- Some BME680 breakout boards use **0x76**; if yours does, change the address in `main.py` when constructing `BME680_I2C`.

### Second I2C sensor
- Make sure its I2C address does **not** conflict with the BME680 address.
- If the sensor supports multiple addresses (ADDR pin / solder jumper), set it accordingly.

## MicroPython dependencies

This project uses only standard MicroPython modules plus an MQTT client:

- Built-in modules: `machine`, `network`, `rp2`, `time`, `json`, `math`
- MQTT library: this folder includes `simple.py` (provides `MQTTClient`, `MQTTException`)

### Using the bundled MQTT client (`simple.py`)
Most Pico MicroPython builds do **not** ship with `umqtt` by default.

`main.py` currently imports MQTT like this:

```python
from umqtt.simple import MQTTClient, MQTTException
```

You now have `simple.py` in this folder. To satisfy the import, choose one of these options:

- Option A (no code changes): create an `umqtt/` folder on the Pico and place this file at `umqtt/simple.py`.
- Option B (simplest file layout): change the import in `main.py` to:

```python
from simple import MQTTClient, MQTTException
```

So the Pico filesystem should include either:

```
- `/umqtt/simple.py`

or:

- `/simple.py`
```

## Configuration (Wi‑Fi + MQTT)

For the project we set up the lab network and keep the keys in the files. Files are in private repo, the network will be removed after the end of the project. For production use more secure ways to handle login and password. 

Edit the constants at the top of `main.py`:

- `WIFI_SSID`, `WIFI_PASSWORD`
- `MQTT_BROKER`, `MQTT_PORT`
- `MQTT_USER`, `MQTT_PASSWORD` (set to `None` if not used)
- `MQTT_CLIENT_ID` (must be unique per device on your broker)
- `MQTT_TOPIC` (bytes string)
- `MQTT_KEEPALIVE`
- `PUBLISH_INTERVAL_MS`

Example:

```python
MQTT_BROKER = "192.168.50.176"
MQTT_TOPIC = b"sensors/pico/air_mmwave"
PUBLISH_INTERVAL_MS = 100
```

Country is set for the Wi‑Fi radio here:

```python
rp2.country("NL")
```

Change if needed.

## What gets published (MQTT payload)

Each publish is JSON combining readings from the connected sensors.

Topic:

- `sensors/pico/air_mmwave` (default)

Payload structure:

```json
{
  "timestamp_ms": 123456,
  "radar": { "...": "..." },
  "environment": {
    "temperature_c": 21.75,
    "temperature_f": 71.15,
    "humidity_pct": 45.2,
    "pressure_hpa": 1012.8,
    "gas_kohms": 12.34
  }
}
```

Notes:
- `environment` can be `null` if the BME680 read fails (`OSError`).
- If you’re not using the RD03D module, adapt/remove the `radar` portion of the payload in `main.py`.

## Running on the Pico

1. Flash MicroPython firmware for **Pico 2 W**.
2. Copy these files to the Pico:
   - `main.py`
   - `bme680.py`
  - `simple.py` (or place it as `umqtt/simple.py` — see notes above)
  - (optional) `rd03d.py` only if you use that module
3. Reboot the board.

You should see console logs like:

- `Wi‑Fi: (...)`
- `MQTT: connecting...`
- `MQTT publish: {...}`

## Debug / performance notes

- If you use `rd03d.py`, it has `DEBUG = True` which prints decoded targets and invalid frames. For steadier MQTT timing, set `DEBUG = False`.
- Publishing every `100ms` is aggressive for some brokers/Wi‑Fi networks; if you see disconnects, try `250`–`1000` ms.

## Troubleshooting

- **No MQTT messages**: verify broker IP/port, and that the Pico can reach it on Wi‑Fi.
- **ImportError: umqtt**: either place `simple.py` at `/umqtt/simple.py` or change the import to `from simple import ...`.
- **BME680 read failures**: check I2C wiring; confirm the address (`0x77` vs `0x76`).
