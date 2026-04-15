## PROMPT PARA GENERACIÓN DE IMAGEN — Diagrama de Bloques Electrónico del Nodo HydroVision AG

---

### ESTILO VISUAL

Diagrama de bloques electrónico profesional, estilo datasheet de referencia o application note de Texas Instruments / Espressif. Fondo blanco. Bloques rectangulares con bordes sólidos, color de relleno suave por tipo de bus (amarillo para I2C, verde para SPI, celeste para UART/RS485, rosa para GPIO/analógico). Líneas de conexión coloreadas por bus con etiquetas de pines GPIO. Texto negro monoespaciado para pines y direcciones, sans-serif para nombres de componentes. Sin efectos 3D ni sombras. Organización jerárquica con el MCU en el centro.

---

### ESTRUCTURA DEL DIAGRAMA

El ESP32-S3 DevKit está en el centro del diagrama, como un bloque rectangular grande con sus pines GPIO numerados en ambos lados. Todos los periféricos se conectan radialmente al MCU, agrupados por tipo de bus.

---

### BLOQUE CENTRAL — ESP32-S3 DevKit (WROOM-1-N4)

Rectángulo grande central, color gris claro, con borde negro grueso.

**Título:** "ESP32-S3 DevKit — WROOM-1-N4"

**Specs dentro del bloque:**
- "Dual-core Xtensa LX7, 240 MHz"
- "8 MB PSRAM, 4 MB Flash"
- "Firmware: MicroPython"
- "Deep sleep: 8 µA"
- "USB-C (debug/programación)"

**Pines GPIO listados en ambos lados** del rectángulo, con líneas de conexión saliendo hacia cada periférico. Los pines usados están resaltados; los libres en gris tenue.

---

### BUS I2C (líneas amarillas, lado izquierdo del MCU)

Título de grupo: **"Bus I2C — SDA/SCL"**

Una línea amarilla horizontal (bus compartido) con ramificaciones verticales hacia cada módulo I2C:

| Módulo | Dirección | Función |
|--------|-----------|---------|
| **MLX90640** (Adafruit 4407, placa roja) | 0x33 | Cámara térmica 32×24 px, NETD 100 mK |
| **SHT31** interno | 0x44 | T_air ±0,3°C, RH ±2% (backup) |
| **SHT31** externo (en shelter Gill) | 0x44 (bus secundario) | T_air ±0,3°C, RH ±2% (principal) |
| **VEML7700** | 0x10 | Piranómetro digital 16-bit (W/m²) |
| **DS3231** RTC | 0x68 | Reloj ±2 ppm, batería CR2032 |

**Anotación:** "Cables Stemma QT / Qwiic (JST-SH 4 pines, funda amarilla). Plug & play, sin soldadura."

---

### BUS SPI (líneas verdes, lado derecho del MCU)

Título de grupo: **"Bus SPI — MOSI=34, MISO=33, SCLK=32"**

Una línea verde horizontal (bus compartido MOSI/MISO/SCLK) con líneas CS individuales hacia cada módulo:

| Módulo | CS (GPIO) | Otros pines | Función |
|--------|-----------|-------------|---------|
| **LoRa E32-900T20D** (SX1276) | — | — | 915 MHz, SF7, 17 dBm, 1-3 km |
| **ICM-42688-P** IMU | GPIO 22 | INT1=GPIO 23 | 6 ejes, verifica estabilización gimbal |
| **MAX31855** termopar #1 | GPIO 25 | — | Termopar tipo T, resolución 0,25°C |
| **MAX31855** termopar #2 (v2) | GPIO 26 | — | Redundancia, degradación elegante |

---

### UART / RS485 (líneas celestes, parte superior del MCU)

Título de grupo: **"UART / RS485"**

| Módulo | Pines | Interfaz | Función |
|--------|-------|----------|---------|
| **MAX485** → Anemómetro RS485 | DE=GPIO 3 | Modbus RTU 9600 baud, reg 0x0000 | Velocidad viento 0-60 m/s, IP65 |
| **PMS5003** (Plantower) | RX=GPIO 12, TX=GPIO 13 | UART 9600 baud, protocolo 32 bytes | PM2.5 µg/m³ — detección fumigación |
| **GPS u-blox NEO-6M** | RX=GPIO 5 | UART (solo boot 0, timeout 2s) | Lat/lon → RTC memory, luego OFF |

**Anotación:** "PMS5003 y GPS comparten UART1 (multiplexado temporal: GPS solo en boot 0, PMS5003 desde boot 1 en adelante)."

---

### GPIO DIRECTOS (líneas rosas, parte inferior del MCU)

Título de grupo: **"GPIO — PWM, pulsos, control"**

| Módulo | GPIO | Tipo | Función |
|--------|------|------|---------|
| **Servo MG90S** PAN | GPIO 20 | PWM 50 Hz | Gimbal horizontal ±20° |
| **Servo MG90S** TILT | GPIO 21 | PWM 50 Hz | Gimbal vertical +15°/-10° |
| **Pluviómetro** tipping bucket | GPIO 2 | ISR (interrupción) | 0,2 mm/pulso, debounce 200 ms |
| **Piezo Murata** MZB1001T02 | GPIO 24 | Digital | Limpieza lente 500 ms/ciclo |
| **Bomba peristáltica** 6V Wet Ref | GPIO 35 | Digital | Pulso 3s/ciclo, humecta fieltro |
| **Relé SSR** 24VAC (Tier 3) | GPIO 41 | Digital | Solenoide Rain Bird — riego autónomo |

---

### BUS ANALÓGICO / BIT-BANG SPI (líneas naranjas, esquina inferior)

Título de grupo: **"ADC de precisión — Extensómetro"**

| Módulo | Pines | Función |
|--------|-------|---------|
| **ADS1231** ADC 24-bit | SCLK=GPIO 14, DOUT=GPIO 15, PDWN=GPIO 16 | Strain gauge 120Ω → resolución 1 µm |
| **DS18B20** (OneWire) | — (en cable extensómetro) | Corrección térmica tronco α=2,5 µm/°C |

---

### BLOQUE DE ENERGÍA (esquina superior izquierda, fondo amarillo claro)

Título: **"Sistema de energía"**

Diagrama de flujo lineal:

```
Panel solar 6W (6V) → MPPT DFR0559 → LiFePO4 3,2V 6Ah (19,2 Wh)
                                    ↓
                              Regulador 3,3V → ESP32-S3 + todos los sensores
```

**Anotaciones:**
- "Balance: genera 24-36 Wh/día vs. consume 4,3 Wh/día"
- "Autonomía sin sol: ~120 horas (~5 días)"
- "Deep sleep 8 µA × 14,5 min + activo 180 mA × 30s = ~14 µA promedio equivalente"

---

### BLOQUE DE COMUNICACIÓN (esquina superior derecha, fondo azul claro)

Título: **"Salida de datos"**

```
ESP32-S3 → LoRa E32-900T20D (SPI) → Antena SMA 915 MHz
                                          ↓ (aire, 1-3 km)
                                    Gateway RAK7268
                                          ↓ (Ethernet/4G)
                                    Backend FastAPI
```

**Anotación:** "Payload JSON ~200 bytes cada 15 min. Sin Wi-Fi ni internet en campo."

---

### ANOTACIONES GENERALES

**Esquina superior izquierda — recuadro de identificación:**
```
HydroVision AG — Diagrama de Bloques Electrónico
Nodo IoT LWIR v1 — Arquitectura modular TRL 4
ESP32-S3 DevKit + breakouts I2C/SPI — sin PCB custom
```

**Esquina inferior izquierda — resumen de buses:**
- I2C: 5 dispositivos (MLX90640, 2× SHT31, VEML7700, DS3231)
- SPI: 4 dispositivos (LoRa, IMU, 2× MAX31855)
- UART: 3 dispositivos (MAX485→anemómetro, PMS5003, GPS)
- GPIO directo: 6 señales (2× servo, pluviómetro, piezo, bomba, relé)
- ADC bit-bang: 1 dispositivo (ADS1231)
- **Total: 19 señales en 16 módulos**

**Esquina inferior derecha — nota TRL:**
"Arquitectura TRL 4: DevKit + breakouts modulares. Cada módulo reemplazable en 5 min sin soldadura. Para TRL 5+ (vol. 500+): migrar a PCB custom 4-layer, COGS −$25-30/nodo."

---

### LO QUE NO DEBE INCLUIR

* No incluir esquemáticos eléctricos detallados (resistencias, capacitores)
* No incluir layout de PCB ni footprints
* No usar colores neón ni fondos oscuros
* No incluir fotos reales de componentes — solo bloques esquemáticos con nombres
* No simplificar omitiendo módulos — mostrar los 16 completos
* No incluir precios
