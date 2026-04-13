/*
 * HydroVision AG — Driver DS3231 RTC
 * Librería: RTClib (instalar desde Library Manager)
 * Propósito: timestamp Unix para cada sesión. Persiste ante cortes de energía.
 */

#pragma once
#include <RTClib.h>
#include "config.h"

RTC_DS3231 _rtc;

bool rtc_init() {
    if (!_rtc.begin(&Wire)) {
        Serial.println("[RTC] ERROR: DS3231 no encontrado");
        return false;
    }
    if (_rtc.lostPower()) {
        Serial.println("[RTC] WARN: perdió energía — hora no confiable");
        // Opción: sincronizar desde GPS cuando esté disponible
    }
    Serial.println("[RTC] OK");
    return true;
}

// Retorna epoch Unix (segundos desde 1970-01-01 00:00:00 UTC)
uint32_t rtc_timestamp() {
    DateTime now = _rtc.now();
    return now.unixtime();
}

// Sincroniza el RTC con la hora del GPS (llamar cuando GPS tiene fix válido)
void rtc_sync_gps(uint32_t gps_epoch) {
    _rtc.adjust(DateTime(gps_epoch));
    Serial.printf("[RTC] Sincronizado con GPS: %lu\n", gps_epoch);
}

// Temperatura interna del DS3231 (±3°C, útil como diagnóstico)
float rtc_temperatura() {
    return _rtc.getTemperature();
}

// Hora local Argentina (UTC-3, sin horario de verano — Argentina no lo usa desde 2009)
// Retorna entero 0-23.
// Usado por ventana_solar_activa() en nodo_main.ino para HW-02.
int rtc_leer_hora_local() {
    DateTime now = _rtc.now();
    int hora_utc = now.hour();
    int hora_local = hora_utc - 3;   // UTC-3
    if (hora_local < 0) hora_local += 24;
    return hora_local;
}
