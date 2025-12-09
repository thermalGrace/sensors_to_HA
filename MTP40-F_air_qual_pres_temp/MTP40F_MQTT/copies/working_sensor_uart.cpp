

#include "MTP40F.h"

const int MTP40F_RX_PIN = 6;  // Pico GPIO 6 connects to MTP40F TX (pin 6)
const int MTP40F_TX_PIN = 7;  // Pico GPIO 7 connects to MTP40F RX (pin 7)

MTP40F mtp(&Serial1);

int lines = 10;


void setup()
{
  Serial1.begin(115200);
  Serial.println(__FILE__);
  Serial.print("MTP40F_LIB_VERSION:\t");
  Serial.println(MTP40F_LIB_VERSION);

 
  //  sws.begin(9600);
  Serial1.begin(9600);
  mtp.begin();

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
    Serial.print(mtp.getGasConcentration());
    Serial.println();
    lines++;
  }
}



//  -- END OF FILE --
