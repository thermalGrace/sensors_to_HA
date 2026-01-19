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

Presentation: https://drive.google.com/file/d/1HQB2eRdxE1k00cNu16dpNNQweOrkac1l

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

- system_specs/
  - 📐 System specification / architecture notes.
 

# Thermal Grace - System Architecture

This document describes the architecture of the **Thermal Grace** Perceived Thermal Comfort system using the [C4 model](https://c4model.com/).

## Level 1: System Context Diagram
This diagram shows the high-level system boundary and its interactions with users and external entities.

![System Context Diagram](system_specs/c4/thermal_grace_c4_lvl1.png)

## Level 2: Container Diagram
This diagram zooms into the **Thermal Grace System** to show its high-level executable units and data stores.

![Container Diagram](system_specs/c4/thermal_grace_c4_lvl2.png)

## Level 3: Component Diagram (Dashboard)
This diagram details the internal components of the **Data Handler Dashboard** container.

![Component Diagram](system_specs/c4/thermal_grace_c4_lvl3.png)



## 4. Component Details

### 4.1 Edge Devices (Raspberry Pi Pico W)

- **Hardware**: Raspberry Pi Pico W (RP2040 + WiFi)
- **Firmware**: MicroPython
- **Sensors Supported**:
  - BME680: Temperature, humidity, air pressure, VOC
  - mmWave Radar: Occupancy detection (2D)
  - GRID-EYE: Thermal imaging (heatmap)
- **Communication**: MQTT (paho-mqtt library)
- **Power**: USB-C (5V)

### 4.2 MQTT Broker

- **Software**: Mosquitto (or HiveMQ)
- **Topics**:
  - `sensors/pico1/bme680` - BME680 sensor data
  - `sensors/pico1/radar` - Radar occupancy data
  - `sensors/pico1/grideye` - GRID-EYE thermal data
  - `feedback/user` - User feedback from survey app

### 4.3 Data Handler (Python)

- **Location**: `data_handler/` directory
- **Functionality**:
  - Subscribe to MQTT topics
  - Parse sensor data
  - Store data in CSV files
  - Provide data to Streamlit app
  - Calculate PMV/PPD metrics
  - Integrate with external APIs

### 4.4 Streamlit Dashboard

- **Location**: `data_handler/` directory
- **Features**:
  - **Live Metrics**: Real-time sensor data display
  - **Multi-User Comfort**: Adaptive PMV/PPD for multiple users
  - **LLM Assistant**: AI-powered insights and recommendations
  - **Radar Visualization**: 2D occupancy heatmap
  - **Thermal Visualization**: GRID-EYE thermal heatmap
  - **Weather Integration**: Real-time outdoor weather data

## 5. Data Flow

1. **Sensor Data Acquisition**:
   - Pico W reads sensors (BME680, Radar, GRID-EYE)
   - Data is formatted as JSON
   - JSON is published to MQTT broker

2. **Data Processing**:
   - Data Handler subscribes to MQTT topics
   - Sensor data is parsed and validated
   - User feedback is processed from `feedback/user` topic
   - Data is stored in CSV files:
     - `sensor_data.csv` - Time-series sensor readings
     - `responses.csv` - User feedback and comfort ratings

3. **Visualization and Analysis**:
   - Streamlit app polls Data Handler for latest data
   - **Multi-User Comfort**: Calculates PMV/PPD for all users
   - **LLM Assistant**: Generates insights using GitHub LLM
   - **Radar Visualization**: Displays occupancy heatmap
   - **Thermal Visualization**: Displays thermal heatmap
   - **Weather Integration**: Fetches outdoor weather data

## 6. Key Features

### 6.1 Multi-User Adaptive Comfort

- Tracks comfort preferences for multiple users
- Calculates personalized PMV/PPD based on:
  - Air temperature
  - Relative humidity
  - Radiant temperature
  - Air velocity
  - Metabolic rate (activity level)
  - Clothing insulation
- Adapts to changing environmental conditions

### 6.2 LLM-Powered Insights

- Uses GitHub LLM for natural language explanations
- Provides actionable recommendations for comfort improvement
- Answers user questions about thermal comfort
- Analyzes multi-user feedback for group insights

### 6.3 Advanced Sensor Integration

- **mmWave Radar**: Occupancy detection with 2D visualization
- **GRID-EYE**: Thermal imaging with heatmap visualization
- **BME680**: Comprehensive environmental monitoring

### 6.4 Weather Integration

- Fetches real-time outdoor weather data
- Calculates outdoor comfort metrics
- Provides comparative analysis between indoor and outdoor conditions

## 7. Technology Stack

- **Hardware**: Raspberry Pi Pico W
- **Firmware**: MicroPython
- **Communication**: MQTT (paho-mqtt)
- **Backend**: Python 3.x
- **Frontend**: Streamlit
- **Data Storage**: CSV files
- **AI/ML**: GitHub LLM API
- **Sensors**: BME680, mmWave Radar, GRID-EYE

## 8. Setup and Installation

### 8.1 Hardware Setup

1. Connect sensors to Raspberry Pi Pico W:
   - BME680: I2C (SCL/SDA/VCC/GND)
   - mmWave Radar: GPIO (TX/RX/VCC/GND)
   - GRID-EYE: SPI (MOSI/MISO/SCK/CS/VCC/GND)

2. Power the Pico W via USB-C

### 8.2 Software Setup

1. Install MicroPython on Pico W
2. Install libraries:
   ```bash
   pip install paho-mqtt
   pip install bme680
   pip install adafruit-circuitpython-mlx90640
   ```

3. Install Data Handler dependencies:
   ```bash
   pip install streamlit paho-mqtt pandas requests
   ```

4. Configure MQTT:
   - Update `data_handler/mqtt_config.py` with broker details

5. Configure Weather API:
   - Get API key from OpenWeatherMap
   - Update `data_handler/weather_integration.py`

6. Configure GitHub LLM:
   - Get API token from GitHub
   - Update `data_handler/llm_utils.py`

### 8.3 Run the System

1. Start the Data Handler:
   `cd data_handler && streamlit run streamlit_app.py`
