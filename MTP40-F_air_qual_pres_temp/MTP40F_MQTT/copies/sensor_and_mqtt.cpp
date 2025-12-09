// Linear flow: 1) show sensor locally, 2) connect Wi-Fi once, 3) connect MQTT once, 4) publish sensor every 2.5s with clear serial logs

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

// Publish every 2.5s
const unsigned long PUBLISH_INTERVAL_MS = 2500;
const unsigned long BLINK_INTERVAL_MS = 500;  // Hardware liveness indicator

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
MTP40F mtp(&Serial1);

unsigned long lastPublish = 0;
unsigned long lastBlink = 0;
bool ledState = false;

// Wait for serial enumeration so early logs are visible
void waitForSerial(unsigned long timeoutMs = 4000)
{
  unsigned long start = millis();
  while (!Serial && (millis() - start) < timeoutMs)
  {
    delay(10);
  }

  Serial.println();
  Serial.println(Serial ? "USB serial ready" : "USB serial not detected, continuing");
  Serial.flush();
}

bool connectWifiOnce()
{
  Serial.println("WiFi: connecting...");
  WiFi.disconnect(true);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - start) < 15000)
  {
    delay(200);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.print("WiFi connected, IP=");
    Serial.println(WiFi.localIP());
    return true;
  }

  Serial.println("WiFi failed");
  return false;
}

bool connectMqttOnce()
{
  mqttClient.setServer(MQTT_HOST, MQTT_PORT);

  Serial.print("MQTT: connecting to ");
  Serial.print(MQTT_HOST);
  Serial.print(":");
  Serial.println(MQTT_PORT);

  if (mqttClient.connect(MQTT_CLIENT_ID))
  {
    Serial.println("MQTT connected");
    return true;
  }

  Serial.print("MQTT failed, rc=");
  Serial.println(mqttClient.state());
  return false;
}

void publishSensor()
{
  uint32_t co2 = mtp.getGasConcentration();
  unsigned long now = millis();

  char payload[96];
  snprintf(payload, sizeof(payload), "{\"timestamp_ms\":%lu,\"co2_ppm\":%lu}", now, (unsigned long)co2);

  Serial.print("CO2 ppm: ");
  Serial.println((unsigned long)co2);
  Serial.print("MQTT payload: ");
  Serial.println(payload);

  if (!mqttClient.publish(MQTT_TOPIC, payload))
  {
    Serial.println("MQTT publish failed");
  }
  else
  {
    Serial.println("MQTT publish ok");
  }
}

void setup()
{
  Serial.begin(115200);
  waitForSerial();
  Serial.println("\nBooting linear sensor->WiFi->MQTT flow...");

  // Hardware liveness indicator (may be a no-op if LED_BUILTIN not wired)
#ifdef LED_BUILTIN
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
#endif

  // Sensor first
  Serial.println("Configuring UART for MTP40F...");
  Serial1.setRX(MTP40F_RX_PIN);
  Serial1.setTX(MTP40F_TX_PIN);
  Serial1.begin(9600);
  mtp.begin();
  Serial.println("MTP40F init done");

  // Show a couple sensor reads before networking
  for (int i = 0; i < 3; i++)
  {
    delay(300);
    uint32_t co2 = mtp.getGasConcentration();
    Serial.print("Startup CO2 read ");
    Serial.print(i);
    Serial.print(": ");
    Serial.println((unsigned long)co2);
  }

  // Wi-Fi once
  if (!connectWifiOnce())
  {
    Serial.println("Stopping: WiFi failed");
    return;
  }

  // MQTT once
  if (!connectMqttOnce())
  {
    Serial.println("Stopping: MQTT failed");
    return;
  }

  Serial.println("Setup complete. Streaming sensor over MQTT...");
}

void loop()
{
  // Blink LED for liveness even if serial is not visible
#ifdef LED_BUILTIN
  unsigned long nowBlink = millis();
  if (nowBlink - lastBlink >= BLINK_INTERVAL_MS)
  {
    ledState = !ledState;
    digitalWrite(LED_BUILTIN, ledState ? HIGH : LOW);
    lastBlink = nowBlink;
  }
#endif

  // If Wi-Fi or MQTT dropped, just log and halt publishes to keep it simple
  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.println("WiFi lost. Halt publishes.");
    delay(1000);
    return;
  }

  if (!mqttClient.connected())
  {
    Serial.println("MQTT lost. Halt publishes.");
    delay(1000);
    return;
  }

  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastPublish >= PUBLISH_INTERVAL_MS)
  {
    publishSensor();
    lastPublish = now;
  }
}
