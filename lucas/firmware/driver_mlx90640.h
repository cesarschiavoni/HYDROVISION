/*
 * HydroVision AG — Driver MLX90640 (cámara térmica LWIR)
 * Librería: Adafruit_MLX90640 (instalar desde Arduino Library Manager)
 *
 * Retorna: tc_mean, tc_max y valid_pixels de la región foliar.
 * Filtro foliar P20–P75: elimina fondo frío (cielo/suelo) y puntos calientes
 * (reflexión solar directa). Solo los píxeles en ese rango pertenecen al canopeo.
 */

#pragma once
#include <Adafruit_MLX90640.h>
#include "config.h"

Adafruit_MLX90640 mlx;
static float _mlx_frame[32 * 24];   // 768 píxeles

bool mlx_init() {
    if (!mlx.begin(MLX90640_I2C_ADDR, &Wire)) {
        Serial.println("[MLX] ERROR: no encontrado en I2C");
        return false;
    }
    mlx.setMode(MLX90640_CHESS);
    mlx.setResolution(MLX90640_ADC_18BIT);
    mlx.setRefreshRate(MLX_REFRESH_RATE);
    Serial.println("[MLX] OK");
    return true;
}

// Compara dos floats para qsort
static int _cmp_float(const void* a, const void* b) {
    float fa = *(const float*)a, fb = *(const float*)b;
    return (fa > fb) - (fa < fb);
}

struct MlxResult {
    float    tc_mean;       // temperatura media foliar (°C)
    float    tc_max;        // temperatura máxima foliar (°C)
    uint16_t valid_pixels;  // píxeles dentro del rango foliar (P20-P75, puede superar 255 de 768)
    bool     ok;
};

// ─────────────────────────────────────────
// ISO_nodo — Auto-diagnóstico de lente (obstrucción por polvo/rocío)
//
// Principio: los paneles Dry Ref y Wet Ref están en posiciones fijas conocidas
// del frame (calibrar en instalación con mlx_calibrar_iso_nodo()).
// Si T_dry_ref_medido > T_dry_ref_esperado + ISO_DELTA_MAX → lente sucio.
//
// T_dry_ref_esperado ≈ T_aire + 15°C (panel aluminio negro en sol directo).
// ISO_nodo = 0–100 (100 = lente limpio, < 80 = requiere limpieza).
// ─────────────────────────────────────────
#define ISO_DRY_ROW_DEFAULT    20   // fila del píxel Dry Ref (calibrar en campo)
#define ISO_DRY_COL_DEFAULT    28   // columna del píxel Dry Ref (calibrar en campo)
#define ISO_WET_ROW_DEFAULT    20   // fila del píxel Wet Ref
#define ISO_WET_COL_DEFAULT    4    // columna del píxel Wet Ref
#define ISO_DELTA_MAX          3.0f // °C — desviación máxima aceptable Dry Ref

static uint8_t _iso_dry_row = ISO_DRY_ROW_DEFAULT;
static uint8_t _iso_dry_col = ISO_DRY_COL_DEFAULT;
static uint8_t _iso_wet_row = ISO_WET_ROW_DEFAULT;
static uint8_t _iso_wet_col = ISO_WET_COL_DEFAULT;

// Permite calibrar en campo las coordenadas de los paneles de referencia.
// Llamar durante instalación: apuntar al frame cuando ambos paneles son visibles.
void mlx_calibrar_iso_nodo(uint8_t dry_row, uint8_t dry_col,
                            uint8_t wet_row, uint8_t wet_col) {
    _iso_dry_row = dry_row;
    _iso_dry_col = dry_col;
    _iso_wet_row = wet_row;
    _iso_wet_col = wet_col;
    Serial.printf("[MLX] ISO calibrado: Dry[%u,%u] Wet[%u,%u]\n",
                  dry_row, dry_col, wet_row, wet_col);
}

struct IsoResult {
    float   t_dry_ref;     // temperatura medida del panel Dry Ref (°C)
    float   t_wet_ref;     // temperatura medida del panel Wet Ref (°C)
    uint8_t iso_nodo;      // 0–100 (100 = limpio; <80 = limpiar)
    bool    lente_sucio;   // true si iso_nodo < 80
    bool    ok;
};

// Evalúa ISO_nodo a partir del último frame capturado (llamar después de mlx_read()).
// t_air: temperatura del aire del ciclo actual (para estimar T_dry_ref esperado).
IsoResult mlx_iso_nodo(float t_air) {
    IsoResult r = {0, 0, 100, false, false};

    uint16_t idx_dry = _iso_dry_row * 32 + _iso_dry_col;
    uint16_t idx_wet = _iso_wet_row * 32 + _iso_wet_col;

    if (idx_dry >= 768 || idx_wet >= 768) {
        Serial.println("[MLX] ISO ERROR: coordenadas fuera de rango");
        return r;
    }

    r.t_dry_ref = _mlx_frame[idx_dry];
    r.t_wet_ref = _mlx_frame[idx_wet];
    r.ok        = true;

    // T_dry_ref esperado: aluminio negro en sol directo ≈ T_aire + 15°C
    // (ajustar con mediciones reales en campo)
    float t_dry_esperado = t_air + 15.0f;
    float delta = fabsf(r.t_dry_ref - t_dry_esperado);

    // ISO = 100 si delta=0, 0 si delta > ISO_DELTA_MAX × 3
    float iso_f = 100.0f * (1.0f - fminf(delta / (ISO_DELTA_MAX * 3.0f), 1.0f));
    r.iso_nodo    = (uint8_t)iso_f;
    r.lente_sucio = (r.iso_nodo < 80);

    Serial.printf("[MLX] ISO: Dry=%.1f°C Wet=%.1f°C esperado=%.1f → ISO=%u%s\n",
                  r.t_dry_ref, r.t_wet_ref, t_dry_esperado,
                  r.iso_nodo, r.lente_sucio ? " ⚠ LENTE SUCIO" : "");
    return r;
}

MlxResult mlx_read() {
    MlxResult r = {0, 0, 0, false};

    if (mlx.getFrame(_mlx_frame) != 0) {
        Serial.println("[MLX] ERROR: fallo de lectura de frame");
        return r;
    }

    // Copiar a array auxiliar para ordenar y calcular percentiles
    float sorted[768];
    memcpy(sorted, _mlx_frame, sizeof(sorted));
    qsort(sorted, 768, sizeof(float), _cmp_float);

    float p20 = sorted[(int)(768 * 0.20f)];
    float p75 = sorted[(int)(768 * 0.75f)];

    // Filtrar píxeles foliares
    float sum = 0;
    uint8_t count = 0;
    float tc_max = -999.0f;

    for (int i = 0; i < 768; i++) {
        float t = _mlx_frame[i];
        if (t >= p20 && t <= p75) {
            sum += t;
            if (t > tc_max) tc_max = t;
            count++;
        }
    }

    if (count == 0) {
        Serial.println("[MLX] WARN: 0 píxeles foliares válidos");
        return r;
    }

    r.tc_mean     = sum / count;
    r.tc_max      = tc_max;
    r.valid_pixels = count;
    r.ok          = true;

    Serial.printf("[MLX] tc_mean=%.2f tc_max=%.2f valid_px=%u (P20=%.1f P75=%.1f)\n",
                  r.tc_mean, r.tc_max, r.valid_pixels, p20, p75);
    return r;
}
