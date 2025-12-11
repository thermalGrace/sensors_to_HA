import json
import time
import paho.mqtt.client as mqtt
from amg8833_i2c import AMG8833
import logging
import subprocess
import socket

# Configuration
MQTT_BROKER = "192.168.50.62"
MQTT_PORT = 1883
MQTT_USER = None
MQTT_PASSWORD = None
MQTT_CLIENT_ID = "rpi-thermal-camera"
MQTT_TOPIC = "sensors/thermal/amg8833"
MQTT_KEEPALIVE = 60
PUBLISH_INTERVAL_MS = 500  # 500ms for thermal camera (slower than radar)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_connected_to_network():
    """Check if device has network connectivity"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def wait_for_network(max_retries=30):
    """Wait for network connection"""
    for i in range(max_retries):
        if is_connected_to_network():
            logger.info("Network connected")
            return True
        logger.info(f"Waiting for network... ({i+1}/{max_retries})")
        time.sleep(1)
    logger.error("Network connection failed")
    return False

def grid_to_payload(pixels, thermistor_temp):
    """Convert AMG8833 thermal grid to JSON payload"""
    return {
        "timestamp_ms": int(time.time() * 1000),
        "thermistor_temp_c": round(thermistor_temp, 2),
        "pixels": [round(p, 2) for p in pixels],
        "grid_shape": [8, 8],
    }

class ThermalMQTTClient:
    def __init__(self):
        self.client = None
        self.connected = False
        self.sensor = None
        self.last_pub = 0

    def on_connect(self, client, userdata, flags, rc):
        """MQTT connect callback"""
        if rc == 0:
            self.connected = True
            logger.info("MQTT: connected")
        else:
            logger.error(f"MQTT: connection failed with code {rc}")

    def on_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback"""
        self.connected = False
        if rc != 0:
            logger.warning(f"MQTT: unexpected disconnection with code {rc}")

    def on_publish(self, client, userdata, mid):
        """MQTT publish callback"""
        pass  # Silent publish confirmation

    def connect_mqtt(self):
        """Initialize and connect MQTT client"""
        try:
            self.client = mqtt.Client(client_id=MQTT_CLIENT_ID)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish

            if MQTT_USER and MQTT_PASSWORD:
                self.client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

            logger.info("MQTT: connecting...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
            self.client.loop_start()
            
            # Wait for connection
            timeout = time.time() + 10
            while not self.connected and time.time() < timeout:
                time.sleep(0.1)
            
            return self.connected
        except Exception as exc:
            logger.error(f"MQTT connection error: {exc}")
            return False

    def disconnect_mqtt(self):
        """Disconnect MQTT client"""
        if self.client:
            self.client.loop_stop()
            try:
                self.client.disconnect()
            except Exception as e:
                logger.error(f"MQTT disconnect error: {e}")
            self.connected = False

    def publish(self, payload):
        """Publish payload to MQTT topic"""
        try:
            if self.connected:
                self.client.publish(MQTT_TOPIC, json.dumps(payload), qos=0)
                return True
        except Exception as exc:
            logger.error(f"MQTT publish error: {exc}")
            self.connected = False
        return False

    def init_sensor(self):
        """Initialize AMG8833 sensor"""
        try:
            t0 = time.time()
            while (time.time() - t0) < 2:
                try:
                    # Try address 0x69 first, fallback to 0x68
                    self.sensor = AMG8833(addr=0x69)
                    logger.info("AMG8833: initialized at address 0x69")
                    return True
                except Exception:
                    try:
                        self.sensor = AMG8833(addr=0x68)
                        logger.info("AMG8833: initialized at address 0x68")
                        return True
                    except Exception:
                        time.sleep(0.2)
            logger.error("AMG8833: sensor not found")
            return False
        except Exception as exc:
            logger.error(f"Sensor initialization error: {exc}")
            return False

    def run(self):
        """Main loop"""
        if not wait_for_network():
            logger.error("Cannot start without network")
            return

        if not self.init_sensor():
            logger.error("Cannot start without sensor")
            return

        if not self.connect_mqtt():
            logger.error("Cannot start without MQTT connection")
            return

        logger.info("Starting main loop...")
        reconnect_attempts = 0
        
        try:
            while True:
                try:
                    # Check network connectivity
                    if not is_connected_to_network():
                        logger.warning("Network lost, reconnecting...")
                        self.disconnect_mqtt()
                        if wait_for_network():
                            if not self.connect_mqtt():
                                logger.warning("MQTT reconnection failed, retrying...")
                                reconnect_attempts += 1
                                if reconnect_attempts > 5:
                                    logger.error("Too many reconnection attempts")
                                    break
                                time.sleep(5)
                        continue
                    
                    reconnect_attempts = 0

                    # Reconnect MQTT if needed
                    if not self.connected:
                        logger.info("MQTT reconnecting...")
                        if not self.connect_mqtt():
                            time.sleep(2)
                            continue

                    # Read sensor data
                    status, pixels = self.sensor.read_temp(64)
                    if status:
                        logger.warning("Sensor read error, retrying...")
                        continue

                    thermistor_temp = self.sensor.read_thermistor()

                    # Publish at interval
                    now = time.time() * 1000
                    if (now - self.last_pub) >= PUBLISH_INTERVAL_MS:
                        payload = grid_to_payload(pixels, thermistor_temp)
                        if self.publish(payload):
                            self.last_pub = now
                            logger.debug(f"Published: {thermistor_temp:.2f}°C")

                    time.sleep(0.05)

                except Exception as exc:
                    logger.error(f"Main loop error: {exc}")
                    self.connected = False
                    time.sleep(2)

        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.disconnect_mqtt()

if __name__ == "__main__":
    mqtt_app = ThermalMQTTClient()
    mqtt_app.run()