# BME680 on Pi Pico 2 W (MicroPython) — test + driver

This folder contains a minimal **MicroPython** driver for the **Bosch BME680** environmental sensor plus a simple test script that prints readings to the serial console.

## Files

- `bme680.py` – BME680 driver (trimmed version of Adafruit’s CircuitPython driver for MicroPython)
- `main.py` – test program: reads sensor values and prints them every 5 seconds

## Hardware / wiring

The test script uses **I2C0** on the Pico:

- SDA: **GP4**
- SCL: **GP5**
- VCC: **3V3**
- GND: **GND**

Connect the BME680 to these pins (I2C is a shared bus; only one sensor is assumed here).

### I2C address

The driver defaults to address **0x77**:

```python
bme = BME680_I2C(i2c=i2c)
```

If your board uses **0x76**, change the constructor:

```python
bme = BME680_I2C(i2c=i2c, address=0x76)
```

## Dependencies

No external libraries required.

Uses only built-in MicroPython modules:

- `machine` (`Pin`, `I2C`)
- `time`
- `micropython`, `math`, `ubinascii`

## Running the test

1. Flash MicroPython firmware to your **Pi Pico 2 W**.
2. Copy `main.py` and `bme680.py` to the Pico filesystem.
3. Reset the Pico.

You should see output similar to:

- Temperature (°C)
- Humidity (%)
- Pressure (hPa)
- Gas resistance (kΩ)

If you see `Failed to read sensor.`, double-check wiring and I2C address.

## Notes

- Gas resistance is **not** a direct air quality index; it’s a raw resistance value often used as an input to further calculations.
- This test is based on the wiring/pin assignment used in `main.py`.
