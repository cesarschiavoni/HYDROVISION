/*
 * HydroVision AG — Driver LoRa SX1276 (915 MHz, SF7, BW125)
 * Librería: arduino-LoRa by sandeepmistry (instalar desde Library Manager)
 * Interfaz SPI: pines definidos en config.h (SS=10, RST=18, DIO0=19)
 *
 * Protocolo de payload LoRa (binario simple):
 *   [1 byte: len_topic][topic ASCII][payload JSON]
 *   Receptor (gateway) separa topic y payload por el primer byte.
 *
 * Máximo payload: ~250 bytes con SF7 y airtime < 1s (regulación AR 915 MHz).
 * Payload JSON del nodo: ~380 bytes → usar SF7+BW125 para mantener airtime < 1s.
 *
 * NOTA: LoRaWAN completo (OTAA, ADR, duty cycle) queda para TRL5.
 *       TRL4 usa LoRa privado punto-a-punto con gateway propio.
 */

#pragma once
#include <LoRa.h>
#include "config.h"

bool lora_init() {
    LoRa.setPins(PIN_LORA_SS, PIN_LORA_RST, PIN_LORA_DIO0);

    if (!LoRa.begin(LORA_FREQ_HZ)) {
        Serial.println("[LORA] ERROR: SX1276 no encontrado");
        return false;
    }

    LoRa.setSpreadingFactor(LORA_SF);
    LoRa.setSignalBandwidth(LORA_BW);
    LoRa.setCodingRate4(LORA_CR);
    LoRa.setTxPower(LORA_TX_POWER);
    LoRa.enableCrc();

    Serial.printf("[LORA] OK — %.0f MHz SF%d BW%.0fkHz CR4/%d %ddBm\n",
                  (float)LORA_FREQ_HZ / 1e6,
                  LORA_SF,
                  (float)LORA_BW / 1e3,
                  LORA_CR,
                  LORA_TX_POWER);
    return true;
}

/*
 * Publica topic + payload JSON por LoRa.
 * Formato: [1 byte len_topic][topic][json_payload]
 *
 * Retorna true si el paquete fue transmitido, false si hubo error.
 */
bool publicar_lora(const char* topic, const char* json_payload) {
    uint8_t topic_len = (uint8_t)strlen(topic);
    size_t  json_len  = strlen(json_payload);
    size_t  total     = 1 + topic_len + json_len;

    if (total > 255) {
        Serial.printf("[LORA] WARN: payload %u bytes excede límite (255)\n", (unsigned)total);
        // Truncar JSON — el backend ignorará el mensaje malformado
        json_len = 254 - topic_len;
        total    = 255;
    }

    LoRa.beginPacket();
    LoRa.write(topic_len);
    LoRa.write((const uint8_t*)topic,        topic_len);
    LoRa.write((const uint8_t*)json_payload, json_len);
    int result = LoRa.endPacket();  // bloqueante hasta fin de TX

    if (result == 1) {
        Serial.printf("[LORA] TX OK — topic=%s (%u bytes total)\n", topic, (unsigned)total);
        return true;
    } else {
        Serial.println("[LORA] ERROR: TX fallida");
        return false;
    }
}

/*
 * Recibe respuesta downlink del gateway después de un TX.
 * Protocolo: el gateway reenvía la respuesta HTTP del backend
 * como paquete LoRa dentro de la ventana RX post-TX.
 *
 * Formato downlink: JSON plano (sin prefijo de topic).
 * Ejemplo: {"status":"ok","varietal":"vid - malbec","command":{"irrigate":false}}
 *
 * Retorna puntero a buffer estático con el payload, o nullptr si timeout.
 * El buffer se sobreescribe en cada llamada.
 */
static char _lora_rx_buf[256];

const char* lora_receive_response(uint32_t timeout_ms = 5000) {
    unsigned long t0 = millis();

    // Poner en modo recepción
    LoRa.receive();

    while ((millis() - t0) < timeout_ms) {
        int pkt_size = LoRa.parsePacket();
        if (pkt_size > 0) {
            int i = 0;
            while (LoRa.available() && i < (int)sizeof(_lora_rx_buf) - 1) {
                _lora_rx_buf[i++] = (char)LoRa.read();
            }
            _lora_rx_buf[i] = '\0';

            int rssi = LoRa.packetRssi();
            float snr = LoRa.packetSnr();
            Serial.printf("[LORA] RX downlink %d bytes RSSI=%d SNR=%.1f\n",
                          i, rssi, snr);
            return _lora_rx_buf;
        }
        delay(10);  // polling a 100 Hz — bajo consumo relativo al TX previo
    }

    Serial.println("[LORA] RX timeout — sin respuesta downlink");
    return nullptr;
}

// Poner SX1276 en sleep antes de deep sleep del ESP32
void lora_sleep() {
    LoRa.sleep();
}
