# Lucas Bergon — Hardware / PCB / Embebidos
## HydroVision AG — Nodo de Campo

Carpeta de trabajo para las tareas de hardware y firmware del proyecto.

---

## Estructura

```
lucas/
├── firmware/          → Código embebido del nodo (ESP32 + sensores)
├── hardware/          → Esquemáticos, BOM, pinouts
└── documentacion/     → Sección hardware para formulario ANPCyT
```

## Cómo compilar y flashear

### Requisitos
1. **Thonny IDE** (recomendado) o **mpremote** (CLI)
2. **ESP32-S3 DevKit** off-the-shelf con módulo WROOM-1-N4 integrado
3. Instalar **MicroPython** en el DevKit:
   - Descargar firmware MicroPython para ESP32-S3 desde micropython.org/download/ESP32_GENERIC_S3
   - Flashear con: `esptool.py --chip esp32s3 --port COM_X erase_flash` y luego `esptool.py --chip esp32s3 write_flash -z 0x0 firmware.bin`
4. Copiar módulos Python al DevKit con Thonny o `mpremote cp`
5. Librerías MicroPython: instalar con `mpremote mip install` según `firmware/requirements.txt`

### Secuencia de primer flash
```
1. Conectar ESP32-S3 DevKit por USB-C
2. Mantener presionado BOOT, presionar RESET, soltar RESET, soltar BOOT
3. Flashear MicroPython con esptool.py
4. Conectar Thonny → seleccionar intérprete MicroPython (ESP32)
5. Copiar archivos .py al DevKit
6. Presionar RESET — ver log de inicialización en REPL
```

### Log de arranque esperado
```
[SOLENOIDE] OK/SKIP      ← restaura estado relé (Tier 3) o skip (Tier 1)
[MLX] OK
[MDS] OK
[SHT31] OK
[RTC] OK
[ANEMO] OK
[IMU] OK — ICM-42688-P
[LORA] OK — 915.0 MHz SF7 BW125kHz CR4/5 17dBm
[GPS] fix: lat=-31.20xx lon=-64.09xx
[HV] ========== Ciclo 1 — HV-A4CF12B3E7 ==========
```

---

## Tareas principales (Lucas)

### ✅ Ya resuelto con Claude — Lucas no necesita hacer esto

| Qué | Dónde |
|---|---|
| Ciclo principal: deep sleep, wakeup, RTC memory | `firmware/nodo_main.ino` |
| Node ID automático desde MAC ESP32 (`esp_read_mac`) | `firmware/nodo_main.ino` |
| Cálculo CWSI (Jackson 1981) con Tc_wet / Tc_dry | `firmware/nodo_main.ino` |
| Cálculo HSI con pesos adaptativos + rampa gradual viento 4-18 m/s + termopar | `firmware/nodo_main.ino` |
| Normalización MDS + corrección térmica | `firmware/nodo_main.ino` |
| Auto-calibración Tc_wet (lluvia + MDS≈0, EMA learning_rate=0.25) | `firmware/nodo_main.ino` |
| Serialización JSON payload v1 completa (todos los campos) | `firmware/nodo_main.ino` |
| Topics MQTT: telemetry / status / alert con Node ID dinámico | `firmware/nodo_main.ino` |
| Lógica de alerta HSI ≥ umbral configurable | `firmware/nodo_main.ino` |
| Variables persistentes entre ciclos (RTC_DATA_ATTR) | `firmware/nodo_main.ino` |
| BOM v1 completa con todos los componentes decididos | `hardware/BOM-nodo-v1.md` |
| Todas las decisiones de diseño documentadas | `hardware/BOM-nodo-v1.md` |
| Sección hardware completa para formulario ANPCyT | `documentacion/hardware-formulario-ANPCyT.md` |

### ✅ Drivers firmware — todos generados con Claude

| Driver | Archivo | Qué hace |
|---|---|---|
| MLX90640 | `driver_mlx90640.h` | I2C, filtro foliares P20–P75, retorna `tc_mean` / `tc_max` / `valid_pixels` |
| ADS1231 + DS18B20 | `driver_mds.h` | Bit-bang 24-bit, corrección térmica α=2.5 µm/°C |
| SHT31 | `driver_sht31.h` | I2C, retorna `t_air` / `rh` |
| DS3231 RTC | `driver_rtc.h` | epoch Unix, sync GPS, temperatura interna |
| GPS NEO-6M | `driver_gps.h` | UART1, TinyGPSPlus, epoch desde fecha GPS |
| Anemómetro RS485 | `driver_anemometro.h` | Modbus RTU, CRC16, retorna `wind_ms` |
| Pluviómetro | `driver_pluviometro.h` | ISR + debounce, acumula `rain_mm` |
| Piranómetro BPW34 | `driver_piranometro.h` | ADC1, promedio 8 muestras, retorna `rad_wm2` |
| Bomba Wet Ref | `driver_bomba_wetref.h` | GPIO, pulso temporizado `BOMBA_PULSO_MS` |
| Gimbal MG90S | `driver_gimbal.h` | LEDC PWM, 6 pos fijas + 1 nadir condicional (= 7 ángulos totales), fusión multi-frame con `valid_pixels` promediado |
| LoRa SX1276 | `driver_lora.h` | `publicar_lora(topic, json)`, encuadre binario, sleep pre-deep-sleep |
| PMS5003 partículas | `driver_pms5003.h` | UART1 compartido con GPS, PM2.5 → detección automática fumigación/lluvia |
| ICM-42688-P IMU | `driver_imu.h` | SPI, verifica estabilización gimbal antes de captura, detecta desplazamiento del nodo |
| ~~LED tricolor + sirena~~ | ~~`driver_alertas.h`~~ | REMOVIDO — alertas físicas eliminadas del diseño. Mercado = riego automatizado, el nodo actúa o reporta vía app. |
| Motor GDD + Fenología | `driver_gdd.h` | GDD multi-varietal (Malbec/Cabernet/Bonarda/Syrah/Olivo/Cerezo), T_base por especie, umbrales CWSI dinámicos por estadio, sleep adaptativo, inhibe solenoide en reposo. Varietal recibido del backend via /ingest |
| ISO_nodo (diagnóstico lente) | en `driver_mlx90640.h` | `mlx_iso_nodo(t_air)` — detecta lente sucio/empañado comparando T_dry_ref vs. esperado |

**nodo_main.ino** conecta todos los drivers.

### ⏳ Pendiente para Lucas (trabajo de hardware real)

| Prioridad | Tarea | Carpeta | Nota |
|---|---|---|---|
| 🔴 Alta | **Validar firmware en banco**: cargar módulos MicroPython en ESP32-S3 DevKit, confirmar REPL de cada sensor | firmware/ | Flashear MicroPython primero. Ver guía de compilación arriba. |
| 🔴 Alta | Calibrar **ADS1231_COUNTS_PER_UM** con medición de referencia conocida | `driver_mds.h` | Requiere extensómetro de referencia — sin esto MDS es arbitrario |
| 🔴 Alta | Calibrar **PYRANO_WPM2_PER_MV** con piranómetro de referencia | `driver_piranometro.h` | Piranómetro de referencia (e.g. Davis Vantage Pro2 ya en BOM) |
| 🟡 Media | Calibrar **PLUV_MM_PER_PULSE** con datasheet del sensor comprado | `config.h` | Dato en el datasheet del fabricante (típico: 0.2 mm/pulso) |
| 🟡 Media | Calibrar **ISO_nodo**: `mlx_calibrar_iso_nodo(dry_row, dry_col, wet_row, wet_col)` | `driver_mlx90640.h` | Ejecutar en instalación — mirar frame con Serial y ubicar los píxeles de Dry Ref / Wet Ref |
| 🟡 Media | Verificar umbrales **GDD por estadio** con Dra. Monteoliva (INTA) | `driver_gdd.h` | Los valores actuales son orientativos Malbec Mendoza — ajustar para Colonia Caroya |
| 🟡 Media | **Integrar `ventana_solar_activa()`** en el ciclo principal de `nodo_main.ino` | `firmware/nodo_main.ino` | Función ya escrita — solo falta el `if (ventana_solar_activa())` antes del bloque MLX. Ver HW-02 abajo. |
| 🟡 Media | **Actualizar `driver_mlx90640.h`** para usar `SENSOR_TERM_W/H/ADDR` de config.h en lugar de hardcoded 32/24/0x33 | `firmware/driver_mlx90640.h` | Habilita HW-03 (footprint dual). 15 min de edición. |
| ~~🟡~~ | ~~**Diseño PCB** 4-layer KiCad~~ | ~~hardware/~~ | **ELIMINADA para TRL4** — arquitectura modular DevKit + breakouts I2C/SPI. Reservada para TRL5+ producción (vol. 500+). |
| 🟡 Media | **Integración modular** — cableado I2C/SPI en carcasa Hammond IP67 200×150×100mm | hardware/ | Montar DevKit + breakouts con tornillos M2.5 o velcro industrial. Cables Stemma QT/Qwiic. |
| 🟢 Baja | **Instalación** 10 nodos en viñedo experimental (5 calibración + 5 producción) | campo | Mes 4–5 con Javier. Planta central de cada fila (planta 68). Filas 1–5: calibración (5 regímenes hídricos). Filas 6–10: producción (100% ETc, modo comercial). |
| ✅ Hecho | **Riego autonomo en nodo (Tier 3)** — `driver_solenoide.h` integrado en `nodo_main.ino` | firmware/ | El nodo decide localmente cuando regar (HSI >= umbral dinámico por estadio). `SOLENOIDE_CANAL = 0` desactiva la logica de riego en nodos Tier 1-2. |
| ✅ Hecho | **Control fenológico del riego** — inhibición automática en dormancia/post-cosecha | firmware/ + mvc/ | El solenoide NO se activa durante reposo (Ky ≤ 0.15). Aplica en nodo (Protección 0), backend (/irrigate, /ingest) y dashboard. Umbral HSI dinámico por estadio. Sleep 6h en dormancia. **Ver `documentacion/control-fenologico-riego.md`** |

---

### 🔧 Mejoras de hardware identificadas en análisis Venture Architect (doc-02 sec. 4.6.3)

Estas tres tareas cierran desventajas reales del sistema dual CWSI+MDS identificadas
en el análisis competitivo. No son opcionales para TRL 5 — afectan el COGS, la
autonomía y el riesgo de supply chain.

#### HW-01 — Reducción de COGS del componente óptico (lote 1: +USD 47 → lote 500+: +USD 22)

**Objetivo:** reducir el sobrecosto del MLX90640 vs. MDS-solo de USD 47 a USD 22 con escala.

Tres acciones independientes, cada una reduce costo:

**a) Panel de referencia de emisividad — fabricación interna (USD 6 → USD 2)**
El panel PTFE + anodizado negro se fabrica con materiales de ferretería industrial.
El costo de USD 6 es el precio de compra externa. Fabricando internamente:
- PTFE varilla 20mm Ø × 3cm: USD 0,80 (MercadoLibre / plásticos industriales)
- Pintura aerosol negro mate alta temperatura (Rust-Oleum o similar): USD 0,50 por panel
- Aluminio anodizado negro 5×5cm: USD 0,70
- Total fabricación: ~USD 2 por panel

**b) Carcasa óptica integrada en molde principal (USD 5 → USD 0)**
La versión actual tiene una pieza separada (protector lente IP54).
Al diseñar el molde de inyección de la carcasa principal (para tirada ≥50 unidades),
incluir el alojamiento del MLX90640 y el domo óptico como parte del molde único.
Costo adicional del molde: +USD 200-300 one-time → amortizado en 50 unidades = USD 4-6/u.
A partir de la unidad 51: costo de la pieza separada = USD 0.
Pendiente: diseñar el alojamiento óptico en el CAD de la carcasa antes de mandar a
moldear. Dimensiones MLX90640: 4,9×3,9 mm footprint, TO39 package, lente 78°×55° FOV.

**c) Precio MLX90640 a volumen — contactar Melexis directamente**
Precio Mouser/DigiKey lote 1-10u: USD 28-32.
Precio directo Melexis con NDA + forecast 500 u/año: USD 18-22 (estimado basado en
descuentos publicados para sensores de visión térmica automotriz de Melexis).
Acción: enviar inquiry a sales@melexis.com con descripción de la aplicación y forecast
de volumen. Hacerlo antes de la fabricación del lote TRL 5 (no TRL 4).

---

#### HW-02 — Activación adaptativa del MLX90640 ✅ código listo — falta integrar en ciclo

**Objetivo:** eliminar la penalización de −20% de autonomía de batería del sistema dual
sin comprometer la cobertura de datos CWSI.

**Razonamiento:** el CWSI requiere gradiente térmico solar activo para ser válido.
Capturar fuera de la ventana solar (06:00-07:00 y 18:30-06:00) gasta energía sin
producir datos usables — el CWSI calculado a las 03:00 AM es inválido por definición.

**Implementación en firmware — `nodo_main.ino`:**

```cpp
// En la función de decisión de ciclo, antes de activar el MLX90640:
bool ventana_solar_activa() {
    int hora = rtc_hora_local();  // hora local desde DS3231
    // Ventana solar útil: 07:00 a 18:30 (ajustar por zona y estación)
    return (hora >= 7 && hora < 19);
}

// En el ciclo principal:
if (ventana_solar_activa()) {
    mlx_capturar_frame();       // activa el MLX90640
    calcular_cwsi();
} else {
    // Solo MDS + meteo — sin térmica
    payload.cwsi = NAN;         // campo vacío en JSON, no error
    payload.cwsi_valid = false;
}
```

**Impacto en consumo:**
```
Sin ventana solar:  96 activaciones/día × 8 seg × 5mW = 11,5 mWh/día
Con ventana solar:  46 activaciones/día × 8 seg × 5mW =  5,5 mWh/día  (−52%)
Equivalente µA:     ~22 µA → ~14 µA promedio
Autonomía sin sol:  ~13 meses → ~17 meses  (+30%)
Con solar 6W:       ilimitada en cualquier caso
```

**Mejora adicional: modo bajo consumo en días nublados**
Si el piranómetro reporta rad_wm2 < 150 W/m² durante 3 ciclos consecutivos (nublado):
aumentar intervalo de captura MLX a 60 minutos en lugar de 15. El MDS sigue a 15 min.
Esto preserva la señal de tallo con resolución completa en días sin información térmica útil.

**Dónde integrar — código ya escrito, falta el llamado:**

La función `ventana_solar_activa()` ya está en `nodo_main.ino` y `rtc_leer_hora_local()`
ya está en `driver_rtc.h`. Solo falta envolver el bloque de captura MLX en el ciclo principal:

```cpp
// En setup() — bloque de captura MLX90640, buscar "mlx_capturar" y envolver así:
if (ventana_solar_activa()) {
    MlxResult mlx_r = mlx_capturar_frame_multiangular(...);
    // ... resto del bloque térmico existente ...
} else {
    d.tc_mean = NAN;
    d.cwsi    = NAN;
    d.valid_pixels = 0;
    d.calidad_captura = "fuera_ventana";
}
```

Las constantes `MLX_VENTANA_SOLAR_INI/FIN` y `MLX_RAD_MIN_WM2` ya están en `config.h`.

---

#### HW-03 — Breakout alternativo para sensor térmico (elimina riesgo de proveedor único)

**Objetivo:** tener módulos breakout alternativos listos para intercambiar con el MLX90640 breakout principal, usando el mismo conector I2C.

**Contexto:** el MLX90640 tuvo escasez en 2021-2023 con precio ×2,4 (USD 28 → USD 68).
Con la arquitectura modular TRL4, cambiar de sensor es simplemente desconectar un breakout y conectar otro — sin rediseño de PCB.

**Sensores alternativos compatibles (todos con breakout I2C):**

| Sensor | Fabricante | Resolución | Protocolo | Breakout disponible | Precio est. |
|---|---|---|---|---|---|
| MLX90640 (BAB, 110° FOV) | Melexis (Bélgica) | 32×24 px | I2C 0x33 | Adafruit 4407 / SparkFun SEN-14844 | USD 45-55 |
| **MLX90641BAB** | Melexis (Bélgica) | 16×12 px | I2C 0x33 | Adafruit / AliExpress clone | USD 18-22 |
| **Heimann HMS-C11L** | Heimann Sensor (Alemania) | 16×16 px | I2C 0x40 | Contacto directo Heimann | USD 22-28 |

**Ajuste de firmware MicroPython por variante:**
- MLX90640 (32×24): código principal sin cambios
- MLX90641 (16×12): cambiar `MLX_WIDTH=16`, `MLX_HEIGHT=12` en configuración — los aliases de compatibilidad ya existen en el pipeline Python de César
- HMS-C11L (16×16): verificar datasheet protocolo I2C (dirección 0x40 — cambiar en config)

**Ventaja de la arquitectura modular:** ante una escasez del MLX90640, producción puede cambiar a MLX90641 o HMS-C11L desconectando un cable I2C y conectando otro breakout — sin fabricar nueva PCB, solo cambiar la configuración MicroPython. Para TRL5+ con PCB custom: diseñar footprint dual TO39.

## Sensores del nodo (decididos)

| Sensor | Modelo | Protocolo |
|---|---|---|
| Cámara LWIR | MLX90640 breakout integrado (Adafruit 4407, sensor BAB 110°×75°, 32×24 px) | I2C (Stemma QT) |
| Extensómetro | Strain gauge + ADS1231 24-bit + DS18B20 | SPI + 1-Wire |
| Anemómetro | RS485 Modbus RTU (0–60 m/s) | RS485 via MAX485 |
| Pluviómetro | Báscula balancín, pulso digital | GPIO interrupción |
| Sensor T/HR | SHT31 (±0.3°C, ±2% RH) | I2C |
| Piranómetro | BPW34 + ADC o equivalente | ADC analógico |
| GPS | u-blox NEO-6M | UART |
| RTC | DS3231 + CR2032 | I2C |
| IMU + Gimbal | ICM-42688-P + 2× MG90S | SPI + PWM (LEDC) |
| Dry/Wet Ref | Panel Al + fieltro + bomba peristáltica 6V + reservorio 10L | GPIO |
| Solenoide (Tier 3) | Relé SSR 24VAC 2A + Rain Bird 24VAC 1" | GPIO 41 (`driver_solenoide.h`) |

## Comunicación (decidido)

- **LoRaWAN privado**: nodo ↔ gateway de campo (SX1276, 915 MHz)
- **Gateway → backend César**: MQTT over TLS
- **Payload**: JSON v1 — topic `hydrovision/{node_id}/telemetry` cada 15 min
- **Node ID**: `HV-` + últimos 5 bytes MAC ESP32 (burned en eFuse)

## Pines — resumen rápido (ESP32-S3)

| Bus | Pines | Dispositivos |
|---|---|---|
| I2C | SDA=8, SCL=9 | MLX90640, SHT31, DS3231, ICM-42688-P (alt.) |
| SPI (explícito) | MOSI=34, MISO=33, SCLK=32 | LoRa SX1276 (CS=10), IMU ICM-42688-P (CS=22) |
| UART1 | RX=5, TX=6(NC) | GPS NEO-6M (solo boot 1) |
| UART1 (reasignado) | RX=12, TX=13 | PMS5003 (ciclos siguientes) |
| UART2 | RX=7, TX=4, DE=3 | Anemómetro RS485 |
| SPI bit-bang | SCLK=14, DOUT=15, PDWN=16 | ADS1231 extensómetro |
| 1-Wire | GPIO=17 | DS18B20 |
| LEDC PWM | GPIO=20, 21 | Servo PAN, TILT |
| ADC1 | GPIO=1, 40 | Piranómetro, Batería |
| GPIO salida | 22(IMU-CS), 23(IMU-INT), 24(Piezo), 35(Bomba), 41(Solenoide Tier 3) | 36-39 libres (LED/sirena removidos) |
| GPIO entrada | 2(Pluviómetro ISR), 19(LoRa DIO0) | |

**Conflictos resueltos:**
- GPIO 11/12/13 (SPI default ESP32-S3) → NO usar; reasignado a SPI=34/33/32
- GPIO 6 (GPS TX) → sin conectar en PCB (solo lectura GPS)
- GPIO 40 para batería ADC (libre, sin conflicto)

## Energía (decidido)

- Panel solar **6W** policristalino + LiFePO4 32650 3,2V 6Ah
- Deep sleep ESP32-S3: ~8 µA
- Consumo promedio: ~0.18W (pico 0.7W durante captura MLX90640)
- Autonomía sin sol: **~120 horas** (LiFePO4 6Ah / 0.18W promedio)
