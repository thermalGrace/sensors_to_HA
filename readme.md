# Thermal Grace

## Perceived Thermal Comfort Application | Comfort-as-a-Service (CaaS)

Pico sensor nodes → MQTT → dashboard

[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-2%20W-C51A4A?logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com/products/raspberry-pi-pico-2/)
[![MicroPython](https://img.shields.io/badge/MicroPython-F7DF1E?logo=micropython&logoColor=000000)](https://micropython.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![C++](https://img.shields.io/badge/C%2B%2B-00599C?logo=cplusplus&logoColor=white)](https://isocpp.org/)
[![PlatformIO](https://img.shields.io/badge/PlatformIO-F5822A?logo=platformio&logoColor=white)](https://platformio.org/)
[![Arduino](https://img.shields.io/badge/Arduino-00979D?logo=arduino&logoColor=white)](https://www.arduino.cc/)
[![MQTT](https://img.shields.io/badge/MQTT-660066?logo=eclipse-mosquitto&logoColor=white)](https://mqtt.org/)
[![Processing](https://img.shields.io/badge/Processing-006699?logo=processingfoundation&logoColor=white)](https://processing.org/)

Presentation: [system_specs/Thermal Grace.pdf](system_specs/Thermal%20Grace.pdf)

Demo video: https://youtu.be/vrhQb1QjbCg (sensor values streaming, monitorng dashboard, PMV/PPD calcualtion, LLM assistant, mmWave radar 2D visualization, GRID-EYE heatmap over MQTT)

Updated functionalidy demo video: https://youtu.be/Dp8xyD23VpI (multi-user adaptive comfort, LLM assistant, weather integration, occupancy tracking)

A compact repo of **Raspberry Pi Pico 2 W** experiments and tooling:

- 📟 Firmware in **MicroPython** and **C++ (PlatformIO/Arduino-Pico)**
- 📡 Sensor streaming over **MQTT**
- 🖥️ A **Python / Streamlit** dashboard that merges indoor sensors, weather, and user feedback
- 👥 **Adaptive Multi-User Tracking**: Calculates personalized comfort (PMV/PPD/UTCI) for all occupants and computes group-level aggregate metrics.
- 🤖 **LLM Recommendations**: Provides targeted, personalized comfort advice per user and general HVAC summaries.

## ⚠️ Security Notice

**This codebase currently contains hardcoded MQTT credentials, IP addresses, login, and password for our lab network.** These will be removed soon. Always add your own credentials when deploying - currently safe keys handling is not implemented, consider updates for production use.

## Repo structure

Each folder is self-documented; start with the README inside the directory you care about.

- [data_handler/README.md](data_handler/README.md)
  - 🖥️ Python/Streamlit application: MQTT ingestion, weather API integration, comfort calculations, and user feedback workflow.

- [air_quality_mmWave_mqtt/README.md](air_quality_mmWave_mqtt/README.md)
  - 📡 MicroPython firmware (Pico 2 W) for environmental sensing + MQTT publishing.

- [bme680_air_quality_pi_pico_2_w/README.md](bme680_air_quality_pi_pico_2_w/README.md)
  - 🌡️ MicroPython BME680 driver + simple sensor bring-up test.

- [mmWave_pico_2_w/readme.md](mmWave_pico_2_w/readme.md)
  - 🛰️ RD03D mmWave radar experimentation: bring-up, MQTT-based streaming, and visualization tooling.

- [MTP40-F_CO2_sensor/readme.md](MTP40-F_CO2_sensor/readme.md)
  - 🧰 PlatformIO/C++ firmware for MTP40-F NDIR CO₂ sensing (demo + MQTT variant).

- [AMG_8833_Grid_eye](AMG_8833_Grid_eye)/
  - 🌡️ Code for AMG8833 Grid-EYE thermal sensor.

- [system_specs/](system_specs/)
  - 📐 System specifications, architecture notes, C4 diagrams, hardware specs, and planning requirements.
