# Thermal Grace - System Architecture

This document describes the architecture of the **Thermal Grace** Perceived Thermal Comfort system using the [C4 model](https://c4model.com/).

## Level 1: System Context Diagram
This diagram shows the high-level system boundary and its interactions with users and external entities.

![System Context Diagram](thermal_grace_c4_lvl1.png)

## Level 2: Container Diagram
This diagram zooms into the **Thermal Grace System** to show its high-level executable units and data stores.

![Container Diagram](thermal_grace_c4_lvl2.png)

## Level 3: Component Diagram (Dashboard)
This diagram details the internal components of the **Data Handler Dashboard** container.

![Component Diagram](thermal_grace_c4_lvl3.png)



## 4. Component Details

### 4.1 Edge Devices (Raspberry Pi Pico 2 W + Pi Zero 2 W)

- **Pico 2 W (Air + mmWave node)**
   - **Hardware**: Raspberry Pi Pico 2 W (RP2350 + Wi‑Fi)
   - **Firmware**: MicroPython
   - **Sensors**:
      - BME680: temperature, humidity, pressure, VOC
      - RD03D mmWave radar: occupancy targets
   - **MQTT topic**: `sensors/pico/air_mmwave`

- **Pico 2 W (CO₂ node)**
   - **Hardware**: Raspberry Pi Pico 2 W (RP2350 + Wi‑Fi)
   - **Firmware**: Arduino‑Pico / PlatformIO
   - **Sensor**: MTP40‑F NDIR CO₂ (UART)
   - **MQTT topic**: `sensors/pico/mtp40f/co2`

- **Raspberry Pi Zero 2 W (Thermal node)**
   - **Hardware**: Raspberry Pi Zero 2 W
   - **Software**: Python
   - **Sensor**: AMG8833 GRID‑EYE (I²C)
   - **MQTT topic**: `sensors/thermal/amg8833`

- **Communication**: MQTT over Wi‑Fi
- **Power**: USB (5V)

### 4.2 MQTT Broker

- **Software**: Mosquitto (or HiveMQ)
- **Topics**:
   - `sensors/pico/air_mmwave` - Combined BME680 environment + mmWave radar payload
   - `sensors/pico/mtp40f/co2` - CO₂ ppm payload
   - `sensors/thermal/amg8833` - AMG8833 thermal grid payload

### 4.3 Data Handler (Python)

- **Location**: `data_handler/` directory
- **Functionality**:
   - Subscribe to MQTT topics (`sensors/pico/air_mmwave`, `sensors/pico/mtp40f/co2`)
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
  - **Weather Integration**: Real-time outdoor weather data

## 5. Data Flow

1. **Sensor Data Acquisition**:
   - Pico 2 W (Air + mmWave) reads BME680 + RD03D and publishes JSON to `sensors/pico/air_mmwave`
   - Pico 2 W (CO₂) reads MTP40‑F and publishes JSON to `sensors/pico/mtp40f/co2`
   - Pi Zero 2 W reads AMG8833 and publishes JSON to `sensors/thermal/amg8833`

2. **Data Processing**:
    - Data Handler subscribes to MQTT topics (`sensors/pico/air_mmwave`, `sensors/pico/mtp40f/co2`)
   - Sensor data is parsed and validated
    - Data is stored in CSV files:
       - `live_metrics.csv` - Time-series sensor readings
       - `responses.csv` - User feedback and comfort ratings

3. **Visualization and Analysis**:
   - Streamlit app polls Data Handler for latest data
   - **Multi-User Comfort**: Calculates PMV/PPD for all users
   - **LLM Assistant**: Generates insights using GitHub LLM
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

- **mmWave Radar**: Occupancy detection (target count)
- **BME680**: Comprehensive environmental monitoring
- **AMG8833 GRID‑EYE**: Thermal grid published on a separate Pi Zero 2 W

### 6.4 Weather Integration

- Fetches real-time outdoor weather data
- Calculates outdoor comfort metrics
- Provides comparative analysis between indoor and outdoor conditions

## 7. Technology Stack

- **Hardware**: Raspberry Pi Pico 2 W, Raspberry Pi Zero 2 W
- **Firmware**: MicroPython (Pico), Arduino‑Pico/PlatformIO (CO₂ node)
- **Communication**: MQTT (umqtt.simple / PubSubClient on devices, paho‑mqtt on backend)
- **Backend**: Python 3.x
- **Frontend**: Streamlit
- **Data Storage**: CSV files
- **AI/ML**: GitHub LLM API
- **Sensors**: BME680, RD03D mmWave, MTP40‑F CO₂, AMG8833 GRID‑EYE

## 8. Setup and Installation

### 8.1 Hardware Setup

1. Connect sensors to Raspberry Pi Pico 2 W:
   - BME680: I2C (SCL/SDA/VCC/GND)
   - RD03D mmWave Radar: UART (TX/RX/VCC/GND)
   - MTP40‑F CO₂: UART (TX/RX/VCC/GND)

2. Connect AMG8833 to Raspberry Pi Zero 2 W:
   - AMG8833: I2C (SDA/SCL/3.3V/GND)

3. Power the devices via USB

### 8.2 Software Setup

1. Install MicroPython on Pico 2 W (air + mmWave node)
2. Flash PlatformIO firmware to Pico 2 W (CO₂ node)
3. Install Data Handler dependencies:
   - `pip install streamlit paho-mqtt pandas requests buienradar pythermalcomfort`
4. Configure MQTT broker:
   - Update `HOST` / `PORT` in `data_handler/mqtt_monitor.py`
5. Configure GitHub LLM:
   - Set API token used by `data_handler/llm_utils.py`

### 8.3 Run the System

1. Start the Data Handler:
   `cd data_handler && streamlit run streamlit_app.py`
