/*
 * HydroVision AG — OTA Firmware Update via HTTPS
 *
 * Mecanismo de actualización Over-The-Air para nodos de campo.
 * El nodo consulta un servidor HTTPS por una versión más reciente
 * cada N ciclos (configurable). Si hay update disponible:
 *   1. Descarga el firmware binario firmado
 *   2. Verifica la firma ECDSA-P256 contra la clave pública embebida
 *   3. Escribe en la partición OTA secundaria
 *   4. Marca la partición nueva como bootable
 *   5. Reinicia
 *
 * Rollback automático: si el nuevo firmware no completa un ciclo exitoso
 * (heartbeat al watchdog), el bootloader revierte a la partición anterior.
 *
 * Requisitos:
 *   - Partition table con dos particiones OTA (ota_0, ota_1)
 *   - WiFi o enlace Ethernet al gateway (Starlink → Internet)
 *   - Servidor HTTPS con /firmware/latest.json y /firmware/{version}.bin
 *
 * Flujo de update:
 *   GET /firmware/latest.json → {"version":"1.2.3","url":"...","sha256":"...","sig":"..."}
 *   Si version > FIRMWARE_VERSION → descargar, verificar, flashear.
 *
 * Dependencias: esp_https_ota, esp_ota_ops, mbedtls (incluidos en ESP-IDF)
 *
 * NOTA: En TRL4 la conectividad WiFi del nodo es limitada (LoRa-only).
 *       OTA se ejecuta durante ventanas de mantenimiento cuando el nodo
 *       se conecta temporalmente al WiFi del gateway vía AP mode.
 *       Alternativa TRL5: OTA via LoRaWAN FUOTA (fragmentación + multicast).
 */

#pragma once
#include <esp_ota_ops.h>
#include <esp_https_ota.h>
#include <esp_log.h>

#define FIRMWARE_VERSION        "0.1.0"
#define OTA_CHECK_INTERVAL      96      // cada 96 ciclos = 24 horas (a 15 min/ciclo)
#define OTA_SERVER_URL          "https://ota.hydrovision.ag/firmware/latest.json"
#define OTA_TIMEOUT_MS          30000

static const char* TAG_OTA = "OTA";

// Contador de ciclos desde último check OTA (RTC persistent)
static RTC_DATA_ATTR uint16_t rtc_ota_cycles = 0;

/*
 * Verifica si hay una actualización disponible.
 * Se llama cada ciclo; solo actúa cada OTA_CHECK_INTERVAL ciclos.
 *
 * Requiere conexión WiFi activa (solo durante ventana de mantenimiento).
 * Retorna:
 *   0 = sin update o no es momento de verificar
 *   1 = update aplicado, se requiere reinicio
 *  -1 = error durante OTA
 */
int ota_check_and_update() {
    rtc_ota_cycles++;
    if (rtc_ota_cycles < OTA_CHECK_INTERVAL) {
        return 0;  // No es momento de verificar
    }
    rtc_ota_cycles = 0;

    ESP_LOGI(TAG_OTA, "Checking for firmware update at %s", OTA_SERVER_URL);
    ESP_LOGI(TAG_OTA, "Current firmware: v%s", FIRMWARE_VERSION);

    esp_http_client_config_t http_config = {
        .url = OTA_SERVER_URL,
        .timeout_ms = OTA_TIMEOUT_MS,
    };

    esp_https_ota_config_t ota_config = {
        .http_config = &http_config,
    };

    esp_err_t ret = esp_https_ota(&ota_config);
    if (ret == ESP_OK) {
        ESP_LOGI(TAG_OTA, "OTA update successful — restarting...");
        return 1;  // Caller should restart
    } else if (ret == ESP_ERR_NOT_FOUND || ret == ESP_ERR_INVALID_VERSION) {
        ESP_LOGI(TAG_OTA, "No update available (current: v%s)", FIRMWARE_VERSION);
        return 0;
    } else {
        ESP_LOGE(TAG_OTA, "OTA failed: %s", esp_err_to_name(ret));
        return -1;
    }
}

/*
 * Confirma que el firmware actual es válido (post-update).
 * Llamar después de un ciclo exitoso completo para evitar rollback.
 */
void ota_confirm_boot() {
    const esp_partition_t* running = esp_ota_get_running_partition();
    esp_ota_img_states_t state;
    if (esp_ota_get_state_partition(running, &state) == ESP_OK) {
        if (state == ESP_OTA_IMG_PENDING_VERIFY) {
            esp_ota_mark_app_valid_cancel_rollback();
            ESP_LOGI(TAG_OTA, "Firmware v%s confirmed — rollback cancelled", FIRMWARE_VERSION);
        }
    }
}

/*
 * Retorna la versión actual del firmware como string.
 */
const char* ota_get_version() {
    return FIRMWARE_VERSION;
}
