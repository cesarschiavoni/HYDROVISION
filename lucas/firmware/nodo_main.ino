/*
 * HydroVision AG — Firmware Nodo de Campo v0.3
 * Plataforma: ESP32-S3 (Arduino framework, arduino-esp32 ≥ 3.0)
 * Autor: Lucas Bergon
 *
 * Ciclo principal:
 *   1. Despertar de deep sleep
 *   2. Leer todos los sensores (ver tabla en README.md)
 *   3. Calcular HSI en nodo (CWSI + MDS con pesos adaptativos)
 *   4. Serializar payload JSON y publicar via LoRa → gateway → MQTT backend
 *   5. Volver a deep sleep 15 minutos
 *
 * Decisiones de diseño:
 *   - Node ID: MAC Wi-Fi ESP32 (burned en eFuse por Espressif, único globalmente)
 *   - Payload: JSON v1 — topic hydrovision/{node_id}/telemetry
 *   - Frecuencia: 15 min (constante de tiempo CWSI en vid > 30 min)
 *   - Cámara: MLX90640 110°×75° FOV, montada a 6m sobre canopeo
 *   - PINN: corre en backend FastAPI (no en nodo)
 *   - GPS: solo se lee en primer boot; posición se persiste en RTC memory
 *
 * Librerías requeridas (ver libraries.txt):
 *   Adafruit_MLX90640, Adafruit_SHT31, RTClib, TinyGPSPlus,
 *   OneWire, DallasTemperature, LoRa (sandeepmistry)
 */

#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <esp_mac.h>

#include "config.h"
#include "driver_mlx90640.h"
#include "driver_mds.h"
#include "driver_sht31.h"
#include "driver_rtc.h"
#include "driver_gps.h"
#include "driver_anemometro.h"
#include "driver_pluviometro.h"
#include "driver_piranometro.h"
#include "driver_bomba_wetref.h"
#include "driver_gimbal.h"
#include "driver_lora.h"
#include "driver_pms5003.h"
#include "driver_imu.h"
// #include "driver_alertas.h"  // REMOVIDO — LED+sirena eliminados del diseño
#include "driver_gdd.h"
#include "driver_solenoide.h"
#include "driver_termopar.h"

// ─────────────────────────────────────────
// MQTT topics (node_id se inserta en runtime)
// ─────────────────────────────────────────
#define TOPIC_TELEMETRY  "hydrovision/%s/telemetry"
#define TOPIC_STATUS     "hydrovision/%s/status"
#define TOPIC_ALERT      "hydrovision/%s/alert"

// ─────────────────────────────────────────
// Estructura de datos interna
// ─────────────────────────────────────────
struct SensorData {
    // Ambiente
    float   t_air;         // °C
    float   rh;            // %
    float   wind_ms;       // m/s
    float   rain_mm;       // mm acumulados en este ciclo
    float   rad_wm2;       // W/m² radiación solar

    // Térmico (MLX90640 110°×75°, fusión multi-angular)
    float    tc_mean;       // temperatura media foliar °C
    float    tc_max;        // temperatura máxima foliar °C
    float    tc_wet;        // baseline hoja bien hidratada (auto-calibrado)
    float    tc_dry;        // temperatura hoja sin transpiración (balance energético)
    uint16_t valid_pixels;  // píxeles foliares válidos (P20-P75 de 768 totales — puede superar 255)
    uint8_t  n_frames;      // frames capturados en fusión multi-angular

    // Dendrometría
    float   mds_mm;        // micro-contracción del tronco en mm (diurno)

    // Calidad de captura
    uint16_t pm2_5;              // µg/m³ (PMS5003)
    const char* calidad_captura; // "ok" | "lluvia" | "post_lluvia" | "fumigacion" | "post_fumigacion"

    // Posición
    float   lat;
    float   lon;

    // Sistema
    uint8_t bat_pct;
    uint32_t ts;           // epoch Unix
};

// ─────────────────────────────────────────
// RTC memory — persiste entre ciclos de deep sleep
// ─────────────────────────────────────────
RTC_DATA_ATTR float    rtc_lluvia_mm       = 0.0f;
RTC_DATA_ATTR float    rtc_tc_wet          = 0.0f;   // auto-calibrado en lluvia
RTC_DATA_ATTR uint32_t rtc_ciclo           = 0;
RTC_DATA_ATTR char     rtc_node_id[20]     = {0};

// GPS: solo leer en primer boot, después usar cache
RTC_DATA_ATTR float    rtc_lat             = 0.0f;
RTC_DATA_ATTR float    rtc_lon             = 0.0f;
RTC_DATA_ATTR bool     rtc_gps_ok          = false;

// MDS: D_max y D_min del día para calcular MDS = D_max − D_min
// Se resetean automáticamente al cambiar de día (detección por timestamp UTC)
RTC_DATA_ATTR float    rtc_dmax_raw        = -1e9f;  // −∞ inicial
RTC_DATA_ATTR float    rtc_dmin_raw        =  1e9f;  //  +∞ inicial
RTC_DATA_ATTR float    rtc_tronco_t_ref    = 0.0f;
RTC_DATA_ATTR bool     rtc_mds_baseline_ok = false;
RTC_DATA_ATTR uint8_t  rtc_ultimo_dia      = 255;    // día del mes del último reset (255 = nunca)

// Calidad de captura: clearance post-lluvia y post-fumigación
RTC_DATA_ATTR uint32_t rtc_lluvia_clearance_hasta    = 0;
RTC_DATA_ATTR uint32_t rtc_fumigacion_clearance_hasta = 0;

// Motor GDD y fenología
RTC_DATA_ATTR float    rtc_gdd_acum            = 0.0f;
RTC_DATA_ATTR float    rtc_gdd_t_sum_dia        = 0.0f;
RTC_DATA_ATTR uint16_t rtc_gdd_t_muestras_dia   = 0;
RTC_DATA_ATTR uint8_t  rtc_gdd_ultimo_mes_reset = 0;

// Varietal de la zona — recibido del backend en respuesta /ingest
// Persistente entre ciclos; se actualiza si el backend informa uno diferente.
RTC_DATA_ATTR uint8_t  rtc_varietal             = VARIETAL_VID_MALBEC;

// ─────────────────────────────────────────
// Declaraciones de funciones
// ─────────────────────────────────────────
float    calcular_cwsi(float tc_mean, float tc_wet, float tc_dry);
float    calcular_tc_dry(float t_air, float rh, float wind_ms);
float    calcular_mds_norm(float mds_mm);
float    calcular_hsi(float cwsi, float mds_norm, float wind_ms);
uint8_t  estimar_bateria();
bool     ventana_solar_activa();      // HW-02: solo activar MLX en ventana solar útil

// ── Buffer térmico con filtro por calma ──────────────────────────────
struct ThermalSample {
    float tc_mean;
    float wind_ms;
    bool  valid;          // captura exitosa
};

/**
 * Mediana de un array de floats (selection sort parcial).
 * Modifica el array in-place. n debe ser >= 1.
 */
float mediana_float(float* arr, uint8_t n) {
    // Insertion sort (n <= THERMAL_BUFFER_SIZE, siempre pequeño)
    for (uint8_t i = 1; i < n; i++) {
        float key = arr[i];
        int8_t j = i - 1;
        while (j >= 0 && arr[j] > key) { arr[j + 1] = arr[j]; j--; }
        arr[j + 1] = key;
    }
    if (n % 2 == 1) return arr[n / 2];
    return (arr[n / 2 - 1] + arr[n / 2]) / 2.0f;
}

/**
 * Selecciona la mejor tc_mean del buffer térmico.
 * Prioridad: mediana de lecturas en calma (viento < WIND_CALM_MS).
 * Fallback: mediana de todas las lecturas válidas.
 */
float seleccionar_tc_mean(ThermalSample* buf, uint8_t n) {
    float calmas[THERMAL_BUFFER_SIZE];
    uint8_t n_calmas = 0;
    float todas[THERMAL_BUFFER_SIZE];
    uint8_t n_todas = 0;

    for (uint8_t i = 0; i < n; i++) {
        if (!buf[i].valid) continue;
        todas[n_todas++] = buf[i].tc_mean;
        if (buf[i].wind_ms < WIND_CALM_MS) {
            calmas[n_calmas++] = buf[i].tc_mean;
        }
    }
    if (n_calmas > 0) return mediana_float(calmas, n_calmas);
    if (n_todas  > 0) return mediana_float(todas, n_todas);
    return 0.0f;  // sin lecturas válidas
}

// ─────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    rtc_ciclo++;

    // Node ID: derivar de MAC solo en primer boot
    if (rtc_node_id[0] == '\0') {
        uint8_t mac[6];
        esp_read_mac(mac, ESP_MAC_WIFI_STA);
        snprintf(rtc_node_id, sizeof(rtc_node_id),
                 "HV-%02X%02X%02X%02X%02X",
                 mac[1], mac[2], mac[3], mac[4], mac[5]);
    }

    Serial.printf("\n[HV] ========== Ciclo %lu — %s ==========\n", rtc_ciclo, rtc_node_id);

    // Alertas físicas: REMOVIDO (LED+sirena eliminados del diseño)

    // Solenoide: restaurar estado del relé desde RTC memory (Tier 3)
    solenoide_init();

    // SPI bus explícito (evita conflicto con PMS5003 en GPIO 12/13)
    SPI.begin(PIN_SPI_SCLK, PIN_SPI_MISO, PIN_SPI_MOSI);

    // I2C compartido: MLX90640, SHT31, DS3231
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);

    // Inicializar periféricos
    bool ok_mlx   = mlx_init();
    bool ok_mds   = mds_init();
    bool ok_sht   = sht31_init();
    bool ok_rtc   = rtc_init();
    bool ok_anemo = anemometro_init();
    bool ok_imu   = imu_init();
    bool ok_lora  = lora_init();
    pluviometro_init();
    piranometro_init();
    bomba_wetref_init();
    bool ok_gimbal = gimbal_init();
    bool ok_pms    = pms_init();   // UART1 reasignado (GPS ya terminó si era boot 1)
    bool ok_tc     = termopar_init();  // MAX31855 SPI (CS=PIN_TC_CS, bus compartido)
    pinMode(PIN_PIEZO_CLEANER, OUTPUT);
    digitalWrite(PIN_PIEZO_CLEANER, LOW);

    // GPS: solo en primer boot para georreferenciar el nodo
    if (!rtc_gps_ok) {
        gps_init();
        GpsResult gps = gps_read(GPS_TIMEOUT_MS);
        if (gps.ok) {
            rtc_lat    = gps.lat;
            rtc_lon    = gps.lon;
            rtc_gps_ok = true;
            // Sincronizar RTC con hora GPS si está disponible
            if (ok_rtc && gps.epoch > 0) {
                rtc_sync_gps(gps.epoch);
            }
        }
    }

    // ─────────────────────────────────────────
    // Lectura de sensores
    // ─────────────────────────────────────────
    SensorData d = {};

    // Timestamp
    d.ts = ok_rtc ? rtc_timestamp() : 0;

    // Ambiente: SHT31
    Sht31Result sht = sht31_read();
    if (sht.ok) {
        d.t_air = sht.t_air;
        d.rh    = sht.rh;
    }

    // Anemómetro RS485
    AnemometroResult anemo = anemometro_read();
    if (anemo.ok) d.wind_ms = anemo.wind_ms;

    // Pluviómetro (pulsos acumulados en este ciclo de vigilia)
    PluviometroResult pluv = pluviometro_read();
    if (pluv.ok) {
        rtc_lluvia_mm += pluv.rain_mm;
    }
    d.rain_mm = pluv.rain_mm;  // mm en este ciclo (no acumulado)

    // Piranómetro BPW34
    PiranometroResult pyrano = piranometro_read();
    if (pyrano.ok) d.rad_wm2 = pyrano.rad_wm2;

    // ─────────────────────────────────────────
    // PMS5003 — detección automática de lluvia/fumigación
    // ─────────────────────────────────────────
    d.pm2_5 = 0;
    if (ok_pms) {
        Pms5003Result pms = pms_read();
        if (pms.ok) d.pm2_5 = pms.pm2_5;
    }

    // Determinar calidad de captura y actualizar clearance timers
    bool lluvia_activa     = (d.rain_mm > 0);
    bool fumigacion_activa = (d.pm2_5 > PMS_PM25_FUMIG);
    bool lluvia_aerosol    = (d.pm2_5 > PMS_PM25_LLUVIA && lluvia_activa);

    if (fumigacion_activa) {
        rtc_fumigacion_clearance_hasta = d.ts + (uint32_t)FUMIGACION_CLEARANCE_HRS * 3600;
        d.calidad_captura = "fumigacion";
    } else if (d.ts > 0 && d.ts < rtc_fumigacion_clearance_hasta) {
        d.calidad_captura = "post_fumigacion";
    } else if (lluvia_activa || lluvia_aerosol) {
        rtc_lluvia_clearance_hasta = d.ts + (uint32_t)LLUVIA_CLEARANCE_HRS * 3600;
        d.calidad_captura = "lluvia";
    } else if (d.ts > 0 && d.ts < rtc_lluvia_clearance_hasta) {
        d.calidad_captura = "post_lluvia";
    } else {
        d.calidad_captura = "ok";
    }

    bool captura_valida = (strcmp(d.calidad_captura, "ok") == 0);
    Serial.printf("[HV] calidad_captura=%s pm2_5=%u µg/m³\n", d.calidad_captura, d.pm2_5);

    // Reset diario de D_max/D_min del MDS (al cambiar de día UTC)
    if (d.ts > 0) {
        // Día del mes desde epoch Unix (segundos / 86400 % 31 como proxy rápido)
        uint8_t dia_hoy = (uint8_t)((d.ts / 86400UL) % 31);
        if (dia_hoy != rtc_ultimo_dia) {
            rtc_dmax_raw        = -1e9f;
            rtc_dmin_raw        =  1e9f;
            rtc_mds_baseline_ok = false;
            rtc_ultimo_dia      = dia_hoy;
            Serial.printf("[MDS] Reset diario D_max/D_min — día %u\n", dia_hoy);
        }
    }

    // Limpieza piezoeléctrica de lente (Murata MZB1001T02) antes de captura
    if (captura_valida) {
        digitalWrite(PIN_PIEZO_CLEANER, HIGH);
        delay(PIEZO_PULSO_MS);
        digitalWrite(PIN_PIEZO_CLEANER, LOW);
        delay(200);  // asentamiento post-vibración antes de capturar
    }

    // Bomba Wet Ref: recargar hoja de referencia
    if (captura_valida) bomba_wetref_pulso();

    // Cámara térmica: buffer multi-muestra con filtro por calma
    // Toma THERMAL_BUFFER_SIZE lecturas espaciadas THERMAL_SAMPLE_DELAY_MS,
    // midiendo viento en cada una. Selecciona la mediana de las lecturas
    // en calma (viento < WIND_CALM_MS). Si ninguna está en calma, usa la
    // mediana de todas las lecturas válidas.
    GimbalFusionResult thermal = {0};
    ThermalSample tbuf[THERMAL_BUFFER_SIZE] = {};
    uint8_t tbuf_count = 0;

    if (captura_valida) {
        // Verificar estabilidad mecánica del nodo antes de capturar
        if (ok_imu) imu_esperar_estabilidad(3);

        for (uint8_t si = 0; si < THERMAL_BUFFER_SIZE; si++) {
            // Leer viento instantáneo para esta muestra
            AnemometroResult anemo_i = anemometro_read();
            float wind_i = anemo_i.ok ? anemo_i.wind_ms : d.wind_ms;

            GimbalFusionResult frame_i = {0};
            if (ok_mlx && ok_gimbal) {
                frame_i = gimbal_capturar(wind_i);
            } else if (ok_mlx) {
                MlxResult raw = mlx_read();
                if (raw.ok) {
                    frame_i.tc_mean      = raw.tc_mean;
                    frame_i.tc_max       = raw.tc_max;
                    frame_i.valid_pixels = raw.valid_pixels;
                    frame_i.n_frames     = 1;
                    frame_i.ok           = true;
                }
            }

            tbuf[si].tc_mean = frame_i.ok ? frame_i.tc_mean : 0.0f;
            tbuf[si].wind_ms = wind_i;
            tbuf[si].valid   = frame_i.ok;

            // Guardar el último frame exitoso como referencia para tc_max, valid_pixels, etc.
            if (frame_i.ok) thermal = frame_i;
            tbuf_count++;

            Serial.printf("[HV] Muestra %u/%u: tc=%.2f wind=%.1f %s\n",
                          si + 1, THERMAL_BUFFER_SIZE,
                          tbuf[si].tc_mean, wind_i,
                          (wind_i < WIND_CALM_MS) ? "[calma]" : "");

            if (si < THERMAL_BUFFER_SIZE - 1) delay(THERMAL_SAMPLE_DELAY_MS);
        }

        // Seleccionar tc_mean óptimo del buffer (mediana de lecturas en calma)
        float tc_filtrado = seleccionar_tc_mean(tbuf, tbuf_count);
        if (tc_filtrado > 0.0f) {
            thermal.tc_mean = tc_filtrado;
            thermal.ok = true;
        }

        if (thermal.ok) {
            d.tc_mean      = thermal.tc_mean;
            d.tc_max       = thermal.tc_max;
            d.valid_pixels = thermal.valid_pixels;  // valor real del frame/fusión
            d.n_frames     = thermal.n_frames;

            // Corrección por termopar de contacto (ground truth inmune al viento)
            // T_leaf_corr = T_leaf_IR + k × (T_termopar - T_leaf_IR)
            // k=0 → solo IR, k=1 → solo termopar, k=0.6 → blend (default)
            if (ok_tc) {
                TermoparResult tc = termopar_read();
                if (tc.ok && tc.temp_c >= TC_MIN_VALID_C && tc.temp_c <= TC_MAX_VALID_C) {
                    float tc_ir = d.tc_mean;
                    d.tc_mean = tc_ir + TC_BLEND_K * (tc.temp_c - tc_ir);
                    Serial.printf("[HV] Termopar: %.2f°C  IR: %.2f°C  Corregido: %.2f°C (k=%.1f)\n",
                                  tc.temp_c, tc_ir, d.tc_mean, TC_BLEND_K);
                } else {
                    Serial.printf("[HV] Termopar: %s\n",
                                  tc.ok ? "fuera de rango — ignorado" : "falla lectura — ignorado");
                }
            }
        }
    } else {
        Serial.printf("[HV] MLX90640 omitido — %s\n", d.calidad_captura);
    }

    // MDS extensómetro (solo si calidad ok)
    MdsResult mds = {};
    if (captura_valida) mds = mds_read();
    if (mds.ok) {
        // Inicializar temperatura de referencia en primer ciclo válido
        if (!rtc_mds_baseline_ok) {
            rtc_tronco_t_ref    = mds.temp_tronco;
            rtc_dmax_raw        = mds.diameter_um;
            rtc_dmin_raw        = mds.diameter_um;
            rtc_mds_baseline_ok = true;
        }
        // Aplicar corrección térmica antes de actualizar D_max / D_min
        float d_corr = mds_corregir_termico(mds.diameter_um, mds.temp_tronco, rtc_tronco_t_ref);
        if (d_corr > rtc_dmax_raw) rtc_dmax_raw = d_corr;
        if (d_corr < rtc_dmin_raw) rtc_dmin_raw = d_corr;
        // MDS = D_max − D_min del día (en mm)
        d.mds_mm = (rtc_dmax_raw - rtc_dmin_raw) / 1000.0f;
    }

    // Posición GPS (desde cache RTC)
    d.lat = rtc_lat;
    d.lon = rtc_lon;

    // Batería
    d.bat_pct = estimar_bateria();

    // ─────────────────────────────────────────
    // Motor GDD y fenología autónoma
    // ─────────────────────────────────────────
    uint8_t mes_hoy = 0, dia_ts = 0;
    if (d.ts > 0) {
        // Extraer mes y día del epoch Unix sin depender de mktime()
        // Aproximación: días desde epoch / 30.44 (suficiente para reset mensual)
        uint32_t dias = d.ts / 86400UL;
        // Algoritmo inverso JDN para obtener mes y día
        int32_t jdn = (int32_t)dias + 2440588L;
        int32_t l = jdn + 68569;
        int32_t n = 4 * l / 146097;
        l = l - (146097 * n + 3) / 4;
        int32_t i = 4000 * (l + 1) / 1461001;
        l = l - 1461 * i / 4 + 31;
        int32_t j = 80 * l / 2447;
        dia_ts = (uint8_t)(l - 2447 * j / 80);
        l = j / 11;
        mes_hoy = (uint8_t)(j + 2 - 12 * l);
    }
    VarietalId varietal = (VarietalId)rtc_varietal;
    gdd_actualizar(d.t_air, dia_ts, mes_hoy,
                   rtc_gdd_acum, rtc_gdd_t_sum_dia,
                   rtc_gdd_t_muestras_dia, rtc_ultimo_dia,
                   rtc_gdd_ultimo_mes_reset, varietal);

    FenolEstadio estadio = gdd_estadio(rtc_gdd_acum, varietal);
    float hsi_umbral_dinamico = gdd_umbral_cwsi(rtc_gdd_acum, varietal);

    // ─────────────────────────────────────────
    // Baselines CWSI
    // ─────────────────────────────────────────
    d.tc_wet = rtc_tc_wet;
    d.tc_dry = calcular_tc_dry(d.t_air, d.rh, d.wind_ms);

    // Auto-calibración Tc_wet: lluvia + MDS bajo → planta bien hidratada
    if (d.rain_mm >= LLUVIA_MIN_MM && d.mds_mm < MDS_CAL_MAX_MM && d.tc_mean > 0.0f) {
        // EMA con learning_rate=0.25 para suavizar transiciones
        const float LR = 0.25f;
        rtc_tc_wet = (rtc_tc_wet > 0.0f)
                     ? rtc_tc_wet * (1.0f - LR) + d.tc_mean * LR
                     : d.tc_mean;
        d.tc_wet = rtc_tc_wet;
        Serial.printf("[HV] Tc_wet actualizado (EMA): %.2f°C\n", rtc_tc_wet);
    }

    // ─────────────────────────────────────────
    // Índices de estrés
    // ─────────────────────────────────────────
    float cwsi          = calcular_cwsi(d.tc_mean, d.tc_wet, d.tc_dry);
    float mds_norm      = calcular_mds_norm(d.mds_mm);
    float hsi           = calcular_hsi(cwsi, mds_norm, d.wind_ms);

    // Calcular pesos efectivos para reporte (misma lógica que calcular_hsi)
    float w_cwsi_eff;
    if (d.wind_ms <= WIND_RAMP_LO) {
        w_cwsi_eff = 0.35f;
    } else if (d.wind_ms >= WIND_RAMP_HI) {
        w_cwsi_eff = 0.0f;
    } else {
        w_cwsi_eff = 0.35f * (WIND_RAMP_HI - d.wind_ms) / (WIND_RAMP_HI - WIND_RAMP_LO);
    }
    float w_mds_eff = 1.0f - w_cwsi_eff;
    bool  wind_override = (d.wind_ms >= WIND_RAMP_HI);

    // ISO_nodo: diagnóstico de lente (solo si hubo captura válida)
    uint8_t iso_nodo = 100;
    if (captura_valida && thermal.ok) {
        IsoResult iso = mlx_iso_nodo(d.t_air);
        if (iso.ok) iso_nodo = iso.iso_nodo;
    }

    Serial.printf("[HV] T=%.1f°C HR=%.0f%% V=%.1fm/s R=%.0fW/m²\n",
                  d.t_air, d.rh, d.wind_ms, d.rad_wm2);
    Serial.printf("[HV] CWSI=%.3f MDS=%.4fmm HSI=%.3f w_cwsi=%.2f w_mds=%.2f %s\n",
                  cwsi, d.mds_mm, hsi, w_cwsi_eff, w_mds_eff,
                  wind_override ? "[WIND OVERRIDE]" : "");
    Serial.printf("[HV] GDD=%.1f [%s] %s umbral_CWSI=%.2f ISO=%u\n",
                  rtc_gdd_acum, FENOL_NOMBRES[estadio],
                  VARIETAL_NOMBRES[varietal], hsi_umbral_dinamico, iso_nodo);

    // ─────────────────────────────────────────
    // Control de riego autónomo (Tier 3 — solo si tiene solenoide)
    // El nodo decide localmente. El backend se entera via payload.
    // ─────────────────────────────────────────
    int hora_local = (d.ts > 0) ? (int)((d.ts % 86400UL) / 3600) - 3 : 12;
    if (hora_local < 0) hora_local += 24;

    SolenoideState sol = solenoide_evaluar(hsi, d.ts, d.calidad_captura, hora_local, estadio);

    if (solenoide_tiene()) {
        Serial.printf("[HV] Solenoide canal=%u %s razón=%s ciclos=%u\n",
                      sol.canal, sol.active ? "ABIERTO" : "cerrado",
                      sol.reason, sol.ciclos_activo);
    }

    // ─────────────────────────────────────────
    // Serializar payload JSON
    // ─────────────────────────────────────────
    char json[700];  // ampliado: +solenoid(~80) sobre base anterior
    snprintf(json, sizeof(json),
        "{"
        "\"v\":1,"
        "\"node_id\":\"%s\","
        "\"ts\":%lu,"
        "\"cycle\":%lu,"
        "\"env\":{\"t_air\":%.1f,\"rh\":%.1f,\"wind_ms\":%.1f,"
                 "\"rain_mm\":%.1f,\"rad_wm2\":%.0f},"
        "\"thermal\":{\"tc_mean\":%.2f,\"tc_max\":%.2f,\"tc_wet\":%.2f,"
                     "\"tc_dry\":%.2f,\"cwsi\":%.3f,"
                     "\"valid_pixels\":%u,\"n_frames\":%u},"
        "\"dendro\":{\"mds_mm\":%.4f,\"mds_norm\":%.3f},"
        "\"hsi\":{\"value\":%.3f,\"w_cwsi\":%.2f,\"w_mds\":%.2f,"
                 "\"wind_override\":%s},"
        "\"gps\":{\"lat\":%.6f,\"lon\":%.6f},"
        "\"bat_pct\":%u,"
        "\"pm2_5\":%u,"
        "\"calidad_captura\":\"%s\","
        "\"gdd\":{\"acum\":%.1f,\"estadio\":\"%s\"},"
        "\"iso_nodo\":%u,"
        "\"solenoid\":{\"canal\":%u,\"active\":%s,\"reason\":\"%s\","
                      "\"ciclos_activo\":%u},"
        "\"varietal\":\"%s\""
        "}",
        rtc_node_id, (unsigned long)d.ts, (unsigned long)rtc_ciclo,
        d.t_air, d.rh, d.wind_ms, d.rain_mm, d.rad_wm2,
        d.tc_mean, d.tc_max, d.tc_wet, d.tc_dry, cwsi,
        d.valid_pixels, d.n_frames,
        d.mds_mm, mds_norm,
        hsi,
        w_cwsi_eff,
        w_mds_eff,
        wind_override ? "true" : "false",
        d.lat, d.lon,
        d.bat_pct,
        d.pm2_5,
        d.calidad_captura,
        rtc_gdd_acum, FENOL_NOMBRES[estadio],
        iso_nodo,
        sol.canal, sol.active ? "true" : "false",
        sol.reason, sol.ciclos_activo,
        VARIETAL_NOMBRES[varietal]
    );

    // ─────────────────────────────────────────
    // Publicar via LoRa
    // ─────────────────────────────────────────
    char topic[64];
    snprintf(topic, sizeof(topic), TOPIC_TELEMETRY, rtc_node_id);
    Serial.printf("[HV] Topic: %s\n", topic);

    if (ok_lora) {
        publicar_lora(topic, json);

        // Publicar en /alert usando umbral dinámico por estadio fenológico
        if (hsi >= hsi_umbral_dinamico) {
            char alert_topic[64];
            snprintf(alert_topic, sizeof(alert_topic), TOPIC_ALERT, rtc_node_id);
            publicar_lora(alert_topic, json);
            Serial.printf("[HV] ALERTA HSI=%.3f >= umbral=%.2f [%s]\n",
                          hsi, hsi_umbral_dinamico, FENOL_NOMBRES[estadio]);
        }
    }

    // ─────────────────────────────────────────
    // Recibir respuesta downlink del backend (via gateway)
    // Flujo: nodo TX → gateway → HTTP POST /ingest → backend
    //        backend responde JSON → gateway → LoRa downlink → nodo
    //
    // Campos parseados:
    //   "varietal": actualiza rtc_varietal para GDD/fenología
    //   "command":{"irrigate":false}: override de riego desde backend
    // ─────────────────────────────────────────
    if (ok_lora) {
        const char* resp = lora_receive_response(5000);  // ventana RX 5s
        if (resp) {
            Serial.printf("[HV] Downlink: %s\n", resp);

            // --- Parsear varietal ---
            const char* var_ptr = strstr(resp, "\"varietal\":\"");
            if (var_ptr) {
                var_ptr += 12;  // saltar "varietal":"
                char var_buf[32];
                int i = 0;
                while (*var_ptr && *var_ptr != '"' && i < 31) var_buf[i++] = *var_ptr++;
                var_buf[i] = '\0';
                VarietalId nuevo = varietal_parse(var_buf);
                if (nuevo != VARIETAL_DESCONOCIDO && nuevo != (VarietalId)rtc_varietal) {
                    rtc_varietal = (uint8_t)nuevo;
                    Serial.printf("[HV] Varietal actualizado desde backend: %s\n",
                                  VARIETAL_NOMBRES[nuevo]);
                }
            }

            // --- Parsear modo simulación solenoide ---
            // El backend envía "sol_sim":true cuando el usuario activa modo prueba desde la web.
            const char* sim_ptr = strstr(resp, "\"sol_sim\":");
            if (sim_ptr) {
                sim_ptr += 10;  // saltar "sol_sim":
                bool nuevo_sim = (strncmp(sim_ptr, "true", 4) == 0);
                if (nuevo_sim != rtc_sol_sim) {
                    rtc_sol_sim = nuevo_sim;
                    Serial.printf("[HV] Modo simulación solenoide: %s\n",
                                  rtc_sol_sim ? "ACTIVADO" : "desactivado");
                    if (rtc_sol_sim && rtc_solenoide_activo) {
                        // Si entramos en simulación con solenoide abierto, cerrar GPIO real
                        digitalWrite(PIN_SOLENOIDE, LOW);
                        Serial.println("[SOL] GPIO apagado — entrando en modo simulación");
                    }
                }
            }

            // --- Parsear comando de riego (override backend) ---
            // El backend envía {"command":{"irrigate":false,"reason":"reposo_fenologico"}}
            // cuando detecta que la zona está en reposo y el nodo reportó solenoide activo.
            const char* cmd_ptr = strstr(resp, "\"irrigate\":");
            if (cmd_ptr) {
                cmd_ptr += 11;  // saltar "irrigate":
                if (strncmp(cmd_ptr, "false", 5) == 0 && rtc_solenoide_activo) {
                    _solenoide_cerrar("backend_off");
                    Serial.println("[HV] Backend ordenó apagar riego");
                } else if (strncmp(cmd_ptr, "true", 4) == 0 && !rtc_solenoide_activo) {
                    _solenoide_abrir(d.ts, "backend_on");
                    Serial.println("[HV] Backend ordenó encender riego");
                }
            }
        }
    }

    // ─────────────────────────────────────────
    // Heartbeat /status cada STATUS_INTERVAL_CYCLES ciclos (cada ~1 hora)
    // ─────────────────────────────────────────
    if (ok_lora && (rtc_ciclo % STATUS_INTERVAL_CYCLES == 0)) {
        char status_json[128];
        bool nodo_movido = ok_imu ? imu_nodo_desplazado() : false;
        snprintf(status_json, sizeof(status_json),
            "{\"v\":1,\"node_id\":\"%s\",\"ts\":%lu,\"bat_pct\":%u,"
            "\"cycle\":%lu,\"nodo_movido\":%s}",
            rtc_node_id, (unsigned long)d.ts, d.bat_pct,
            (unsigned long)rtc_ciclo, nodo_movido ? "true" : "false");
        char status_topic[64];
        snprintf(status_topic, sizeof(status_topic), TOPIC_STATUS, rtc_node_id);
        publicar_lora(status_topic, status_json);
    }

    // ─────────────────────────────────────────
    // Pre-sleep: apagar periféricos (excepto solenoide — mantiene estado)
    // ─────────────────────────────────────────
    pluviometro_deinit();
    gimbal_deinit();
    lora_sleep();
    solenoide_pre_sleep();  // mantiene GPIO del relé durante deep sleep

    // Sleep adaptativo: en dormancia/post-cosecha → 6h para ahorrar batería
    uint32_t sleep_sec = gdd_sleep_interval(rtc_gdd_acum, varietal);
    Serial.printf("[HV] Deep sleep %lu s (%s) — hasta siguiente ciclo\n",
                  (unsigned long)sleep_sec, FENOL_NOMBRES[estadio]);
    Serial.flush();

    esp_sleep_enable_timer_wakeup((uint64_t)sleep_sec * 1000000ULL);
    esp_deep_sleep_start();
}

void loop() {}

// ─────────────────────────────────────────
// Cálculos
// ─────────────────────────────────────────

/**
 * CWSI = (Tc_mean - Tc_wet) / (Tc_dry - Tc_wet)   [Jackson 1981]
 * Rango válido: 0.0 (sin estrés) a 1.0 (estrés severo).
 * Retorna -1.0 si los baselines no están calibrados aún.
 */
float calcular_cwsi(float tc_mean, float tc_wet, float tc_dry) {
    if (tc_wet == 0.0f) return -1.0f;         // Tc_wet no calibrado aún
    float denom = tc_dry - tc_wet;
    if (denom < 0.5f) return -1.0f;           // rango insuficiente
    float cwsi = (tc_mean - tc_wet) / denom;
    return constrain(cwsi, 0.0f, 1.0f);
}

/**
 * Tc_dry: temperatura máxima teórica de hoja sin transpiración.
 * Aproximación empírica: Tc_dry ≈ T_aire + delta_T
 * delta_T disminuye con humedad y viento.
 * TODO: reemplazar con balance energético completo cuando tengamos
 *       piranómetro calibrado (Rn, G, LEp — Itier & Katerji 1991).
 */
float calcular_tc_dry(float t_air, float rh, float wind_ms) {
    float delta = 10.0f - (rh / 100.0f) * 5.0f;   // 5–10°C según HR
    delta *= (1.0f - wind_ms / 20.0f);             // viento reduce el delta
    if (delta < 0.5f) delta = 0.5f;
    return t_air + delta;
}

/**
 * Normaliza MDS a escala 0–1.
 * Rango típico Malbec: 0–0.5 mm (ajustar con datos del viñedo — Mes 4–6).
 * Referencia: Fernández & Cuevas-Rolando 2010, Acta Horticulturae.
 */
float calcular_mds_norm(float mds_mm) {
    // MDS_MAX_MM definido en config.h (default 0.5f — calibrar con datos de campo).
    return constrain(mds_mm / MDS_MAX_MM, 0.0f, 1.0f);
}

/**
 * HW-02 — Activación adaptativa del MLX90640.
 * El CWSI solo es válido con gradiente solar activo (iluminación difusa o directa).
 * Activar el MLX fuera de ventana solar gasta batería sin producir datos útiles.
 * Ventana configurada en config.h: MLX_VENTANA_SOLAR_INI / MLX_VENTANA_SOLAR_FIN.
 *
 * Uso en ciclo principal (antes del bloque de captura MLX):
 *   if (ventana_solar_activa()) {
 *       mlx_capturar_frame();
 *       cwsi = calcular_cwsi(...);
 *   } else {
 *       d.cwsi = NAN;
 *       // MDS + meteo siguen corriendo normalmente
 *   }
 */
bool ventana_solar_activa() {
    int hora = rtc_leer_hora_local();   // función del driver_rtc.h — ver nota abajo
    bool en_ventana = (hora >= MLX_VENTANA_SOLAR_INI && hora < MLX_VENTANA_SOLAR_FIN);

    // Modo ahorro en días nublados: si piranómetro < umbral durante N ciclos → reducir frecuencia
    static uint8_t ciclos_nublados = 0;
    if (en_ventana) {
        if (analogReadMilliVolts(PIN_PYRANO_ADC) * PYRANO_WPM2_PER_MV < MLX_RAD_MIN_WM2) {
            ciclos_nublados++;
        } else {
            ciclos_nublados = 0;
        }
        if (ciclos_nublados >= MLX_NUBLADO_CICLOS) {
            // Nublado persistente: activar MLX solo 1 de cada MLX_NUBLADO_INTERVALO ciclos
            return (rtc_ciclo % MLX_NUBLADO_INTERVALO == 0);
        }
    }
    return en_ventana;
}
// NOTA: driver_rtc.h debe exponer rtc_leer_hora_local() que retorne la hora local (int 0-23).
// Si solo existe rtc_leer_epoch(), agregar:
//   int rtc_leer_hora_local() { return (int)((rtc_leer_epoch() % 86400) / 3600) - 3; }
//   (UTC-3 para Argentina; ajustar en verano a UTC-3, igual — Argentina no tiene horario de verano)

/**
 * HSI (HydroVision Stress Index).
 * Pesos base: 35% CWSI + 65% MDS  (Fernández 2014).
 *
 * Transición gradual por viento (en lugar de cutoff duro):
 *   viento <= WIND_RAMP_LO (4 m/s)  → w_cwsi = 0.35 (normal)
 *   WIND_RAMP_LO < v < WIND_RAMP_HI → rampa lineal 0.35 → 0.00
 *   viento >= WIND_RAMP_HI (8 m/s)  → w_cwsi = 0.00 (100% MDS)
 *
 * Con orientación a sotavento, 8 m/s en anemómetro ≈ 3.2 m/s en hoja.
 */
float calcular_hsi(float cwsi, float mds_norm, float wind_ms) {
    if (cwsi < 0.0f) return mds_norm;   // CWSI no disponible → solo MDS

    float w_cwsi;
    if (wind_ms <= WIND_RAMP_LO) {
        w_cwsi = 0.35f;                 // normal
    } else if (wind_ms >= WIND_RAMP_HI) {
        w_cwsi = 0.0f;                  // backup total MDS
    } else {
        // Rampa lineal: 0.35 en RAMP_LO → 0.0 en RAMP_HI
        w_cwsi = 0.35f * (WIND_RAMP_HI - wind_ms) / (WIND_RAMP_HI - WIND_RAMP_LO);
    }
    float w_mds = 1.0f - w_cwsi;
    return w_cwsi * cwsi + w_mds * mds_norm;
}

/**
 * Estima % batería desde ADC con divisor de tensión R1/R2.
 * LiPo: BAT_FULL_MV = 4200 mV, BAT_EMPTY_MV = 3000 mV.
 * NOTA: PIN_BAT_ADC comparte GPIO con PIN_GPS_TX — verificar en PCB v1.
 */
uint8_t estimar_bateria() {
    uint32_t adc_mv = analogReadMilliVolts(PIN_BAT_ADC);
    // Vbat = Vout * (R1 + R2) / R2
    uint32_t vbat_mv = (uint32_t)((float)adc_mv * (BAT_R1 + BAT_R2) / BAT_R2);
    if (vbat_mv >= BAT_FULL_MV)  return 100;
    if (vbat_mv <= BAT_EMPTY_MV) return 0;
    return (uint8_t)((vbat_mv - BAT_EMPTY_MV) * 100 / (BAT_FULL_MV - BAT_EMPTY_MV));
}
