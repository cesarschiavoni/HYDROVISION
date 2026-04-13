/*
 * HydroVision AG — Cifrado AES-128-CTR para payload LoRa
 *
 * Cifra el payload JSON antes de transmitir por LoRa y descifra en recepción.
 * Usa AES-128-CTR con clave derivada del eFuse unique_id del ESP32-S3.
 *
 * Formato del paquete cifrado:
 *   [2 bytes: sequence_counter][N bytes: AES-128-CTR(plaintext)]
 *
 * El IV (nonce) se construye como:
 *   [6 bytes: MAC address][2 bytes: sequence_counter][8 bytes: 0x00 padding]
 *
 * Anti-replay: el gateway rechaza paquetes con sequence <= último recibido.
 * El nodo incrementa el counter en cada TX y lo persiste en RTC memory.
 *
 * Dependencia: mbedtls (incluido en ESP-IDF / Arduino ESP32 core)
 */

#pragma once
#include <mbedtls/aes.h>
#include <mbedtls/md.h>
#include <esp_system.h>
#include <esp_efuse.h>
#include <string.h>

// Sequence counter en RTC memory (persiste deep sleep, se pierde en power cycle)
static RTC_DATA_ATTR uint16_t rtc_lora_seq = 0;

// Clave AES-128 derivada (se calcula una vez en init)
static uint8_t _aes_key[16];
static bool    _crypto_ready = false;

/*
 * Deriva la clave AES-128 a partir de:
 *   - Master key (pre-shared, almacenada en NVS o hardcoded para TRL4)
 *   - MAC address del ESP32 (unique per device)
 *
 * Resultado: HMAC-SHA256(master_key, mac_address), truncado a 16 bytes.
 * Esto genera una clave única por dispositivo sin exponer la master key.
 */
static const uint8_t MASTER_KEY[] = "HydroVision-TRL4-AES";  // TODO: mover a NVS en TRL5

bool crypto_init() {
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);

    // HMAC-SHA256(master_key, mac) → 32 bytes → truncar a 16 para AES-128
    uint8_t hmac_out[32];
    mbedtls_md_context_t ctx;
    mbedtls_md_init(&ctx);
    mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 1);
    mbedtls_md_hmac_starts(&ctx, MASTER_KEY, sizeof(MASTER_KEY) - 1);
    mbedtls_md_hmac_update(&ctx, mac, 6);
    mbedtls_md_hmac_finish(&ctx, hmac_out);
    mbedtls_md_free(&ctx);

    memcpy(_aes_key, hmac_out, 16);
    _crypto_ready = true;

    Serial.printf("[CRYPTO] AES-128 key derived from MAC %02X:%02X:%02X:%02X:%02X:%02X\n",
                  mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    return true;
}

/*
 * Construye el IV (16 bytes) para AES-128-CTR:
 *   [6 bytes MAC][2 bytes seq][8 bytes 0x00]
 */
static void _build_iv(uint16_t seq, uint8_t iv[16]) {
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    memcpy(iv, mac, 6);
    iv[6] = (uint8_t)(seq >> 8);
    iv[7] = (uint8_t)(seq & 0xFF);
    memset(iv + 8, 0, 8);
}

/*
 * Cifra un buffer in-place con AES-128-CTR.
 * Prepone 2 bytes de sequence counter al output.
 *
 * Parámetros:
 *   plaintext   — datos a cifrar (se sobreescriben)
 *   len         — largo del plaintext
 *   out         — buffer de salida (debe tener al menos len + 2 bytes)
 *   out_len     — se escribe el largo total del output (2 + len)
 *
 * Retorna true si ok, false si crypto no inicializado.
 */
bool crypto_encrypt(const uint8_t* plaintext, size_t len,
                    uint8_t* out, size_t* out_len) {
    if (!_crypto_ready) return false;

    rtc_lora_seq++;
    uint16_t seq = rtc_lora_seq;

    // Preponer sequence counter (big-endian)
    out[0] = (uint8_t)(seq >> 8);
    out[1] = (uint8_t)(seq & 0xFF);

    // AES-128-CTR
    uint8_t iv[16];
    _build_iv(seq, iv);

    mbedtls_aes_context aes;
    mbedtls_aes_init(&aes);
    mbedtls_aes_setkey_enc(&aes, _aes_key, 128);

    size_t nc_off = 0;
    uint8_t stream_block[16] = {0};
    mbedtls_aes_crypt_ctr(&aes, len, &nc_off, iv, stream_block,
                          plaintext, out + 2);
    mbedtls_aes_free(&aes);

    *out_len = 2 + len;
    return true;
}

/*
 * Descifra un paquete recibido (para gateway o testing).
 *
 * Parámetros:
 *   encrypted   — paquete completo [2 bytes seq + ciphertext]
 *   enc_len     — largo total
 *   out         — buffer de salida para plaintext
 *   out_len     — largo del plaintext (enc_len - 2)
 *   seq_out     — sequence counter extraído (para validación anti-replay)
 *
 * Retorna true si ok.
 */
bool crypto_decrypt(const uint8_t* encrypted, size_t enc_len,
                    uint8_t* out, size_t* out_len, uint16_t* seq_out) {
    if (!_crypto_ready || enc_len < 3) return false;

    uint16_t seq = ((uint16_t)encrypted[0] << 8) | encrypted[1];
    if (seq_out) *seq_out = seq;

    size_t plain_len = enc_len - 2;

    uint8_t iv[16];
    _build_iv(seq, iv);

    mbedtls_aes_context aes;
    mbedtls_aes_init(&aes);
    mbedtls_aes_setkey_enc(&aes, _aes_key, 128);

    size_t nc_off = 0;
    uint8_t stream_block[16] = {0};
    mbedtls_aes_crypt_ctr(&aes, plain_len, &nc_off, iv, stream_block,
                          encrypted + 2, out);
    mbedtls_aes_free(&aes);

    *out_len = plain_len;
    return true;
}
