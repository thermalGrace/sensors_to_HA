#include <SIMPLE_MTP40F.h>

SimpleMTP40F sensor(&Serial1);

void setup()
{
  Serial1.begin(9600);
  Serial.println("Initializing sensor...");
}

void loop()
{
  uint32_t co2 = sensor.getFilteredPPM();

  Serial.print("CO2: ");
  Serial.print(co2);
  Serial.print(" ppm [");
  Serial.print(sensor.getAirQuality());
  Serial.println("]");

  delay(2000); // Standard reading interval
}