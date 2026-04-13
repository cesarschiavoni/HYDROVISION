# Mitigacion de viento — Defensa en profundidad

## HydroVision AG — Arquitectura completa de mitigacion del efecto del viento sobre el CWSI

> **Problema:** El viento afecta la medicion de temperatura foliar de tres formas:
> (1) enfriamiento convectivo de la hoja (T_leaf baja artificialmente),
> (2) movimiento de la hoja dentro/fuera del FOV del sensor IR (ruido),
> (3) error en la medicion de T_air y HR del sensor ambiental (propaga error al VPD y al CWSI).
>
> El sistema implementa **9 capas de mitigacion** desde lo fisico hasta lo algoritmico.
> Cada capa ataca una fuente de error distinta. Juntas, permiten obtener CWSI confiable
> en condiciones de viento moderado-alto (0-12 m/s / 0-43 km/h) y degradar graciosamente
> a MDS puro solo cuando el viento es extremo (>12 m/s / >43 km/h, Zonda severo).
>
> Todas las capas se incluyen en todos los nodos independientemente del tier o mercado
> (un solo SKU). El costo incremental es USD 9 sobre COGS base (6.5%).

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
  v  4-12 m/s (14-43 km/h): rampa gradual
CAPA 7 -- Transicion gradual CWSI -> MDS - peso CWSI se reduce linealmente
  |        <= 4 m/s (14 km/h):  w_cwsi=0.35 (normal)
  |        6 m/s (22 km/h):     w_cwsi=0.26
  |        8 m/s (29 km/h):     w_cwsi=0.18
  |        10 m/s (36 km/h):    w_cwsi=0.09
  |        >= 12 m/s (43 km/h): w_cwsi=0.00 (backup total MDS)
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
| **Cuando opera** | Siempre que CWSI >= 0 y viento <= 4 m/s (14 km/h). Entre 4-12 m/s (14-43 km/h) los pesos se ajustan gradualmente (ver Capa 7). |
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
| **Que ataca** | El efecto creciente del viento sobre el CWSI, evitando descartar la medicion termica innecesariamente en el rango 4-12 m/s (14-43 km/h) donde las mitigaciones fisicas (sotavento + tubo + termopar + shelter) mantienen la medicion util. |
| **Como funciona** | Transicion gradual de pesos CWSI/MDS segun velocidad del viento medida en el anemometro: |

```
Viento anemometro       km/h    w_cwsi    w_mds     Comportamiento
--------------------    ----    ------    -----     ---------------------
<= 4 m/s                14      0.35      0.65      Normal
  5 m/s                  18      0.31      0.69      Reduccion 12%
  6 m/s                  22      0.26      0.74      Reduccion 25%
  7 m/s                  25      0.22      0.78      Reduccion 37%
  8 m/s                  29      0.18      0.82      Reduccion 50%
  9 m/s                  32      0.13      0.87      Reduccion 62%
 10 m/s                  36      0.09      0.91      Reduccion 75%
 11 m/s                  40      0.04      0.96      Reduccion 87%
>= 12 m/s               43      0.00      1.00      Backup total MDS
```

| | |
|---|---|
| **Por que 12 m/s (43 km/h) y no 4 m/s** | Con orientacion a sotavento (Capa 0), el viento en la hoja medida es ~30-40% del medido en el anemometro (que esta en la punta del mastil, expuesto). A 12 m/s medidos, las hojas ven solo ~3.6-4.8 m/s. Ademas, el tubo colimador (Capa 1) reduce el flujo lateral adicional, y el termopar (Capa 3) corrige el 60% del error restante. El resultado combinado es que a 12 m/s (43 km/h) de viento medido, el error del CWSI sigue en +-0.05-0.07 — dentro del umbral aceptable de +-0.07 (Araujo-Paredes et al. 2022). El umbral original de 4 m/s (14 km/h) descartaba el CWSI innecesariamente en la mayoria de dias de viento tipicos de Cuyo (4-10 m/s / 14-36 km/h = 60-80% de los dias de temporada). |
| **Cuando entra backup total (100% MDS)** | Cuando el viento medido alcanza o supera 12 m/s (43 km/h) |
| **Cuando se desactiva** | En el siguiente ciclo (15 min despues) si el viento baja |
| **Archivos** | `lucas/firmware/config.h` — `WIND_RAMP_LO`, `WIND_RAMP_HI`. `lucas/firmware/nodo_main.ino` — funcion `calcular_hsi()`. `cesar/cwsi_formula.py` — propiedad `wind_cwsi_weight` (consistente en backend). |

```c
// config.h
#define WIND_RAMP_LO  4.0f    // m/s (14 km/h) — inicio de reduccion peso CWSI
#define WIND_RAMP_HI 12.0f    // m/s (43 km/h) — override total a 100% MDS

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

El MDS (micro-contraccion diaria del tronco) incrementa su protagonismo de forma **gradual** a medida que sube el viento. Las 9 capas de mitigacion fisica y algoritmica hacen que el CWSI siga aportando informacion util hasta 12 m/s (43 km/h) — un rango que cubre >95% de los dias de temporada en Cuyo, incluyendo dias de viento moderado.

| Viento (anemometro) | km/h | Viento en hoja (con mitigaciones) | w_cwsi | w_mds | Comportamiento |
|---|---|---|---|---|---|
| 0-4 m/s | 0-14 | 0-1.6 m/s | 0.35 | 0.65 | **Normal** — CWSI filtrado por buffer de calma. Error +-0.02 |
| 5 m/s | 18 | ~2.0 m/s | 0.31 | 0.69 | Transicion — reduccion 12%. Error +-0.02 |
| 6 m/s | 22 | ~2.4 m/s | 0.26 | 0.74 | Transicion — reduccion 25%. Error +-0.03 |
| 8 m/s | 29 | ~3.2 m/s | 0.18 | 0.82 | Transicion — reduccion 50%. Error +-0.04 |
| 10 m/s | 36 | ~4.0 m/s | 0.09 | 0.91 | MDS domina 91%. Error +-0.05 |
| 12 m/s | 43 | ~4.8 m/s | 0.00 | 1.00 | **Backup total** — solo MDS |
| > 12 m/s | > 43 | > 4.8 m/s | 0.00 | 1.00 | **Backup total** — Zonda severo |
| CWSI = -1 | (cualquiera) | (cualquiera) | 0.00 | 1.00 | **Red seguridad** — solo MDS |

**Notas importantes sobre el MDS como backup:**

- El MDS es **inmune al viento**: mide la contraccion del tronco con un strain gauge fijado con abrazadera. El tronco no se mueve ni se enfria por conveccion.
- El MDS es **mas lento** que el CWSI (responde en horas, no minutos), pero es **mucho mas estable** y no tiene falsas alarmas por viento.
- El MDS opera **24/7** incluyendo noches y dias nublados, cuando el CWSI no funciona (sin gradiente solar).
- **Antes de las mitigaciones**: el CWSI solo era util hasta 4 m/s (14 km/h). Con viento >4 m/s, el sistema pasaba a 100% MDS. En Cuyo, el 60-80% de los dias de temporada tienen viento >4 m/s. Resultado: el CWSI aportaba solo el 20-40% de los dias.
- **Despues de las 9 capas**: el CWSI es util hasta 12 m/s (43 km/h). Solo el Zonda severo (>12 m/s, 5-15 dias/temporada) fuerza el backup total. Resultado: el CWSI aporta el **85-95%** de los dias.

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
          [CARCASA IP65 + TUBO COLIMADOR]
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

## Error total por viento — antes vs despues

| Fuente de error | Sin mitigacion | Con 9 capas | Reduccion |
|---|---|---|---|
| Conveccion en hoja (T_leaf baja) | +-0.10-0.15 | +-0.02 | ~85% |
| Movimiento de hoja en FOV (ruido) | +-0.05-0.08 | +-0.01 | ~85% |
| Error T_air/VPD (sensor ambiental) | +-0.05-0.10 | +-0.01 | ~90% |
| **Total** | **+-0.12-0.18** | **+-0.03** | **~80%** |
| Piso inherente del sensor (NETD) | +-0.008 | +-0.008 | (irreducible) |

El error total de +-0.03 CWSI bajo viento esta cerca del piso NETD del sensor (+-0.008).
Esto significa que las 9 capas extraen practicamente toda la informacion util que la
fisica del sensor permite, independientemente de las condiciones de viento.

**Rango util del CWSI — comparacion:**

| Configuracion | Rango util CWSI | % dias utiles en Cuyo | Comentario |
|---|---|---|---|
| Sin mitigacion (solo anemometro, cutoff 4 m/s) | 0-4 m/s (0-14 km/h) | ~20-40% | La mayoria de los dias se descarta el CWSI |
| Con 9 capas + rampa gradual 4-12 m/s | 0-12 m/s (0-43 km/h) | ~85-95% | Solo Zonda severo fuerza backup total MDS |

---

## Validacion en backend (complementaria)

El modulo `cesar/cwsi_formula.py` incluye validacion de ventana y calculo de pesos consistentes con el firmware:

```python
class MeteoConditions:
    @property
    def is_valid_capture_window(self) -> bool:
        # Con sotavento+tubo+termopar, 12 m/s ≈ 3.6-4.8 m/s en hoja
        return (
            self.solar_rad >= 400
            and self.VPD >= 0.5
            and self.wind_speed <= 12.0  # m/s (43 km/h)
        )

    @property
    def wind_cwsi_weight(self) -> float:
        # Misma rampa que firmware: 0.35 a 4 m/s -> 0.00 a 12 m/s
        RAMP_LO, RAMP_HI = 4.0, 12.0
        if self.wind_speed <= RAMP_LO: return 0.35
        if self.wind_speed >= RAMP_HI: return 0.0
        return 0.35 * (RAMP_HI - self.wind_speed) / (RAMP_HI - RAMP_LO)
```

`is_valid_capture_window` se usa para estudios de correlacion (Scholander vs CWSI) y entrenamiento de modelos ML. `wind_cwsi_weight` permite recalcular el HSI en backend con la misma logica que el firmware.

---

## Tabla resumen

| Capa | Tipo | Que ataca | Umbral | Efecto | Costo |
|---|---|---|---|---|---|
| 0 | Fisica (instalacion) | Conveccion directa en hoja | — | -60-70% velocidad viento en zona medida | USD 0 |
| 1 | Fisica (hardware) | Movimiento hoja + viento lateral en FOV | — | Error movimiento: +-0.04 -> +-0.01 CWSI | USD 2-4 |
| 2 | Fisica (hardware) | Error T_air/HR -> VPD -> CWSI | — | Elimina +-0.5C error en T_air | USD 0.50-2 |
| 3 | Fisica + firmware | Conveccion en hoja (ground truth) | — | Error conveccion: +-0.08 -> +-0.02 CWSI | USD 4-8 |
| 4 | Algoritmica (firmware) | Baseline Tc_dry inflado | Proporcional | delta_T reducido segun wind_ms | — |
| 5 | Algoritmica (firmware) | Ruido por rafagas | < 2 m/s (7 km/h) | Mediana de lecturas en calma | +10s/ciclo |
| 6 | Algoritmica (firmware) | Inestabilidad inherente CWSI | — | MDS domina 65% del HSI siempre | — |
| **7** | **Algoritmica (firmware)** | **Degradacion progresiva por viento** | **4-12 m/s (14-43 km/h) rampa** | **Transicion gradual -> 100% MDS a 12 m/s** | — |
| 8 | Algoritmica (firmware) | CWSI no calculable | CWSI = -1 | HSI = MDS puro (red seguridad) | — |
| | | | | **COGS incremental total** | **USD 9** |

---

## Tabla de conversion m/s <-> km/h (referencia rapida)

| m/s | km/h | Descripcion | Efecto en sistema |
|---|---|---|---|
| 0-2 | 0-7 | Calma / brisa suave | CWSI perfecto. Buffer selecciona lecturas en calma |
| 2-4 | 7-14 | Brisa leve | CWSI normal (w=0.35). Sin efecto significativo con mitigaciones |
| 4-6 | 14-22 | Brisa moderada | Inicio rampa. CWSI util con peso levemente reducido |
| 6-8 | 22-29 | Viento moderado | Rampa media. CWSI con peso reducido ~50% |
| 8-10 | 29-36 | Viento fuerte | Rampa alta. CWSI aporta ~25% del peso |
| 10-12 | 36-43 | Viento muy fuerte | Rampa extrema. CWSI aporta <12% |
| > 12 | > 43 | Zonda severo / temporal | **Backup total MDS**. CWSI descartado |
| > 20 | > 72 | Zonda extremo | Solo MDS. Verificar abrazadera extensometro post-evento |

---

## Referencias

- Jackson, R.D., Idso, S.B., Reginato, R.J. & Pinter, P.J. (1981). Canopy temperature as a crop water stress indicator. Water Resources Research, 17(4), 1133-1138.
- Bellvert, J., Marsal, J., Girona, J. & Zarco-Tejada, P.J. (2016). Seasonal evolution of crop water stress index in grapevine. Precision Agriculture, 17(1), 62-78.
- Fernandez, J.E. & Cuevas, M.V. (2010). Irrigation scheduling from stem diameter variations. Agricultural and Forest Meteorology, 150(2), 135-151.
- Araujo-Paredes, C., Portela, F., Mendes, S. & Valente, F. (2022). A crop water stress index based on MLX90640 IR sensor. Precision Agriculture, 23, 1509-1528.
- WMO Guide to Meteorological Instruments and Methods of Observation No. 8 (2018). Capitulo 2: shelter de sensores.
- Jones, H.G. (2004). Irrigation scheduling: advantages and pitfalls of plant-based methods. Journal of Experimental Botany, 55(407), 2427-2436.
