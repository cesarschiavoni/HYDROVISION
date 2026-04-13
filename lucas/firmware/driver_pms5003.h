/*
 * HydroVision AG — Driver sensor de partículas PMS5003 (Plantower)
 * Conexión: PIN_PMS_RX / PIN_PMS_TX → UART1 (compartido con GPS, ver nota)
 * Protocolo: UART pasivo — el sensor envía un paquete de 32 bytes cada ~1s
 *
 * NOTA UART: comparte HardwareSerial(1) con el GPS.
 *   - Boot 1: UART1 se usa primero para GPS (GPIO 5/6), luego se reasigna aquí (GPIO 12/13).
 *   - Boot 2+: GPS no se inicializa → UART1 queda libre para PMS5003 desde el inicio.
 *   La reasignación es segura porque el GPS ya terminó su lectura antes de que se llame pms_init().
 *
 * Detección de fumigación: PM2.5 > PMS_PM25_FUMIG (200 µg/m³).
 *   En campo abierto sin eventos: PM2.5 típico 10–30 µg/m³.
 *   Durante fumigación con sprayer: PM2.5 sube a 500–5000 µg/m³ en segundos.
 *   Durante lluvia leve: PM2.5 sube a 50–150 µg/m³ (distinguible de fumigación).
 *
 * Formato del paquete PMS5003 (32 bytes):
 *   [0] 0x42  [1] 0x4D  [2-3] frame_len(28)
 *   [4-5]  PM1.0 std   [6-7]  PM2.5 std   [8-9]  PM10 std
 *   [10-11] PM1.0 atm  [12-13] PM2.5 atm  [14-15] PM10 atm
 *   [16-25] conteos por tamaño  [28-29] reservado  [30-31] checksum
 */

#pragma once
#include "config.h"

static HardwareSerial _pmsSerial(1);  // UART1, reasignado desde GPS

bool pms_init() {
    _pmsSerial.begin(PMS_BAUD, SERIAL_8N1, PIN_PMS_RX, PIN_PMS_TX);
    // Esperar calentamiento del láser interno
    delay(PMS_WARMUP_MS);
    Serial.println("[PMS] OK — UART1 reasignado a PMS5003");
    return true;
}

struct Pms5003Result {
    uint16_t pm1_0;    // µg/m³
    uint16_t pm2_5;    // µg/m³ — principal para detección
    uint16_t pm10;     // µg/m³
    bool     ok;
};

// Lee un paquete completo. Descarta bytes hasta encontrar 0x42 0x4D.
Pms5003Result pms_read(uint32_t timeout_ms = 3000) {
    Pms5003Result r = {0, 0, 0, false};

    uint32_t t0 = millis();
    uint8_t  buf[32];
    uint8_t  idx = 0;
    bool     synced = false;

    while (millis() - t0 < timeout_ms) {
        if (!_pmsSerial.available()) { delay(10); continue; }

        uint8_t b = _pmsSerial.read();

        if (!synced) {
            // Buscar byte de inicio 0x42
            if (b == 0x42) { buf[0] = b; idx = 1; synced = true; }
            continue;
        }

        buf[idx++] = b;

        if (idx == 2 && buf[1] != 0x4D) {
            // Segundo byte inválido — resetear
            synced = false; idx = 0;
            continue;
        }

        if (idx == 32) {
            // Verificar checksum: suma de bytes 0..29 == bytes 30-31 (big-endian)
            uint16_t csum_calc = 0;
            for (uint8_t i = 0; i < 30; i++) csum_calc += buf[i];
            uint16_t csum_recv = ((uint16_t)buf[30] << 8) | buf[31];

            if (csum_calc != csum_recv) {
                Serial.println("[PMS] WARN: checksum inválido");
                synced = false; idx = 0;
                continue;
            }

            // Extraer valores (big-endian, bytes 4-9: PM std)
            r.pm1_0 = ((uint16_t)buf[4]  << 8) | buf[5];
            r.pm2_5 = ((uint16_t)buf[6]  << 8) | buf[7];
            r.pm10  = ((uint16_t)buf[8]  << 8) | buf[9];
            r.ok    = true;

            Serial.printf("[PMS] PM1.0=%u PM2.5=%u PM10=%u µg/m³\n",
                          r.pm1_0, r.pm2_5, r.pm10);
            return r;
        }
    }

    Serial.println("[PMS] WARN: timeout sin paquete");
    return r;
}

// Classify: fumigacion / lluvia_aerosol / ok
// Retorna string literal para incluir directamente en JSON
const char* pms_calidad(uint16_t pm2_5, bool lluvia_activa) {
    if (pm2_5 > PMS_PM25_FUMIG)  return "fumigacion";
    if (pm2_5 > PMS_PM25_LLUVIA && lluvia_activa) return "lluvia";
    return "ok";
}
