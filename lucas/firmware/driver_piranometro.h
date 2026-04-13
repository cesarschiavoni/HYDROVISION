/*
 * HydroVision AG — Driver piranómetro BPW34 (fotodiodo + ADC)
 * Conexión: BPW34 + resistor de carga → PIN_PYRANO_ADC (ADC1_CH0)
 * Rango típico BPW34: 0–1100 W/m² (plena radiación solar)
 *
 * Conversión: Vout (mV) → W/m²  mediante PYRANO_WPM2_PER_MV
 * NOTA: PYRANO_WPM2_PER_MV debe calibrarse con piranómetro de referencia en campo.
 *       Valor inicial conservador: 1.0 W/m² por mV (R_carga ≈ 1kΩ, BPW34 ~0.4A/W typ).
 *
 * Usa analogReadMilliVolts() (arduino-esp32 ≥ 2.0) para mayor precisión.
 */

#pragma once
#include "config.h"

bool piranometro_init() {
    // ADC1 no requiere inicialización explícita en Arduino ESP32
    // ADC_11db fue renombrado a ADC_ATTEN_DB_12 en arduino-esp32 v3.0+
    // Ambas son equivalentes (rango 0–3.3V). Usar la nueva para evitar warning.
    analogSetPinAttenuation(PIN_PYRANO_ADC, ADC_ATTEN_DB_12);
    Serial.println("[PYRANO] OK — ADC configurado");
    return true;
}

struct PiranometroResult {
    float  rad_wm2;   // radiación solar W/m²
    float  mV;        // tensión medida (diagnóstico)
    bool   ok;
};

// Promedia N lecturas ADC para reducir ruido
PiranometroResult piranometro_read(uint8_t n_samples = 8) {
    PiranometroResult r = {0.0f, 0.0f, false};

    uint32_t sum_mv = 0;
    for (uint8_t i = 0; i < n_samples; i++) {
        sum_mv += analogReadMilliVolts(PIN_PYRANO_ADC);
        delayMicroseconds(500);
    }
    float mv = (float)sum_mv / n_samples;

    r.mV      = mv;
    r.rad_wm2 = mv * PYRANO_WPM2_PER_MV;
    r.ok      = true;

    Serial.printf("[PYRANO] %.1f mV → %.1f W/m²\n", r.mV, r.rad_wm2);
    return r;
}
