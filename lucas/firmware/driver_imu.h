/*
 * HydroVision AG — Driver ICM-42688-P (IMU 6-DOF)
 * Interfaz: SPI (bus compartido con LoRa, CS separado en PIN_IMU_CS)
 * Librería: SparkFun ICM-42688-P (instalar desde Library Manager)
 *
 * Propósito en HydroVision:
 *   1. Verificar estabilización del gimbal antes de capturar frame MLX90640
 *      → si |accel| > IMU_VIB_UMBRAL_MS2, esperar y reintentar (máx 3 veces)
 *   2. Detectar movimiento del nodo por viento extremo o vandalismo
 *      → incluir flag "imu_movimiento" en el payload de status
 *
 * Reivindicación patente #1: nodo fijo con gimbal + IMU para compensación
 * de vibración → este driver es parte del diferencial patentable.
 */

#pragma once
#include <SparkFun_ICM42688.h>
#include <SPI.h>
#include "config.h"

static ICM42688 _imu(SPI, PIN_IMU_CS);

struct ImuResult {
    float ax;        // aceleración X (m/s²)
    float ay;        // aceleración Y (m/s²)
    float az;        // aceleración Z (m/s²)
    float gx;        // giróscopo X (deg/s)
    float gy;        // giróscopo Y (deg/s)
    float gz;        // giróscopo Z (deg/s)
    float magnitud;  // |a| = sqrt(ax²+ay²+az²) en m/s²
    bool  ok;
};

bool imu_init() {
    if (_imu.begin() < 0) {
        Serial.println("[IMU] ERROR: ICM-42688-P no encontrado en SPI");
        return false;
    }
    // Rango acelerómetro ±2g (suficiente para detectar vibración de campo)
    _imu.setAccelFS(ICM42688::gpm2);
    // Rango giróscopo ±250 dps
    _imu.setGyroFS(ICM42688::dps250);
    // ODR 100 Hz (más que suficiente; el nodo lee en polling)
    _imu.setAccelODR(ICM42688::odr100);
    _imu.setGyroODR(ICM42688::odr100);

    // Pin INT1: configurar como entrada (polling — no se usa interrupción)
    if (PIN_IMU_INT1 >= 0) {
        pinMode(PIN_IMU_INT1, INPUT);
    }

    Serial.println("[IMU] OK — ICM-42688-P");
    return true;
}

ImuResult imu_read() {
    ImuResult r = {0, 0, 0, 0, 0, 0, 0, false};

    _imu.getAGT();  // actualiza datos internos de la librería

    // Convertir a m/s² (la librería retorna en g, 1g = 9.80665 m/s²)
    const float G = 9.80665f;
    r.ax = _imu.accX() * G;
    r.ay = _imu.accY() * G;
    r.az = _imu.accZ() * G;

    r.gx = _imu.gyrX();
    r.gy = _imu.gyrY();
    r.gz = _imu.gyrZ();

    // Magnitud total de aceleración (en reposo debe ser ~9.8 m/s²; vibraciones suman)
    float magnitud_total = sqrtf(r.ax*r.ax + r.ay*r.ay + r.az*r.az);
    // Vibración = desviación respecto a gravedad estática
    r.magnitud = fabsf(magnitud_total - G);

    r.ok = true;

    Serial.printf("[IMU] vib=%.3f m/s² (ax=%.2f ay=%.2f az=%.2f)\n",
                  r.magnitud, r.ax, r.ay, r.az);
    return r;
}

/*
 * Verifica si hay vibración excesiva que invalide la captura térmica.
 * Espera hasta que la vibración se calme (máx REINTENTOS × 500 ms).
 * Retorna true si el nodo está estable al final del intento.
 */
bool imu_esperar_estabilidad(uint8_t reintentos = 3) {
    for (uint8_t i = 0; i < reintentos; i++) {
        ImuResult r = imu_read();
        if (!r.ok) return true;  // si el IMU falla, no bloquear captura
        if (r.magnitud <= IMU_VIB_UMBRAL_MS2) {
            return true;  // estable
        }
        Serial.printf("[IMU] vib=%.3f > umbral=%.2f — esperando... (%d/%d)\n",
                      r.magnitud, IMU_VIB_UMBRAL_MS2, i + 1, reintentos);
        delay(500);
    }
    Serial.println("[IMU] WARN: vibración persistente — frame marcado igualmente");
    return false;  // sigue vibrando, pero no bloqueamos; la calidad la registra el payload
}

/*
 * Detecta si el nodo fue movido desde el último ciclo.
 * Compara orientación actual (eje Z del acelerómetro) con valor esperado
 * de un nodo fijo (az ≈ −g). Variación > 0.5g indica desplazamiento.
 */
bool imu_nodo_desplazado() {
    ImuResult r = imu_read();
    if (!r.ok) return false;
    const float G = 9.80665f;
    // En nodo vertical fijo: az ≈ −g (±0.3g tolerancia)
    return (fabsf(r.az + G) > 0.3f * G);
}
