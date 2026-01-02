#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "MTP40F.h"

const int MTP40F_RX_PIN = 6;  // Pico GPIO 6 connects to MTP40F TX (pin 6)
const int MTP40F_TX_PIN = 7;  // Pico GPIO 7 connects to MTP40F RX (pin 7)

// Wi-Fi credentials
const char *WIFI_SSID = "thermal_grace_iot_24";
const char *WIFI_PASSWORD = "45_#_101_G.";

// MQTT settings
const char *MQTT_HOST = "192.168.50.176";
const uint16_t MQTT_PORT = 1883;
const char *MQTT_CLIENT_ID = "pico2w-mtp40f";
const char *MQTT_TOPIC_CO2 = "sensors/pico/mtp40f/co2";

MTP40F mtp(&Serial1);
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

int lines = 10;
unsigned long lastWifiReport = 0;
const unsigned long WIFI_REPORT_MS = 5000;

const char *statusToString(int s)
{
  switch (s)
  {
  case WL_IDLE_STATUS: return "WL_IDLE_STATUS";
  case WL_NO_SSID_AVAIL: return "WL_NO_SSID_AVAIL";
  case WL_SCAN_COMPLETED: return "WL_SCAN_COMPLETED";
  case WL_CONNECTED: return "WL_CONNECTED";
  case WL_CONNECT_FAILED: return "WL_CONNECT_FAILED";
  case WL_CONNECTION_LOST: return "WL_CONNECTION_LOST";
  case WL_DISCONNECTED: return "WL_DISCONNECTED";
  default: return "UNKNOWN";
  }
}

bool ensureWifiConnected()
{
  if (WiFi.status() == WL_CONNECTED)
  {
    return true;
  }

  Serial.print("WiFi: connecting to ");
  Serial.println(WIFI_SSID);

  Serial.print("WiFi status before begin: ");
  Serial.println(statusToString(WiFi.status()));

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
    Serial.print("WiFi MAC: ");
    Serial.println(WiFi.macAddress());
    return true;
  }

  Serial.println("WiFi: failed to connect");
  Serial.print("WiFi status now: ");
  Serial.println(statusToString(WiFi.status()));
  return false;
}

bool ensureMqttConnected()
{
  if (mqttClient.connected())
  {
    return true;
  }

  if (!ensureWifiConnected())
  {
    return false;
  }

  mqttClient.setServer(MQTT_HOST, MQTT_PORT);

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

void publishCo2(int ppm)
{
  if (!mqttClient.connected())
  {
    if (!ensureMqttConnected())
    {
      Serial.println("MQTT: cannot publish, not connected");
      return;
    }
  }

  char payload[64];
  snprintf(payload, sizeof(payload), "{\"co2_ppm\":%d}", ppm);

  if (mqttClient.publish(MQTT_TOPIC_CO2, payload))
  {
    Serial.print("MQTT: published CO2 to ");
    Serial.print(MQTT_TOPIC_CO2);
    Serial.print(" -> ");
    Serial.println(payload);
  }
  else
  {
    Serial.println("MQTT: publish failed");
  }
}


void setup()
{
  Serial.begin(115200);
  delay(100); // allow USB CDC to enumerate

  Serial.println(__FILE__);
  Serial.print("MTP40F_LIB_VERSION:\t");
  Serial.println(MTP40F_LIB_VERSION);

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  Serial1.begin(9600);
  mtp.begin();

  ensureWifiConnected();
  Serial.println("WiFi init attempt completed");

  ensureMqttConnected();
  Serial.println("MQTT init attempt completed");

  // if (mtp.begin() == false)
  // {
  //   Serial.println("could not connect!");
  //   while(1);
  // }

}


void loop()
{
  if (lines == 10)
  {
    lines = 0;
    Serial.println("\nTIME\tCO2 LEVEL");
  }

  if (millis() - mtp.lastRead() >= 2500)
  {
    Serial.print(millis());
    Serial.print("\t");
    int ppm = mtp.getGasConcentration();
    Serial.print(ppm);
    Serial.println();
    digitalWrite(LED_BUILTIN, HIGH);
    delay(50);
    digitalWrite(LED_BUILTIN, LOW);
    lines++;

    publishCo2(ppm);
  }

  // Periodic Wi-Fi status report
  if (millis() - lastWifiReport >= WIFI_REPORT_MS)
  {
    lastWifiReport = millis();
    Serial.print("WiFi status periodic: ");
    Serial.println(statusToString(WiFi.status()));
    if (WiFi.status() != WL_CONNECTED)
    {
      ensureWifiConnected();
    }
    else
    {
      if (!mqttClient.connected())
      {
        ensureMqttConnected();
      }
    }
  }

  if (mqttClient.connected())
  {
    mqttClient.loop();
  }
}



//  -- END OF FILE --
