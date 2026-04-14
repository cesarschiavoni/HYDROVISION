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
float    calcular_tc_dry(float t_air, float rh, float wind_ms, float rad_wm2);  // [B4] +radiación
float    calcular_mds_norm(float mds_mm);
float    calcular_hsi(float cwsi, float mds_norm, float wind_ms);
uint8_t  estimar_bateria();
bool     ventana_solar_activa();      // HW-02: solo activar MLX en ventana solar útil
float    calcular_quality_score(float wind_ms, float rad_wm2, float vpd,        // [B6]
                                 uint8_t calm_samples, uint8_t total_samples,
                                 bool tc_ok, bool muller_ok);
float    calcular_jones_ig(float tc_canopy, float tc_wet_ref, float tc_dry_ref); // [C3]
float    muller_gbh(float t_black, float t_white, float rad_wm2);               // [C4]

// ── Buffer térmico adaptativo con filtro Hampel + calma  [B1+B2] ────
struct ThermalSample {
    float tc_mean;
    float wind_ms;
    bool  valid;          // captura exitosa
};

/**
 * Ordena array de floats in-place (insertion sort, n <= 15).
 */
void sort_float(float* arr, uint8_t n) {
    for (uint8_t i = 1; i < n; i++) {
        float key = arr[i];
        int8_t j = i - 1;
        while (j >= 0 && arr[j] > key) { arr[j + 1] = arr[j]; j--; }
        arr[j + 1] = key;
    }
}

/**
 * Mediana de un array de floats (modifica in-place). n >= 1.
 */
float mediana_float(float* arr, uint8_t n) {
    sort_float(arr, n);
    if (n % 2 == 1) return arr[n / 2];
    return (arr[n / 2 - 1] + arr[n / 2]) / 2.0f;
}

/**
 * Filtro Hampel: identifica outliers por MAD (Median Absolute Deviation),
 * los reemplaza con la mediana, y retorna el promedio de las muestras limpias.
 * Más robusto que mediana sola y más preciso que promedio puro.
 * Reduce NETD efectivo ~40% vs mediana (promedia más muestras "buenas").
 *   [B2] — Referencia: Pearson (2002), Hampel (1974).
 */
float hampel_mean(float* arr, uint8_t n) {
    if (n <= 2) return mediana_float(arr, n);

    // Paso 1: mediana
    float tmp[THERMAL_BUFFER_MAX];
    for (uint8_t i = 0; i < n; i++) tmp[i] = arr[i];
    float med = mediana_float(tmp, n);

    // Paso 2: MAD (Median Absolute Deviation)
    float devs[THERMAL_BUFFER_MAX];
    for (uint8_t i = 0; i < n; i++) devs[i] = fabsf(arr[i] - med);
    float mad = mediana_float(devs, n);
    if (mad < 0.001f) mad = 0.001f;  // evitar div/0 si datos idénticos

    // Paso 3: promediar muestras no-outlier (|x - med| <= HAMPEL_K × MAD)
    float threshold = HAMPEL_K * mad;
    float sum = 0.0f;
    uint8_t count = 0;
    for (uint8_t i = 0; i < n; i++) {
        if (fabsf(arr[i] - med) <= threshold) {
            sum += arr[i];
            count++;
        }
    }
    return (count > 0) ? (sum / count) : med;
}

/**
 * Selecciona la mejor tc_mean del buffer térmico.
 * [B1+B2] Prioridad: filtro Hampel sobre lecturas en calma.
 * Fallback: Hampel sobre todas las lecturas válidas.
 * Retorna también n_calmas para quality score.
 */
struct TcSelection {
    float tc_mean;
    uint8_t n_calmas;
    uint8_t n_todas;
};

TcSelection seleccionar_tc_mean(ThermalSample* buf, uint8_t n) {
    float calmas[THERMAL_BUFFER_MAX];
    uint8_t n_calmas = 0;
    float todas[THERMAL_BUFFER_MAX];
    uint8_t n_todas = 0;

    for (uint8_t i = 0; i < n; i++) {
        if (!buf[i].valid) continue;
        todas[n_todas++] = buf[i].tc_mean;
        if (buf[i].wind_ms < WIND_CALM_MS) {
            calmas[n_calmas++] = buf[i].tc_mean;
        }
    }

    TcSelection sel = {0.0f, n_calmas, n_todas};
    if (n_calmas > 0)     sel.tc_mean = hampel_mean(calmas, n_calmas);
    else if (n_todas > 0) sel.tc_mean = hampel_mean(todas, n_todas);
    return sel;
}

// ── Filtro Kalman 1D para fusión IR-termopar  [B5] ──────────────────
struct KalmanState {
    float x;       // estado estimado (T_leaf)
    float P;       // varianza del error de estimación
    bool  init;    // inicializado
};

RTC_DATA_ATTR KalmanState rtc_kalman = {0.0f, 1.0f, false};

/**
 * Filtro Kalman para fusión óptima IR-termopar.
 * A viento bajo: IR y termopar coinciden → confía más en IR (más píxeles).
 * A viento alto: divergen → confía más en termopar (inmune a convección).
 *   [B5] — Referencia: Kalman (1960), sensor fusion IoT.
 */
float kalman_fuse_ir_tc(float t_ir, float t_tc, float wind_ms, bool tc_valid) {
    if (!KALMAN_ENABLED || !tc_valid) return t_ir;

    // Varianza del IR crece con viento (convección → más ruido)
    float R_ir = KALMAN_R_IR_BASE + KALMAN_R_IR_WIND_SCALE * wind_ms * wind_ms;
    float R_tc = KALMAN_R_TC;

    if (!rtc_kalman.init) {
        // Inicializar con promedio ponderado
        float w_tc = R_ir / (R_ir + R_tc);
        rtc_kalman.x = t_ir * (1.0f - w_tc) + t_tc * w_tc;
        rtc_kalman.P = (R_ir * R_tc) / (R_ir + R_tc);
        rtc_kalman.init = true;
        return rtc_kalman.x;
    }

    // Predict: x_pred = x_prev (modelo estático — inercia térmica foliar)
    float P_pred = rtc_kalman.P + KALMAN_Q;

    // Update con medición IR
    float K_ir = P_pred / (P_pred + R_ir);
    float x_upd = rtc_kalman.x + K_ir * (t_ir - rtc_kalman.x);
    float P_upd = (1.0f - K_ir) * P_pred;

    // Update con medición termopar
    float K_tc = P_upd / (P_upd + R_tc);
    x_upd = x_upd + K_tc * (t_tc - x_upd);
    P_upd = (1.0f - K_tc) * P_upd;

    rtc_kalman.x = x_upd;
    rtc_kalman.P = P_upd;
    return x_upd;
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

    // ─────────────────────────────────────────
    // Cámara térmica: buffer adaptativo + Hampel + Kalman + Muller  [B1+B2+B5+C4+A3+C3]
    // Toma hasta THERMAL_BUFFER_MAX lecturas a 1s. Si alcanza THERMAL_BUFFER_MIN
    // lecturas en calma, para (ahorra tiempo). Aplica filtro Hampel sobre el buffer,
    // luego fusión Kalman con termopar(es), corrección Muller por gbh local,
    // y cálculo de Jones Ig + quality score.
    // ─────────────────────────────────────────
    GimbalFusionResult thermal = {0};
    ThermalSample tbuf[THERMAL_BUFFER_MAX] = {};
    uint8_t tbuf_count = 0;
    uint8_t n_calmas_captura = 0;
    bool    tc_ok_flag = false;
    bool    muller_ok_flag = false;
    float   jones_ig = -1.0f;       // [C3] Índice Jones (-1 = no disponible)
    float   quality_score = 0.0f;   // [B6]
    float   muller_gbh_val = 0.0f;  // [C4]
    float   wind_dir_deg = -1.0f;   // [A1] dirección viento (-1 = no disponible)

    if (captura_valida) {
        // Verificar estabilidad mecánica del nodo antes de capturar
        if (ok_imu) imu_esperar_estabilidad(3);

        // [B1] Buffer adaptativo: capturar hasta THERMAL_BUFFER_MAX, parar si
        // ya tenemos THERMAL_BUFFER_MIN lecturas en calma (ahorra tiempo + batería)
        uint8_t calm_count = 0;
        for (uint8_t si = 0; si < THERMAL_BUFFER_MAX; si++) {
            // Leer viento instantáneo para esta muestra
            AnemometroResult anemo_i = anemometro_read();
            float wind_i = anemo_i.ok ? anemo_i.wind_ms : d.wind_ms;

            // [A1] Leer dirección si anemómetro ultrasónico
            #if ANEMO_TYPE == ANEMO_TYPE_ULTRASONIC
            if (anemo_i.ok && si == 0) wind_dir_deg = anemo_i.dir_deg;
            #endif

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

            if (frame_i.ok) thermal = frame_i;
            tbuf_count++;

            if (wind_i < WIND_CALM_MS) calm_count++;

            Serial.printf("[HV] Muestra %u/%u: tc=%.2f wind=%.1f %s\n",
                          si + 1, THERMAL_BUFFER_MAX,
                          tbuf[si].tc_mean, wind_i,
                          (wind_i < WIND_CALM_MS) ? "[calma]" : "");

            // [B1] Parada temprana: ya tenemos suficientes muestras en calma
            if (si >= THERMAL_BUFFER_MIN - 1 && calm_count >= THERMAL_BUFFER_MIN) {
                Serial.printf("[HV] Parada temprana: %u muestras en calma\n", calm_count);
                break;
            }

            if (si < THERMAL_BUFFER_MAX - 1) delay(THERMAL_SAMPLE_DELAY_MS);
        }

        // [B1+B2] Seleccionar tc_mean con filtro Hampel (reemplaza mediana simple)
        TcSelection sel = seleccionar_tc_mean(tbuf, tbuf_count);
        n_calmas_captura = sel.n_calmas;
        if (sel.tc_mean > 0.0f) {
            thermal.tc_mean = sel.tc_mean;
            thermal.ok = true;
        }
        Serial.printf("[HV] Hampel: calmas=%u/%u tc=%.2f\n",
                      sel.n_calmas, sel.n_todas, sel.tc_mean);

        if (thermal.ok) {
            d.tc_mean      = thermal.tc_mean;
            d.tc_max       = thermal.tc_max;
            d.valid_pixels = thermal.valid_pixels;
            d.n_frames     = thermal.n_frames;

            // ── [A3+B5] Fusión con termopar(es) — Kalman o blending ──
            // Leer termopar(es) y fusionar con IR
            float tc_contact = 0.0f;
            uint8_t tc_valid_count = 0;

            if (ok_tc) {
                TermoparResult tc1 = termopar_read();
                if (tc1.ok && tc1.temp_c >= TC_MIN_VALID_C && tc1.temp_c <= TC_MAX_VALID_C) {
                    tc_contact = tc1.temp_c;
                    tc_valid_count = 1;
                }

                // [A3] Segundo termopar — promedio si ambos válidos
                #if TC2_ENABLED
                TermoparResult tc2 = termopar_read_ch2();  // driver_termopar.h
                if (tc2.ok && tc2.temp_c >= TC_MIN_VALID_C && tc2.temp_c <= TC_MAX_VALID_C) {
                    if (tc_valid_count == 1) {
                        tc_contact = (tc_contact + tc2.temp_c) / 2.0f;  // promedio
                        tc_valid_count = 2;
                        Serial.printf("[HV] Termopar dual: TC1=%.2f TC2=%.2f prom=%.2f\n",
                                      tc1.temp_c, tc2.temp_c, tc_contact);
                    } else {
                        tc_contact = tc2.temp_c;
                        tc_valid_count = 1;
                    }
                }
                #endif

                if (tc_valid_count > 0) {
                    tc_ok_flag = true;
                    float tc_ir = d.tc_mean;

                    // [B5] Kalman o blending estático
                    #if KALMAN_ENABLED
                    d.tc_mean = kalman_fuse_ir_tc(tc_ir, tc_contact, d.wind_ms, true);
                    Serial.printf("[HV] Kalman: IR=%.2f TC=%.2f → %.2f (P=%.4f)\n",
                                  tc_ir, tc_contact, d.tc_mean, rtc_kalman.P);
                    #else
                    d.tc_mean = tc_ir + TC_BLEND_K * (tc_contact - tc_ir);
                    Serial.printf("[HV] Blend: IR=%.2f TC=%.2f → %.2f (k=%.1f)\n",
                                  tc_ir, tc_contact, d.tc_mean, TC_BLEND_K);
                    #endif
                } else {
                    Serial.println("[HV] Termopar: sin lectura válida — solo IR");
                }
            }

            // ── [C4] Referencia dual Muller — corrección gbh local ──
            #if PIN_MULLER_ENABLED
            if (thermal.ok) {
                // Leer píxeles de las placas de aluminio del último frame MLX
                // NOTA: en producción, leer directamente del buffer de frame MLX90640
                // Aquí usamos posiciones de píxel fijas (calibradas en instalación)
                float t_black = thermal.muller_black_mean;  // temp media placa negra
                float t_white = thermal.muller_white_mean;  // temp media placa blanca
                if (t_black > 0.0f && t_white > 0.0f && d.rad_wm2 > 100.0f) {
                    muller_gbh_val = muller_gbh(t_black, t_white, d.rad_wm2);
                    if (muller_gbh_val > 0.001f) {
                        muller_ok_flag = true;
                        // Corrección: si gbh_local > gbh_ref → más convección que la referencia
                        float correction = (d.tc_mean - d.t_air) *
                                           (1.0f - fminf(muller_gbh_val / MULLER_GBH_REF, 2.0f));
                        // Aplicar corrección parcial (solo 50% para ser conservador en TRL 3)
                        d.tc_mean += correction * 0.5f;
                        Serial.printf("[HV] Muller: Tblk=%.1f Twht=%.1f gbh=%.4f corr=%.2f\n",
                                      t_black, t_white, muller_gbh_val, correction * 0.5f);
                    }
                }
            }
            #endif

            // ── [C3] Jones Ig desde paneles Wet/Dry Ref del bracket ──
            if (d.tc_wet > 0.0f && d.tc_dry > 0.0f) {
                jones_ig = calcular_jones_ig(d.tc_mean, d.tc_wet, d.tc_dry);
                if (jones_ig >= 0.0f) {
                    Serial.printf("[HV] Jones Ig=%.3f (CWSI_equiv=%.3f)\n",
                                  jones_ig, 1.0f - jones_ig);
                }
            }
        }
    } else {
        Serial.printf("[HV] MLX90640 omitido — %s\n", d.calidad_captura);
    }

    // [B6] Quality score
    float vpd_calc = 0.0f;
    {
        float es = 0.6108f * expf(17.27f * d.t_air / (d.t_air + 237.3f));
        float ea = es * d.rh / 100.0f;
        vpd_calc = es - ea;
    }
    quality_score = calcular_quality_score(d.wind_ms, d.rad_wm2, vpd_calc,
                                            n_calmas_captura, tbuf_count,
                                            tc_ok_flag, muller_ok_flag);

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
    d.tc_dry = calcular_tc_dry(d.t_air, d.rh, d.wind_ms, d.rad_wm2);  // [B4] +radiación

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
    char json[900];  // ampliado: +jones_ig, quality_score, muller, wind_dir
    snprintf(json, sizeof(json),
        "{"
        "\"v\":2,"
        "\"node_id\":\"%s\","
        "\"ts\":%lu,"
        "\"cycle\":%lu,"
        "\"env\":{\"t_air\":%.1f,\"rh\":%.1f,\"wind_ms\":%.1f,"
                 "\"wind_dir\":%.0f,"
                 "\"rain_mm\":%.1f,\"rad_wm2\":%.0f},"
        "\"thermal\":{\"tc_mean\":%.2f,\"tc_max\":%.2f,\"tc_wet\":%.2f,"
                     "\"tc_dry\":%.2f,\"cwsi\":%.3f,"
                     "\"jones_ig\":%.3f,"
                     "\"valid_pixels\":%u,\"n_frames\":%u,"
                     "\"n_calmas\":%u,\"n_muestras\":%u},"
        "\"dendro\":{\"mds_mm\":%.4f,\"mds_norm\":%.3f},"
        "\"hsi\":{\"value\":%.3f,\"w_cwsi\":%.2f,\"w_mds\":%.2f,"
                 "\"wind_override\":%s},"
        "\"quality\":{\"score\":%.1f,\"tc_ok\":%s,\"muller_ok\":%s,"
                     "\"muller_gbh\":%.4f},"
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
        d.t_air, d.rh, d.wind_ms,
        wind_dir_deg,
        d.rain_mm, d.rad_wm2,
        d.tc_mean, d.tc_max, d.tc_wet, d.tc_dry, cwsi,
        jones_ig,
        d.valid_pixels, d.n_frames,
        n_calmas_captura, tbuf_count,
        d.mds_mm, mds_norm,
        hsi,
        w_cwsi_eff,
        w_mds_eff,
        wind_override ? "true" : "false",
        quality_score, tc_ok_flag ? "true" : "false",
        muller_ok_flag ? "true" : "false", muller_gbh_val,
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
 * [B4] Ahora incorpora radiación solar además de HR y viento.
 * Jackson (1981) define ΔT_UL como función de Rn, ra y γ.
 * Baselines más precisos en días nublados y atardeceres.
 *   Referencia: Jackson et al. (1981) WRR 17(4):1133-1138.
 */
float calcular_tc_dry(float t_air, float rh, float wind_ms, float rad_wm2) {
    float delta = 10.0f - (rh / 100.0f) * 5.0f;   // 5–10°C según HR
    // [B4] Factor radiación: escalar por fracción de Rn vs. máximo típico mediodía
    float rad_factor = fminf(rad_wm2 / 900.0f, 1.0f);  // 900 W/m² = pico Cuyo verano
    if (rad_factor < 0.1f) rad_factor = 0.1f;           // mínimo 10% para evitar Tc_dry ≈ T_air
    delta *= rad_factor;
    // Factor viento (existente)
    delta *= (1.0f - wind_ms / 20.0f);
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
 *   viento >= WIND_RAMP_HI (18 m/s) → w_cwsi = 0.00 (100% MDS)
 *
 * Con mitigaciones v2 firmware (Kalman+Muller+Hampel+2do termopar),
 * 18 m/s en anemómetro ≈ 5.4-7.2 m/s en hoja, con corrección dinámica.
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
 * [B6] Quality score continuo (0-100).
 * Pondera la confianza de la lectura CWSI según condiciones ambientales
 * y disponibilidad de sensores. El backend usa esto para promedios ponderados.
 */
float calcular_quality_score(float wind_ms, float rad_wm2, float vpd,
                              uint8_t calm_samples, uint8_t total_samples,
                              bool tc_ok, bool muller_ok) {
    float score = 100.0f;
    // Penalizar por viento alto
    if (wind_ms > 4.0f) score -= (wind_ms - 4.0f) * QS_WIND_PENALTY_PER_MS;
    // Bonificar si >50% muestras en calma
    if (total_samples > 0 && (float)calm_samples / total_samples > 0.5f) {
        score += QS_CALM_BONUS;
    }
    // Penalizar sin termopar
    if (!tc_ok) score -= QS_NO_TC_PENALTY;
    // Penalizar baja radiación
    if (rad_wm2 < 400.0f) score -= QS_LOW_RAD_PENALTY;
    // Penalizar bajo VPD
    if (vpd < 0.5f) score -= QS_LOW_VPD_PENALTY;
    // Bonus corrección Muller disponible
    if (muller_ok) score += QS_MULLER_BONUS;
    return constrain(score, 0.0f, 100.0f);
}

/**
 * [C3] Índice Jones (Ig) — Jones (1999).
 * Ig = (Tc_dry - Tc_canopy) / (Tc_dry - Tc_wet)
 * Ig ≈ 0 → estomas cerrados (estrés máximo)
 * Ig ≈ 1 → transpiración libre (sin estrés)
 * Las referencias reciben el mismo viento que las hojas → auto-cancelación parcial.
 * Retorna -1 si datos insuficientes.
 */
float calcular_jones_ig(float tc_canopy, float tc_wet_ref, float tc_dry_ref) {
    float denom = tc_dry_ref - tc_wet_ref;
    if (denom < 0.5f) return -1.0f;
    float ig = (tc_dry_ref - tc_canopy) / denom;
    return constrain(ig, -0.2f, 1.2f);
}

/**
 * [C4] Conductancia de boundary layer (gbh) por método Muller.
 * Dos placas de aluminio (negra ε=0.95, blanca ε=0.15), misma masa térmica.
 * ΔT entre ellas depende de radiación absorbida y gbh.
 * gbh = (α_black - α_white) × Rn / (ρCp × thickness × ΔT_medido)
 * Referencia: Muller et al. (2021) New Phytologist 232:2535-2546.
 */
float muller_gbh(float t_black, float t_white, float rad_wm2) {
    float delta_t = t_black - t_white;
    if (delta_t < 0.2f) return 0.0f;   // placas indistinguibles
    float delta_alpha = MULLER_ALPHA_BLACK - MULLER_ALPHA_WHITE;
    // gbh ≈ (Δα × Rn) / (ρCp × d × ΔT)
    float gbh = (delta_alpha * rad_wm2) /
                (MULLER_RHO_CP * MULLER_THICKNESS_M * delta_t);
    return fmaxf(gbh, 0.0f);
}

/**
 * Estima % batería desde ADC con divisor de tensión R1/R2.
 * LiFePO4: BAT_FULL_MV = 3600 mV, BAT_EMPTY_MV = 2800 mV.
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
