
# MTP40-F (NDIR CO2) on Pi Pico 2 W — PlatformIO firmware

This folder contains **C++ / Arduino-Pico** firmware projects (built with **PlatformIO**) for the **MTP40-F NDIR CO2 sensor** connected to a **Raspberry Pi Pico 2 W**.

There are two sub-projects:

- **MTP40-F/**: initial bring-up / demo firmware that reads CO2 and prints values over USB serial (UART sensor → Pico → USB serial).
- **MTP40F_MQTT/**: reads CO2 and publishes values over **MQTT** (Wi‑Fi on Pico 2 W).

## Repo layout

- `MTP40-F/`
	- `src/main.cpp`: UART read + serial print demo
	- `lib/MTP40F/`: sensor library (C++ sources)
	- `platformio.ini`: PlatformIO configuration for `rpipico2w`

- `MTP40F_MQTT/`
	- `src/main.cpp`: UART read + MQTT publish
	- `copies/`: scratch copies of working snippets (`working_mqtt_connection.cpp`, `working_sensor_uart.cpp`)
	- `platformio.ini`: PlatformIO config + dependencies (`PubSubClient`, `MTP40F`)

## Hardware wiring

### Sensor UART ↔ Pico 2 W

Both firmwares use `Serial1` at **9600 baud** to talk to the sensor.

The code comments indicate the intended pins:

- Pico GPIO **6** ← sensor TX
- Pico GPIO **7** → sensor RX

Notes:
- The current `main.cpp` files call `Serial1.begin(9600)` but do **not** explicitly set UART pins.
	- If your board/core default Serial1 pins are different, set them before `Serial1.begin(...)` (RP2040 Arduino core supports `Serial1.setRX(pin)` / `Serial1.setTX(pin)`).
- Ensure voltage levels are compatible with the sensor’s UART (often 3.3V logic; verify your module).

## MQTT firmware details (`MTP40F_MQTT/`)

### Configuration

Edit these constants in `MTP40F_MQTT/src/main.cpp`:

- `WIFI_SSID`, `WIFI_PASSWORD`
- `MQTT_HOST`, `MQTT_PORT`
- `MQTT_CLIENT_ID`
- `MQTT_TOPIC_CO2`

Default topic:

- `sensors/pico/mtp40f/co2`

### Published payload

The MQTT firmware publishes JSON:

```json
{"co2_ppm": 1234}
```

It prints debug logs to USB serial and blinks `LED_BUILTIN` on each publish.

## Building / flashing (PlatformIO)

Prereqs:

- VS Code + PlatformIO extension, or PlatformIO Core (`pio`) installed

### Build

From the project folder you want to build:

- `cd MTP40-F_air_qual_pres_temp/MTP40-F`
- or `cd MTP40-F_air_qual_pres_temp/MTP40F_MQTT`

Then:

- `pio run`

### Upload (flash)

- Plug the Pico 2 W in while holding **BOOTSEL** (or use your normal upload workflow).
- `pio run -t upload`

### Serial monitor

For the MQTT project, `monitor_speed` is set to **115200** in `platformio.ini`.

- `pio device monitor`

## Troubleshooting

- **No CO2 readings**: verify sensor UART wiring and that `Serial1` pins match your hardware.
- **Wi‑Fi connects but MQTT doesn’t**: confirm broker IP/port are reachable from the Pico’s subnet.
- **Nothing on MQTT topic**: subscribe from a LAN host:
	- `mosquitto_sub -h <broker-ip> -t sensors/pico/mtp40f/co2 -v`

