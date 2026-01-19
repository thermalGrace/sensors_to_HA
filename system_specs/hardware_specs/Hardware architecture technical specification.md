# Thermal Grace — Hardware Architecture

> **Comfort-as-a-Service (CaaS) IoT System**

**Author:** Artur Kraskov  
**Course:** ICT & OL, Delta — Fontys 2025-2026  

---

## Overview

This document describes the hardware architecture of the **Thermal Grace** system — an MVP prototype for monitoring indoor thermal comfort. The system collects environmental data from distributed sensor nodes and streams it over MQTT to a central processing unit.

### Key Points

| Aspect | Summary |
|--------|---------|
| **Architecture** | Distributed wireless sensor nodes → MQTT → central Raspberry Pi 5 |
| **Sensor Nodes** | 2× Raspberry Pi Pico 2 W + 1× Raspberry Pi Zero 2 W |
| **Sensors** | BME680 (env), RD03D (radar), MTP40-F (CO₂), AMG8833 (thermal) |
| **Communication** | Wi-Fi + MQTT (topics: `sensors/pico/air_mmwave`, `sensors/pico/mtp40f/co2`, `sensors/thermal/amg8833`) |
| **Total Cost** | ~€160 |

---

## Table of Contents

1. [Introduction](#introduction)
2. [Hardware Architecture](#hardware-architecture)
3. [Hardware Components](#hardware-components)
4. [Sensor Usage & PMV/PPD Calculation](#sensor-usage)
5. [System Specifications](#system-specifications)
6. [Conclusion](#conclusion)
7. [References](#references)
8. [Appendix: Detailed Node Specifications](#appendix-detailed-node-specifications)

---

## Introduction

This document covers the design of a distributed IoT system for indoor thermal comfort monitoring. It details the microcontrollers, sensors, timing, resource usage, and performance characteristics.

### Background

The project plan (objectives, literature review, scope, risk analysis) is documented in [1]. User stories derived from the literature review defined the system requirements [2]. 

---

## Hardware Architecture

The architecture collects sensor data and processes it locally. Sensor nodes stream values over MQTT to a central Raspberry Pi 5 for processing and visualization.

![Hardware Architecture Diagram][image1]

### Design Rationale

| Decision | Reasoning |
|----------|-----------|
| **Multiple node types** | One sensor required C++ (no MicroPython library); the AMG8833 needed full Python (runs on Pi Zero 2 W) |
| **Wireless connectivity** | Enables modular kit — sensors can be relocated around the office for experiments |
| **I²C as primary bus** | Reliable, widely supported; UART used only where I²C unavailable |

---

## Hardware Components

| # | Role | Component | Price |
|---|------|-----------|-------|
| 1 | Central computer | Raspberry Pi 5 (8GB) | €75 |
| 2 | Sensor nodes (×2) | Raspberry Pi Pico 2 W | €7 ea. |
| 3 | Thermal sensor node | Raspberry Pi Zero 2 W | €17 |
| 4 | Occupancy/radar | Ai-Thinker RD-03D (24 GHz mmWave) | €7.50 |
| 5 | CO₂ | MTP40-F NDIR sensor | €17.25 |
| 6 | Environment | BME680 (temp, humidity, pressure, VOC) | €10.50 |
| 7 | Thermal imaging | Grove AMG8833 (8×8 IR array) | €26 |

**Total:** ~€160

> 📎 See datasheets: [Pico 2 W](https://datasheets.raspberrypi.com/pico/pico-2-product-brief.pdf) · [RD-03D](https://www.tinytronics.nl/product_files/007073_rd-03d_v1.0.0_specification20240103.pdf) · [MTP40-F](https://www.tinytronics.nl/product_files/004660_MTP40-F-CO2-sensor-module-single-channel.pdf) · [BME680](https://www.tinytronics.nl/en/sensors/air/pressure/bme680-sensor-module-with-level-converter-air-pressure-air-quality-humidity-temperature) · [AMG8833](https://www.seeedstudio.com/Grove-Infrared-Temperature-Sensor-Array-AMG8833.html)

---

## Sensor Usage

### PMV/PPD Calculation

Sensors are selected to provide the inputs required by the **PyThermalComfort** library's ISO 7730 PMV/PPD model.

```python
from pythermalcomfort.models import pmv_ppd_iso

result = pmv_ppd_iso(
    tdb=25,      # Dry-bulb air temperature (°C)
    tr=25,       # Mean radiant temperature (°C)
    vr=0.1,      # Relative air speed (m/s)
    rh=50,       # Relative humidity (%)
    met=1.4,     # Metabolic rate (met)
    clo=0.5,     # Clothing insulation (clo)
    model="7730-2005"
)
```

### Input Sources

| Parameter | Source | Notes |
|-----------|--------|-------|
| `tdb` (air temp) | BME680 via MQTT | Live |
| `tr` (radiant temp) | Assumed = `tdb` | Static assumption |
| `rh` (humidity) | BME680 via MQTT | Live |
| `vr` (air speed) | Hard-coded 0.1 m/s | Still indoor air |
| `met` (metabolic rate) | User feedback app | Falls back to 1.2 |
| `clo` (clothing) | User feedback app | Falls back to 0.7 |

**How PMV/PPD works:** PMV balances human heat gains/losses under steady-state conditions — skin heat loss via convection, radiation, sweat evaporation, respiration, and diffusion — then maps the balance to a scale from −3 (cold) to +3 (hot). PPD is derived via ISO exponential relation (even at PMV=0, ~5% are dissatisfied).

### Additional Sensors

| Sensor | Purpose |
|--------|---------|
| **CO₂, VOC, Pressure** | Additional context for analysis; fed to LLM alongside PMV/PPD |
| **mmWave Radar** | Indoor occupancy tracking (up to 3 targets); 2D coordinate output |
| **AMG8833 GRID-EYE** | 8×8 thermal heatmap; experimental people/temperature sensing |

---

## System Specifications

This section provides a quick reference for each sensor node. For detailed technical specifications (timing, protocols, payloads), see the [Appendix](#appendix-detailed-node-specifications).

### Air + mmWave Node (Pico 2 W)

> MicroPython edge node combining radar-based occupancy detection with environmental sensing.

| Aspect | Details |
|--------|---------|
| **MCU** | Raspberry Pi Pico 2 W (RP2350 + Wi-Fi) |
| **Firmware** | MicroPython |
| **Sensors** | RD03D mmWave radar (UART) + BME680 (I²C) |
| **MQTT Topic** | `sensors/pico/air_mmwave` |
| **Update Rate** | Up to 10 Hz (when targets detected) |

**What it measures:**
- 🎯 **Occupancy:** Detects up to 3 people with position (x, y), distance, angle, and speed
- 🌡️ **Environment:** Temperature, humidity, pressure, VOC/gas resistance

---

### CO₂ Node (Pico 2 W)

> C++ (PlatformIO) firmware for accurate CO₂ measurement using NDIR technology.

| Aspect | Details |
|--------|---------|
| **MCU** | Raspberry Pi Pico 2 W (RP2350 + Wi-Fi) |
| **Firmware** | C++ / Arduino (PlatformIO) |
| **Sensor** | MTP40-F NDIR (UART @ 9600 baud) |
| **MQTT Topic** | `sensors/pico/mtp40f/co2` |
| **Update Rate** | 0.4 Hz (every 2.5 seconds) |

**Why C++?** No MicroPython library exists for the MTP40-F sensor, so this node uses the Arduino ecosystem.

---

### Thermal Camera Node (Pi Zero 2 W)

> Full Python environment for 8×8 thermal imaging.

| Aspect | Details |
|--------|---------|
| **MCU** | Raspberry Pi Zero 2 W (Linux) |
| **Firmware** | Python 3 |
| **Sensor** | AMG8833 GRID-EYE (I²C) |
| **MQTT Topic** | `sensors/thermal/amg8833` |
| **Output** | 64-pixel (8×8) temperature array |

**Why Pi Zero?** The AMG8833 library requires full Python (not MicroPython), and the thermal array benefits from the extra processing power for potential heatmap analysis.

---

## Conclusion

The hardware architecture meets the requirements for a modular sensor kit:

- **Modular:** Sensors are easily mountable and swappable
- **Wireless:** Nodes can be relocated anywhere within Wi-Fi range
- **Cost-effective:** Total BOM ~€160
- **Extensible:** Additional nodes can be added by following the same MQTT pattern

---

## References

1. Kraskov A., Kaszuba B., (2025), *Vitality HUB Perceived Thermal Comfort | Project Plan*, Thermal Comfort-as-a-Service (CaaS) IoT system, FHICT Delta. [Online](https://drive.google.com/file/d/1BXHXlD4_SPatpJrU1mDwF0ZKnESl2W_U)
2. Kraskov A., Kaszuba B., (2025), *Vitality HUB Perceived Thermal Comfort | Requirements*, Thermal Comfort-as-a-Service (CaaS) IoT system, FHICT Delta. [Online](https://drive.google.com/file/d/1NooyuNM97BFz3jYOX2aPSRkbFZ7f5yJF)

---

## Appendix: Detailed Node Specifications

> This appendix provides in-depth technical details for developers working directly with the firmware or troubleshooting sensor nodes.

### A1. Air + mmWave Node — Technical Deep Dive

#### Pin Configuration

| Sensor | Bus | Pins | Settings |
|--------|-----|------|----------|
| RD03D Radar | UART0 | GP0 (TX), GP1 (RX) | 256000 baud |
| BME680 | I²C0 | GP5 (SCL), GP4 (SDA) | Default address 0x77 |

#### RD03D Radar Protocol

The radar operates in **multi-target mode**, detecting up to 3 people simultaneously.

| Property | Value |
|----------|-------|
| Frame size | 30 bytes |
| Header | `0xAA 0xFF` |
| Tail | `0x55 0xCC` |
| Per-target data | x, y (mm), speed (cm/s), distance (mm) |

**How it works:** The firmware waits up to 120 ms for a valid frame, polling the UART every 10 ms. Once a frame arrives, the code computes angle and distance for each target before publishing.

#### Timing & Performance

| Metric | Value | Explanation |
|--------|-------|-------------|
| Wi-Fi timeout | ~15 s | 30 attempts × 0.5 s spacing |
| Loop cadence | 20 ms | Base sleep between iterations |
| Radar timeout | 120 ms | Max wait for valid frame |
| Publish interval | ≥100 ms | Limits rate to 10 Hz max |
| End-to-end latency | <220 ms | Detection → MQTT publish |
| Payload size | 200–600 bytes | Depends on target count |

#### MQTT Contract

```
Broker:    192.168.x.x:1883 (no TLS)
Client ID: pico-mmwave-air
Topic:     sensors/pico/air_mmwave
QoS:       0 (fire-and-forget)
```

**Payload structure:**
```json
{
  "timestamp_ms": 123456,
  "radar": {
    "target_count": 2,
    "targets": [
      {"id": 0, "angle": 45, "distance_mm": 1500, "speed_cms": 10, "x_mm": 1060, "y_mm": 1060},
      {"id": 1, "angle": -30, "distance_mm": 2000, "speed_cms": 0, "x_mm": -1000, "y_mm": 1732}
    ]
  },
  "environment": {
    "temperature_c": 23.5,
    "humidity": 45,
    "pressure_hpa": 1013.25,
    "gas_kohm": 50.2
  }
}
```

#### Error Handling

| Scenario | Behavior |
|----------|----------|
| Wi-Fi disconnects | Client cleared, 2 s pause, reconnect on next loop |
| Sensor read fails | Returns `null` environment block; radar data still published |
| MQTT error | Same recovery as Wi-Fi drop |

---

### A2. CO₂ Node — Technical Deep Dive

#### Pin Configuration

| Sensor | Bus | Pins | Settings |
|--------|-----|------|----------|
| MTP40-F | UART (Serial1) | GP6 (RX), GP7 (TX) | 9600 baud |

#### Timing & Performance

| Metric | Value | Explanation |
|--------|-------|-------------|
| Sample interval | 2.5 s | CO₂ reading + publish cycle |
| LED feedback | 50 ms strobe | Visual indicator per sample |
| Wi-Fi timeout | 10 s | Connection deadline |
| Publish rate | ~0.4 Hz | One message every 2.5 s |
| Payload size | <64 bytes | Simple JSON structure |

#### MQTT Contract

```
Broker:    192.168.50.176:1883 (no TLS)
Client ID: pico2w-mtp40f
Topic:     sensors/pico/mtp40f/co2
QoS:       0
```

**Payload structure:**
```json
{"co2_ppm": 850}
```

---

### A3. Configuration Options

These settings can be adjusted in firmware for different deployment scenarios:

| Option | Default | How to Adjust |
|--------|---------|---------------|
| Publish interval | 100 ms | Increase `PUBLISH_INTERVAL_MS` to reduce network load or save power |
| QoS level | 0 | Use QoS 1 for guaranteed delivery (higher latency) |
| TLS | Disabled | Enable if deploying outside trusted LAN |
| BME680 oversampling | Library default | Adjust for accuracy vs. speed tradeoff |

---

### A4. Network Deployment Options

**Standard setup:** All nodes connect to the local Wi-Fi network and publish to an MQTT broker on the Raspberry Pi 5.

**Offline mode (no internet required):** The Pi 5 can act as a Wi-Fi Access Point:
- Sensor nodes connect directly to the Pi 5's network
- Use Ethernet on Pi 5 for any external connectivity needed
- Ideal for isolated deployments or demonstrations

> ⚠️ **Security note:** TLS and authentication are not configured by default. Deploy only on trusted networks, or enable credentials before production use.
