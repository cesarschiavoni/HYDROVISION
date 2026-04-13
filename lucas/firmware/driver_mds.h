/*
 * HydroVision AG — Driver ADS1231 + DS18B20 (extensómetro de tronco MDS)
 * ADS1231: ADC 24-bit para strain gauge, interfaz bit-bang (SCLK + DOUT + PDWN)
 * DS18B20: temperatura del tronco para corrección de dilatación térmica
 * Librerías: OneWire, DallasTemperature (instalar desde Library Manager)
 *
 * MDS = D_max − D_min del día (micro-contracciones del tronco)
 * Corrección térmica: ΔD_corr = α × ΔT_tronco  (α = 2.5 µm/°C, Pérez-López 2008)
 */

#pragma once
#include <OneWire.h>
#include <DallasTemperature.h>
#include "config.h"

OneWire         _ow(PIN_DS18B20);
DallasTemperature _ds(&_ow);

// D_max y D_min del día — persisten en RTC memory (declarar en nodo_main.ino)
// extern RTC_DATA_ATTR float rtc_dmax_raw;
// extern RTC_DATA_ATTR float rtc_dmin_raw;
// extern RTC_DATA_ATTR float rtc_tronco_t_prev;

bool mds_init() {
    // Configurar pines ADS1231
    pinMode(PIN_ADS_SCLK, OUTPUT);
    pinMode(PIN_ADS_DOUT, INPUT);
    pinMode(PIN_ADS_PDWN, OUTPUT);
    digitalWrite(PIN_ADS_PDWN, HIGH);  // encender ADS1231
    digitalWrite(PIN_ADS_SCLK, LOW);

    // Iniciar DS18B20
    _ds.begin();
    _ds.setResolution(DS18B20_RESOLUTION);

    delay(100);  // esperar estabilización ADS1231

    Serial.println("[MDS] OK");
    return true;
}

// Lee 24 bits del ADS1231 (bit-bang)
// Retorna valor en counts (complemento a dos, 24-bit)
static int32_t _ads1231_read_raw() {
    // Esperar DOUT = LOW = datos listos (timeout 200ms)
    uint32_t t0 = millis();
    while (digitalRead(PIN_ADS_DOUT) == HIGH) {
        if (millis() - t0 > 200) {
            Serial.println("[ADS] timeout esperando DOUT");
            return INT32_MIN;
        }
        delayMicroseconds(10);
    }

    int32_t value = 0;
    for (int i = 23; i >= 0; i--) {
        digitalWrite(PIN_ADS_SCLK, HIGH);
        delayMicroseconds(2);
        value |= ((int32_t)digitalRead(PIN_ADS_DOUT) << i);
        digitalWrite(PIN_ADS_SCLK, LOW);
        delayMicroseconds(2);
    }
    // 25° pulso: resetea DOUT a HIGH
    digitalWrite(PIN_ADS_SCLK, HIGH);
    delayMicroseconds(2);
    digitalWrite(PIN_ADS_SCLK, LOW);

    // Extender signo: 24-bit → 32-bit
    if (value & 0x800000) value |= 0xFF000000;
    return value;
}

// Convierte counts a µm (calibrar COUNTS_PER_UM con setup real)
#define ADS1231_COUNTS_PER_UM   100.0f   // TODO: calibrar con medición conocida

static float _ads1231_to_um(int32_t raw) {
    return (float)raw / ADS1231_COUNTS_PER_UM;
}

struct MdsResult {
    float diameter_um;    // diámetro actual del tronco (µm, relativo al baseline)
    float diameter_mm;    // mismo en mm
    float temp_tronco;    // temperatura del tronco (°C)
    bool  ok;
};

MdsResult mds_read() {
    MdsResult r = {0, 0, 0, false};

    // Leer temperatura DS18B20
    _ds.requestTemperatures();
    float t_tronco = _ds.getTempCByIndex(0);
    if (t_tronco == DEVICE_DISCONNECTED_C) {
        Serial.println("[DS18B20] ERROR: sensor desconectado");
        return r;
    }

    // Leer ADS1231 (promedio de 3 lecturas)
    int32_t sum = 0;
    int valid = 0;
    for (int i = 0; i < 3; i++) {
        int32_t raw = _ads1231_read_raw();
        if (raw != INT32_MIN) { sum += raw; valid++; }
    }
    if (valid == 0) return r;

    float diameter_um = _ads1231_to_um(sum / valid);
    r.diameter_um  = diameter_um;
    r.diameter_mm  = diameter_um / 1000.0f;
    r.temp_tronco  = t_tronco;
    r.ok           = true;

    Serial.printf("[MDS] D=%.4f mm T_tronco=%.2f°C\n", r.diameter_mm, r.temp_tronco);
    return r;
}

// Aplica corrección térmica al diámetro medido
// ΔD_corr = α × (T_actual − T_ref)   con α = 2.5 µm/°C
float mds_corregir_termico(float diameter_um, float t_actual, float t_ref) {
    const float ALPHA = 2.5f;  // µm/°C (Pérez-López et al. 2008)
    return diameter_um - ALPHA * (t_actual - t_ref);
}
