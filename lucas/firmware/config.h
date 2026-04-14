/*
 * HydroVision AG — Configuración de pines y constantes globales
 * Plataforma: ESP32-S3 (Arduino framework)
 *
 * IMPORTANTE: confirmar todos los pines contra el esquemático PCB v1 antes de compilar.
 */

#pragma once

// ─────────────────────────────────────────
// I2C — compartido: MLX90640, SHT31, DS3231, IMU
// ─────────────────────────────────────────
#define PIN_I2C_SDA         8
#define PIN_I2C_SCL         9

// ─────────────────────────────────────────
// MLX90640 — cámara térmica (I2C)
// ─────────────────────────────────────────
#define MLX90640_I2C_ADDR   0x33
#define MLX_REFRESH_RATE    MLX90640_2_HZ   // 2 Hz es suficiente para una captura

// ─────────────────────────────────────────
// ADS1231 — extensómetro 24-bit (bit-bang)
// ─────────────────────────────────────────
#define PIN_ADS_SCLK        14
#define PIN_ADS_DOUT        15   // input
#define PIN_ADS_PDWN        16   // active LOW = power down

// ─────────────────────────────────────────
// DS18B20 — corrección térmica extensómetro (OneWire)
// ─────────────────────────────────────────
#define PIN_DS18B20         17
#define DS18B20_RESOLUTION  12   // bits (0.0625°C)

// ─────────────────────────────────────────
// SHT31 — temperatura + humedad aire (I2C)
// ─────────────────────────────────────────
#define SHT31_I2C_ADDR      0x44

// ─────────────────────────────────────────
// GPS u-blox NEO-6M (UART1)
// ─────────────────────────────────────────
#define PIN_GPS_RX          5
#define PIN_GPS_TX          6    // no usado si solo leemos
#define GPS_BAUD            9600
#define GPS_TIMEOUT_MS      2000

// ─────────────────────────────────────────
// DS3231 RTC (I2C)
// ─────────────────────────────────────────
#define DS3231_I2C_ADDR     0x68

// ─────────────────────────────────────────
// Anemómetro RS485 Modbus RTU (UART2 + MAX485)
// ─────────────────────────────────────────
#define PIN_RS485_RX        7
#define PIN_RS485_TX        4
#define PIN_RS485_DE        3    // driver enable MAX485 (HIGH = transmit)
#define RS485_BAUD          9600
#define RS485_MODBUS_ADDR   1    // dirección Modbus del anemómetro
#define RS485_REG_WIND      0x0000  // registro velocidad de viento
#define RS485_SCALE         0.1f    // factor escala: valor_raw × 0.1 = m/s

// ─────────────────────────────────────────
// Pluviómetro — báscula balancín (GPIO interrupción)
// ─────────────────────────────────────────
#define PIN_PLUV_INT        2
#define PLUV_MM_PER_PULSE   0.2f  // mm de lluvia por pulso (calibrar con fabricante)
#define PLUV_DEBOUNCE_MS    200

// ─────────────────────────────────────────
// Piranómetro BPW34 + ADC (ADC1, sin conflicto WiFi)
// ─────────────────────────────────────────
#define PIN_PYRANO_ADC      1    // ADC1_CH0
#define PYRANO_ADC_REF_MV   3300 // referencia ADC en mV
#define PYRANO_ADC_BITS     12   // resolución
#define PYRANO_WPM2_PER_MV  1.0f // calibrar con sensor real (W/m² por mV)

// ─────────────────────────────────────────
// Gimbal — servos MG90S (LEDC ESP32-S3)
// ─────────────────────────────────────────
#define PIN_SERVO_PAN       20
#define PIN_SERVO_TILT      21
#define SERVO_FREQ_HZ       50
#define SERVO_MIN_US        500   // pulso mínimo (0°)
#define SERVO_MAX_US        2500  // pulso máximo (180°)
#define SERVO_CENTER_US     1500  // centro (90°)
// Posiciones del scan (en grados, referencia centro = 0°)
#define GIMBAL_PAN_L        -20
#define GIMBAL_PAN_R        +20
#define GIMBAL_TILT_UP      +15
#define GIMBAL_TILT_DOWN    -10
#define GIMBAL_SETTLE_MS    300   // tiempo para que el servo llegue a posición

// ─────────────────────────────────────────
// Bomba peristáltica Wet Ref (GPIO)
// ─────────────────────────────────────────
#define PIN_BOMBA_WETREF    35
#define BOMBA_PULSO_MS      3000  // ms que corre la bomba por ciclo de recarga

// ─────────────────────────────────────────
// SPI bus compartido: LoRa SX1276 + IMU ICM-42688-P
// Pines explícitos para evitar conflicto con PMS5003 (UART1 GPIO 12/13)
// y con PIN_BAT_ADC (GPIO 11 = MOSI default del ESP32-S3 — NO usar).
// Llamar SPI.begin(PIN_SPI_SCLK, PIN_SPI_MISO, PIN_SPI_MOSI) antes de lora_init().
// ─────────────────────────────────────────
#define PIN_SPI_MOSI        34
#define PIN_SPI_MISO        33
#define PIN_SPI_SCLK        32

// ─────────────────────────────────────────
// LoRa SX1276 (SPI — pines CS/RST/DIO0 solo este módulo)
// ─────────────────────────────────────────
#define PIN_LORA_SS         10
#define PIN_LORA_RST        18
#define PIN_LORA_DIO0       19
#define LORA_FREQ_HZ        915E6  // 915 MHz (regulación AR — banda ISM)
#define LORA_SF             7      // spreading factor
#define LORA_BW             125E3  // bandwidth
#define LORA_CR             5      // coding rate 4/5
#define LORA_TX_POWER       17     // dBm

// ─────────────────────────────────────────
// IMU ICM-42688-P (SPI — bus compartido con LoRa, CS separado)
// Verifica estabilización del gimbal antes de capturar frame MLX90640.
// INT1: interrupción de datos listos (opcional; polling también soportado).
// ─────────────────────────────────────────
#define PIN_IMU_CS          22
#define PIN_IMU_INT1        23
#define IMU_VIB_UMBRAL_MS2  0.5f    // m/s² — aceleración máxima aceptable durante captura

// ─────────────────────────────────────────
// Limpieza piezoeléctrica de lente MLX90640
// Actuador: Murata MZB1001T02 (~200 Hz, 20 Vpp via driver boost).
// Activar antes de cada secuencia de captura para eliminar polvo/rocío.
// ─────────────────────────────────────────
#define PIN_PIEZO_CLEANER   24
#define PIEZO_PULSO_MS      500     // ms de vibración por ciclo de limpieza

// ─────────────────────────────────────────
// Termopar foliar — MAX31855 (SPI, bus compartido)
// Mide T_leaf por contacto directo, inmune al viento.
// Se usa para corregir la lectura IR del MLX90640:
//   T_leaf_corr = T_leaf_IR + TC_BLEND_K × (T_termopar - T_leaf_IR)
// TC_BLEND_K = factor de corrección (0.0 = solo IR, 1.0 = solo termopar)
// Valor inicial 0.6 — calibrar en campo con Scholander por varietal.
// ─────────────────────────────────────────
// Termopar 1 (principal) — MAX31855 SPI
#define PIN_TC_CS               25      // GPIO chip select MAX31855 (SPI compartido)
#define TC_BLEND_K              0.6f    // factor de corrección IR↔termopar (calibrar en campo)
#define TC_MIN_VALID_C          5.0f    // °C mín para considerar lectura válida (descarta fallas)
#define TC_MAX_VALID_C          60.0f   // °C máx para considerar lectura válida
// Termopar 2 (redundancia + promediado)  [A3]
// Segundo termopar en hoja separada del mismo canopeo. Si ambos válidos,
// se promedian antes del blending con IR → reduce error contacto ÷√2.
#define PIN_TC2_CS              26      // GPIO chip select MAX31855 #2 (SPI compartido)
#define TC2_ENABLED             true    // false si no hay segundo termopar instalado

// ─────────────────────────────────────────
// Alertas físicas — REMOVIDO
// ─────────────────────────────────────────
// LED tricolor + sirena eliminados del diseño (abril 2026).
// Mercado objetivo = plantaciones con riego automatizado.
// El nodo actúa autónomamente (Tier 2) o reporta vía app (Tier 1).
// Alertas visuales/sonoras en campo no aportan valor al productor.
// GPIO 36-39 quedan libres para uso futuro.
// #define PIN_LED_VERDE    36
// #define PIN_LED_AMBAR    37
// #define PIN_LED_ROJO     38
// #define PIN_SIRENA       39

// ─────────────────────────────────────────
// Batería — ADC divisor de tensión
// GPIO 40 (ADC libre, sin conflicto con SPI ni UART).
// GPIO 6 (GPS TX): no conectar en PCB — solo leemos GPS, TX no se usa.
// GPIO 11 reservado para SPI MOSI — NO usar como ADC.
// ─────────────────────────────────────────
#define PIN_BAT_ADC         40   // ADC libre — sin conflicto SPI/UART
#define BAT_R1              100000  // ohm (resistor hacia Vbat)
#define BAT_R2              47000   // ohm (resistor hacia GND)
#define BAT_FULL_MV         4200    // LiFePO4 llena (usar 3600 si se cambia a LiFePO4)
#define BAT_EMPTY_MV        3000    // mínimo operativo

// ─────────────────────────────────────────
// Sensor de partículas PMS5003 (UART1, compartido con GPS)
// GPS usa GPIO 5/6 solo en primer boot; PMS5003 usa GPIO 12/13 desde boot 1.
// ─────────────────────────────────────────
#define PIN_PMS_RX              12
#define PIN_PMS_TX              13
#define PMS_BAUD                9600
#define PMS_WARMUP_MS           3000    // ms calentamiento láser antes de lectura válida
#define PMS_PM25_FUMIG          200     // µg/m³ — umbral detección fumigación
                                        // (campo limpio: 10–30; fumigación: 500–5000)
#define PMS_PM25_LLUVIA         80      // µg/m³ — aerosol de lluvia (menor que fumigación)

// ─────────────────────────────────────────
// Clearance post-evento (horas hasta retomar captura MLX90640 + extensómetro)
// ─────────────────────────────────────────
#define LLUVIA_CLEARANCE_HRS    3       // h post-lluvia: gotas en canopeo + tronco saturado
#define FUMIGACION_CLEARANCE_HRS 4      // h post-fumigación: residuo en lente + hoja

// ─────────────────────────────────────────
// Ciclo de operación
// ─────────────────────────────────────────
#define SLEEP_INTERVAL_SEC      (15 * 60)   // 15 min entre mediciones
#define STATUS_INTERVAL_CYCLES  4           // publicar /status cada 4 ciclos = 1 hora
// Transición gradual de pesos CWSI/MDS según viento:
//   viento <= WIND_RAMP_LO  → w_cwsi = 0.35 (normal)
//   WIND_RAMP_LO < v < WIND_RAMP_HI → rampa lineal (0.35 → 0.00)
//   viento >= WIND_RAMP_HI → w_cwsi = 0.00 (backup 100% MDS)
//
// Con orientación a sotavento (60-70%), tubo colimador, termopar con Kalman [B5],
// Muller gbh [C4], buffer Hampel [B2] y segundo termopar [A3], el viento efectivo
// en la hoja medida es ~30-40% del medido en el anemómetro y la medición se corrige
// dinámicamente. 18 m/s medido ≈ 5.4-7.2 m/s en hoja → límite útil del CWSI con
// mitigaciones v2 firmware. Backend extiende a 21-22 m/s con ML (C1, C2, C6).
#define WIND_RAMP_LO            4.0f        // m/s (14 km/h) — inicio de reducción peso CWSI
#define WIND_RAMP_HI           18.0f        // m/s (65 km/h) — override total a 100% MDS
#define HSI_ALERT_THRESHOLD     0.70f       // HSI >= esto → topic /alert
#define LLUVIA_MIN_MM           5.0f        // umbral para auto-calibración Tc_wet
#define MDS_CAL_MAX_MM          0.05f       // MDS < esto = planta bien hidratada

// ─────────────────────────────────────────
// Buffer térmico adaptativo con filtro Hampel + calma  [B1+B2]
// El nodo toma hasta THERMAL_BUFFER_MAX lecturas térmicas por ciclo.
// Si alcanza THERMAL_BUFFER_MIN lecturas en calma antes, para (ahorra tiempo).
// Selección: filtro Hampel (MAD) sobre lecturas en calma, o todas si no hay calma.
// Hampel reemplaza outliers con la mediana antes de promediar → más preciso que
// mediana sola y más robusto que promedio (reduce NETD efectivo ~40%).
// ─────────────────────────────────────────
#define THERMAL_BUFFER_MIN      5           // mín lecturas antes de evaluar parada temprana
#define THERMAL_BUFFER_MAX     15           // máx lecturas por ciclo (total: 15 × 1s = 15s)
#define THERMAL_SAMPLE_DELAY_MS 1000        // ms entre lecturas (1s para capturar micro-calmas)
#define WIND_CALM_MS            2.0f        // m/s — umbral de calma para filtro térmico
#define HAMPEL_K                3.0f        // factor MAD para detección de outliers Hampel
// Backward compat alias
#define THERMAL_BUFFER_SIZE     THERMAL_BUFFER_MAX

// ─────────────────────────────────────────
// HW-02 — Activación adaptativa del MLX90640
// El CWSI requiere gradiente solar activo → no activar fuera de ventana solar.
// Reduce consumo de ~22 µA a ~14 µA equivalente (+30% autonomía sin solar).
// Ajustar según latitud y estación: Cuyo (31°S) amanecer/atardecer verano ≈ 6:30/20:30
// Usar margen conservador: activo 07:00-19:00 (pico VPD 11-16hs siempre incluido).
// ─────────────────────────────────────────
#define MLX_VENTANA_SOLAR_INI   7    // hora local inicio activación MLX (hora entera)
#define MLX_VENTANA_SOLAR_FIN   19   // hora local fin activación MLX (hora entera)
// NOTA: fuera de ventana, el ciclo corre igualmente (MDS + meteo) pero no activa el MLX.
// El campo thermal.cwsi en el JSON queda como NaN / null — el backend lo maneja.

// ─────────────────────────────────────────
// HW-02 — Modo ahorro en días nublados
// Si rad < MLX_RAD_MIN_WM2 durante 3 ciclos consecutivos → ampliar intervalo MLX a 60 min.
// El MDS sigue a 15 min (no cambia). Solo ahorra batería si hay nubosidad persistente.
// ─────────────────────────────────────────
#define MLX_RAD_MIN_WM2         150  // W/m² — por debajo = nublado, CWSI poco informativo
#define MLX_NUBLADO_CICLOS      3    // ciclos consecutivos bajo umbral → modo ahorro
#define MLX_NUBLADO_INTERVALO   4    // activar MLX 1 de cada N ciclos en modo nublado

// ─────────────────────────────────────────
// HW-03 — Variante de sensor térmico (footprint PCB dual)
// Cambiar este define según el sensor montado. Ajusta resolución y dirección I2C.
// MLX90640:  32×24 px, I2C 0x33 — sensor de producción nominal
// MLX90641:  16×12 px, I2C 0x33 — alternativa Melexis (mismo footprint TO39, menor res.)
// HMS_C11L:  16×16 px, I2C 0x40 — alternativa Heimann Sensor (footprint TO39-compatible)
// ─────────────────────────────────────────
#define SENSOR_TERMICO_MLX90640  0
#define SENSOR_TERMICO_MLX90641  1
#define SENSOR_TERMICO_HMS_C11L  2
#define SENSOR_TERMICO           SENSOR_TERMICO_MLX90640  // ← cambiar según BOM del lote

#if SENSOR_TERMICO == SENSOR_TERMICO_MLX90640
  #define SENSOR_TERM_W   32
  #define SENSOR_TERM_H   24
  #define SENSOR_TERM_ADDR 0x33
#elif SENSOR_TERMICO == SENSOR_TERMICO_MLX90641
  #define SENSOR_TERM_W   16
  #define SENSOR_TERM_H   12
  #define SENSOR_TERM_ADDR 0x33
#elif SENSOR_TERMICO == SENSOR_TERMICO_HMS_C11L
  #define SENSOR_TERM_W   16
  #define SENSOR_TERM_H   16
  #define SENSOR_TERM_ADDR 0x40
#endif
// NOTA firmware: driver_mlx90640.h usa SENSOR_TERM_W/H/ADDR en lugar de 32/24/0x33.
// Pendiente: validar protocolo HMS-C11L contra datasheet (API I2C ligeramente distinta).

// ─────────────────────────────────────────
// Referencia dual Muller (gbh desde ΔT aluminio)  [C4]
// Dos placas de aluminio (5×5 cm) en bracket: una negra (ε=0.95), una blanca (ε=0.15).
// Misma masa térmica, distinta absorción solar → ΔT entre ellas permite derivar
// conductancia de boundary layer (gbh) sin anemómetro, en el micro-sitio exacto.
// Corrección T_leaf: T_corr = T_leaf - (T_leaf - T_air) × (1 - gbh_local/gbh_ref)
// Referencia: Muller et al. (2021) New Phytologist 232:2535-2546.
// ─────────────────────────────────────────
#define PIN_MULLER_ENABLED      true        // false si no hay placas Muller instaladas
// Posición en frame MLX90640 (píxeles fijos, calibrar en instalación)
#define MULLER_BLACK_ROW_INI    20          // fila inicio placa negra
#define MULLER_BLACK_ROW_FIN    22          // fila fin
#define MULLER_BLACK_COL_INI    2           // col inicio
#define MULLER_BLACK_COL_FIN    5           // col fin
#define MULLER_WHITE_ROW_INI    20          // fila inicio placa blanca
#define MULLER_WHITE_ROW_FIN    22
#define MULLER_WHITE_COL_INI    27
#define MULLER_WHITE_COL_FIN    30
#define MULLER_GBH_REF          0.05f       // gbh de referencia [m/s] (calma, ~0.5 m/s viento)
// Propiedades térmicas del aluminio (para cálculo de gbh)
#define MULLER_RHO_CP           2400000.0f  // ρ×Cp aluminio [J/m³/K]
#define MULLER_THICKNESS_M      0.002f      // espesor placa [m] (2mm)
#define MULLER_ALPHA_BLACK      0.95f       // absortividad placa negra
#define MULLER_ALPHA_WHITE      0.15f       // absortividad placa blanca

// ─────────────────────────────────────────
// Anemómetro ultrasónico 2D (alternativa al mecánico)  [A1]
// Mismo bus RS485, cambio de registros Modbus. Detección automática por ID.
// Ventajas: sin partes móviles, 10-20 Hz, detección de ráfagas <1s,
// mide dirección (valida que sotavento funciona en ese instante).
// ─────────────────────────────────────────
#define ANEMO_TYPE_MECHANICAL   0
#define ANEMO_TYPE_ULTRASONIC   1
#define ANEMO_TYPE              ANEMO_TYPE_MECHANICAL  // ← cambiar si se instala ultrasónico
#define ANEMO_ULTRA_REG_SPEED   0x0000      // registro velocidad (m/s × 10)
#define ANEMO_ULTRA_REG_DIR     0x0001      // registro dirección (grados 0-359)
#define ANEMO_ULTRA_SCALE       0.1f

// ─────────────────────────────────────────
// Quality score continuo  [B6]
// Score 0-100 que pondera la confianza de cada lectura CWSI según condiciones.
// El backend puede hacer promedios ponderados por calidad.
// ─────────────────────────────────────────
#define QS_WIND_PENALTY_PER_MS  5.0f        // puntos por cada m/s sobre 4
#define QS_CALM_BONUS           10.0f       // bonus si >50% muestras en calma
#define QS_NO_TC_PENALTY        15.0f       // penalización sin termopar
#define QS_LOW_RAD_PENALTY      20.0f       // penalización rad < 400 W/m²
#define QS_LOW_VPD_PENALTY      15.0f       // penalización VPD < 0.5 kPa
#define QS_MULLER_BONUS         5.0f        // bonus si corrección Muller disponible

// ─────────────────────────────────────────
// Captura oportunista en calma  [B3]
// Si el viento promedio del último minuto baja de WIND_CALM_MS entre ciclos
// normales (15 min), hacer captura extra adelantada.
// Máximo OPORT_MAX_PER_HOUR capturas extra por hora para no agotar batería.
// ─────────────────────────────────────────
#define OPORT_ENABLED           true
#define OPORT_MAX_PER_HOUR      2           // máx capturas oportunistas por hora
#define OPORT_WIND_AVG_WINDOW   60          // segundos de promedio para evaluar calma

// ─────────────────────────────────────────
// Filtro Kalman para fusión IR-termopar  [B5]
// Ajusta el peso IR↔termopar dinámicamente según la confianza de cada sensor.
// Viento bajo → IR y termopar coinciden → más peso a IR (más píxeles).
// Viento alto → divergen → más peso al termopar (inmune a convección).
// ─────────────────────────────────────────
#define KALMAN_ENABLED          true
#define KALMAN_Q                0.01f       // process noise (varianza predicción)
#define KALMAN_R_IR_BASE        0.04f       // measurement noise IR base (varianza)
#define KALMAN_R_IR_WIND_SCALE  0.02f       // incremento R_IR por m/s de viento
#define KALMAN_R_TC             0.01f       // measurement noise termopar (fijo, bajo)

// ─────────────────────────────────────────
// MDS — normalización (sacar de nodo_main.ino → centralizar aquí)
// MDS_MAX_MM: contracción máxima de referencia para normalizar a 0-1.
// Rango típico Malbec: 0.3–0.5 mm (ajustar con datos campo — Mes 4-6, ver pendientes README).
// Referencia: Fernández & Cuevas-Rolando 2010, Acta Horticulturae.
// ─────────────────────────────────────────
#define MDS_MAX_MM              0.5f  // mm — CALIBRAR con datos reales del viñedo (ver HW pendientes)

// ─────────────────────────────────────────
// HW-04 — Control de riego autónomo en nodo (Tier 3)
//
// Arquitectura: el nodo decide localmente cuándo regar. No espera órdenes
// del backend. El backend solo se entera via /ingest del estado del solenoide.
//
// Lógica:
//   - HSI >= RIEGO_HSI_ACTIVAR  → activar solenoide (abrir válvula)
//   - HSI <  RIEGO_HSI_DESACTIVAR → desactivar (cerrar válvula)
//   - Histéresis (0.30→0.20) evita ciclos rápidos ON/OFF
//   - Duración máxima: RIEGO_MAX_CICLOS × 15 min = 120 min de seguridad
//   - Solo se activa dentro de la ventana de riego (configurable por hora)
//
// El nodo informa en el payload JSON:
//   "solenoid": {canal, active, reason, ciclos_activo}
//
// El backend puede enviar un override manual via LoRa (TRL 5+):
//   topic hydrovision/{node_id}/command/irrigate → {active: bool}
// ─────────────────────────────────────────

// Solenoide: GPIO del relé SSR (0 = nodo sin solenoide instalado)
// En nodos Tier 1-2 (solo sensor): dejar en 0. El firmware detecta
// automáticamente si tiene solenoide y omite toda la lógica de riego.
#define PIN_SOLENOIDE           41   // GPIO → SSR → solenoide Rain Bird 24VAC
#define SOLENOIDE_CANAL         0    // canal Rain Bird (0 = sin solenoide, 1-5 = canal asignado)

// Modo simulación de solenoide: controlado dinámicamente desde la web.
// El backend envía "sol_sim":true/false en la respuesta /ingest (downlink LoRa).
// El nodo lo almacena en rtc_sol_sim (RTC memory, ver driver_solenoide.h).
// En simulación: la lógica de riego corre pero el GPIO no se activa.

// Umbrales HSI para activación autónoma (con histéresis)
// Referencia: Jackson et al. 1981 — CWSI > 0.30 = inicio estrés moderado
// El umbral de activación usa HSI (fusión CWSI+MDS), no CWSI solo.
#define RIEGO_HSI_ACTIVAR       0.30f  // HSI >= esto → abrir solenoide
#define RIEGO_HSI_DESACTIVAR    0.20f  // HSI <  esto → cerrar solenoide (histéresis)

// Protecciones
#define RIEGO_MAX_CICLOS        8      // máx ciclos consecutivos con solenoide abierto
                                       // = 8 × 15 min = 120 min. Seguridad anti-fuga.
#define RIEGO_VENTANA_INI       6      // hora local inicio ventana de riego permitido
#define RIEGO_VENTANA_FIN       22     // hora local fin. Fuera de ventana: no activa.
#define RIEGO_INHIBIR_LLUVIA    true   // no regar si calidad_captura == "lluvia"
