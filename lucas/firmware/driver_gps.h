/*
 * HydroVision AG — Driver GPS u-blox NEO-6M
 * Librería: TinyGPSPlus (instalar desde Library Manager)
 * El GPS se usa principalmente para georreferenciar el nodo.
 * Una vez obtenido el primer fix, la posición se guarda en RTC memory
 * y el GPS no se enciende en cada ciclo (ahorro de energía).
 */

#pragma once
#include <TinyGPSPlus.h>
#include "config.h"

TinyGPSPlus  _gps;
HardwareSerial _gpsSerial(1);  // UART1

bool gps_init() {
    _gpsSerial.begin(GPS_BAUD, SERIAL_8N1, PIN_GPS_RX, PIN_GPS_TX);
    Serial.println("[GPS] OK — UART1 iniciado");
    return true;
}

struct GpsResult {
    float    lat;
    float    lon;
    uint32_t epoch;    // tiempo GPS como epoch Unix (si disponible)
    bool     ok;
};

// Intenta obtener fix en timeout_ms milisegundos
GpsResult gps_read(uint32_t timeout_ms = GPS_TIMEOUT_MS) {
    GpsResult r = {0, 0, 0, false};
    uint32_t t0 = millis();

    while (millis() - t0 < timeout_ms) {
        while (_gpsSerial.available()) {
            _gps.encode(_gpsSerial.read());
        }
        if (_gps.location.isUpdated() && _gps.location.isValid()) {
            r.lat = (float)_gps.location.lat();
            r.lon = (float)_gps.location.lng();

            // Construir epoch UTC directamente desde la fecha/hora GPS.
            // NO usar mktime() — aplica zona horaria local del sistema (indefinida en ESP32).
            // Cálculo manual de epoch Unix (válido para fechas 2000–2099).
            if (_gps.date.isValid() && _gps.time.isValid()) {
                uint16_t y  = _gps.date.year();
                uint8_t  mo = _gps.date.month();
                uint8_t  d  = _gps.date.day();
                uint8_t  h  = _gps.time.hour();
                uint8_t  mi = _gps.time.minute();
                uint8_t  s  = _gps.time.second();

                // Días desde 1970-01-01 usando algoritmo de Fliegel & Van Flandern
                // Reducido a enteros para evitar float precision issues
                int32_t jdn = (int32_t)d - 32075
                    + 1461 * ((int32_t)y + 4800 + ((int32_t)mo - 14) / 12) / 4
                    + 367  * ((int32_t)mo - 2 - ((int32_t)mo - 14) / 12 * 12) / 12
                    - 3    * (((int32_t)y + 4900 + ((int32_t)mo - 14) / 12) / 100) / 4;
                // Epoch Unix desde JDN (JDN de 1970-01-01 = 2440588)
                r.epoch = (uint32_t)((jdn - 2440588L) * 86400L
                          + (int32_t)h * 3600 + (int32_t)mi * 60 + s);
            }

            r.ok = true;
            Serial.printf("[GPS] lat=%.6f lon=%.6f\n", r.lat, r.lon);
            return r;
        }
        delay(10);
    }

    Serial.println("[GPS] WARN: timeout sin fix");
    return r;
}
