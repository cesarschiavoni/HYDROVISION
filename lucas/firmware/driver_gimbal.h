/*
 * HydroVision AG — Driver gimbal MG90S (2 ejes: PAN + TILT)
 * Conexión: PIN_SERVO_PAN + PIN_SERVO_TILT → señal PWM 50 Hz, pulso 500–2500 µs
 * Librería: ESP32 LEDC (arduino-esp32 ≥ 3.0, API nueva)
 *
 * Secuencia de captura multi-angular:
 *   5 posiciones fijas + 1 condicional (viento > 20 km/h = 5.56 m/s)
 *   En cada posición: esperar GIMBAL_SETTLE_MS + capturar frame MLX90640
 *   Resultado: tc_mean fusionada (promedio de posiciones válidas)
 *
 * Referencia de ángulos: Pan 0° = frente, Tilt 0° = horizontal
 * Positivo: Pan = giro derecha, Tilt = inclinación hacia arriba
 */

#pragma once
#include "config.h"
#include "driver_mlx90640.h"

// ─────────────────────────────────────────
// LEDC helpers (arduino-esp32 ≥ 3.0)
// ─────────────────────────────────────────
#define _SERVO_RES_BITS  16
#define _SERVO_PERIOD_US 20000UL   // 50 Hz = 20 ms

static uint32_t _us_to_duty(uint32_t pulse_us) {
    // duty = pulse_us / period_us * 2^bits
    return (uint32_t)((uint64_t)pulse_us * ((1UL << _SERVO_RES_BITS) - 1) / _SERVO_PERIOD_US);
}

// Convierte grados (-90..+90 relativo a centro) a microsegundos de pulso
static uint32_t _deg_to_us(int8_t deg) {
    // Mapear -90°..+90° → SERVO_MIN_US..SERVO_MAX_US
    int32_t us = SERVO_CENTER_US + (int32_t)deg * (SERVO_MAX_US - SERVO_MIN_US) / 180;
    if (us < SERVO_MIN_US) us = SERVO_MIN_US;
    if (us > SERVO_MAX_US) us = SERVO_MAX_US;
    return (uint32_t)us;
}

static void _servo_write_deg(uint8_t pin, int8_t deg) {
    ledcWrite(pin, _us_to_duty(_deg_to_us(deg)));
}

bool gimbal_init() {
    if (!ledcAttach(PIN_SERVO_PAN,  SERVO_FREQ_HZ, _SERVO_RES_BITS)) {
        Serial.println("[GIMBAL] ERROR: ledcAttach PAN");
        return false;
    }
    if (!ledcAttach(PIN_SERVO_TILT, SERVO_FREQ_HZ, _SERVO_RES_BITS)) {
        Serial.println("[GIMBAL] ERROR: ledcAttach TILT");
        return false;
    }
    // Mover a centro
    _servo_write_deg(PIN_SERVO_PAN,  0);
    _servo_write_deg(PIN_SERVO_TILT, 0);
    delay(GIMBAL_SETTLE_MS);
    Serial.println("[GIMBAL] OK — servos centrados");
    return true;
}

// Deshabilitar PWM antes de deep sleep (evita consumo residual del servo)
void gimbal_deinit() {
    ledcWrite(PIN_SERVO_PAN,  0);
    ledcWrite(PIN_SERVO_TILT, 0);
    ledcDetach(PIN_SERVO_PAN);
    ledcDetach(PIN_SERVO_TILT);
}

// ─────────────────────────────────────────
// Tabla de posiciones
// ─────────────────────────────────────────
struct GimbalPos {
    int8_t pan;   // grados (relativo a centro)
    int8_t tilt;  // grados (relativo a horizontal)
};

// 5 posiciones fijas
static const GimbalPos _pos_fijas[5] = {
    {  0,   0 },  // 0: Centro (referencia)
    { GIMBAL_PAN_L,  0 },  // 1: Izquierda
    { GIMBAL_PAN_R,  0 },  // 2: Derecha
    {  0, GIMBAL_TILT_UP   },  // 3: Arriba
    {  0, GIMBAL_TILT_DOWN },  // 4: Abajo
};

// 1 posición condicional: nadir (plomada) — para viento > 20 km/h = 5.56 m/s
// Minimiza error de perspectiva cuando el dosel se mueve
static const GimbalPos _pos_nadir = { 0, -30 };

// ─────────────────────────────────────────
// Captura multi-angular fusionada
// ─────────────────────────────────────────
struct GimbalFusionResult {
    float    tc_mean;        // temperatura foliar media fusionada (°C)
    float    tc_max;         // máximo global entre todas las posiciones
    uint16_t valid_pixels;   // promedio de píxeles foliares válidos por frame
    uint8_t  n_frames;       // número de frames válidos capturados
    bool     ok;
};

GimbalFusionResult gimbal_capturar(float wind_ms) {
    GimbalFusionResult result = {0.0f, 0.0f, 0, false};

    bool usar_nadir = (wind_ms > 5.56f);  // > 20 km/h
    uint8_t n_pos = usar_nadir ? 6 : 5;

    float    sum_tc_mean = 0.0f;
    float    max_tc      = -999.0f;
    uint32_t sum_pixels  = 0;   // uint32 para sumar hasta 6 frames × 422 px sin overflow
    uint8_t  validos     = 0;

    for (uint8_t i = 0; i < n_pos; i++) {
        GimbalPos pos;
        if (i < 5) {
            pos = _pos_fijas[i];
        } else {
            pos = _pos_nadir;
            Serial.println("[GIMBAL] pos condicional: nadir (viento alto)");
        }

        // Mover servo
        _servo_write_deg(PIN_SERVO_PAN,  pos.pan);
        _servo_write_deg(PIN_SERVO_TILT, pos.tilt);
        delay(GIMBAL_SETTLE_MS);

        // Capturar frame MLX90640
        MlxResult frame = mlx_read();
        if (!frame.ok) {
            Serial.printf("[GIMBAL] pos %d: frame MLX inválido — skip\n", i);
            continue;
        }

        sum_tc_mean += frame.tc_mean;
        if (frame.tc_max > max_tc) max_tc = frame.tc_max;
        sum_pixels  += frame.valid_pixels;
        validos++;

        Serial.printf("[GIMBAL] pos %d (pan=%d° tilt=%d°): tc_mean=%.2f°C px=%u\n",
                      i, pos.pan, pos.tilt, frame.tc_mean, frame.valid_pixels);
    }

    // Volver al centro al terminar
    _servo_write_deg(PIN_SERVO_PAN,  0);
    _servo_write_deg(PIN_SERVO_TILT, 0);

    if (validos == 0) {
        Serial.println("[GIMBAL] ERROR: ningún frame válido");
        return result;
    }

    result.tc_mean       = sum_tc_mean / validos;
    result.tc_max        = max_tc;
    result.valid_pixels  = (uint16_t)(sum_pixels / validos);  // promedio por frame
    result.n_frames      = validos;
    result.ok            = true;

    Serial.printf("[GIMBAL] Fusión %u frames: tc_mean=%.2f°C tc_max=%.2f°C\n",
                  validos, result.tc_mean, result.tc_max);
    return result;
}
