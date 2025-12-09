#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>

// Wi-Fi credentials
const char *WIFI_SSID = "thermal_grace_iot_24";
const char *WIFI_PASSWORD = "45_#_101_G.";

// MQTT settings
const char *MQTT_HOST = "192.168.50.176";
const uint16_t MQTT_PORT = 1883;
const char *MQTT_CLIENT_ID = "pico2w-mtp40f";
const char *MQTT_TOPIC = "sensors/pico/mtp40f";

// Publish heartbeat every N milliseconds to prove end-to-end connectivity
const unsigned long PUBLISH_INTERVAL_MS = 5000;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

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

  // Optional: set clean session and no credentials; adapt if your broker needs auth
  if (mqttClient.connect(MQTT_CLIENT_ID))
  {
    Serial.println("MQTT: connected");
    return true;
  }

  Serial.print("MQTT: connect failed, rc=");
  Serial.println(mqttClient.state());
  return false;
}

void publishHeartbeat()
{
  unsigned long now = millis();

  char payload[96];
  snprintf(payload, sizeof(payload), "{\"timestamp_ms\":%lu,\"msg\":\"hello\",\"uptime_ms\":%lu}", now, now);

  Serial.print("Publishing heartbeat: ");
  Serial.println(payload);

  if (!mqttClient.publish(MQTT_TOPIC, payload))
  {
    Serial.println("MQTT: publish failed");
  }
  else
  {
    Serial.println("MQTT: published heartbeat");
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
    publishHeartbeat();
    lastPublish = now;
  }
}
