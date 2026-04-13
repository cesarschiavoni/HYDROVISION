/*
 * HydroVision AG — Driver bomba peristáltica Wet Reference
 * Conexión: MOSFET gate → PIN_BOMBA_WETREF (GPIO, active HIGH)
 * Propósito: mantener húmeda la hoja de referencia (Wet Ref) para calibración Tc_wet
 *
 * Uso recomendado:
 *   - Llamar bomba_wetref_pulso() antes de cada captura MLX90640
 *   - BOMBA_PULSO_MS = 3000 ms recarga ~0.5 mL con bomba Kamoer tipo 12V
 *   - Ajustar BOMBA_PULSO_MS según caudal real de la bomba seleccionada
 */

#pragma once
#include "config.h"

bool bomba_wetref_init() {
    pinMode(PIN_BOMBA_WETREF, OUTPUT);
    digitalWrite(PIN_BOMBA_WETREF, LOW);  // apagada por defecto
    Serial.println("[BOMBA] OK — GPIO configurado");
    return true;
}

// Activa la bomba durante BOMBA_PULSO_MS milisegundos (bloqueante)
void bomba_wetref_pulso() {
    Serial.printf("[BOMBA] pulso %d ms\n", BOMBA_PULSO_MS);
    digitalWrite(PIN_BOMBA_WETREF, HIGH);
    delay(BOMBA_PULSO_MS);
    digitalWrite(PIN_BOMBA_WETREF, LOW);
}

// Control manual para pruebas (no bloqueante, usar bomba_off() después)
void bomba_wetref_on()  { digitalWrite(PIN_BOMBA_WETREF, HIGH); }
void bomba_wetref_off() { digitalWrite(PIN_BOMBA_WETREF, LOW);  }
