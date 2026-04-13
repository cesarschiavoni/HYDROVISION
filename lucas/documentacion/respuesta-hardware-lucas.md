# Respuesta tecnica a consultas de Lucas — Hardware nodo HydroVision AG
## Abril 2026 — Discusion de arquitectura para TRL 4

> **Contexto:** Lucas planteo 3 preguntas sobre el diseño fisico del nodo.
> Este documento responde cada una con analisis tecnico y propuesta concreta.

---

## Pregunta 1 — Tamaño, forma y montaje real del nodo

> *"Que tamaño tiene el dispositivo? Hacer algo compacto puede resultar poco robusto.
> Me imagino algo un poco mas grande. Tambien tengo dudas con lo del panel solar.
> Podes pasarme un modelo de como seria el sistema integrado a un arbol?"*

### Respuesta

El nodo NO es un dispositivo compacto tipo wearable. Es un **instrumento de campo** montado
en una estaca de acero inoxidable junto al tronco de la planta. El tamaño final depende de
la carcasa — y estamos de acuerdo en que debe ser **robusta, no miniaturizada**.

### Dimensiones recomendadas

| Componente | Dimensiones | Peso estimado |
|---|---|---|
| Carcasa IP67 (electronica + bateria) | **200 × 150 × 100 mm** | ~800g con electronica |
| Panel solar 6W | 200 × 170 mm | ~300g |
| Tubo colimador IR | Ø110 × 250 mm | ~200g |
| Shelter SHT31 | Ø120 × 100 mm | ~150g |
| Anemometro | Ø60 × 150 mm | ~200g |
| **Total nodo montado** | — | **~1.6 kg** |

La carcasa de 200×150×100mm es un modelo estandar de Hammond o Gewiss IP67, disponible
en MercadoLibre. Es lo suficientemente grande para que quepan todos los modulos holgados,
con espacio para el cableado, la bateria y ventilacion pasiva.

### Vista lateral — nodo montado en estaca junto a vid Malbec

```
                      ANEMOMETRO RS485 (copa, Ø60mm)
                      Marca "N" al norte
                      |
                      |  2.4 m
     =================|=================  ← punta estaca (acero inox 3m, 60cm enterrada)
                      |
            ┌─────────┴─────────┐
            │   PANEL SOLAR 6W  │  ← 200×170mm, orientado al NORTE
            │   ┌───────────┐   │
            │   │           │   │     2.0-2.2 m
            │   │  CARCASA  │   │  ← 200×150×100mm IP67
            │   │  Hammond  │   │     Adentro: ESP32-S3 DevKit
            │   │  IP67     │   │              MLX90640 breakout (I2C)
            │   │           │   │              SHT31 breakout (I2C)
            │   │  Ventana  │───┤              MAX31855 (termopar)
            │   │  HDPE     │   │              ADS1231 (extensometro)
            │   │  (camara) │   │              LoRa SX1276
            │   └───────────┘   │              LiFePO4 6Ah
            │   ┌───────────┐   │              MPPT cargador
            │   │   TUBO    │   │
            │   │ COLIMADOR │   │  ← PVC Ø110×250mm, negro mate interior
            │   │    IR     │   │     Concentrico con ventana MLX90640
            │   └───────────┘   │     Apunta abajo/este (al canopeo)
            └───────────────────┘
                      │
            SHELTER SHT31           ← 1.8-2.0 m (lado norte del poste)
            (6 placas blancas)         Ø120×100mm
                      │
            PLUVIOMETRO             ← 1.8-2.0 m (horizontal, nivelado)
                      │
            PANELES DRY/WET REF    ← 1.5-1.8 m (apuntando al cielo)
                      │
     =================|=================  ← nivel canopeo (~1.5 m)
                      │
            TERMOPAR FOLIAR         ← clip en enves de hoja (lado este)
            (cable 2m → carcasa)       Misma orientacion que camara
                      │
                      │  ← ESTACA acero inox
                      │     en línea de hilera, ~50cm del tronco
                      │
            EXTENSOMETRO MDS        ← 30 cm sobre suelo
            (abrazadera en tronco)     Cara norte, cable 3m → carcasa
                      │
     =================|=================  ← nivel suelo
            60 cm estaca enterrada
```

### Vista frontal — comparacion con planta de vid Malbec

```
     Anemometro
         |
    ┌────┴────┐
    │  Panel  │
    │  Solar  │        ···  hojas  ···
    │ ┌─────┐ │      ···              ···
    │ │Nodo │ │    ···    CANOPEO VID    ···
    │ │     │ │   ···    (1.2-1.8m)       ···
    │ └─────┘ │    ···                  ···
    │  Tubo   │      ···              ···
    │ colim.  │        ···  ···  ···
    ├─────────┤              |
    │ Shelter │         TRONCO VID
    │ Pluv.   │              |
    ├─────────┤        [Extensometro]
    │ Dry/Wet │              |
    │  Ref    │              |
    └────┬────┘              |
         │                   |
    ═════╧═══════════════════╧═════  suelo

     ← ~50cm →
     estaca      tronco
     (en línea de hilera, entre plantas)
```

### Respuesta a la duda del panel solar

El panel de 6W (200×170mm) se monta **solidario a la carcasa**, orientado al norte.
No es un panel grande — es del tamaño de un libro de bolsillo. El balance energetico:

| | Generacion | Consumo | Balance |
|---|---|---|---|
| Verano Cuyo (6h sol) | 36 Wh/dia | 4.3 Wh/dia | **+31 Wh excedente** |
| Invierno Cuyo (4h sol) | 24 Wh/dia | 4.3 Wh/dia | **+19 Wh excedente** |
| 3 dias nublados | 0 Wh | 12.9 Wh | Bateria 6Ah = 19.2 Wh → **aguanta** |

El panel solar es viable. No es una duda — son numeros.

---

## Pregunta 2 — Raspberry Pi 4/5 vs. ESP32-S3

> *"Te propongo que usemos la Raspberry Pi 4 o 5 y modulos apilables.
> En cuanto a los sensores, trabajar en I2C o Modbus RTU."*

### Respuesta

La propuesta tiene dos partes. Una es excelente y la otra tiene un problema serio.

### Parte excelente: modulos I2C / Modbus RTU apilables

**100% de acuerdo.** Todos los sensores del nodo ya usan I2C o Modbus RTU:

| Sensor | Protocolo | Modulo off-the-shelf |
|---|---|---|
| MLX90640 (camara IR) | I2C (0x33) | Breakout Adafruit/Pimoroni con lente |
| SHT31 (temp/humedad) | I2C (0x44) | Breakout Adafruit/Sensirion |
| GPS NEO-6M | UART (I2C disponible) | Modulo breakout estandar |
| Anemometro RS485 | Modbus RTU (9600 baud) | Sensor con protocolo integrado |
| DS3231 RTC | I2C (0x68) | Modulo breakout estandar |
| VEML7700 (piranometro) | I2C (0x10) | Breakout Adafruit |
| MAX31855 (termopar) | SPI | Breakout Adafruit |
| ADS1231 (extensometro) | SPI bit-bang | Breakout disponible |

Esto elimina el diseño de PCB custom para TRL4. Todos los modulos se conectan con cables
Stemma/Qwiic (I2C) o par trenzado (RS485). Se montan dentro de la carcasa con tornillos
o velcro industrial. Si un modulo falla, se reemplaza en 5 minutos.

### Parte problematica: RPi 4/5 como plataforma final

El problema es el consumo de energia. Los numeros son objetivos:

| Plataforma | Consumo activo | Consumo sleep | Consumo promedio/dia |
|---|---|---|---|
| **ESP32-S3** | 180 mA × 15s | 8 µA × 14m45s | **~0.3 Ah/dia** |
| **RPi Zero 2W** | 300 mA × 40s (con boot) | 0 mA (apagado por HW) | **~0.35 Ah/dia** |
| **RPi 4B** | 700 mA continuo | 100 mA standby | **~2.6 Ah/dia** |
| **RPi 5** | 800 mA continuo | 120 mA standby | **~3.1 Ah/dia** |

El RPi4/5 no tiene deep sleep real. Nunca baja de 100 mA en standby. Eso significa:

- **Panel solar necesario:** 25-30W (600×350mm) en vez de 6W (200×170mm)
- **Bateria necesaria:** 40-50 Ah (6 kg) en vez de 6 Ah (200g)
- **Autonomia sin sol:** <2 dias en vez de >4 dias
- **COGS:** +USD 60-80 solo en energia (panel mas grande + bateria mas grande)
- **Calor:** RPi4 llega a 80°C bajo carga. En carcasa IP67 cerrada con 45°C de ambiente
  en Cuyo, la electronica se cocina. Requiere ventilacion activa (rompe IP67) o disipador
  masivo.
- **Confiabilidad:** Linux sobre SD card se corrompe con cortes de energia. Un nodo que
  no arranca en un vinedo de San Juan a 200 km no se puede debugear por telefono.

### Propuesta: ESP32-S3 DevKit + MicroPython

La solucion que resuelve lo que Lucas quiere (desarrollo rapido, modular, sin PCB custom)
sin romper el presupuesto energetico:

**ESP32-S3 DevKit** (USD 10) programado en **MicroPython** (Python, no C).

| Lo que Lucas quiere | RPi4/5 | ESP32-S3 + MicroPython |
|---|---|---|
| Programar en Python | Si | **Si** (MicroPython) |
| Modulos I2C apilables | Si | **Si** (mismos breakouts) |
| Sin PCB custom | Si | **Si** (DevKit off-the-shelf) |
| Desarrollo rapido | Si | **Si** (REPL interactivo) |
| Deep sleep 8 µA | No (imposible) | **Si** |
| Panel solar 6W | No (necesita 25W) | **Si** |
| Bateria 6 Ah | No (necesita 40 Ah) | **Si** |
| COGS ~USD 148 | No (~USD 220+) | **Si** |
| Sin riesgo de corrupcion SD | No | **Si** |

Ejemplo de codigo MicroPython para el ciclo completo del nodo:

```python
# nodo_main.py — ciclo completo en MicroPython
from machine import I2C, Pin, deepsleep
import json

# Inicializar buses
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# 1. Leer sensores (todos I2C o SPI)
frame    = mlx90640_read(i2c)           # 768 pixels termicos
t_air    = sht31_read_temp(i2c)         # temperatura aire
rh       = sht31_read_rh(i2c)          # humedad relativa
wind_ms  = modbus_read_wind()           # anemometro RS485
mds_um   = ads1231_read()               # strain gauge tronco
tc_leaf  = max31855_read()              # termopar foliar

# 2. Calcular indices
tc_mean  = median_foliar_pixels(frame)
tc_corr  = tc_mean + TC_BLEND_K * (tc_leaf - tc_mean)  # correccion termopar
cwsi     = (tc_corr - tc_wet) / (tc_dry - tc_wet)
hsi      = calculate_hsi(cwsi, mds_um, wind_ms)

# 3. Armar y transmitir payload
payload = {
    "v": 1, "node_id": NODE_ID, "ts": rtc_epoch(),
    "env": {"t_air": t_air, "rh": rh, "wind_ms": wind_ms},
    "thermal": {"tc_mean": tc_corr, "cwsi": cwsi},
    "dendro": {"mds_mm": mds_um / 1000},
    "hsi": {"value": hsi}
}
lora_send(json.dumps(payload))

# 4. Deep sleep 15 minutos
deepsleep(15 * 60 * 1000)   # 8 µA durante 15 min
```

Lucas puede tener esto funcionando en **1-2 semanas** con modulos off-the-shelf.
La curva de aprendizaje de MicroPython para alguien que sabe Python es de **1 dia**.

### Alternativa: si Lucas insiste en Linux

Existe una opcion intermedia: **RPi Zero 2W con corte de energia por hardware**.

```
┌───────────────────────────────────────────────┐
│  ESP32-C3 (USD 3)           RPi Zero 2W       │
│  "watchdog de energia"      (USD 15)           │
│                                                │
│  Siempre encendido          APAGADO 99%        │
│  Timer 15 min               del tiempo         │
│  Consume 8 µA                                  │
│           │                                    │
│           ├── cada 15 min ──► MOSFET enciende  │
│           │                   RPi Zero 2W      │
│           │                   Boot: 20s        │
│           │                   Leer: 10s        │
│           │                   Calcular: 5s     │
│           │                   Transmitir: 5s   │
│           │                   Total: 40s       │
│           │                                    │
│           ◄── "termine" ───── RPi avisa        │
│           │                   MOSFET apaga     │
│           │                   Consumo: 0 mA    │
│                                                │
│  Consumo promedio: ~13 mA (comparable a ESP32) │
│  Panel solar: 10W (alcanza)                    │
│  Bateria: 12 Ah (alcanza)                      │
│  COGS: +USD 15-20 vs ESP32 solo                │
└───────────────────────────────────────────────┘
```

**Ventaja:** Linux completo, Python nativo, SSH para debug remoto.
**Desventaja:** Mas complejo (2 chips), boot de 20s cada ciclo desperdicia energia,
riesgo de corrupcion SD (mitigable con filesystem read-only + overlayfs).

### Recomendacion

**ESP32-S3 + MicroPython** es la opcion mas simple, barata, confiable y
energeticamente viable. Da todo lo que Lucas pide sin los problemas del RPi.

Si despues de probar el prototipo Lucas necesita mas potencia de computo local,
la solucion es poner un **RPi4 en el galpon** como gateway inteligente (con
corriente de red), no en el nodo de campo:

```
CAMPO (solar, autonomo)              GALPON (red electrica)
┌──────────────────────┐             ┌──────────────────────┐
│ Nodo 1  ESP32-S3     │─── LoRa ──►│                      │
│ Nodo 2  ESP32-S3     │─── LoRa ──►│  RPi4 + LoRa HAT     │
│ Nodo 3  ESP32-S3     │─── LoRa ──►│  (reemplaza RAK7268) │
│ Nodo 4  ESP32-S3     │─── LoRa ──►│                      │
│ Nodo 5  ESP32-S3     │─── LoRa ──►│  - Edge AI (PINN)    │
│                      │             │  - Dashboard local   │
│ MicroPython          │             │  - OTA manager       │
│ I2C / Modbus RTU     │             │  - Data logger       │
│ Panel 6W + bat 6Ah   │             │  - 4G / Starlink     │
│ Deep sleep 8 µA      │             │  - Python completo   │
└──────────────────────┘             └──────────────────────┘
```

---

## Pregunta 3 — Camara IR integrada con lente

> *"Viene la camara infrarroja ya integrada con el lente y todo.
> Me parece la mejor opcion. No usar la camara suelta."*

### Respuesta

**Totalmente de acuerdo.** Es la decision correcta.

### Opciones de modulo MLX90640 integrado

| Modulo | Resolucion | FOV | Precio | Interfaz | Donde comprar |
|---|---|---|---|---|---|
| **Adafruit MLX90640 breakout** | 32×24 px | 110°×75° | USD 50 | I2C (Stemma QT) | adafruit.com / MercadoLibre |
| **Pimoroni MLX90640 breakout** | 32×24 px | 110°×75° | USD 55 | I2C | pimoroni.com |
| **SparkFun MLX90640 breakout** | 32×24 px | 110°×75° | USD 55 | I2C (Qwiic) | sparkfun.com / MercadoLibre |
| **Waveshare MLX90640 module** | 32×24 px | 110°×75° | USD 45 | I2C + USB | waveshare.com / AliExpress |

**Recomendacion: Adafruit o SparkFun.**

Razones:
- Lente 110°×75° FOV ya montado y enfocado
- Conector I2C estandar (Stemma QT / Qwiic) — se conecta al ESP32 con un cable
- Level shifter integrado (3.3V safe)
- Montaje con 4 tornillos M2.5 (agujeros estandar)
- Librerias MicroPython disponibles y probadas
- Documentacion completa con ejemplos

### Que cambia respecto al BOM actual

| BOM actual | BOM propuesto |
|---|---|
| MLX90640ESF-BAB bare chip (USD 30-38) | MLX90640 breakout Adafruit (USD 50) |
| Lente separado (incluido en PCB custom) | Lente integrado en breakout |
| Requiere footprint TO39 en PCB custom | No requiere PCB — I2C plug & play |
| Riesgo: soldar chip TO39 en campo | Sin riesgo — modulo sellado |

**COGS:** sube ~USD 15-20 por nodo (breakout vs bare chip), pero elimina la complejidad
del diseño optico en la PCB y reduce el riesgo de falla en campo.

### Verificar antes de comprar

1. **FOV 110°** (suffix BAB). La version de 55° (suffix BAD/CAD) cubre muy pocas plantas.
2. **Disponibilidad en Argentina.** Buscar en MercadoLibre "MLX90640" — hay vendedores
   importadores. Si no hay stock, importar directo por Correo Internacional (Adafruit
   envia a Argentina, ~USD 15 de envio, 15-25 dias).
3. **Comprar 7 unidades** (5 nodos + 2 spare). A USD 50 c/u = USD 350 total.

### Como se monta el breakout con el tubo colimador

```
          ┌──────────────────────────┐
          │      CARCASA IP67        │
          │                          │
          │   ┌──────────────────┐   │
          │   │ MLX90640 breakout│   │
          │   │ (tornillos M2.5) │   │
          │   │                  │   │
          │   │   [lente 110°]   │   │
          │   └────────┬─────────┘   │
          │            │             │
          └────────────┼─────────────┘
                       │ ventana HDPE
                ┌──────┴──────┐
                │             │
                │   TUBO      │
                │   COLIMADOR │  ← PVC Ø110×250mm
                │   IR        │     Negro mate interior
                │             │     Concentrico con lente
                │             │
                └─────────────┘
                       │
                       ▼ apunta al canopeo (abajo/este)
```

El breakout se atornilla adentro de la carcasa, alineado con la ventana HDPE.
El tubo colimador se monta afuera, concentrico con la ventana. El lente del breakout
mira a traves de la ventana y el tubo.

---

## Resumen de la propuesta integrada

| Aspecto | Diseño anterior | Propuesta revisada |
|---|---|---|
| **MCU** | ESP32-S3 bare chip en PCB custom | **ESP32-S3 DevKit** off-the-shelf |
| **Firmware** | C / Arduino | **MicroPython** (Python) |
| **Camara IR** | MLX90640 bare chip TO39 | **MLX90640 breakout** (Adafruit/SparkFun) |
| **Conexiones** | PCB custom traces | **I2C cables Stemma/Qwiic** + Modbus RTU |
| **Carcasa** | ABS IP65 150×100×70mm | **Hammond IP67 200×150×100mm** |
| **Panel solar** | 6W (sin cambio) | 6W (sin cambio) |
| **Bateria** | LiFePO4 6Ah (sin cambio) | LiFePO4 6Ah (sin cambio) |
| **PCB custom** | Necesaria (8 semanas diseño) | **Eliminada para TRL4** |
| **COGS estimado** | USD 148 | **USD 155-165** (+5-11%) |
| **Tiempo a prototipo** | 8-12 semanas (PCB + firmware) | **2-3 semanas** |

### Proximos pasos concretos

1. **Lucas compra** los breakouts: MLX90640 + SHT31 + GPS + ESP32-S3 DevKit (total ~USD 80/nodo)
2. **Cesar** prepara el firmware MicroPython base (ciclo de lectura + CWSI + LoRa)
3. **Lucas arma** el primer prototipo en mesa con cables I2C — verifica que todo lee
4. **Lucas monta** en carcasa Hammond IP67 con cableado definitivo
5. **Instalacion** en vinedo fila 2 (control) — primer nodo operativo
