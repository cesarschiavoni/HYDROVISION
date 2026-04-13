/*
 * HydroVision AG — Motor GDD y Fenología Autónoma (multi-varietal)
 * Plataforma: ESP32-S3 (no depende de conectividad)
 *
 * Calcula Growing Degree Days (GDD) y detecta el estadio fenológico actual,
 * ajustando automáticamente los umbrales CWSI y la inhibición de riego.
 *
 * El nodo recibe el varietal de su zona desde el backend en la respuesta
 * de /ingest (campo "varietal"). Lo persiste en RTC memory.
 *
 * Variedades soportadas:
 *   VID_MALBEC, VID_CABERNET, VID_BONARDA, VID_SYRAH, OLIVO, CEREZO
 *
 * Modelo GDD:
 *   GDD_diario = max(0, T_media_diaria - T_base)
 *   T_base: 10°C vid (Winkler 1974), 12.5°C olivo (Connor & Fereres 2005)
 *   Acumulación desde 1° septiembre. Reset automático anual.
 *
 * Persistencia: acumuladores en RTC_DATA_ATTR (sobreviven deep sleep).
 */

#pragma once
#include <Arduino.h>
#include "config.h"

// ─────────────────────────────────────────
// Variedades soportadas
// ─────────────────────────────────────────
typedef enum {
    VARIETAL_DESCONOCIDO    = 0,
    VARIETAL_VID_MALBEC     = 1,
    VARIETAL_VID_CABERNET   = 2,
    VARIETAL_VID_BONARDA    = 3,
    VARIETAL_VID_SYRAH      = 4,
    VARIETAL_OLIVO          = 5,
    VARIETAL_CEREZO         = 6,
} VarietalId;

#define VARIETAL_COUNT  7

static const char* VARIETAL_NOMBRES[] = {
    "desconocido", "vid - malbec", "vid - cabernet",
    "vid - bonarda", "vid - syrah", "olivo", "cerezo"
};

/*
 * Parsea string de varietal (del backend) a VarietalId.
 * Comparación case-insensitive parcial.
 */
VarietalId varietal_parse(const char* str) {
    if (!str || str[0] == '\0') return VARIETAL_DESCONOCIDO;
    // Buscar keywords
    if (strstr(str, "malbec"))   return VARIETAL_VID_MALBEC;
    if (strstr(str, "cabernet")) return VARIETAL_VID_CABERNET;
    if (strstr(str, "bonarda"))  return VARIETAL_VID_BONARDA;
    if (strstr(str, "syrah"))    return VARIETAL_VID_SYRAH;
    if (strstr(str, "olivo"))    return VARIETAL_OLIVO;
    if (strstr(str, "cerezo"))   return VARIETAL_CEREZO;
    // Fallback vid genérica
    if (strstr(str, "vid"))      return VARIETAL_VID_MALBEC;
    return VARIETAL_DESCONOCIDO;
}

// ─────────────────────────────────────────
// Parámetros del modelo
// ─────────────────────────────────────────
#define GDD_RESET_MES       9       // septiembre — inicio acumulación GDD (hemisferio sur)

// T_base por varietal (°C)
static const float GDD_T_BASE[] = {
    10.0f,  // DESCONOCIDO (default vid)
    10.0f,  // VID_MALBEC — Winkler 1974
    10.0f,  // VID_CABERNET
    10.0f,  // VID_BONARDA
    10.0f,  // VID_SYRAH
    12.5f,  // OLIVO — Connor & Fereres 2005
    4.5f,   // CEREZO — Richardson et al. 1974
};

// ─────────────────────────────────────────
// Estadios fenológicos
// ─────────────────────────────────────────
typedef enum {
    FENOL_DORMANCIA         = 0,
    FENOL_BROTACION         = 1,
    FENOL_DESARROLLO_FOLIAR = 2,
    FENOL_FLORACION         = 3,
    FENOL_CUAJE             = 4,
    FENOL_CRECIMIENTO_FRUTO = 5,
    FENOL_ENVERO            = 6,
    FENOL_MADURACION        = 7,
    FENOL_COSECHA           = 8,
    FENOL_POST_COSECHA      = 9,
} FenolEstadio;

#define FENOL_COUNT  10

static const char* FENOL_NOMBRES[] = {
    "dormancia", "brotacion", "desarrollo_foliar", "floracion",
    "cuaje", "crecimiento_fruto", "envero", "maduracion",
    "cosecha", "post_cosecha"
};

// ─────────────────────────────────────────
// Umbrales GDD por varietal [estadio] = gdd_inicio
// El estadio actual es el último cuyo gdd_inicio <= gdd_acum.
// Sincronizados con mvc/app.py::_GDD_MODELS
// ─────────────────────────────────────────

// Estructura: umbrales GDD para transición entre estadios
// Índice = FenolEstadio, valor = GDD mínimo para entrar en ese estadio
// DORMANCIA siempre tiene gdd=0 (antes de brotación o después de cosecha)

struct VarietalGDD {
    float   umbrales[FENOL_COUNT];   // GDD inicio de cada estadio
    float   gdd_max;                 // GDD de fin de temporada (> esto = post-cosecha)
};

// Vid — Malbec (Colonia Caroya)
// Ref: Winkler 1974, Ojeda 2002, INTA Manfredi ajustado altitudinal
static const VarietalGDD GDD_VID_MALBEC = {
    {0, 50, 130, 280, 420, 560, 820, 1050, 1380, 1500},
    1500.0f
};

// Vid — Cabernet (ciclo +2-3 semanas)
static const VarietalGDD GDD_VID_CABERNET = {
    {0, 60, 180, 320, 480, 630, 900, 1150, 1500, 1650},
    1650.0f
};

// Vid — Bonarda (similar a Malbec, ligeramente más temprano)
static const VarietalGDD GDD_VID_BONARDA = {
    {0, 45, 120, 260, 400, 540, 800, 1020, 1350, 1480},
    1480.0f
};

// Vid — Syrah (entre Malbec y Cabernet)
static const VarietalGDD GDD_VID_SYRAH = {
    {0, 50, 140, 290, 440, 580, 850, 1080, 1400, 1520},
    1520.0f
};

// Olivo (T_base=12.5°C, ciclo diferente)
// Ref: Connor & Fereres 2005, Fernández 2012 FAO-66
static const VarietalGDD GDD_OLIVO = {
    {0, 40, 100, 200, 320, 450, 650, 850, 1050, 1150},
    1150.0f
};

// Cerezo (T_base=4.5°C, floración muy temprana)
// Ref: Richardson et al. 1974, Pérez-Pastor 2009
static const VarietalGDD GDD_CEREZO = {
    {0, 100, 250, 400, 550, 750, 1000, 1250, 1500, 1650},
    1650.0f
};

// Tabla de lookup por VarietalId
static const VarietalGDD* GDD_TABLAS[] = {
    &GDD_VID_MALBEC,    // DESCONOCIDO → default Malbec
    &GDD_VID_MALBEC,    // VID_MALBEC
    &GDD_VID_CABERNET,  // VID_CABERNET
    &GDD_VID_BONARDA,   // VID_BONARDA
    &GDD_VID_SYRAH,     // VID_SYRAH
    &GDD_OLIVO,         // OLIVO
    &GDD_CEREZO,        // CEREZO
};

// ─────────────────────────────────────────
// Umbral CWSI de alerta por estadio (compartido todas las variedades)
// Fuente: Bellvert 2016, Schultz 2003, Ojeda 2002
// ─────────────────────────────────────────
static const float CWSI_UMBRAL_POR_ESTADIO[] = {
    0.90f,  // DORMANCIA
    0.35f,  // BROTACION
    0.40f,  // DESARROLLO_FOLIAR
    0.30f,  // FLORACION: crítico — estrés → aborto floral
    0.35f,  // CUAJE
    0.50f,  // CRECIMIENTO_FRUTO: RDI moderado tolerable
    0.60f,  // ENVERO: RDI severo intencional para calidad
    0.65f,  // MADURACION
    0.75f,  // COSECHA
    0.85f,  // POST_COSECHA
};

// Intervalo de deep sleep adaptativo por estadio (segundos)
static const uint32_t SLEEP_ESTADIO[] = {
    6 * 3600,  // DORMANCIA: 6h (ahorro batería)
    15 * 60,   // BROTACION
    15 * 60,   // DESARROLLO_FOLIAR
    15 * 60,   // FLORACION
    15 * 60,   // CUAJE
    15 * 60,   // CRECIMIENTO_FRUTO
    15 * 60,   // ENVERO
    15 * 60,   // MADURACION
    15 * 60,   // COSECHA
    6 * 3600,  // POST_COSECHA: 6h
};

// ─────────────────────────────────────────
// Funciones
// ─────────────────────────────────────────

/*
 * Detecta estadio fenológico según GDD acumulados y varietal.
 */
FenolEstadio gdd_estadio(float gdd_acum, VarietalId varietal = VARIETAL_VID_MALBEC) {
    const VarietalGDD* tabla = GDD_TABLAS[varietal];

    // Post-cosecha
    if (gdd_acum >= tabla->gdd_max) return FENOL_POST_COSECHA;

    // Buscar el estadio más avanzado cuyo umbral se alcanzó
    FenolEstadio estadio = FENOL_DORMANCIA;
    for (int i = FENOL_COUNT - 1; i >= 0; i--) {
        if (gdd_acum >= tabla->umbrales[i]) {
            estadio = (FenolEstadio)i;
            break;
        }
    }
    return estadio;
}

/*
 * Actualiza acumulador GDD. Usa T_base de la varietal.
 */
void gdd_actualizar(float t_air, uint8_t dia_hoy, uint8_t mes_hoy,
                    float& gdd_acum, float& t_sum_dia,
                    uint16_t& t_muestras, uint8_t& ultimo_dia,
                    uint8_t& ultimo_mes_reset,
                    VarietalId varietal = VARIETAL_VID_MALBEC)
{
    float t_base = GDD_T_BASE[varietal];

    // Reset anual: 1° de septiembre
    if (mes_hoy == GDD_RESET_MES && ultimo_mes_reset != GDD_RESET_MES) {
        gdd_acum         = 0.0f;
        t_sum_dia        = 0.0f;
        t_muestras       = 0;
        ultimo_mes_reset = GDD_RESET_MES;
        Serial.printf("[GDD] Reset anual — %s T_base=%.1f°C\n",
                      VARIETAL_NOMBRES[varietal], t_base);
    } else if (mes_hoy != GDD_RESET_MES && mes_hoy == 10) {
        ultimo_mes_reset = 0;
    }

    t_sum_dia  += t_air;
    t_muestras += 1;

    // Al cambiar de día: calcular GDD del día anterior
    if (dia_hoy != ultimo_dia && t_muestras > 0) {
        float t_media = t_sum_dia / (float)t_muestras;
        float gdd_dia = fmaxf(0.0f, t_media - t_base);
        gdd_acum  += gdd_dia;
        t_sum_dia  = 0.0f;
        t_muestras = 0;
        ultimo_dia = dia_hoy;
        Serial.printf("[GDD] Día %u: T_media=%.1f GDD_dia=%.1f acum=%.1f [%s] %s\n",
                      dia_hoy, t_media, gdd_dia, gdd_acum,
                      FENOL_NOMBRES[gdd_estadio(gdd_acum, varietal)],
                      VARIETAL_NOMBRES[varietal]);
    }
}

/*
 * Umbral CWSI de alerta para el estadio actual.
 */
float gdd_umbral_cwsi(float gdd_acum, VarietalId varietal = VARIETAL_VID_MALBEC) {
    return CWSI_UMBRAL_POR_ESTADIO[gdd_estadio(gdd_acum, varietal)];
}

/*
 * Intervalo de sleep recomendado (segundos).
 */
uint32_t gdd_sleep_interval(float gdd_acum, VarietalId varietal = VARIETAL_VID_MALBEC) {
    return SLEEP_ESTADIO[gdd_estadio(gdd_acum, varietal)];
}
