/*
 * HydroVision AG — Driver pluviómetro báscula balancín
 * Conexión: GPIO interrupción (PIN_PLUV_INT) + resistor pull-up externo
 * Cada pulso = PLUV_MM_PER_PULSE mm de lluvia (calibrar con fabricante del sensor)
 *
 * Diseño: ISR incrementa contador volátil → pluv_read() convierte a mm y resetea.
 * El acumulado diario persiste en RTC memory (declarar en nodo_main.ino).
 */

#pragma once
#include "config.h"

// Contador de pulsos — modificado desde ISR, leído desde tarea principal
static volatile uint32_t _pluv_pulsos = 0;
static volatile uint32_t _pluv_last_ms = 0;  // para debounce

// ISR: se llama en cada flanco de bajada del reed switch
static void IRAM_ATTR _pluv_isr() {
    uint32_t now = millis();
    if (now - _pluv_last_ms > PLUV_DEBOUNCE_MS) {
        _pluv_pulsos++;
        _pluv_last_ms = now;
    }
}

bool pluviometro_init() {
    pinMode(PIN_PLUV_INT, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_PLUV_INT), _pluv_isr, FALLING);
    Serial.println("[PLUV] OK — interrupción GPIO configurada");
    return true;
}

struct PluviometroResult {
    float  rain_mm;   // mm acumulados desde la última llamada a pluv_read()
    uint32_t pulsos;  // pulsos crudos (útil para diagnóstico)
    bool   ok;
};

// Lee y resetea el contador de pulsos
// Llamar una vez por ciclo; el acumulado histórico se gestiona en nodo_main.ino
PluviometroResult pluviometro_read() {
    PluviometroResult r = {0, 0, false};

    // Leer con interrupción deshabilitada para consistencia
    noInterrupts();
    uint32_t pulsos = _pluv_pulsos;
    _pluv_pulsos = 0;
    interrupts();

    r.pulsos  = pulsos;
    r.rain_mm = (float)pulsos * PLUV_MM_PER_PULSE;
    r.ok      = true;

    if (pulsos > 0) {
        Serial.printf("[PLUV] %lu pulsos → %.1f mm\n", pulsos, r.rain_mm);
    }
    return r;
}

// Detach seguro antes de deep sleep (recomendado en ESP32)
void pluviometro_deinit() {
    detachInterrupt(digitalPinToInterrupt(PIN_PLUV_INT));
}
