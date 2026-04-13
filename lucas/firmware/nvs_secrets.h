/*
 * HydroVision AG — Gestión de secrets en NVS (Non-Volatile Storage)
 *
 * Migra parámetros sensibles de config.h (hardcoded) a NVS cifrado del ESP32.
 * NVS usa cifrado flash nativo del ESP32-S3 (AES-256-XTS con clave en eFuse).
 *
 * Secrets almacenados:
 *   - lora_freq      : frecuencia LoRa (Hz)
 *   - lora_sf        : spreading factor
 *   - lora_bw        : bandwidth (Hz)
 *   - lora_tx_power  : potencia TX (dBm)
 *   - master_key     : clave maestra para derivación AES-128 por nodo
 *   - ingest_secret  : shared secret para HMAC de payload
 *   - node_id        : identificador del nodo (MAC-based o custom)
 *   - sol_canal      : canal de solenoide asignado
 *
 * Primera provisión: si NVS está vacío, se cargan valores por defecto de config.h.
 * Rotación de claves: se puede actualizar via OTA o comando serial de provisión.
 *
 * Dependencia: nvs_flash (incluido en ESP-IDF / Arduino ESP32 core)
 */

#pragma once
#include <nvs_flash.h>
#include <nvs.h>
#include "config.h"

#define NVS_NAMESPACE "hydrovision"

static nvs_handle_t _nvs_handle;
static bool _nvs_ready = false;

// Valores leídos de NVS (con fallback a config.h)
static uint32_t nvs_lora_freq     = (uint32_t)LORA_FREQ_HZ;
static uint8_t  nvs_lora_sf       = LORA_SF;
static uint32_t nvs_lora_bw       = (uint32_t)LORA_BW;
static uint8_t  nvs_lora_tx_power = LORA_TX_POWER;
static char     nvs_master_key[33]   = "HydroVision-TRL4-AES";  // default
static char     nvs_ingest_secret[65] = "dev-secret-change-in-production";
static uint8_t  nvs_sol_canal     = SOLENOIDE_CANAL;

bool nvs_secrets_init() {
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        // NVS partition was truncated, erase and retry
        nvs_flash_erase();
        err = nvs_flash_init();
    }
    if (err != ESP_OK) {
        Serial.printf("[NVS] ERROR: init failed (%s)\n", esp_err_to_name(err));
        return false;
    }

    err = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &_nvs_handle);
    if (err != ESP_OK) {
        Serial.printf("[NVS] ERROR: open failed (%s)\n", esp_err_to_name(err));
        return false;
    }

    _nvs_ready = true;

    // Leer valores existentes o escribir defaults si primera provisión
    uint32_t val32;
    uint8_t  val8;
    size_t   str_len;

    if (nvs_get_u32(_nvs_handle, "lora_freq", &val32) == ESP_OK) {
        nvs_lora_freq = val32;
    } else {
        nvs_set_u32(_nvs_handle, "lora_freq", nvs_lora_freq);
    }

    if (nvs_get_u8(_nvs_handle, "lora_sf", &val8) == ESP_OK) {
        nvs_lora_sf = val8;
    } else {
        nvs_set_u8(_nvs_handle, "lora_sf", nvs_lora_sf);
    }

    if (nvs_get_u32(_nvs_handle, "lora_bw", &val32) == ESP_OK) {
        nvs_lora_bw = val32;
    } else {
        nvs_set_u32(_nvs_handle, "lora_bw", nvs_lora_bw);
    }

    if (nvs_get_u8(_nvs_handle, "lora_tx_pwr", &val8) == ESP_OK) {
        nvs_lora_tx_power = val8;
    } else {
        nvs_set_u8(_nvs_handle, "lora_tx_pwr", nvs_lora_tx_power);
    }

    str_len = sizeof(nvs_master_key);
    if (nvs_get_str(_nvs_handle, "master_key", nvs_master_key, &str_len) != ESP_OK) {
        nvs_set_str(_nvs_handle, "master_key", nvs_master_key);
    }

    str_len = sizeof(nvs_ingest_secret);
    if (nvs_get_str(_nvs_handle, "ingest_sec", nvs_ingest_secret, &str_len) != ESP_OK) {
        nvs_set_str(_nvs_handle, "ingest_sec", nvs_ingest_secret);
    }

    if (nvs_get_u8(_nvs_handle, "sol_canal", &val8) == ESP_OK) {
        nvs_sol_canal = val8;
    } else {
        nvs_set_u8(_nvs_handle, "sol_canal", nvs_sol_canal);
    }

    nvs_commit(_nvs_handle);

    Serial.printf("[NVS] Secrets loaded — LoRa %.0f MHz SF%d, sol_canal=%d\n",
                  (float)nvs_lora_freq / 1e6, nvs_lora_sf, nvs_sol_canal);
    return true;
}

/*
 * Actualizar un secret en NVS (para provisión remota o rotación de claves).
 * Retorna true si el valor se actualizó correctamente.
 */
bool nvs_update_str(const char* key, const char* value) {
    if (!_nvs_ready) return false;
    esp_err_t err = nvs_set_str(_nvs_handle, key, value);
    if (err == ESP_OK) {
        nvs_commit(_nvs_handle);
        Serial.printf("[NVS] Updated key '%s'\n", key);
        return true;
    }
    return false;
}

bool nvs_update_u32(const char* key, uint32_t value) {
    if (!_nvs_ready) return false;
    esp_err_t err = nvs_set_u32(_nvs_handle, key, value);
    if (err == ESP_OK) {
        nvs_commit(_nvs_handle);
        return true;
    }
    return false;
}

void nvs_secrets_close() {
    if (_nvs_ready) {
        nvs_close(_nvs_handle);
        _nvs_ready = false;
    }
}
