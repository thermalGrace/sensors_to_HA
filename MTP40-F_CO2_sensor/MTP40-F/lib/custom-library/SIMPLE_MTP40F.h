#ifndef SIMPLE_MTP40F_H
#define SIMPLE_MTP40F_H

#include "Arduino.h"

class SimpleMTP40F
{
public:
    SimpleMTP40F(Stream *stream);

    uint32_t getPPM();
    String getAirQuality();

    bool setAirPressureReference(int apr = 1013);

    uint32_t getFilteredPPM();

    bool setSinglePointCorrection(uint32_t spc);
    bool getSinglePointCorrectionReady();

private:
    Stream *_ser;
    uint8_t _buffer[16];
    uint32_t _gasLevel = 0;
    uint32_t _lastRead = 0;

    float _filteredPPM = 0;
    float _alpha = 0.1; // Smoothing factor (0.0 to 1.0)

    bool request(uint8_t *data, uint8_t commandLength, uint8_t responseLength);
    uint16_t CRC(uint8_t *data, uint16_t length);
};

#endif