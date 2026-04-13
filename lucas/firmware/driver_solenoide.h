/*
 * HydroVision AG — Driver Solenoide (control de riego autónomo)
 * Plataforma: ESP32-S3 (Arduino framework)
 *
 * Controla un relé SSR conectado a un solenoide Rain Bird 24VAC.
 * El nodo decide autónomamente cuándo regar basándose en el HSI.
 * El backend solo se entera del estado via el payload /ingest.
 *
 * Arquitectura Tier 3:
 *   Nodo ESP32-S3 → GPIO → SSR relé → Solenoide Rain Bird 24VAC
 *
 * Si SOLENOIDE_CANAL == 0, toda la lógica de riego se desactiva
 * automáticamente (nodo Tier 1-2, solo sensor).
 */

#pragma once
#include "config.h"

// ─────────────────────────────────────────
// Estado persistente entre ciclos de deep sleep
// ─────────────────────────────────────────
RTC_DATA_ATTR bool     rtc_solenoide_activo     = false;
RTC_DATA_ATTR uint8_t  rtc_solenoide_ciclos     = 0;     // ciclos consecutivos activo
RTC_DATA_ATTR uint32_t rtc_solenoide_activado_ts = 0;    // timestamp de activación
RTC_DATA_ATTR char     rtc_solenoide_razon[16]  = "idle"; // razón última acción
RTC_DATA_ATTR bool     rtc_sol_sim              = false;  // modo simulación (controlado desde web)

// ─────────────────────────────────────────
// Estructura de resultado para incluir en payload
// ─────────────────────────────────────────
struct SolenoideState {
    uint8_t  canal;           // canal Rain Bird (0 = sin solenoide)
    bool     active;          // estado actual del relé
    uint8_t  ciclos_activo;   // ciclos consecutivos encendido
    uint32_t activado_ts;     // timestamp de última activación
    const char* reason;       // "hsi_alto" | "hsi_bajo" | "max_ciclos" | "lluvia" |
                              // "fuera_ventana" | "manual_on" | "manual_off" | "idle"
};

// ─────────────────────────────────────────
// Inicialización
// ─────────────────────────────────────────
inline bool solenoide_tiene() {
    return SOLENOIDE_CANAL > 0;
}

inline void solenoide_init() {
    if (!solenoide_tiene()) return;
    if (!rtc_sol_sim) {
        pinMode(PIN_SOLENOIDE, OUTPUT);
        // Restaurar estado del relé desde RTC memory (persistente en deep sleep)
        digitalWrite(PIN_SOLENOIDE, rtc_solenoide_activo ? HIGH : LOW);
    }
    Serial.printf("[SOL] Init canal=%d estado=%s ciclos=%u%s\n",
                  SOLENOIDE_CANAL,
                  rtc_solenoide_activo ? "ACTIVO" : "inactivo",
                  rtc_solenoide_ciclos,
                  rtc_sol_sim ? " (SIMULACION)" : "");
}

// ─────────────────────────────────────────
// Activar / desactivar relé
// ─────────────────────────────────────────
inline void _solenoide_abrir(uint32_t ts, const char* razon) {
    if (!rtc_sol_sim) {
        digitalWrite(PIN_SOLENOIDE, HIGH);
    }
    if (!rtc_solenoide_activo) {
        // Transición OFF → ON
        rtc_solenoide_activado_ts = ts;
        rtc_solenoide_ciclos = 0;
    }
    rtc_solenoide_activo = true;
    rtc_solenoide_ciclos++;
    strncpy(rtc_solenoide_razon, razon, sizeof(rtc_solenoide_razon) - 1);
    Serial.printf("[SOL] %sABIERTO — razón=%s ciclo=%u\n",
                  rtc_sol_sim ? "(SIM) " : "",
                  razon, rtc_solenoide_ciclos);
}

inline void _solenoide_cerrar(const char* razon) {
    if (!rtc_sol_sim) {
        digitalWrite(PIN_SOLENOIDE, LOW);
    }
    rtc_solenoide_activo = false;
    rtc_solenoide_ciclos = 0;
    strncpy(rtc_solenoide_razon, razon, sizeof(rtc_solenoide_razon) - 1);
    Serial.printf("[SOL] %sCERRADO — razón=%s\n",
                  rtc_sol_sim ? "(SIM) " : "",
                  razon);
}

// ─────────────────────────────────────────
// Lógica autónoma de riego
//
// Llamar una vez por ciclo después de calcular HSI.
// Retorna el estado actual para incluir en el payload JSON.
//
// Decisión local, sin depender de conectividad:
//   1. Protecciones: lluvia, fuera de ventana, max ciclos
//   2. HSI >= umbral activar → abrir
//   3. HSI <  umbral desactivar → cerrar (histéresis)
// ─────────────────────────────────────────
SolenoideState solenoide_evaluar(float hsi, uint32_t ts,
                                  const char* calidad_captura,
                                  int hora_local,
                                  FenolEstadio estadio) {
    SolenoideState st = {};
    st.canal = SOLENOIDE_CANAL;

    if (!solenoide_tiene()) {
        st.active = false;
        st.reason = "sin_solenoide";
        return st;
    }

    // --- Protección 0: inhibir riego en dormancia y post-cosecha ---
    // En reposo la vid no transpira. Regar favorece enfermedades fúngicas
    // y retrasa la lignificación del sarmiento. Ref: Keller 2010, Chapter 4.
    if (estadio == FENOL_DORMANCIA || estadio == FENOL_POST_COSECHA) {
        if (rtc_solenoide_activo) _solenoide_cerrar("reposo");
        st.active = false;
        st.ciclos_activo = 0;
        st.reason = "reposo";
        Serial.printf("[SOL] Riego inhibido — %s (Ky~0.10)\n",
                      FENOL_NOMBRES[estadio]);
        return st;
    }

    // --- Protección 1: inhibir riego durante lluvia ---
    if (RIEGO_INHIBIR_LLUVIA &&
        (strcmp(calidad_captura, "lluvia") == 0 ||
         strcmp(calidad_captura, "post_lluvia") == 0)) {
        if (rtc_solenoide_activo) _solenoide_cerrar("lluvia");
        st.active = false;
        st.ciclos_activo = 0;
        st.reason = "lluvia";
        return st;
    }

    // --- Protección 2: fuera de ventana horaria ---
    if (hora_local < RIEGO_VENTANA_INI || hora_local >= RIEGO_VENTANA_FIN) {
        if (rtc_solenoide_activo) _solenoide_cerrar("fuera_ventana");
        st.active = false;
        st.ciclos_activo = 0;
        st.reason = "fuera_ventana";
        return st;
    }

    // --- Protección 3: duración máxima (anti-fuga) ---
    if (rtc_solenoide_activo && rtc_solenoide_ciclos >= RIEGO_MAX_CICLOS) {
        _solenoide_cerrar("max_ciclos");
        st.active = false;
        st.ciclos_activo = 0;
        st.reason = "max_ciclos";
        return st;
    }

    // --- Decisión por HSI con histéresis ---
    // Usar umbral dinámico por estadio fenológico en lugar del fijo
    float umbral_activar   = CWSI_UMBRAL_POR_ESTADIO[estadio];
    float umbral_desactivar = umbral_activar - 0.10f;  // histéresis de 0.10

    if (hsi >= umbral_activar && !rtc_solenoide_activo) {
        _solenoide_abrir(ts, "hsi_alto");
    } else if (hsi < umbral_desactivar && rtc_solenoide_activo) {
        _solenoide_cerrar("hsi_bajo");
    }
    // Si está activo y HSI en zona de histéresis: mantener abierto

    st.active = rtc_solenoide_activo;
    st.ciclos_activo = rtc_solenoide_ciclos;
    st.activado_ts = rtc_solenoide_activado_ts;
    st.reason = rtc_solenoide_razon;
    return st;
}

// ─────────────────────────────────────────
// Pre-sleep: NO apagar el relé — debe mantener estado durante deep sleep.
// El GPIO del ESP32-S3 mantiene su nivel durante deep sleep si está
// configurado como RTC GPIO (hold). Usamos esp_sleep_pd_config()
// o rtc_gpio_hold_en() para garantizarlo.
// ─────────────────────────────────────────
inline void solenoide_pre_sleep() {
    if (!solenoide_tiene()) return;
    if (rtc_sol_sim) return;  // no hay GPIO que mantener
    // Mantener el estado del GPIO durante deep sleep
    gpio_hold_en((gpio_num_t)PIN_SOLENOIDE);
    // Para liberar al despertar: gpio_hold_dis() se llama implícitamente
    // al hacer pinMode() en solenoide_init()
}
