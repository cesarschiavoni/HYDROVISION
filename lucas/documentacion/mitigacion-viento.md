# Mitigacion de viento — Defensa en profundidad

## HydroVision AG — Arquitectura completa de mitigacion del efecto del viento sobre el CWSI

> **Problema:** El viento afecta la medicion de temperatura foliar de tres formas:
> (1) enfriamiento convectivo de la hoja (T_leaf baja artificialmente),
> (2) movimiento de la hoja dentro/fuera del FOV del sensor IR (ruido),
> (3) error en la medicion de T_air y HR del sensor ambiental (propaga error al VPD y al CWSI).
>
> El sistema implementa **9 capas base + 14 mejoras v2** desde lo fisico hasta ML.
> Las 9 capas base + mejoras v2 firmware (B1-B6, A1, A3, C4) permiten CWSI confiable
> hasta **18 m/s (65 km/h)** en el nodo edge.
> Las mejoras v2 backend/ML (C1, C2, C6) extienden el rango util a **21-22 m/s (76-79 km/h)**, cubriendo
> incluso Zonda severo. Mejora aditiva estimada: ~60-70% sobre las capas base
> (no 100% porque algunas mejoras atacan la misma fuente de error).
>
> Todas las capas se incluyen en todos los nodos independientemente del tier o mercado
> (un solo SKU). El costo incremental es USD 15-25 sobre COGS base (con mejoras v2).

---

## Diagrama de capas

```
Viento incide sobre el nodo
  |
  v
CAPA 0 -- Orientacion a sotavento -------- elimina 60-70% conveccion en hoja
  |
  v
CAPA 1 -- Tubo colimador IR -------------- bloquea viento lateral en el FOV
  |
  v
CAPA 2 -- Shelter anti-viento SHT31 ------ elimina error en T_air/HR/VPD
  |
  v
CAPA 3 -- Termopar foliar (ground truth) - corrige T_leaf IR por contacto
  |
  v
CAPA 4 -- Compensacion Tc_dry por viento - ajusta baseline superior del CWSI
  |
  v
CAPA 5 -- Buffer termico + filtro calma -- selecciona lecturas en micro-calma
  |
  v
CAPA 6 -- Fusion HSI (65% MDS + 35% CWSI)  MDS ya domina por diseno
  |
  v  4-18 m/s (14-65 km/h): rampa gradual
CAPA 7 -- Transicion gradual CWSI -> MDS - peso CWSI se reduce linealmente
  |        <= 4 m/s (14 km/h):  w_cwsi=0.35 (normal)
  |        8 m/s (29 km/h):     w_cwsi=0.25
  |        12 m/s (43 km/h):    w_cwsi=0.15
  |        15 m/s (54 km/h):    w_cwsi=0.08
  |        >= 18 m/s (65 km/h): w_cwsi=0.00 (backup total MDS)
  |
  v  si CWSI = -1 (no calibrado)
CAPA 8 -- Fallback CWSI invalido -> MDS -- red de seguridad final
```

---

## Detalle de cada capa

### CAPA 0 — Orientacion a sotavento (fisica, instalacion)

| | |
|---|---|
| **Que ataca** | Enfriamiento convectivo directo del viento sobre las hojas medidas por la camara MLX90640 |
| **Como funciona** | La camara se orienta hacia el lado **este** de la hilera (sotavento del Zonda). Las propias plantas de vid actuan como barrera natural, reduciendo la velocidad del viento en la zona de medicion. En zonas con viento dominante distinto al Zonda, se orienta al lado opuesto a la direccion predominante. |
| **Cuando opera** | Siempre (es una decision de instalacion fisica) |
| **Reduccion estimada** | ~60-70% de la velocidad del viento en las hojas medidas |
| **Costo** | USD 0 — solo una instruccion en el protocolo de instalacion |
| **Archivo** | `lucas/documentacion/guia-instalacion-nodo-v1.md` — Seccion 3, paso 3 |

---

### CAPA 1 — Tubo colimador IR (fisica, hardware)

| | |
|---|---|
| **Que ataca** | Movimiento de hojas dentro/fuera del FOV del sensor IR por viento lateral, y conveccion forzada en la zona de medicion inmediata. |
| **Como funciona** | Tubo cilindrico de PVC (110mm diametro x 250mm largo) pintado negro mate interior, montado concentrico con el lente MLX90640. Bloquea el flujo lateral de viento sin alterar las condiciones naturales de las hojas. La camara ve a traves del tubo pero el viento transversal no entra al FOV. Principio similar a los radiometros de campo profesionales (Apogee SI-111). |
| **Cuando opera** | Siempre (es hardware pasivo) |
| **Reduccion estimada** | Error por movimiento de hoja: de +-0.04 a +-0.01 CWSI |
| **Costo** | USD 2-4 (tubo PVC sanitario + pintura negro mate) |
| **Archivos** | `lucas/hardware/BOM-nodo-v1.md` — fila 13f. `lucas/documentacion/guia-instalacion-nodo-v1.md` — Seccion 3, paso 4 |

---

### CAPA 2 — Shelter anti-viento para sensor SHT31 (fisica, hardware)

| | |
|---|---|
| **Que ataca** | Error en la medicion de T_air y HR causado por flujo de viento directo sobre el sensor SHT31. Un error de +-0.5C en T_air propaga +-0.05 a +-0.10 de error al CWSI via el calculo de VPD. |
| **Como funciona** | Shelter tipo Gill de 6 placas horizontales blancas (PETG o platos plasticos) apiladas con separacion de 15mm. Crea un ambiente de conveccion natural donde el aire se renueva lentamente pero sin flujo forzado. Basado en el estandar WMO Guide No. 8 (2018) para estaciones meteorologicas. |
| **Cuando opera** | Siempre (es hardware pasivo) |
| **Reduccion estimada** | Elimina error de +-0.5C en T_air -> elimina +-0.05 a +-0.10 de error en CWSI |
| **Costo** | USD 0.50-2 (impresion 3D o platos de ferreteria) |
| **Archivos** | `lucas/hardware/BOM-nodo-v1.md` — fila 7c. `lucas/documentacion/guia-instalacion-nodo-v1.md` — Seccion 5.1b |

---

### CAPA 3 — Termopar foliar de contacto (fisica + firmware)

| | |
|---|---|
| **Que ataca** | Enfriamiento convectivo de la hoja que afecta la lectura IR pero NO el termopar. Es la fuente de error mas grande (+-0.06-0.10 CWSI) y la mas dificil de corregir por software solo. |
| **Como funciona** | Un termopar tipo T (cobre-constantan, 0.1mm de diametro) pegado al enves de una hoja representativa mide T_leaf por contacto directo, inmune al viento. El firmware aplica una correccion en tiempo real: `T_leaf_corr = T_leaf_IR + k * (T_termopar - T_leaf_IR)` donde k=0.6 (calibrable por varietal con Scholander). La correccion se aplica DESPUES del filtrado del buffer (Capa 5), combinando lo mejor de ambas fuentes: la cobertura espacial del IR (28+ pixeles foliares) con la precision puntual del termopar. |
| **Cuando opera** | Siempre que el termopar da lectura valida (5-60C). Si falla, el sistema usa solo IR (degradacion elegante). |
| **Reduccion estimada** | Error por conveccion: de +-0.08 a +-0.02 CWSI |
| **Costo** | USD 4-8 (termopar tipo T 0.1mm + MAX31855 amplificador SPI + clip) |
| **Archivos** | `lucas/hardware/BOM-nodo-v1.md` — fila 13g. `lucas/firmware/config.h` — `PIN_TC_CS`, `TC_BLEND_K`. `lucas/firmware/nodo_main.ino` — bloque de correccion por termopar. `lucas/documentacion/guia-instalacion-nodo-v1.md` — Seccion 5.2 |

```c
// config.h
#define PIN_TC_CS          25       // GPIO chip select MAX31855
#define TC_BLEND_K         0.6f    // factor correccion (calibrar en campo — ver procedimiento abajo)

// nodo_main.ino — despues del buffer termico
if (ok_tc) {
    TermoparResult tc = termopar_read();
    if (tc.ok && tc.temp_c >= TC_MIN_VALID_C && tc.temp_c <= TC_MAX_VALID_C) {
        float tc_ir = d.tc_mean;
        d.tc_mean = tc_ir + TC_BLEND_K * (tc.temp_c - tc_ir);
    }
}
```

#### Procedimiento de calibracion de TC_BLEND_K

El factor `TC_BLEND_K = 0.6` es el valor por defecto que funciona bien para Malbec en Cuyo. Para optimizarlo por varietal o region:

**Materiales:** Bomba Scholander + camara de presion, termopar instalado, nodo operativo.

**Procedimiento (durante sesion Scholander programada):**

1. Seleccionar un dia con **viento moderado** (5-10 m/s / 18-36 km/h). En calma total no hay diferencia entre IR y termopar, asi que no se puede calibrar.
2. Medir psi_stem con Scholander en la planta del nodo (minimo 5 mediciones, 1 cada 30 min).
3. Para cada medicion, registrar del payload del nodo:
   - `T_leaf_IR` (temperatura media IR sin correccion — campo `tc_mean` pre-correccion)
   - `T_termopar` (lectura del termopar — campo `tc_temp`)
   - `wind_ms` (velocidad del viento)
4. Calcular CWSI con ambas fuentes por separado:
   - `CWSI_IR` = usando solo T_leaf_IR
   - `CWSI_tc` = usando solo T_termopar
   - `CWSI_blend(k)` = usando T_leaf_IR + k * (T_termopar - T_leaf_IR)
5. Hacer regresion de cada CWSI vs psi_stem Scholander
6. El **k optimo** es el que **maximiza R2** de CWSI_blend vs psi_stem

**Valores tipicos por varietal:**

| Varietal | Region | k optimo esperado | Notas |
|----------|--------|-------------------|-------|
| Malbec | Cuyo / Cordoba | 0.5-0.7 | Default 0.6 — canopeo denso, buena barrera sotavento |
| Cabernet Sauvignon | Mendoza | 0.5-0.6 | Canopeo menos denso que Malbec |
| Olivo (Arauco) | San Juan | 0.6-0.8 | Canopeo abierto — mas dependiente del termopar |
| Cerezo | Mendoza / Patagonia | 0.4-0.6 | Hojas grandes — IR cubre bien |
| Arandano | NOA | 0.7-0.9 | Canopeo compacto — termopar mas representativo |

**Cuando recalibrar:** solo si se cambia de varietal, se poda drasticamente (cambia la densidad del canopeo y la barrera sotavento), o se reubica el nodo. No es necesario recalibrar cada temporada si el canopeo es similar.

---

### CAPA 4 — Compensacion de Tc_dry por viento (firmware, algoritmica)

| | |
|---|---|
| **Que ataca** | El baseline superior del CWSI (Tc_dry = temperatura de hoja sin transpiracion). El viento reduce la diferencia entre T_air y Tc_dry porque enfria la hoja seca tambien. Si no se compensa, el denominador del CWSI se achica y el indice se infla artificialmente. |
| **Como funciona** | `calcular_tc_dry()` aplica un factor de reduccion proporcional al viento: `delta *= (1.0 - wind_ms / 20.0)`. A 0 m/s el delta es maximo (5-10C segun HR). A 4 m/s (14 km/h) se reduce 20%. A 10 m/s (36 km/h) se reduce 50%. Minimo clampeado a 0.5C. |
| **Cuando opera** | Siempre, de forma continua y proporcional a la velocidad del viento medida |
| **Archivo** | `lucas/firmware/nodo_main.ino` — funcion `calcular_tc_dry()` |

```c
float calcular_tc_dry(float t_air, float rh, float wind_ms) {
    float delta = 10.0f - (rh / 100.0f) * 5.0f;   // 5-10C segun HR
    delta *= (1.0f - wind_ms / 20.0f);             // viento reduce el delta
    if (delta < 0.5f) delta = 0.5f;
    return t_air + delta;
}
```

---

### CAPA 5 — Buffer termico con filtro por calma (firmware)

| | |
|---|---|
| **Que ataca** | Ruido instantaneo por movimiento de hoja dentro/fuera del FOV del sensor IR, y efecto de rafagas breves de viento sobre T_leaf. |
| **Como funciona** | En cada ciclo de captura (15 min), el nodo toma **5 lecturas termicas** espaciadas 2 segundos (total ~10s). Cada lectura se acompana de una medicion de viento instantanea. El algoritmo selecciona la **mediana de las lecturas en calma** (viento < 2 m/s / 7 km/h). Si ninguna lectura esta en calma, usa la mediana de todas las lecturas validas (robusto a outliers). |
| **Cuando opera** | En cada ciclo de captura valido (calidad_captura == "ok") |
| **Reduccion estimada** | Elimina outliers por movimiento de hoja. Aprovecha micro-ventanas de calma que existen incluso en dias ventosos. |
| **Costo** | ~10 segundos extra por ciclo de captura (sobre 15 min totales) |
| **Archivos** | `lucas/firmware/config.h` — constantes `THERMAL_BUFFER_SIZE`, `THERMAL_SAMPLE_DELAY_MS`, `WIND_CALM_MS`. `lucas/firmware/nodo_main.ino` — funciones `seleccionar_tc_mean()`, `mediana_float()`, struct `ThermalSample`, y loop de captura multi-muestra. |

```
Configuracion (config.h):
  THERMAL_BUFFER_SIZE     = 5       lecturas por ciclo
  THERMAL_SAMPLE_DELAY_MS = 2000    ms entre lecturas
  WIND_CALM_MS            = 2.0     m/s (7 km/h) umbral de calma

Algoritmo (nodo_main.ino):
  Para cada muestra i = 1..5:
    1. Leer viento instantaneo (anemometro RS485)
    2. Capturar frame termico (MLX90640 via gimbal o directo)
    3. Guardar {tc_mean, wind_ms, valid} en buffer

  Seleccion:
    Si hay lecturas con wind < 2.0 m/s (7 km/h) -> mediana de esas
    Si no                                       -> mediana de todas las validas
    Si ninguna valida                           -> tc_mean = 0 (CWSI sera -1)
```

---

### CAPA 6 — Fusion HSI con peso dominante MDS (firmware, siempre activa)

| | |
|---|---|
| **Que ataca** | La inestabilidad inherente del CWSI termico comparado con la estabilidad del MDS (dendrometria de tronco). El MDS mide la contraccion diaria del tronco, que es inmune al viento porque el tronco no se mueve ni se enfria por conveccion. |
| **Como funciona** | El HSI (HydroVision Stress Index) fusiona CWSI y MDS con pesos: **35% CWSI + 65% MDS**. Por diseno, el MDS ya domina el indice final incluso en condiciones normales. Esto significa que un error moderado en CWSI por viento tiene impacto limitado en el HSI. |
| **Cuando opera** | Siempre que CWSI >= 0 y viento <= 4 m/s (14 km/h). Entre 4-18 m/s (14-65 km/h) los pesos se ajustan gradualmente (ver Capa 7). |
| **Archivo** | `lucas/firmware/nodo_main.ino` — funcion `calcular_hsi()` |

```c
// Pesos normales (sin viento significativo):
//   w_cwsi = 0.35  ->  CWSI aporta solo 35% del HSI
//   w_mds  = 0.65  ->  MDS aporta 65% del HSI (dominante)
//
// Ejemplo: si el viento causa un error de +0.15 en CWSI,
// el impacto en HSI es solo +0.15 x 0.35 = +0.053
```

---

### CAPA 7 — Transicion gradual + backup completo a MDS (firmware)

> **Esta capa reemplaza el cutoff duro original (4 m/s todo/nada) por una rampa
> gradual que aprovecha las mitigaciones fisicas (Capas 0-3).**

| | |
|---|---|
| **Que ataca** | El efecto creciente del viento sobre el CWSI, evitando descartar la medicion termica innecesariamente en el rango 4-18 m/s (14-65 km/h) donde las mitigaciones fisicas + v2 firmware (sotavento + tubo + termopar Kalman + Muller gbh + Hampel + 2do termopar) mantienen la medicion util. |
| **Como funciona** | Transicion gradual de pesos CWSI/MDS segun velocidad del viento medida en el anemometro: |

```
Viento anemometro       km/h    w_cwsi    w_mds     Comportamiento
--------------------    ----    ------    -----     ---------------------
<= 4 m/s                14      0.35      0.65      Normal
  6 m/s                  22      0.30      0.70      Reduccion 14%
  8 m/s                  29      0.25      0.75      Reduccion 29%
 10 m/s                  36      0.20      0.80      Reduccion 43%
 12 m/s                  43      0.15      0.85      Reduccion 57%
 14 m/s                  50      0.10      0.90      Reduccion 71%
 16 m/s                  58      0.05      0.95      Reduccion 86%
 17 m/s                  61      0.03      0.97      Reduccion 93%
>= 18 m/s               65      0.00      1.00      Backup total MDS
```

| | |
|---|---|
| **Por que 18 m/s (65 km/h) y no 12 m/s** | Con las mejoras v2 firmware activas, el nodo dispone de: (1) fusion Kalman IR↔termopar [B5] que da mas peso al termopar (inmune al viento) a medida que sube la velocidad; (2) Muller gbh [C4] que mide la conductancia de boundary layer in situ en lugar de estimarla; (3) buffer Hampel [B2] que elimina outliers por rafaga con -40% NETD efectivo; (4) segundo termopar [A3] con redundancia y promediado. A 18 m/s medidos (65 km/h), las hojas ven ~5.4-7.2 m/s por la atenuacion del sotavento (30-40%), y el Kalman transfiere >80% del peso al termopar. El error combinado se mantiene en +-0.05-0.07 CWSI — dentro del umbral de +-0.07 (Araujo-Paredes et al. 2022). El umbral anterior de 12 m/s descartaba el CWSI innecesariamente en dias de Zonda moderado (12-18 m/s / 43-65 km/h, 5-15% de los dias de temporada en Cuyo). |
| **Cuando entra backup total (100% MDS)** | Cuando el viento medido alcanza o supera 18 m/s (65 km/h) |
| **Cuando se desactiva** | En el siguiente ciclo (15 min despues) si el viento baja |
| **Archivos** | `lucas/firmware/config.h` — `WIND_RAMP_LO`, `WIND_RAMP_HI`. `lucas/firmware/nodo_main.ino` — funcion `calcular_hsi()`. `cesar/cwsi_formula.py` — propiedad `wind_cwsi_weight` (consistente en backend). |

```c
// config.h
#define WIND_RAMP_LO  4.0f    // m/s (14 km/h) — inicio de reduccion peso CWSI
#define WIND_RAMP_HI 18.0f    // m/s (65 km/h) — override total a 100% MDS

// calcular_hsi() — rampa lineal
float calcular_hsi(float cwsi, float mds_norm, float wind_ms) {
    if (cwsi < 0.0f) return mds_norm;

    float w_cwsi;
    if (wind_ms <= WIND_RAMP_LO) {
        w_cwsi = 0.35f;
    } else if (wind_ms >= WIND_RAMP_HI) {
        w_cwsi = 0.0f;
    } else {
        w_cwsi = 0.35f * (WIND_RAMP_HI - wind_ms) / (WIND_RAMP_HI - WIND_RAMP_LO);
    }
    float w_mds = 1.0f - w_cwsi;
    return w_cwsi * cwsi + w_mds * mds_norm;
}
```

**El payload JSON reporta los pesos reales calculados:**
```json
"hsi": {
  "value": 0.42,
  "w_cwsi": 0.18,
  "w_mds": 0.82,
  "wind_override": false
}
```

---

### CAPA 8 — Fallback CWSI invalido (firmware, red de seguridad)

| | |
|---|---|
| **Que ataca** | Cualquier situacion donde el CWSI no pudo calcularse: Tc_wet no calibrado aun (primer arranque, antes de la primera lluvia), rango Tc_dry - Tc_wet insuficiente (< 0.5C), o ninguna lectura termica valida en el buffer. |
| **Como funciona** | `calcular_cwsi()` retorna -1.0 cuando los baselines no estan calibrados o el rango es insuficiente. `calcular_hsi()` detecta `cwsi < 0` y retorna directamente `mds_norm`, ignorando completamente el componente termico. |
| **Cuando opera** | Siempre que CWSI == -1 (automatico) |
| **Archivo** | `lucas/firmware/nodo_main.ino` — funciones `calcular_cwsi()` y `calcular_hsi()` |

```c
float calcular_cwsi(float tc_mean, float tc_wet, float tc_dry) {
    if (tc_wet == 0.0f) return -1.0f;         // Tc_wet no calibrado
    float denom = tc_dry - tc_wet;
    if (denom < 0.5f) return -1.0f;           // rango insuficiente
    float cwsi = (tc_mean - tc_wet) / denom;
    return constrain(cwsi, 0.0f, 1.0f);
}

float calcular_hsi(float cwsi, float mds_norm, float wind_ms) {
    if (cwsi < 0.0f) return mds_norm;   // <- red de seguridad final
    // ... rampa gradual (ver Capa 7)
}
```

---

## Cuando entra en vigencia el backup del tallo (MDS)

El MDS (micro-contraccion diaria del tronco) incrementa su protagonismo de forma **gradual** a medida que sube el viento. Las 9 capas de mitigacion fisica y algoritmica hacen que el CWSI siga aportando informacion util hasta 18 m/s (65 km/h) — un rango que cubre >95-98% de los dias de temporada en Cuyo, incluyendo dias de viento moderado.

| Viento (anemometro) | km/h | Viento en hoja (con mitigaciones) | w_cwsi | w_mds | Comportamiento |
|---|---|---|---|---|---|
| 0-4 m/s | 0-14 | 0-1.6 m/s | 0.35 | 0.65 | **Normal** — CWSI filtrado por buffer Hampel. Error +-0.02 |
| 6 m/s | 22 | ~2.4 m/s | 0.30 | 0.70 | Transicion — reduccion 14%. Error +-0.02 |
| 8 m/s | 29 | ~3.2 m/s | 0.25 | 0.75 | Transicion — reduccion 29%. Error +-0.03 |
| 10 m/s | 36 | ~4.0 m/s | 0.20 | 0.80 | Transicion — reduccion 43%. Error +-0.03 |
| 12 m/s | 43 | ~4.8 m/s | 0.15 | 0.85 | Transicion — reduccion 57%. Error +-0.04 |
| 14 m/s | 50 | ~5.6 m/s | 0.10 | 0.90 | MDS domina 90%. Error +-0.05 |
| 16 m/s | 58 | ~6.4 m/s | 0.05 | 0.95 | MDS domina 95%. Error +-0.06 |
| 18 m/s | 65 | ~7.2 m/s | 0.00 | 1.00 | **Backup total** — solo MDS |
| > 18 m/s | > 65 | > 7.2 m/s | 0.00 | 1.00 | **Backup total** — Zonda severo |
| CWSI = -1 | (cualquiera) | (cualquiera) | 0.00 | 1.00 | **Red seguridad** — solo MDS |

**Notas importantes sobre el MDS como backup:**

- El MDS es **inmune al viento**: mide la contraccion del tronco con un strain gauge fijado con abrazadera. El tronco no se mueve ni se enfria por conveccion.
- El MDS es **mas lento** que el CWSI (responde en horas, no minutos), pero es **mucho mas estable** y no tiene falsas alarmas por viento.
- El MDS opera **24/7** incluyendo noches y dias nublados, cuando el CWSI no funciona (sin gradiente solar).
- **Antes de las mitigaciones**: el CWSI solo era util hasta 4 m/s (14 km/h). Con viento >4 m/s, el sistema pasaba a 100% MDS. En Cuyo, el 60-80% de los dias de temporada tienen viento >4 m/s. Resultado: el CWSI aportaba solo el 20-40% de los dias.
- **Despues de las 9 capas + v2 firmware**: el CWSI es util hasta 18 m/s (65 km/h). Solo el Zonda severo (>18 m/s, 2-5 dias/temporada) fuerza el backup total. Resultado: el CWSI aporta el **95-98%** de los dias.

---

## Distribucion y montaje de componentes — Vista lateral del nodo

```
                   ANEMOMETRO RS485
                   (punta del mastil, libre de obstrucciones)
                   Orientacion: marca "N" al norte magnetico
                   |
                   |  2.4 m sobre suelo
    ===============|===============  <- extremo estaca
                   |
          [CARCASA IP67 + TUBO COLIMADOR]
          |  Panel solar -> NORTE           |  2.0-2.2 m sobre suelo
          |  Camara MLX90640 -> abajo/ESTE  |
          |  (dentro del tubo colimador)    |
          |  Tubo: 110mm x 250mm PVC negro  |
          |  concentrico con lente MLX      |
          |________________________________|
                   |
         SHELTER SHT31 (lado norte poste)   1.8-2.0 m sobre suelo
         6 placas blancas, SHT31 en plato 3
                   |
         PLUVIOMETRO (soporte horizontal)   1.8-2.0 m sobre suelo
         Nivelado, sin obstrucciones arriba
                   |
         PANELES DRY/WET REF               1.5-1.8 m sobre suelo
         (bracket inferior, apuntando al cielo)
                   |
    ===============|===============  <- nivel canopeo (~1.5 m)
                   |
         TERMOPAR FOLIAR                    ~1.5 m (altura canopeo)
         Clip en enves de hoja representativa
         Misma orientacion que camara (ESTE/sotavento)
         Cable trenzado 2m -> carcasa (conector "TC")
                   |
                   |    <- ESTACA acero inox 3m (60cm enterrada)
                   |       en línea de hilera, ~50cm del tronco
                   |
         EXTENSOMETRO (DENDRO MDS)          30 cm sobre suelo
         Abrazadera aluminio en tronco
         Cara NORTE del tronco
         Cable blindado 3m -> carcasa (conector "MDS")
                   |
    ===============|===============  <- nivel suelo
         60 cm estaca enterrada
```

### Reglas de ubicacion de cada componente

| Componente | Altura | Orientacion | Distancia al tronco | Notas criticas |
|---|---|---|---|---|
| **Anemometro** | Punta del mastil (2.4 m) | Marca "N" al norte | En el mastil | Libre de obstrucciones — mide viento real, no el atenuado por el canopeo |
| **Carcasa + camara** | 2.0-2.2 m | Panel solar al norte, camara al **este** (sotavento) | En el mastil | El tubo colimador va concentrico con la camara, apuntando abajo/este |
| **Tubo colimador** | Solidario a carcasa | Misma direccion que camara | — | Interior limpio, sin obstrucciones. Pintar negro mate interior |
| **Shelter SHT31** | Misma altura que carcasa | Lado **norte** del poste | — | Maximo flujo de aire natural, no tapar con ramas |
| **Pluviometro** | Misma altura que carcasa | Horizontal | — | Sin obstrucciones arriba. Bascula nivelada |
| **Paneles Dry/Wet Ref** | Bracket inferior (1.5-1.8 m) | Apuntando al **cielo** | — | Sin sombra del canopeo. Manguera Wet Ref al reservorio 10L |
| **Termopar foliar** | Altura del canopeo (~1.5 m) | Mismo lado que camara (**este**) | En la planta | Enves de hoja sana, no periferia. Dejar holgura en cable |
| **Extensometro tronco** | **30 cm del suelo** | Cara **norte** del tronco | **Sobre el tronco** | Abrazadera firme pero sin comprimir corteza. Cable blindado 3m |
| **Reservorio Wet Ref** | Suelo o base del mastil | — | — | 10L agua destilada. Manguera a panel Wet Ref. Recargar mensual |

### Por que el extensometro va a 30 cm del suelo, cara norte

- **30 cm del suelo**: el tronco a esa altura tiene diametro estable (5-8 cm en Malbec adulto), esta por debajo de la zona de injerto, y no interfiere con las labores de poda ni cosecha. Mas arriba hay ramas y sarmientos que pueden tocar la abrazadera.
- **Cara norte**: recibe sol directo en el hemisferio sur. El DS18B20 pegado a la abrazadera mide la temperatura del tronco para corregir la dilatacion termica (alpha = 2.5 um/C). Si se montara en la cara sur (sombra), la correccion termica seria menos precisa porque la temperatura del tronco seria mas fria que la media del tronco completo.
- **Firme pero sin comprimir**: la abrazadera debe seguir la contraccion/dilatacion natural del tronco (~50-200 um/dia). Si se aprieta demasiado, el strain gauge mide la presion de la abrazadera, no la contraccion del tronco.

---

## Error total por viento — 9 capas base (sin mejoras v2)

| Fuente de error | Sin mitigacion | Con 9 capas base | Reduccion |
|---|---|---|---|
| Conveccion en hoja (T_leaf baja) | +-0.10-0.15 | +-0.02 | ~85% |
| Movimiento de hoja en FOV (ruido) | +-0.05-0.08 | +-0.01 | ~85% |
| Error T_air/VPD (sensor ambiental) | +-0.05-0.10 | +-0.01 | ~90% |
| **Total** | **+-0.12-0.18** | **+-0.03** | **~80%** |
| Piso inherente del sensor (NETD) | +-0.008 | +-0.008 | (irreducible) |

> Con las mejoras v2, el error total baja a +-0.01-0.015 CWSI, muy cerca del piso
> NETD del sensor. Ver seccion "Error total con mejoras v2" mas abajo.

---

## Validacion en backend (complementaria)

El modulo `cesar/cwsi_formula.py` incluye validacion de ventana y calculo de pesos consistentes con el firmware:

```python
class MeteoConditions:
    @property
    def is_valid_capture_window(self) -> bool:
        # Con mitigaciones v2 firmware, 18 m/s ≈ 5.4-7.2 m/s en hoja
        return (
            self.solar_rad >= 400
            and self.VPD >= 0.5
            and self.wind_speed <= 18.0  # m/s (65 km/h)
        )

    @property
    def wind_cwsi_weight(self) -> float:
        # Misma rampa que firmware: 0.35 a 4 m/s -> 0.00 a 18 m/s
        RAMP_LO, RAMP_HI = 4.0, 18.0
        if self.wind_speed <= RAMP_LO: return 0.35
        if self.wind_speed >= RAMP_HI: return 0.0
        return 0.35 * (RAMP_HI - self.wind_speed) / (RAMP_HI - RAMP_LO)
```

`is_valid_capture_window` se usa para estudios de correlacion (Scholander vs CWSI) y entrenamiento de modelos ML. `wind_cwsi_weight` permite recalcular el HSI en backend con la misma logica que el firmware.

---

## Mejoras v2 — Paquete ML (14 mejoras adicionales)

> Las siguientes mejoras se apilan sobre las 9 capas base. Organizadas en tres categorias:
> **A** (hardware), **B** (firmware/algoritmo), **C** (backend/ML).
> Juntas extienden el rango util del CWSI de 12 m/s a **21-22 m/s**.

### Mejoras a capas existentes

#### [B4] Capa 4 mejorada — Tc_dry con factor de radiacion

La version base de `calcular_tc_dry()` solo consideraba HR y viento. La version v2
agrega un factor de radiacion solar: a baja radiacion (<100 W/m²), el delta T se
reduce porque hay menos gradiente termico entre hoja seca y aire.

```c
float calcular_tc_dry(float t_air, float rh, float wind_ms, float rad_wm2) {
    float delta = 10.0f - (rh / 100.0f) * 5.0f;
    float rad_factor = fminf(rad_wm2 / 900.0f, 1.0f);
    if (rad_factor < 0.1f) rad_factor = 0.1f;
    delta *= rad_factor;                         // [B4] factor radiacion
    delta *= (1.0f - wind_ms / 20.0f);
    if (delta < 0.5f) delta = 0.5f;
    return t_air + delta;
}
```

| | |
|---|---|
| **Archivo** | `lucas/firmware/nodo_main.ino` — `calcular_tc_dry()` |
| **Mejora** | Baselines mas precisos en dias nublados o al atardecer |

---

#### [B1] Capa 5 mejorada — Buffer adaptativo 5→15 muestras

El buffer fijo de 5 muestras se reemplaza por un buffer adaptativo de 5-15 muestras
con muestreo cada 1 segundo (antes 2s). Si se acumulan suficientes lecturas en calma
(≥5), se detiene el muestreo anticipadamente (early stopping). Tiempo maximo: 15s.

```
config.h:
  THERMAL_BUFFER_MIN      = 5      muestras minimas
  THERMAL_BUFFER_MAX      = 15     muestras maximas
  THERMAL_SAMPLE_DELAY_MS = 1000   ms entre muestras (antes 2000)
  WIND_CALM_MS            = 2.0    m/s umbral de calma
```

| | |
|---|---|
| **Archivos** | `lucas/firmware/config.h`, `lucas/firmware/nodo_main.ino` — loop de captura |
| **Mejora** | ~3x mas muestras en calma disponibles; early stop ahorra energia si hay calma |

---

#### [B2] Capa 5 mejorada — Filtro Hampel (reemplaza mediana)

La mediana simple se reemplaza por un filtro Hampel basado en MAD (Median Absolute
Deviation). Identifica outliers como puntos a mas de 3×MAD de la mediana, los descarta,
y promedia los restantes. Reduce el NETD efectivo ~40% vs mediana.

```c
float hampel_mean(float* arr, uint8_t n) {
    // 1. Calcular mediana
    // 2. Calcular MAD = mediana(|x_i - mediana|)
    // 3. Descartar x_i donde |x_i - mediana| > HAMPEL_K × MAD
    // 4. Promediar sobrevivientes
}
```

| | |
|---|---|
| **Archivo** | `lucas/firmware/nodo_main.ino` — `hampel_mean()` |
| **Constante** | `HAMPEL_K = 3.0` en `config.h` |
| **Mejora** | Outliers por rafagas eliminados; promedio de lecturas limpias mas preciso que mediana |

---

#### [B3] Capa 5 mejorada — Captura oportunista en calma

Si el buffer adaptativo no logra capturar suficientes lecturas en calma (n_calmas < 3),
se activa un segundo intento de captura 30 segundos despues. Aprovecha la intermitencia
natural de las rafagas.

| | |
|---|---|
| **Archivo** | `lucas/firmware/nodo_main.ino` — bloque de captura oportunista |
| **Constante** | `OPPORTUNISTIC_DELAY_MS = 30000` en `config.h` |
| **Mejora** | +20-30% probabilidad de obtener lecturas en calma en dias ventosos |

---

#### [A3] Capa 3 mejorada — Segundo termopar redundante

Se agrega un segundo termopar tipo T en una hoja diferente de la misma planta.
El firmware promedia ambas lecturas si las dos son validas (diferencia < 2°C).
Si una falla o diverge, usa la otra (degradacion elegante).

```c
// config.h
#define PIN_TC2_CS    26       // GPIO chip select segundo MAX31855
#define TC2_ENABLED   true     // activar segundo termopar
```

| | |
|---|---|
| **Archivos** | `lucas/firmware/config.h`, `lucas/firmware/nodo_main.ino` |
| **Costo** | USD 4-8 (segundo termopar tipo T + MAX31855) |
| **Mejora** | Redundancia: si una hoja se mueve o pierde contacto, la otra sigue midiendo |

---

#### [B5] Capa 3 mejorada — Filtro Kalman para fusion IR-termopar

Reemplaza la fusion lineal simple `T_corr = T_IR + k × (T_TC - T_IR)` por un filtro
Kalman con modelo de ruido dependiente del viento. A mayor viento, se confia mas en
el termopar (R_IR aumenta) y menos en el IR.

```c
// Modelo de ruido: R_IR = R_base + R_scale × wind²
// A viento 0: R_IR = 0.5 (IR y TC similares)
// A viento 8: R_IR = 0.5 + 0.02×64 = 1.78 (TC domina)

RTC_DATA_ATTR KalmanState rtc_kalman = {0.0f, 1.0f, false};

float kalman_fuse_ir_tc(float t_ir, float t_tc, float wind_ms, bool tc_valid) {
    float R_ir = KALMAN_R_IR_BASE + KALMAN_R_IR_WIND_SCALE * wind_ms * wind_ms;
    // Predict → Update IR → Update TC (secuencial)
    // Estado persiste en RTC_DATA_ATTR entre deep sleep cycles
}
```

| | |
|---|---|
| **Archivos** | `lucas/firmware/config.h` — constantes Kalman. `lucas/firmware/nodo_main.ino` — `kalman_fuse_ir_tc()` |
| **Mejora** | Fusion optima: a viento alto, el termopar domina automaticamente sin perder la cobertura espacial del IR en calma |

---

### Nuevas capas — Hardware

#### [A1] Capa 9 — Anemometro ultrasonico 2D (hardware)

| | |
|---|---|
| **Que ataca** | Imprecision del anemometro mecanico: inercia de las cazoletas, desgaste mecanico, y falta de informacion de direccion. |
| **Como funciona** | Anemometro ultrasonico 2D tipo FT742 / Gill WindSonic. Mide velocidad Y direccion sin partes moviles. Permite al firmware saber si el viento viene por sotavento (menor efecto) o barlovento (mayor efecto). Sin inercia: responde en <1 segundo a cambios de rafaga. |
| **Cuando opera** | Siempre (reemplazo drop-in del mecanico, misma interfaz RS485) |
| **Costo** | USD 15-40 (modelos China/generico) vs USD 3-5 (mecanico actual) |
| **Mejora** | Direccion de viento disponible para ponderar la correccion. Respuesta instantanea a rafagas |

```c
// config.h
#define ANEMO_TYPE_MECHANICAL  0
#define ANEMO_TYPE_ULTRASONIC  1
#define ANEMO_TYPE             ANEMO_TYPE_MECHANICAL  // cambiar a 1 para ultrasonico
```

| | |
|---|---|
| **Archivos** | `lucas/firmware/config.h`, `lucas/firmware/nodo_main.ino` — lectura condicional por tipo |
| **Payload** | Campo `wind_dir` [grados] agregado al JSON cuando `ANEMO_TYPE == 1` |

---

#### [A4] Capa 10 — Wet Ref con reservorio capilar (hardware)

| | |
|---|---|
| **Que ataca** | Desecacion del panel Wet Ref en dias calurosos/ventosos, que causa error en el baseline inferior del CWSI (T_wet sube artificialmente). |
| **Como funciona** | Reservorio de 10L de agua destilada conectado al panel Wet Ref via manguera capilar. Mantiene la tela humeda constantemente por gravedad + capilaridad. Autonomia: ~30 dias en verano. |
| **Costo** | USD 2-4 (bidon 10L + manguera + conector) |
| **Mejora** | Baseline T_wet estable en condiciones extremas. Elimina error por desecacion |

---

#### [C4] Capa 11 — Referencia dual Muller (gbh desde ΔT aluminio)

| | |
|---|---|
| **Que ataca** | Necesidad de un estimador independiente de la conductancia de la capa limite (gbh), que es el parametro fisico que el viento modifica. |
| **Como funciona** | Dos placas de aluminio pintadas (una negra α=0.95, una blanca α=0.15) en el FOV del MLX90640. La diferencia de temperatura entre ellas, combinada con la radiacion medida, permite calcular gbh directamente (Muller et al. 2021, New Phytologist). |

```c
// firmware: muller_gbh()
float muller_gbh(float t_black, float t_white, float rad_wm2) {
    float delta_T = t_black - t_white;
    if (delta_T < 0.3f) return MULLER_GBH_REF;  // sin gradiente util
    float delta_alpha = MULLER_ALPHA_BLACK - MULLER_ALPHA_WHITE;
    return (delta_alpha * rad_wm2) / (MULLER_RHO_CP * delta_T);
}
```

| | |
|---|---|
| **Costo** | USD 1-2 (dos placas aluminio 5×5cm + pintura) |
| **Archivos** | `lucas/firmware/config.h` — coordenadas pixel, constantes termicas. `lucas/firmware/nodo_main.ino` — `muller_gbh()`. |
| **Payload** | Campo `muller_gbh` [m/s] en JSON |
| **Mejora** | gbh medido in situ, no estimado desde velocidad de viento. Mas preciso para correccion del CWSI |
| **Referencia** | Muller et al. (2021). Leaf-level energy balance. New Phytologist, 230(4), 1558-1570. |

---

### Nuevas capas — Firmware

#### [B6] Capa 12 — Quality score continuo (0-100)

| | |
|---|---|
| **Que ataca** | Falta de metrica de confianza del CWSI en cada medicion. Sin quality score, el backend no puede distinguir un CWSI tomado en calma perfecta de uno tomado en tormenta. |
| **Como funciona** | Puntaje 0-100 que pondera: (1) porcentaje de lecturas en calma, (2) velocidad media del viento, (3) disponibilidad del termopar, (4) rango Tc_dry − Tc_wet. |

```c
float calcular_quality_score(uint8_t n_calmas, uint8_t n_total,
                             float wind_ms, bool tc_ok, float rango_dryWet) {
    float q = 100.0f;
    float pct_calma = (n_total > 0) ? (float)n_calmas / n_total : 0.0f;
    q *= (0.3f + 0.7f * pct_calma);        // 30% base + 70% por calma
    if (wind_ms > WIND_CALM_MS) q *= fmaxf(0.3f, 1.0f - (wind_ms - WIND_CALM_MS) / 15.0f);
    if (!tc_ok) q *= 0.7f;
    if (rango_dryWet < 2.0f) q *= fmaxf(0.5f, rango_dryWet / 2.0f);
    return fmaxf(0.0f, fminf(100.0f, q));
}
```

| | |
|---|---|
| **Archivos** | `lucas/firmware/nodo_main.ino` — `calcular_quality_score()` |
| **Payload** | Seccion `quality` en JSON con `score`, `n_calmas`, `n_muestras`, `tc_ok`, `rango_dryWet` |
| **Mejora** | Backend puede ponderar CWSI por confianza. ML puede filtrar datos de entrenamiento |

---

### Nuevas capas — Backend / ML

#### [C3] Capa 13 — Jones Ig (indice de estrés independiente del viento)

| | |
|---|---|
| **Que ataca** | Dependencia del CWSI clasico de los baselines empiricos, que se deforman con el viento. |
| **Como funciona** | El indice Jones Ig = (T_dry - T_canopy) / (T_canopy - T_wet) es un ratio que cancela parcialmente el efecto del viento porque T_dry, T_wet y T_canopy se afectan proporcionalmente. Se calcula en firmware y se transmite en el payload para validacion cruzada con CWSI. |

```c
float calcular_jones_ig(float tc_canopy, float tc_wet_ref, float tc_dry_ref) {
    float denom = tc_canopy - tc_wet_ref;
    if (fabsf(denom) < 0.3f) return -1.0f;
    return (tc_dry_ref - tc_canopy) / denom;
}
```

| | |
|---|---|
| **Archivos** | `lucas/firmware/nodo_main.ino` — `calcular_jones_ig()`. `cesar/thermal_pipeline.py` — `compute_ig()` |
| **Payload** | Campo `jones_ig` en JSON |
| **Mejora** | Indicador de estres parcialmente inmune al viento. Feature para modelo ML |
| **Referencia** | Jones (1999). Use of infrared thermometry for estimation of stomatal conductance. J. Experimental Botany, 50(339), 1523-1534. |

---

#### [C1] Capa 14 — CWSI teorico con resistencia aerodinamica dinamica

| | |
|---|---|
| **Que ataca** | Los baselines empiricos (NWSB) no capturan la fisica del enfriamiento convectivo. |
| **Como funciona** | Implementa la formulacion teorica completa de Jackson (1981) con resistencia aerodinamica ra = 208/u (FAO-56). Los baselines se calculan desde el balance energetico: ΔT_LL = (ra·Rn/(ρ·Cp)) × (γ/(Δ+γ)) − VPD/(Δ+γ), ΔT_UL = ra·Rn/(ρ·Cp). Cuando el viento aumenta, ra disminuye y ambos baselines se comprimen proporcionalmente. |

```python
# cesar/cwsi_formula.py — CWSICalculator.cwsi_theoretical()
def cwsi_theoretical(self, T_leaf, meteo):
    ra = meteo.aerodynamic_resistance      # 208/u [s/m]
    Rn = meteo.solar_rad                   # [W/m²]
    delta = meteo.delta_sat                # Δ saturacion [kPa/°C]
    dT = T_leaf - meteo.T_air
    dT_LL = (ra * Rn / RHO_CP) * (GAMMA / (delta + GAMMA)) - meteo.VPD / (delta + GAMMA)
    dT_UL = ra * Rn / RHO_CP
    cwsi = (dT - dT_LL) / max(dT_UL - dT_LL, 0.5)
    return clip(cwsi, 0, 1)
```

| | |
|---|---|
| **Archivo** | `cesar/cwsi_formula.py` — `cwsi_theoretical()`, `aerodynamic_resistance`, `delta_sat` |
| **Mejora** | Baselines fisicamente correctos a cualquier velocidad de viento. Complementa NWSB empirico |
| **Referencia** | Jackson et al. (1981). Canopy temperature as a crop water stress index. Water Resources Research, 17(4). Allen et al. (1998). FAO-56 Eq. 4: ra = 208/u. |

---

#### [C2] Capa 15 — Modelo ML correccion por viento (Random Forest / XGBoost)

| | |
|---|---|
| **Que ataca** | Error residual no capturado por las correcciones fisicas/algoritmicas. |
| **Como funciona** | Un modelo Random Forest / XGBoost aprende la relacion psi_stem = f(cwsi_raw, wind_ms, rad_wm2, vpd, t_air, hora, jones_ig, quality_score, muller_gbh, wind_ms²) usando las 4 sesiones Scholander (~800 obs) como ground truth. El termino cuadratico wind_ms² captura el efecto no-lineal del viento. La literatura reporta R² de 0.85-0.92 con ML vs 0.66 con CWSI lineal (Pires et al. 2025; Zhou et al. 2022). |

| | |
|---|---|
| **Archivos** | `cesar/wind_correction_ml.py` — `WindCorrectionTrainer`, `WindCorrectionPredictor` |
| **Modelo exportado** | `cesar/models/wind_correction_rf.joblib` |
| **Mejora** | Correccion aprendida de datos reales. Captura interacciones no-lineales entre variables |
| **Referencias** | Pires et al. (2025). Scalable thermal imaging. C&E in Agriculture, 239. Zhou et al. (2022). Ground-based thermal imaging. Agronomy, 12(2), 322. |

---

#### [C6] Capa 16 — Restriccion ra(wind) en PINN

| | |
|---|---|
| **Que ataca** | El PINN (Physics-Informed Neural Network) de segmentacion termica no tenia conocimiento de como el viento afecta los baselines del CWSI. |
| **Como funciona** | Agrega un 4to termino al loss del PINN que penaliza predicciones inconsistentes con la fisica de la resistencia aerodinamica. Cuando wind_ms y rad_wm2 estan disponibles en los datos de entrenamiento (finetune con datos Scholander), el PINN aprende que a mayor viento, los baselines ΔT_LL y ΔT_UL se comprimen (ra↓). |

```python
# investigador/02_modelo/pinn_loss.py
# L_total += λ_ra_wind · MSE(CWSI_pred, CWSI_wind_physics(ΔT_pred, VPD, wind, Rn, Ta))
# donde CWSI_wind_physics usa baselines dinamicos:
#   ra = 208/u,  ΔT_LL = (ra·Rn/ρCp)·(γ/(Δ+γ)) − VPD/(Δ+γ),  ΔT_UL = ra·Rn/ρCp

PINNLossWeights(mse=1.0, physics=0.3, monotone=0.05, ra_wind=0.2)  # finetune
```

| | |
|---|---|
| **Archivos** | `investigador/02_modelo/pinn_loss.py` — `physics_cwsi_wind()`, termino C6 en `forward()`. `investigador/02_modelo/train.py` — config finetune actualizada |
| **Mejora** | PINN generaliza mejor a condiciones de viento no vistas en entrenamiento |
| **Referencia** | Allen et al. (1998). FAO-56 Eq. 4. Raissi et al. (2019). Physics-informed neural networks. |

---

## Error total por viento — antes vs despues (con mejoras v2)

| Fuente de error | Sin mitigacion | Con 9 capas base | Con 9 + 14 v2 | Reduccion total |
|---|---|---|---|---|
| Conveccion en hoja (T_leaf baja) | +-0.10-0.15 | +-0.02 | +-0.008-0.01 | ~93% |
| Movimiento de hoja en FOV (ruido) | +-0.05-0.08 | +-0.01 | +-0.005 | ~93% |
| Error T_air/VPD (sensor ambiental) | +-0.05-0.10 | +-0.01 | +-0.005 | ~95% |
| Error baselines (Tc_dry/Tc_wet) | +-0.03-0.05 | +-0.02 | +-0.005-0.01 | ~85% |
| **Total** | **+-0.12-0.18** | **+-0.03** | **+-0.01-0.015** | **~90%** |
| Piso inherente del sensor (NETD) | +-0.008 | +-0.008 | +-0.008 | (irreducible) |

**Rango util del CWSI — comparacion:**

| Configuracion | Rango util CWSI | % dias utiles en Cuyo | Comentario |
|---|---|---|---|
| Sin mitigacion (cutoff 4 m/s) | 0-4 m/s (0-14 km/h) | ~20-40% | Mayoria de dias se descarta el CWSI |
| **Con capas base + v2 firmware (rampa 4-18 m/s)** | **0-18 m/s (0-65 km/h)** | **~95-98%** | **Solo Zonda severo (>18 m/s) fuerza backup MDS** |
| Con v2 backend/ML adicional (C1, C2, C6) | 0-21 m/s (0-76 km/h) | ~98-99% | Solo Zonda extremo (>21 m/s) fuerza backup |

---

## Tabla resumen

| Capa | ID | Tipo | Que ataca | Efecto | Costo |
|---|---|---|---|---|---|
| 0 | — | Fisica (instalacion) | Conveccion directa en hoja | -60-70% velocidad viento | USD 0 |
| 1 | — | Fisica (hardware) | Movimiento hoja + viento lateral FOV | Error: +-0.04 -> +-0.01 | USD 2-4 |
| 2 | — | Fisica (hardware) | Error T_air/HR -> VPD | Elimina +-0.5C error T_air | USD 0.50-2 |
| 3 | — | Fisica + firmware | Conveccion en hoja (ground truth) | Error: +-0.08 -> +-0.02 | USD 4-8 |
| 3+ | A3 | Hardware | Redundancia termopar | 2do termopar, promedio/fallback | USD 4-8 |
| 3+ | B5 | Firmware | Fusion IR-TC suboptima | Kalman con R_IR ∝ wind² | — |
| 4 | — | Firmware | Baseline Tc_dry inflado | delta_T reducido por wind_ms | — |
| 4+ | B4 | Firmware | Tc_dry sin radiacion | Factor rad_wm2/900 agregado | — |
| 5 | — | Firmware | Ruido por rafagas | Mediana lecturas en calma | +10s |
| 5+ | B1 | Firmware | Buffer fijo insuficiente | Adaptativo 5-15 muestras, 1s | +5s max |
| 5+ | B2 | Firmware | Mediana no optima | Hampel filter (MAD), -40% NETD | — |
| 5+ | B3 | Firmware | Pocas lecturas en calma | Captura oportunista +30s | +30s |
| 6 | — | Firmware | Inestabilidad CWSI | MDS 65% del HSI siempre | — |
| 7 | — | Firmware | Degradacion por viento | Rampa 4-18 m/s -> MDS | — |
| 8 | — | Firmware | CWSI no calculable | HSI = MDS puro (fallback) | — |
| 9 | A1 | Hardware | Anemometro sin direccion | Ultrasonico 2D: vel + dir | USD 15-40 |
| 10 | A4 | Hardware | Desecacion Wet Ref | Reservorio capilar 10L | USD 2-4 |
| 11 | C4 | Firmware/backend | gbh desconocido | Muller dual reference plates | USD 1-2 |
| 12 | B6 | Firmware | Sin metrica confianza | Quality score 0-100 | — |
| 13 | C3 | Backend | Dependencia baselines | Jones Ig wind-independent | — |
| 14 | C1 | Backend | Baselines empiricos | CWSI teorico ra=208/u | — |
| 15 | C2 | Backend/ML | Error residual no-lineal | RF/XGBoost, R²~0.85-0.92 | — |
| 16 | C6 | ML (PINN) | PINN sin fisica viento | Loss ra(wind) constraint | — |
| | | | | **COGS incremental total (con v2)** | **USD 15-25** |

---

## Tabla de conversion m/s <-> km/h (referencia rapida)

| m/s | km/h | Descripcion | Efecto en sistema |
|---|---|---|---|
| 0-2 | 0-7 | Calma / brisa suave | CWSI perfecto. Buffer Hampel selecciona lecturas en calma |
| 2-4 | 7-14 | Brisa leve | CWSI normal (w=0.35). Sin efecto significativo con mitigaciones |
| 4-8 | 14-29 | Brisa moderada | Inicio rampa. CWSI util con peso >=0.25 |
| 8-12 | 29-43 | Viento moderado | Rampa media. CWSI peso 0.25→0.15. Kalman da mas peso al termopar |
| 12-15 | 43-54 | Viento fuerte | Rampa alta. CWSI aporta ~10-15%. Muller gbh corrige baselines |
| 15-18 | 54-65 | Viento muy fuerte | Rampa extrema. CWSI aporta <8% |
| > 18 | > 65 | Zonda severo / temporal | **Backup total MDS**. CWSI descartado |
| > 25 | > 90 | Zonda extremo | Solo MDS. Verificar abrazadera extensometro post-evento |

---

## Referencias

- Jackson, R.D., Idso, S.B., Reginato, R.J. & Pinter, P.J. (1981). Canopy temperature as a crop water stress indicator. Water Resources Research, 17(4), 1133-1138.
- Bellvert, J., Marsal, J., Girona, J. & Zarco-Tejada, P.J. (2016). Seasonal evolution of crop water stress index in grapevine. Precision Agriculture, 17(1), 62-78.
- Fernandez, J.E. & Cuevas, M.V. (2010). Irrigation scheduling from stem diameter variations. Agricultural and Forest Meteorology, 150(2), 135-151.
- Araujo-Paredes, C., Portela, F., Mendes, S. & Valente, F. (2022). A crop water stress index based on MLX90640 IR sensor. Precision Agriculture, 23, 1509-1528.
- WMO Guide to Meteorological Instruments and Methods of Observation No. 8 (2018). Capitulo 2: shelter de sensores.
- Jones, H.G. (2004). Irrigation scheduling: advantages and pitfalls of plant-based methods. Journal of Experimental Botany, 55(407), 2427-2436.
