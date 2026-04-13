/*
 * HydroVision AG — Driver SHT31 (temperatura + humedad del aire)
 * Librería: Adafruit_SHT31 (instalar desde Library Manager)
 */

#pragma once
#include <Adafruit_SHT31.h>
#include "config.h"

Adafruit_SHT31 _sht31;

bool sht31_init() {
    if (!_sht31.begin(SHT31_I2C_ADDR, &Wire)) {
        Serial.println("[SHT31] ERROR: no encontrado en I2C");
        return false;
    }
    _sht31.heater(false);  // calefactor apagado en operación normal
    Serial.println("[SHT31] OK");
    return true;
}

struct Sht31Result {
    float t_air;  // °C
    float rh;     // % humedad relativa
    bool  ok;
};

Sht31Result sht31_read() {
    Sht31Result r = {0, 0, false};
    float t = _sht31.readTemperature();
    float h = _sht31.readHumidity();
    if (isnan(t) || isnan(h)) {
        Serial.println("[SHT31] ERROR: lectura NaN");
        return r;
    }
    r.t_air = t;
    r.rh    = h;
    r.ok    = true;
    Serial.printf("[SHT31] T=%.2f°C RH=%.1f%%\n", r.t_air, r.rh);
    return r;
}
