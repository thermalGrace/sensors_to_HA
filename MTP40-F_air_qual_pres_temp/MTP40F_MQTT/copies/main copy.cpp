#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "MTP40F.h"

// Wi-Fi credentials
const char *WIFI_SSID = "thermal_grace_iot_24";
const char *WIFI_PASSWORD = "45_#_101_G.";

// MQTT settings
const char *MQTT_HOST = "192.168.50.176";
const uint16_t MQTT_PORT = 1883;
const char *MQTT_CLIENT_ID = "pico2w-mtp40f";
const char *MQTT_TOPIC = "sensors/pico/mtp40f";

// Sensor UART pins
const uint8_t MTP40F_RX_PIN = 6;  // Pico GPIO 6 connects to MTP40F TX (pin 6)
const uint8_t MTP40F_TX_PIN = 7;  // Pico GPIO 7 connects to MTP40F RX (pin 7)

// Publish every 2.5s to stay within the sensor update interval
const unsigned long PUBLISH_INTERVAL_MS = 2500;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
MTP40F mtp(&Serial1);

unsigned long lastPublish = 0;
unsigned long lastHeartbeat = 0;

// Give the USB serial time to enumerate so early logs are visible
void waitForSerial(unsigned long timeoutMs = 4000)
{
  unsigned long start = millis();
  while (!Serial && (millis() - start) < timeoutMs)
  {
    delay(10);
  }

  Serial.println();
  Serial.println(Serial ? "USB serial ready" : "USB serial not detected, continuing");
}

// Emit a snapshot of current connectivity state to the serial monitor
void printStatus()
{
  Serial.println("===== STATUS =====");
  Serial.print("WiFi status: ");
  Serial.println(WiFi.status() == WL_CONNECTED ? "connected" : "not connected");

  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.print("  SSID: ");
    Serial.println(WIFI_SSID);
    Serial.print("  IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("  RSSI: ");
    Serial.println(WiFi.RSSI());
  }

  Serial.print("MQTT status: ");
  Serial.println(mqttClient.connected() ? "connected" : "not connected");
  Serial.print("MQTT host: ");
  Serial.print(MQTT_HOST);
  Serial.print(":");
  Serial.println(MQTT_PORT);
  Serial.print("MQTT topic: ");
  Serial.println(MQTT_TOPIC);
  Serial.println("==================");
}

bool ensureWifiConnected()
{
  if (WiFi.status() == WL_CONNECTED)
  {
    return true;
  }

  Serial.println("WiFi: connecting...");
  WiFi.disconnect(true);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - start) < 10000)
  {
    delay(200);
    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.print("WiFi: connected, IP=");
    Serial.println(WiFi.localIP());
    return true;
  }

  Serial.println("WiFi: failed to connect");
  return false;
}

bool ensureMqttConnected()
{
  if (mqttClient.connected())
  {
    return true;
  }

  mqttClient.setServer(MQTT_HOST, MQTT_PORT);

  if (!ensureWifiConnected())
  {
    return false;
  }

  Serial.print("MQTT: connecting to ");
  Serial.print(MQTT_HOST);
  Serial.print(":");
  Serial.println(MQTT_PORT);
  if (mqttClient.connect(MQTT_CLIENT_ID))
  {
    Serial.println("MQTT: connected");
    return true;
  }

  Serial.print("MQTT: connect failed, rc=");
  Serial.println(mqttClient.state());
  return false;
}

void publishReading()
{
  uint32_t co2 = mtp.getGasConcentration();
  unsigned long now = millis();

  // Simple JSON payload without ArduinoJson
  char payload[96];
  snprintf(payload, sizeof(payload), "{\"timestamp_ms\":%lu,\"co2_ppm\":%lu}", now, (unsigned long)co2);

  // Mirror what we plan to send in the serial monitor
  Serial.print("Sensor CO2 ppm: ");
  Serial.println((unsigned long)co2);
  Serial.print("Publishing payload: ");
  Serial.println(payload);

  if (!mqttClient.publish(MQTT_TOPIC, payload))
  {
    Serial.println("MQTT: publish failed");
  }
  else
  {
    Serial.print("MQTT: published -> ");
    Serial.println(payload);
  }
}

// Emit a slow heartbeat so the serial monitor shows liveness even if nothing publishes
void heartbeat()
{
  unsigned long now = millis();
  if (now - lastHeartbeat < 5000)
  {
    return;
  }

  lastHeartbeat = now;

  Serial.print("Heartbeat | WiFi: ");
  Serial.print(WiFi.status() == WL_CONNECTED ? "up" : "down");
  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.print(" IP=");
    Serial.print(WiFi.localIP());
  }

  Serial.print(" | MQTT: ");
  Serial.print(mqttClient.connected() ? "up" : "down");
  Serial.print(" | Topic: ");
  Serial.println(MQTT_TOPIC);
}

void setup()
{
  Serial.begin(115200);
  waitForSerial();
  Serial.println("\n\nBooting MTP40F MQTT client...");

  Serial1.setRX(MTP40F_RX_PIN);
  Serial1.setTX(MTP40F_TX_PIN);
  Serial1.begin(9600);

  mtp.begin();

  ensureWifiConnected();
  ensureMqttConnected();

  // Initial snapshot so the serial monitor shows configuration
  printStatus();
}

void loop()
{
  if (!ensureWifiConnected())
  {
    delay(500);
    return;
  }

  if (!ensureMqttConnected())
  {
    delay(500);
    return;
  }

  mqttClient.loop();

  // Always emit a heartbeat so you can see progress in the serial monitor
  heartbeat();

  unsigned long now = millis();
  if (now - lastPublish >= PUBLISH_INTERVAL_MS)
  {
    publishReading();
    lastPublish = now;
  }
}
