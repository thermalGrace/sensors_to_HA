# Pico 2 W mmWave + BME680 System Specification

## Scope
- Distributed edge node on Raspberry Pi Pico 2 W running MicroPython, pushing mmWave radar targets and BME680 environmental data to MQTT.
- Covers sensor/IO configuration, timing, resource use, performance expectations, and MQTT contract for downstream consumers.

## Sensors and Interfaces
- RD03D mmWave radar
  - Interface: UART0 at 256000 baud on GP0 (TX) / GP1 (RX); initialized in multi-target mode (up to 3 targets) during startup. Frame command bytes set on init; buffer cleared after mode switch. Reference: [mmWave_pico_2_w/rd03d.py#L22-L106](mmWave_pico_2_w/rd03d.py#L22-L106).
  - Frame format: 30 bytes, header 0xAA 0xFF, up to 3 targets, tail 0x55 0xCC. Each target provides x, y (mm), speed (cm/s), pixel_distance (mm); distance and angle are computed per target before publishing.
  - Update loop waits up to 120 ms for a valid frame; polls UART with 10 ms sleep between checks, trimming noise until header alignment.

- BME680 environmental sensor
  - Interface: I2C0 on GP5 (SCL) / GP4 (SDA) created at startup. Reference: [air_quality_mmWave_mqtt/main.py#L66-L99](air_quality_mmWave_mqtt/main.py#L66-L99).
  - Metrics read on each publish: temperature (°C/°F), humidity (%), pressure (hPa), gas resistance (kΩ). Read wrapped in try/except; failures return null env block.

## Timing and Scheduling
- Wi-Fi association attempts up to 30 times with 0.5 s spacing (≈15 s max) before giving up. Reference: [air_quality_mmWave_mqtt/main.py#L21-L35](air_quality_mmWave_mqtt/main.py#L21-L35).
- Main loop base cadence: 20 ms sleep per iteration. Reference: [air_quality_mmWave_mqtt/main.py#L70-L112](air_quality_mmWave_mqtt/main.py#L70-L112).
- Radar polling: `radar.update()` scans UART until a valid frame or a 120 ms timeout; only on success does the loop proceed to publish. Reference: [mmWave_pico_2_w/rd03d.py#L80-L106](mmWave_pico_2_w/rd03d.py#L80-L106).
- Publish guard: minimum spacing `PUBLISH_INTERVAL_MS = 100` (10 Hz max) measured from last successful publish, gated on radar data availability. Reference: [air_quality_mmWave_mqtt/main.py#L13-L102](air_quality_mmWave_mqtt/main.py#L13-L102).
- BME680 read occurs only when a publish is due, keeping sensor sampling aligned with publish cadence.
- Error handling: on MQTT/Wi-Fi exceptions, client is dropped, a 2 s pause is taken, and reconnect attempted next loop. Reference: [air_quality_mmWave_mqtt/main.py#L103-L112](air_quality_mmWave_mqtt/main.py#L103-L112).

## Resource Use and Performance
- Latency: worst-case detection-to-publish path ≈120 ms (radar frame wait) + up to 100 ms (publish guard) + MQTT send; target end-to-end <220 ms for radar-triggered packets.
- Throughput: up to 10 publishes/sec when radar frames stream continuously; bounded by radar availability and Wi-Fi/MQTT health.
- UART load: each radar frame 30 bytes; at 256000 baud transfers in ≈1 ms, well below the 120 ms frame wait budget.
- I2C load: single BME680 read per publish; negligible bus occupancy relative to 100 ms interval.
- MQTT payload size: JSON with timestamp + up to 3 targets + 5 BME fields; typical 200–600 bytes/publish → ~6 kB/s at 10 Hz plus MQTT overhead.
- Memory/CPU: stores at most 3 target objects and one payload dict; main loop includes 20 ms idle sleep and lightweight math, fitting comfortably within typical MicroPython heap and CPU headroom on Pico 2 W.

## MQTT Interface
- Broker: 192.168.50.176, TCP port 1883, no TLS, no auth (user/password None). Reference: [air_quality_mmWave_mqtt/main.py#L7-L16](air_quality_mmWave_mqtt/main.py#L7-L16).
- Client ID: `pico-mmwave-air`; keepalive 60 s; QoS 0 (default); retain flag not set. Reference: [air_quality_mmWave_mqtt/main.py#L7-L16](air_quality_mmWave_mqtt/main.py#L7-L16).
- Topic: sensors/pico/air_mmwave (bytes literal in code). Reference: [air_quality_mmWave_mqtt/main.py#L13-L16](air_quality_mmWave_mqtt/main.py#L13-L16).
- Payload structure (JSON):
  - `timestamp_ms`: MCU tick count (ms).
  - `radar`: `target_count` (0–3), `targets` list with per-target `id`, `angle` (deg), `distance_mm`, `speed_cms`, `x_mm`, `y_mm` as published in `build_radar_payload()`. Reference: [air_quality_mmWave_mqtt/main.py#L36-L98](air_quality_mmWave_mqtt/main.py#L36-L98).
  - `environment`: object with BME680 readings or null if read failed. Reference: [air_quality_mmWave_mqtt/main.py#L49-L99](air_quality_mmWave_mqtt/main.py#L49-L99).
- Session behavior: reconnects if Wi-Fi drops or MQTT errors occur; Wi-Fi rejoin clears the MQTT client so a fresh session is established on the next loop.

## Assumptions and Options
- BME680 oversampling/filter settings use library defaults; actual sample time depends on those defaults but is typically <100 ms.
- If network reliability is critical, consider QoS 1 and retained status beacons; current code uses QoS 0 for lowest latency.
- TLS is not configured; broker must be on trusted LAN. Add TLS and credentials if required by security policy.
- Publish rate can be lowered by increasing `PUBLISH_INTERVAL_MS` to reduce network use or power draw; radar still runs at UART frame rate.

## CO2 NDIR Node (MTP40F on Pico 2 W)
- Sensor: MTP40F NDIR CO2 module on UART Serial1 at 9600 baud, pins GP6 (RX from sensor TX) / GP7 (TX to sensor RX). Reference: [MTP40-F_air_qual_pres_temp/MTP40F_MQTT/src/main.cpp#L6-L153](MTP40-F_air_qual_pres_temp/MTP40F_MQTT/src/main.cpp#L6-L153).
- Timing: CO2 sample pulled every 2.5 s (`mtp.lastRead()` guard) and published immediately; LED strobes 50 ms per sample for operator feedback. Base loop otherwise free-runs; Wi-Fi status reported every 5 s. Reference: [MTP40-F_air_qual_pres_temp/MTP40F_MQTT/src/main.cpp#L169-L218](MTP40-F_air_qual_pres_temp/MTP40F_MQTT/src/main.cpp#L169-L218).
- Connectivity: Wi-Fi station joins with 10 s deadline and 200 ms poll interval; MQTT connect attempted after Wi-Fi success. No TLS or credentials. Reference: [MTP40-F_air_qual_pres_temp/MTP40F_MQTT/src/main.cpp#L42-L110](MTP40-F_air_qual_pres_temp/MTP40F_MQTT/src/main.cpp#L42-L110).
- MQTT: broker 192.168.50.176:1883, client ID `pico2w-mtp40f`, topic sensors/pico/mtp40f/co2, QoS 0/retain false (PubSubClient default), payload JSON `{"co2_ppm":<int>}` sized <64 bytes. Reference: [MTP40-F_air_qual_pres_temp/MTP40F_MQTT/src/main.cpp#L13-L137](MTP40-F_air_qual_pres_temp/MTP40F_MQTT/src/main.cpp#L13-L137).
- Performance: throughput ~0.4 Hz (one publish per 2.5 s), payload <100 bytes → <0.1 kB/s; network latency dominated by Wi-Fi/MQTT but bounded by 2.5 s sensor cadence. CPU/memory load minimal (single integer payload, small stack buffer).
- Reliability: If Wi-Fi disconnects, reconnect is attempted and MQTT session re-established before next publish; publishes are skipped when not connected. Consider adding retained heartbeat or QoS 1 if broker-side reliability is required.
