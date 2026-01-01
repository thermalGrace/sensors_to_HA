***

# SimpleMTP40F Library

## 1. High-Level Overview
The SimpleMTP40F library is a C++ interface for the MTP40F NDIR (Non-Dispersive Infrared) CO2 sensor. It focuses on reliable CO2 ppm aquisition and air quality interpretation.

*   Supported Hardware: MTP40F CO2 Sensor 
*   Communication Protocol: UART (Serial) at 9600 baud.
*   Measurement Range: 400 ppm to 2000 ppm
*   Update Frequency: Internal sensor refresh rate is once every 2 seconds.

## 2. Integration & Dependencies
This library is designed for the Arduino ecosystem but is portable to any system supporting the `Stream` class.

*   **Hardware Requirements:**
    *   Voltage: 4.2V – 5.5V (5V recommended for stable NDIR lamp operation).
    *   Current: ~30mA average, with peaks up to 150mA during infrared pulsing.
    *   Logic Levels: Has a 3.3V output.
*   **Software Dependencies:** 
    *   Requires `Arduino.h`.
    *   Uses `Stream` class for dependency injection (works with `HardwareSerial` and `SoftwareSerial`).

## 3. The Function Prototypes

### `SimpleMTP40F(Stream *stream)`
Constructor.
*   **Parameters:** Pointer to a Serial object (e.g., `&Serial1` or `&mySoftwareSerial`).
*   **Thread Safety:** Not thread-safe. Ensure only one task accesses the serial port at a time.

### `uint32_t getPPM()`
Requests the CO2 concentration.
*   **Return Values:** 
    *   `uint32_t`: CO2 concentration in parts per million (ppm).
    *   `0`: Indicates a communication timeout or Checksum (CRC) failure.
*   **Note:** Implements an internal 2-second rate-limiter to prevent sensor "spamming."

### `uint32_t in getFilteredPPM()`
Requests the CO2 concentration after applying the exponential moving average filter on it. you can change the amount of filtering by tinkering with the "_alpha" variable in the header file.

*   **Return Values:** 
    *   `uint32_t`: CO2 ppm after applying Exponential moving average.
    *   `0`: Indicates a communication timeout or Checksum (CRC) failure.

### `uint32_t setAirPressureReference(int apr)`
Sets pressure which sensor will use to calculate the ppm of CO2.

*   Parameters: apr: Ambient pressure in hPa (Range: 700–1100).

*   **Return Values:** 
    
    * `true`: on success. 
    
    * `false`: on communication failure.

### `bool setSinglePointCorrection(uint32_t spc)`
In case the sensor malfunctions and shows incorrect values you could manually change the referance point of the sensor. Bring sensor to a place with known ppm value and run the function with the ppm entered in as a parameter. To check if function finished utelize function "getSinglePointCorrectionReady".

*   Parameters: ppm: The target concentration (typically 400 for fresh outside air).

*   **Return Values:** 

    * `true`: if command was accepted by the sensor
    
    * `false`: on communication failure.

### `bool getSinglePointCorrectionReady()`
Checks if the setting of the single point correction is finished.

*   **Return Values:**
 
    *   `true`: Calibration complete.

    *   `false`: Still in progress or request failed.

**Provides a human-readable interpretation of the last valid reading.**
*   **Return Values:** 
    *   `"Good"` (< 800 ppm)
    *   `"stuffy"` (800 - 1200 ppm)
    *   `"Poor"` (1200 - 2000 ppm)
    *   `"Hazardous"` (> 2000 ppm)
    *   `"Waiting..."`: If no valid reading has been taken yet.

## 4. Hardware Connection table

| MTP40F Pin | Description | 
| :--- | :--- |
| **G+ Pin 1 (Vin)** | 5V Power |
| **G0 Pin 2 (GND)** | Ground | 
| **RxD Pin 6 (RX)** | Data In |  
| **TxD Pin 7 (TX)** | Data Out |

![alt text](image-1.png)
> **Warning:** Always cross-link RX to TX.

## 5. Typical Operation Flow
1.  **Initialization:** Initialize Serial connection.
2.  **Data Acquisition:** Use one of the "GetPPM" methods in your main `loop()`. The library handles the 4-byte reconstruction (bit-shifting) of the sensor output.
3.  **Error Handling:** The library uses an **Additive Checksum (CRC)**. If the sum of the 14-byte response does not match the checksum sent by the sensor, the library rejects the data to prevent "phantom" high readings caused by electrical noise.
4.  **Air pressure configuration:** Sensor default atmospheric pressure is set to 1013 hPa, if your hPa value in your area drastically differs form default, You can change it by using setAirPressure method with your hPa value as parameter.


## 6. Calibration & Maintenance
**Functions**
*   **AirPressure Reference:** 
Used to calibrate the sensor's internal calculations based on current atmospheric pressure. The sensor defaults to 1013 hPa. Use setAirPressureReference(int apr) with values between 700 and 1100 hPa to match your local environment or an external barometer.
*   **Single Point Correction:**
In case the sensor malfunctions and shows incorrect values you could manually change the referance point of the sensor. Bring sensor to a place with known ppm value and run the function with the ppm entered in as a parameter. To check if function finished utelize function "getSinglePointCorrectionReady".

**Enviroment**
*   **Environmental Factors:** Accuracy is affected by atmospheric pressure. For high-altitude applications, CO2 readings will appear lower than actual unless pressure compensation is applied.


## 7. Code Example (Quick Start) /change/
```cpp
#include <SIMPLE_MTP40F.h>

SimpleMTP40F sensor(&Serial1);

void setup()
{
  Serial1.begin(9600); //initializing connection
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

```