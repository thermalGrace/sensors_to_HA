#include "SIMPLE_MTP40F.h"

SimpleMTP40F::SimpleMTP40F(Stream * stream) {
    _ser = stream;
}

uint32_t SimpleMTP40F::getPPM() {
    // The sensor physically cannot update faster than once every 2 seconds.
    if (millis() - _lastRead < 2000) return _gasLevel;
    _lastRead = millis();

    // Command to read gas (9 bytes)
    uint8_t cmd[9] = {0x42, 0x4D, 0xA0, 0x00, 0x03, 0x00, 0x00, 0x01, 0x32};

    // request() calculates the CRC and communicates with the sensor
    if (request(cmd, 9, 14)) {
        if (_buffer[11] == 0x00) { // Status byte 00 passed = Success
          // Combine bytes 7-10 into a uint32_t value
            uint32_t val = _buffer[7];
            val <<= 8; val |= _buffer[8];
            val <<= 8; val |= _buffer[9];
            val <<= 8; val |= _buffer[10];
            _gasLevel = val;
            return _gasLevel;
        }
    }
    return _gasLevel; // Return last known good value if failed
}

bool SimpleMTP40F::setAirPressureReference(int apr)
{
  if ((apr < 700) || (apr > 1100))  //  page 5 datasheet
  {
    return false;
  }

  uint8_t cmd[11] = { 0x42, 0x4D, 0xA0, 0x00, 0x01, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00 };
  cmd[7] = apr / 256;
  cmd[8] = apr % 256;
  if (request(cmd, 11, 11) )
  {
    return true;
  }
  return false;
}

bool SimpleMTP40F::getSinglePointCorrectionReady()
{
  uint8_t cmd[9] = { 0x42, 0x4D, 0xA0, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00 };
  if (request(cmd, 9, 10) )
  {
    if (_buffer[8] == 0) return true;
  }
  return false;
}

String SimpleMTP40F::getAirQuality() {
    if (_gasLevel == 0)    return "Waiting...";
    else if (_gasLevel < 800)  return "good";
    else if (_gasLevel < 1200) return "Stuffy";
    else if (_gasLevel < 1999) return "Poor";
    return "Hazardous";
}

uint32_t SimpleMTP40F::getFilteredPPM() {
    uint32_t currentPPM = getPPM();
    if (_filteredPPM == 0) _filteredPPM = currentPPM; // Initial seed
    
    _filteredPPM = (_alpha * currentPPM) + ((1.0 - _alpha) * _filteredPPM);
    return (uint32_t)_filteredPPM;
}

bool SimpleMTP40F::setSinglePointCorrection(uint32_t spc)
{
  if ((spc < 400) || (spc > 2000))  //  datasheet unclear 0x2000???
  {
    return false;
  }

  uint8_t cmd[13] = { 0x42, 0x4D, 0xA0, 0x00, 0x04, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
  cmd[7]  = 0;
  cmd[8]  = 0;
  cmd[9]  = spc / 256;
  cmd[10] = spc % 256;
  if (request(cmd, 13, 10) )
  {
    if (_buffer[7] ) return true;
  }
  return false;
}

bool SimpleMTP40F::request(uint8_t *data, uint8_t commandLength, uint8_t responseLength) {
    if (_ser == NULL) return false;

    // 1. Calculate and add CRC to the command
    uint16_t crc = CRC(data, commandLength - 2);
    data[commandLength - 2] = crc / 256;
    data[commandLength - 1] = crc & 0xFF;

    // 2. Send the command
    for (uint8_t i = 0; i < commandLength; i++) {
        _ser->write(data[i]);
        yield();
    }

    // 3. Wait for response
    uint32_t start = millis();
    uint8_t i = 0;
    while (i < responseLength) {
        if (millis() - start > 100) return false; // Timeout
        if (_ser->available()) {
            _buffer[i++] = _ser->read();
        }
        yield();
    }

    // 4. Verify response CRC
    uint16_t expected_crc = (_buffer[responseLength - 2] << 8) | _buffer[responseLength - 1];
    uint16_t calc_crc = CRC(_buffer, responseLength - 2);
    
    return (calc_crc == expected_crc);
}

uint16_t SimpleMTP40F::CRC(uint8_t *data, uint16_t length) {
    uint16_t sum = 0;
    for (uint16_t i = 0; i < length; i++) sum += data[i];
    return sum;
}