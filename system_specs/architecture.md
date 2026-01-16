graph TD
    %% Components
    subgraph "Edge Devices (Pico W)"
        Pico1[Raspberry Pi Pico W 1]
        Pico2[Raspberry Pi Pico W 2]
        PicoN[Raspberry Pi Pico W N]
    end

    subgraph "Sensors"
        BME680[BME680 (Temp/Humidity/VOC)]
        Radar[mmWave Radar (Occupancy)]
        GridEye[GRID-EYE (Thermal)]
    end

    subgraph "Communication"
        MQTTBroker[MQTT Broker (Mosquitto)]
    end

    subgraph "Data Processing"
        DataHandler[Data Handler (Python)]
        CSVStore[CSV Storage (responses.csv, sensor_data.csv)]
    end

    subgraph "User Interface"
        StreamlitApp[Streamlit Dashboard]
        MultiUser[Multi-User Comfort]
        LLMAssistant[LLM Assistant]
        RadarViz[Radar Visualization]
        ThermalViz[Thermal Visualization]
    end

    subgraph "External Services"
        WeatherAPI[Weather API]
        GitHubLLM[GitHub LLM]
    end

    %% Connections
    Pico1 -->|I2C/SPI| BME680
    Pico1 -->|GPIO| Radar
    Pico1 -->|SPI| GridEye
    Pico1 -->|MQTT| MQTTBroker
    Pico2 -->|I2C/SPI| BME680
    PicoN -->|I2C/SPI| BME680

    MQTTBroker -->|Publish| DataHandler
    DataHandler -->|Store| CSVStore
    DataHandler -->|Serve| StreamlitApp

    StreamlitApp -->|REST API| WeatherAPI
    StreamlitApp -->|Query| GitHubLLM

    StreamlitApp -->|Render| MultiUser
    StreamlitApp -->|Render| LLMAssistant
    StreamlitApp -->|Render| RadarViz
    StreamlitApp -->|Render| ThermalViz
```

## 3. Component Details

### 3.1 Edge Devices (Raspberry Pi Pico W)

- **Hardware**: Raspberry Pi Pico W (RP2040 + WiFi)
- **Firmware**: MicroPython
- **Sensors Supported**:
  - BME680: Temperature, humidity, air pressure, VOC
  - mmWave Radar: Occupancy detection (2D)
  - GRID-EYE: Thermal imaging (heatmap)
- **Communication**: MQTT (paho-mqtt library)
- **Power**: USB-C (5V)

### 3.2 MQTT Broker

- **Software**: Mosquitto (or HiveMQ)
- **Topics**:
  - `sensors/pico1/bme680` - BME680 sensor data
  - `sensors/pico1/radar` - Radar occupancy data
  - `sensors/pico1/grideye` - GRID-EYE thermal data
  - `feedback/user` - User feedback from survey app

### 3.3 Data Handler (Python)

- **Location**: `data_handler/` directory
- **Functionality**:
  - Subscribe to MQTT topics
  - Parse sensor data
  - Store data in CSV files
  - Provide data to Streamlit app
  - Calculate PMV/PPD metrics
  - Integrate with external APIs

### 3.4 Streamlit Dashboard

- **Location**: `data_handler/` directory
- **Features**:
  - **Live Metrics**: Real-time sensor data display
  - **Multi-User Comfort**: Adaptive PMV/PPD for multiple users
  - **LLM Assistant**: AI-powered insights and recommendations
  - **Radar Visualization**: 2D occupancy heatmap
  - **Thermal Visualization**: GRID-EYE thermal heatmap
  - **Weather Integration**: Real-time outdoor weather data

## 4. Data Flow

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

## 5. Key Features

### 5.1 Multi-User Adaptive Comfort

- Tracks comfort preferences for multiple users
- Calculates personalized PMV/PPD based on:
  - Air temperature
  - Relative humidity
  - Radiant temperature
  - Air velocity
  - Metabolic rate (activity level)
  - Clothing insulation
- Adapts to changing environmental conditions

### 5.2 LLM-Powered Insights

- Uses GitHub LLM for natural language explanations
- Provides actionable recommendations for comfort improvement
- Answers user questions about thermal comfort
- Analyzes multi-user feedback for group insights

### 5.3 Advanced Sensor Integration

- **mmWave Radar**: Occupancy detection with 2D visualization
- **GRID-EYE**: Thermal imaging with heatmap visualization
- **BME680**: Comprehensive environmental monitoring

### 5.4 Weather Integration

- Fetches real-time outdoor weather data
- Calculates outdoor comfort metrics
- Provides comparative analysis between indoor and outdoor conditions

## 6. Technology Stack

- **Hardware**: Raspberry Pi Pico W
- **Firmware**: MicroPython
- **Communication**: MQTT (paho-mqtt)
- **Backend**: Python 3.x
- **Frontend**: Streamlit
- **Data Storage**: CSV files
- **AI/ML**: GitHub LLM API
- **Sensors**: BME680, mmWave Radar, GRID-EYE

## 7. Setup and Installation

### 7.1 Hardware Setup

1. Connect sensors to Raspberry Pi Pico W:
   - BME680: I2C (SCL/SDA/VCC/GND)
   - mmWave Radar: GPIO (TX/RX/VCC/GND)
   - GRID-EYE: SPI (MOSI/MISO/SCK/CS/VCC/GND)

2. Power the Pico W via USB-C

### 7.2 Software Setup

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

### 7.3 Run the System

1. Start the Data Handler:
   