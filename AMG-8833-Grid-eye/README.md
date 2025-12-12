
# AMG-8833 Thermal Camera - MQTT Integration

## Overview
This project implements a complete MQTT-based thermal camera system using the AMG8833 infrared sensor connected to a Raspberry Pi Zero 2W. The sensor data is published to an MQTT broker and can be visualized in real-time on any machine connected to the network.

## Components

### Hardware
- **Raspberry Pi Zero 2W** - Edge device running the MQTT publisher
- **AMG8833 Thermal Camera** - 8x8 thermal infrared sensor array
- **MQTT Broker** - Receives and distributes thermal data

### Software Architecture
- **Publisher**: `MQTT-protocol/AMG-8833--MQTT.py` - Runs on RPi Zero 2W
- **Display Client**: `AMG-8833-MQTT-broker-display-grid.py` - Visualization on main machine
- **Sensor Driver**: `amg8833_i2c.py` - Low-level I2C communication

## Setup & Installation

### On Raspberry Pi Zero 2W (Publisher)

#### 1. Install Dependencies
```bash
sudo apt-get update
sudo apt-get install python3-pip python3-smbus python3-dev
pip install paho-mqtt

cd /home/bartosz/Documents/ThermalGrace/sensors_to_HA/AMG-8833-Grid-eye
python3 MQTT-protocol/AMG-8833--MQTT.py

`
Network connected
AMG8833: initialized at address 0x69 (or 0x68)
MQTT: connecting...
MQTT: connected
Starting main loop...
`




Broker setup

sudo systemctl status thermal-mqtt.service