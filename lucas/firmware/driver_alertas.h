/*
 * HydroVision AG — Driver alertas físicas (LED tricolor + sirena)
 * Pines: PIN_LED_VERDE / PIN_LED_AMBAR / PIN_LED_ROJO / PIN_SIRENA
 *
 * Lógica de estados:
 *   BOOT        → parpadeo blanco (verde+ambar+rojo) × 3 durante init
 *   OK          → LED verde fijo 2 s, apagar
 *   AVISO       → LED ambar parpadeo lento (HSI 0.50–0.70)
 *   STRESS      → LED rojo fijo + sirena 3 beeps cortos (HSI ≥ 0.70)
 *   ERROR       → LED rojo parpadeo rápido (sensor crítico offline)
 *
 * Durante deep sleep: todos los pines quedan LOW (sin consumo).
 * La sirena es activa-baja o activa-alta según el módulo — verificar
 * en banco con osciloscopio antes de instalar en campo.
 */

#pragma once
#include <Arduino.h>
#include "config.h"

void alertas_init() {
    pinMode(PIN_LED_VERDE, OUTPUT);
    pinMode(PIN_LED_AMBAR, OUTPUT);
    pinMode(PIN_LED_ROJO,  OUTPUT);
    pinMode(PIN_SIRENA,    OUTPUT);

    // Apagar todo al inicio
    digitalWrite(PIN_LED_VERDE, LOW);
    digitalWrite(PIN_LED_AMBAR, LOW);
    digitalWrite(PIN_LED_ROJO,  LOW);
    digitalWrite(PIN_SIRENA,    LOW);

    // Secuencia de boot: encender los 3 LEDs × 3 pulsos (200 ms cada uno)
    for (uint8_t i = 0; i < 3; i++) {
        digitalWrite(PIN_LED_VERDE, HIGH);
        digitalWrite(PIN_LED_AMBAR, HIGH);
        digitalWrite(PIN_LED_ROJO,  HIGH);
        delay(150);
        digitalWrite(PIN_LED_VERDE, LOW);
        digitalWrite(PIN_LED_AMBAR, LOW);
        digitalWrite(PIN_LED_ROJO,  LOW);
        delay(150);
    }
    Serial.println("[ALERTAS] OK");
}

// Apagar todos los pines (llamar antes de deep sleep)
void alertas_apagar() {
    digitalWrite(PIN_LED_VERDE, LOW);
    digitalWrite(PIN_LED_AMBAR, LOW);
    digitalWrite(PIN_LED_ROJO,  LOW);
    digitalWrite(PIN_SIRENA,    LOW);
}

// Estado OK: verde 1.5 s, apagar (confirma ciclo exitoso)
void alerta_ok() {
    alertas_apagar();
    digitalWrite(PIN_LED_VERDE, HIGH);
    delay(1500);
    alertas_apagar();
}

// Aviso moderado: ambar 3 parpadeos lentos (HSI 0.50–0.70)
void alerta_aviso() {
    alertas_apagar();
    for (uint8_t i = 0; i < 3; i++) {
        digitalWrite(PIN_LED_AMBAR, HIGH);
        delay(400);
        digitalWrite(PIN_LED_AMBAR, LOW);
        delay(400);
    }
}

// Alerta estrés hídrico: rojo fijo + 3 beeps cortos (HSI ≥ 0.70)
void alerta_stress() {
    alertas_apagar();
    digitalWrite(PIN_LED_ROJO, HIGH);
    for (uint8_t i = 0; i < 3; i++) {
        digitalWrite(PIN_SIRENA, HIGH);
        delay(200);
        digitalWrite(PIN_SIRENA, LOW);
        delay(300);
    }
    delay(1000);
    alertas_apagar();
}

// Error de sensor crítico: rojo parpadeo rápido × 5 (sin sirena — no es estrés)
void alerta_error_sensor(uint8_t n_parpadeos = 5) {
    alertas_apagar();
    for (uint8_t i = 0; i < n_parpadeos; i++) {
        digitalWrite(PIN_LED_ROJO, HIGH);
        delay(100);
        digitalWrite(PIN_LED_ROJO, LOW);
        delay(100);
    }
}

/*
 * Función de alto nivel: decide el estado de alerta según HSI y estado de sensores.
 * Llamar al final del ciclo, antes de deep sleep.
 *
 * ok_mlx: true si la cámara térmica respondió en este ciclo.
 */
void alertas_aplicar(float hsi, bool ok_mlx) {
    if (!ok_mlx) {
        alerta_error_sensor();
        return;
    }
    if (hsi < 0.0f) {
        // CWSI no calibrado aún — ambar parpadeante para indicar warm-up
        alerta_aviso();
    } else if (hsi >= HSI_ALERT_THRESHOLD) {
        alerta_stress();
    } else if (hsi >= 0.50f) {
        alerta_aviso();
    } else {
        alerta_ok();
    }
}
