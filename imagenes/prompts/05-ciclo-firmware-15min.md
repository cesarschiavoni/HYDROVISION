## PROMPT PARA GENERACIÓN DE IMAGEN — Ciclo de 15 Minutos del Firmware del Nodo

---

### ESTILO VISUAL

Diagrama de línea de tiempo horizontal (timeline), estilo diagrama de secuencia UML simplificado o diagrama de actividad de microcontrolador. Fondo blanco. La línea de tiempo corre de izquierda a derecha. Bloques de colores sobre la línea representan cada fase del ciclo. Texto negro sans-serif. Escala temporal proporcional (el deep sleep domina el 97% del ciclo). Debajo de la línea, íconos pequeños de cada sensor que se activa en cada fase. Calidad de documentación técnica de firmware.

---

### ESTRUCTURA DEL DIAGRAMA

**Eje horizontal:** tiempo total = 15 minutos (900 segundos)

La línea de tiempo está dividida en dos zonas contrastantes:
- **Zona activa** (izquierda, ~25-30 segundos): bloques de colores apilados, con detalle de cada paso
- **Zona deep sleep** (derecha, ~870 segundos): un bloque largo gris tenue con ícono de "Zzz"

**Escala temporal:** la zona activa está expandida (zoom) para mostrar el detalle de los ~30 segundos. Una marca de corte ("//") separa la zona activa de la zona de sleep, indicando que la escala no es uniforme.

---

### FASES DEL CICLO ACTIVO (expandido, ~30 segundos totales)

Cada fase es un bloque rectangular de color sobre la línea de tiempo, con duración proporcional. Debajo de cada bloque, el ícono del sensor o módulo involucrado.

**Fase 0 — Wake-up (0,5s)**
- Color: gris oscuro
- Etiqueta: "Wake ESP32-S3"
- Detalle: "RTC alarm → wake from deep sleep (8 µA → 180 mA). Inicializar I2C, SPI, UART."
- Ícono: chip ESP32

**Fase 1 — PMS5003 warmup (3s)**
- Color: marrón
- Etiqueta: "PMS5003 Warmup"
- Detalle: "Encender láser + ventilador (3 seg). Leer PM2.5 µg/m³."
- Ícono: sensor de partículas
- **Decisión (rombo):** "PM2.5 > 200?" → Sí: "FLAG: fumigación — invalidar captura térmica 4h" → Continuar igualmente (MDS sigue operando)

**Fase 2 — Lectura meteo (1s)**
- Color: celeste
- Etiqueta: "Sensores ambientales"
- Detalle: "SHT31 (T_air, RH) · VEML7700 (radiación W/m²) · Anemómetro RS485 Modbus (viento m/s) · Pluviómetro (acumulado mm)"
- Íconos: termómetro, sol, viento, gota de lluvia
- **Decisión:** "Radiación < 150 W/m²?" → Sí: "Modo ahorro — CWSI no informativo, solo MDS"

**Fase 3 — Limpieza lente (0,5s)**
- Color: amarillo
- Etiqueta: "Piezo limpieza"
- Detalle: "Murata MZB1001T02 vibra ventana HDPE 500 ms. Desprender polvo/rocío."
- Ícono: disco piezoeléctrico vibrando

**Fase 4 — Bomba Wet Ref (3s)**
- Color: azul agua
- Etiqueta: "Bomba peristáltica"
- Detalle: "Pulso 3 seg — humectar fieltro panel Wet Ref desde reservorio 10L."
- Ícono: bomba con manguera

**Fase 5 — Escaneo gimbal + captura térmica (8-10s)**
- Color: rojo (el bloque más largo de la fase activa)
- Etiqueta: "Gimbal scan — MLX90640"
- Detalle expandido en sub-bloques:

| Posición | Pan | Tilt | Acción | Tiempo |
|----------|-----|------|--------|--------|
| P0 | 0° | 0° | Centro — referencia | ~1,3s |
| P1 | -20° | 0° | Izquierda — sombra | ~1,3s |
| P2 | +20° | 0° | Derecha — exposición | ~1,3s |
| P3 | 0° | +15° | Arriba — cobertura foliar | ~1,3s |
| P4 | 0° | -10° | Abajo — dosel inferior | ~1,3s |
| P5 | -20° | +15° | Diagonal IzqArriba — cobertura cruzada | ~1,3s |
| P6* | 0° | -30° | Nadir — solo si viento >20 km/h | ~1,3s |

- "Cada posición: mover servo (300 ms estabilización verificada por IMU) → captura frame 32×24 → clasificar píxeles foliares"
- Ícono: cámara térmica con flechas de movimiento

**Fase 6 — Lectura dendrómetro (0,5s)**
- Color: verde oscuro
- Etiqueta: "ADS1231 → MDS"
- Detalle: "Leer strain gauge (resolución 1 µm). Leer DS18B20 (corrección térmica α=2,5 µm/°C). Calcular MDS = D_max − D_min."
- Ícono: tronco con abrazadera

**Fase 7 — Lectura termopar (0,3s)**
- Color: naranja
- Etiqueta: "MAX31855 → T_foliar"
- Detalle: "Leer termopar tipo T contacto hoja. Corrección: T_corr = T_IR + 0,6 × (T_tc − T_IR)"
- Ícono: hoja con sensor

**Fase 8 — Cálculo edge (1s)**
- Color: púrpura
- Etiqueta: "Edge computing"
- Detalle expandido:
  1. "Seleccionar 3 mejores frames (mayor fracción foliar)"
  2. "CWSI = (Tc − T_LL) / (T_UL − T_LL) — promedio ponderado"
  3. "MDS normalizado (0-1)"
  4. "HSI = w_cwsi × CWSI + w_mds × MDS (pesos adaptados por viento)"
  5. "Quality flags: viento, lluvia, fumigación, ISO_nodo"
- Ícono: engranaje / CPU

**Fase 9 — Transmisión LoRa (2s)**
- Color: azul intenso
- Etiqueta: "LoRa TX"
- Detalle: "Serializar payload JSON v1 (~200 bytes). Transmitir LoRa 915 MHz, SF7, 17 dBm → gateway RAK7268."
- Ícono: antena con ondas

**Fase 10 — Auto-calibración condicional (0,5s)**
- Color: dorado
- Etiqueta: "¿Auto-calibrar?"
- **Decisión (rombo):** "¿Lluvia ≥5 mm AND MDS ≈ 0?"
  - Sí: "Actualizar Tc_wet baseline (EMA, lr=0,25)"
  - No: "Skip"
- Ícono: llave/calibración

---

### ZONA DE DEEP SLEEP (lado derecho, ~870 segundos)

Un bloque largo y ancho de color gris muy claro, con bordes punteados.

**Contenido:**
- Ícono grande de "Zzz" o luna
- Texto: "Deep sleep — 8 µA"
- "~14 min 30 seg"
- "Solo RTC DS3231 activo (mantiene hora)"
- "Pluviómetro GPIO 2 activo (ISR wake-on-rain)"
- Flecha curvada de retorno que conecta el final del sleep con el inicio del siguiente ciclo: "RTC alarm → Wake"

---

### RESUMEN ENERGÉTICO (barra inferior)

Una barra horizontal debajo del timeline mostrando el consumo energético:

| Fase | Duración | Corriente | Energía |
|------|----------|-----------|---------|
| Activo | ~30 s | ~180 mA | ~1,5 mAs |
| Deep sleep | ~870 s | 8 µA | ~7 mAs |
| **Promedio por ciclo** | 900 s | **~14 µA equiv.** | **~8,5 mAs** |

"Con LiFePO4 6Ah: autonomía ~120 horas sin recarga solar"

---

### ANOTACIONES

**Esquina superior izquierda:**
```
HydroVision AG — Ciclo de Firmware v0.3
ESP32-S3 + MicroPython · 96 ciclos/día
Cada 15 min: ~30s activo + ~14,5 min deep sleep
```

**Esquina inferior derecha:**
"El ciclo completo se ejecuta en <30 segundos. El nodo duerme el 97% del tiempo. El pluviómetro puede despertar el nodo anticipadamente si detecta lluvia (ISR en GPIO 2)."

---

### LO QUE NO DEBE INCLUIR

* No incluir código fuente ni pseudocódigo extenso
* No hacer el deep sleep del mismo tamaño visual que la fase activa — usar corte de escala (//)
* No omitir el PMS5003 warmup — es la fase más larga después del sleep y es crítica
* No representar el ciclo como circular — es una línea de tiempo horizontal
* No usar más de 12 colores — mantener paleta contenida
