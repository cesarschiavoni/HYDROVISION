/*
 * HydroVision AG — Driver anemómetro RS485 Modbus RTU
 * Conexión: ESP32-S3 UART2 → MAX485 → anemómetro RS485
 * Protocolo: Modbus RTU, función 0x03 (Read Holding Registers)
 *
 * La mayoría de los anemómetros RS485 de campo usan el registro 0x0000
 * para velocidad de viento. Verificar datasheet del modelo específico.
 */

#pragma once
#include "config.h"

HardwareSerial _rs485Serial(2);  // UART2

bool anemometro_init() {
    _rs485Serial.begin(RS485_BAUD, SERIAL_8N1, PIN_RS485_RX, PIN_RS485_TX);
    pinMode(PIN_RS485_DE, OUTPUT);
    digitalWrite(PIN_RS485_DE, LOW);  // modo recepción por defecto
    Serial.println("[ANEMO] OK — UART2 RS485 iniciado");
    return true;
}

// Calcula CRC16 Modbus
static uint16_t _modbus_crc16(const uint8_t* buf, uint8_t len) {
    uint16_t crc = 0xFFFF;
    for (uint8_t i = 0; i < len; i++) {
        crc ^= buf[i];
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x0001) crc = (crc >> 1) ^ 0xA001;
            else              crc >>= 1;
        }
    }
    return crc;
}

// Lee un registro Modbus RTU (función 0x03)
// Retorna valor del registro o -1 en caso de error
static int32_t _modbus_read_register(uint8_t addr, uint16_t reg) {
    // Construir trama: [addr, 0x03, reg_hi, reg_lo, qty_hi, qty_lo, crc_lo, crc_hi]
    uint8_t request[8];
    request[0] = addr;
    request[1] = 0x03;
    request[2] = (reg >> 8) & 0xFF;
    request[3] = reg & 0xFF;
    request[4] = 0x00;
    request[5] = 0x01;  // 1 registro
    uint16_t crc = _modbus_crc16(request, 6);
    request[6] = crc & 0xFF;
    request[7] = (crc >> 8) & 0xFF;

    // Transmitir
    digitalWrite(PIN_RS485_DE, HIGH);
    delayMicroseconds(100);
    _rs485Serial.write(request, 8);
    _rs485Serial.flush();
    delayMicroseconds(100);
    digitalWrite(PIN_RS485_DE, LOW);

    // Esperar respuesta: [addr, 0x03, byte_count, data_hi, data_lo, crc_lo, crc_hi] = 7 bytes
    uint32_t t0 = millis();
    while (_rs485Serial.available() < 7) {
        if (millis() - t0 > 200) {
            Serial.println("[ANEMO] timeout respuesta Modbus");
            return -1;
        }
        delay(5);
    }

    uint8_t response[7];
    _rs485Serial.readBytes(response, 7);

    // Verificar CRC
    uint16_t crc_recv = response[5] | ((uint16_t)response[6] << 8);
    uint16_t crc_calc = _modbus_crc16(response, 5);
    if (crc_recv != crc_calc) {
        Serial.println("[ANEMO] ERROR: CRC inválido");
        return -1;
    }

    return (int32_t)((response[3] << 8) | response[4]);
}

struct AnemometroResult {
    float wind_ms;  // velocidad del viento en m/s
    bool  ok;
};

AnemometroResult anemometro_read() {
    AnemometroResult r = {0, false};
    int32_t raw = _modbus_read_register(RS485_MODBUS_ADDR, RS485_REG_WIND);
    if (raw < 0) return r;

    r.wind_ms = (float)raw * RS485_SCALE;
    r.ok      = true;
    Serial.printf("[ANEMO] viento=%.1f m/s (raw=%d)\n", r.wind_ms, raw);
    return r;
}
