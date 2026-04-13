# Payload JSON v1 — Protocolo Nodo ↔ Backend
## HydroVision AG · TRL 4

> **Fuente:** `lucas/firmware/nodo_main.ino` líneas 421-463
> **Topic MQTT:** `hydrovision/{node_id}/telemetry`
> **Tamaño máximo:** 700 bytes (buffer firmware)
> **Frecuencia:** 1 payload por ciclo de medición (~15 min en modo normal, configurable)

---

## Estructura del payload

```json
{
  "v": 1,
  "node_id": "HV-A1B2C3D4",
  "ts": 1712678400,
  "cycle": 142,
  "env": {
    "t_air": 28.5,
    "rh": 45.2,
    "wind_ms": 2.3,
    "rain_mm": 0.0,
    "rad_wm2": 850
  },
  "thermal": {
    "tc_mean": 31.24,
    "tc_max": 33.10,
    "tc_wet": 25.80,
    "tc_dry": 38.50,
    "cwsi": 0.425,
    "valid_pixels": 180,
    "n_frames": 5
  },
  "dendro": {
    "mds_mm": 0.0832,
    "mds_norm": 0.620
  },
  "hsi": {
    "value": 0.523,
    "w_cwsi": 0.35,
    "w_mds": 0.65,
    "wind_override": false
  },
  "gps": {
    "lat": -31.201345,
    "lon": -64.092678
  },
  "bat_pct": 87,
  "pm2_5": 12,
  "calidad_captura": "ok",
  "gdd": {
    "acum": 1245.5,
    "estadio": "envero"
  },
  "iso_nodo": 92,
  "solenoid": {
    "canal": 1,
    "active": false,
    "reason": "off",
    "ciclos_activo": 0
  },
  "varietal": "malbec"
}
```

---

## Campos — Referencia

### Raíz

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `v` | int | Versión del protocolo (siempre 1) |
| `node_id` | string | Identificador único derivado de MAC address ESP32-S3 |
| `ts` | uint32 | Epoch seconds (UTC) del momento de medición |
| `cycle` | uint32 | Número de ciclo desde último boot (almacenado en RTC memory) |
| `bat_pct` | uint8 | Porcentaje de batería (0-100) |
| `pm2_5` | uint16 | Partículas PM2.5 en µg/m³ (sensor PMS5003) |
| `calidad_captura` | string | `ok` / `fumigacion` / `lluvia` / `nocturno` / `lente_sucio` |
| `iso_nodo` | uint8 | Diagnóstico de limpieza del lente (0-100, <80 = limpiar) |
| `varietal` | string | Cultivo/variedad configurado en firmware |

### env — Ambiente

| Campo | Tipo | Unidad | Sensor |
|-------|------|--------|--------|
| `t_air` | float | °C | SHT31 |
| `rh` | float | % | SHT31 |
| `wind_ms` | float | m/s | Anemómetro RS485 |
| `rain_mm` | float | mm | Pluviómetro balancín |
| `rad_wm2` | float | W/m² | Piranómetro BPW34 |

### thermal — Cámara térmica

| Campo | Tipo | Unidad | Descripción |
|-------|------|--------|-------------|
| `tc_mean` | float | °C | Temperatura media canopeo (filtro P20-P75 píxeles foliares) |
| `tc_max` | float | °C | Temperatura máxima canopeo |
| `tc_wet` | float | °C | Temperatura referencia húmeda (Wet Ref o modelo) |
| `tc_dry` | float | °C | Temperatura referencia seca (Dry Ref o modelo) |
| `cwsi` | float | 0-1 | Crop Water Stress Index = (Tc-Twet)/(Tdry-Twet) |
| `valid_pixels` | uint16 | count | Píxeles clasificados como foliares en frame 32×24 |
| `n_frames` | uint8 | count | Frames fusionados (gimbal multi-ángulo) |

### dendro — Dendrometría de tronco

| Campo | Tipo | Unidad | Descripción |
|-------|------|--------|-------------|
| `mds_mm` | float | mm | Maximum Daily Shrinkage — contracción diaria del tronco |
| `mds_norm` | float | 0-1 | MDS normalizado por rango de la variedad |

### hsi — Hydric Stress Index (fusión)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `value` | float | HSI = w_cwsi × CWSI + w_mds × MDS_norm |
| `w_cwsi` | float | Peso CWSI (0.35 en condiciones normales) |
| `w_mds` | float | Peso MDS (0.65 en condiciones normales) |
| `wind_override` | bool | true si viento ≥12 m/s (43 km/h) → w_cwsi=0, w_mds=1 (CWSI no confiable). Entre 4-12 m/s (14-43 km/h) el peso se reduce gradualmente (rampa lineal) |

**Detalle de la rampa gradual de pesos (campo `w_cwsi` / `w_mds`):**

El sistema NO usa un cutoff binario. El peso del CWSI se reduce linealmente entre 4-12 m/s gracias a las mitigaciones físicas del nodo (orientación sotavento, tubo colimador IR, shelter SHT31, termopar foliar) que extienden el rango útil del CWSI:

| Viento (anemómetro) | km/h | w_cwsi | w_mds | wind_override |
|---|---|---|---|---|
| ≤4 m/s | ≤14 | 0.35 | 0.65 | false |
| 6 m/s | 22 | 0.26 | 0.74 | false |
| 8 m/s | 29 | 0.18 | 0.82 | false |
| 10 m/s | 36 | 0.09 | 0.91 | false |
| ≥12 m/s | ≥43 | 0.00 | 1.00 | true |

Fórmula: `w_cwsi = 0.35 × (12.0 - wind_ms) / (12.0 - 4.0)` clampeado a [0.0, 0.35]. `w_mds = 1.0 - w_cwsi`.

El campo `wind_override` solo es `true` cuando w_cwsi = 0.00 (backup total MDS). En la zona de transición (4-12 m/s), `wind_override` es `false` pero los pesos reflejan la reducción gradual.

### gdd — Motor fenológico

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `acum` | float | Grados-día acumulados desde brotación |
| `estadio` | string | Estadio fenológico actual (10 estadios Malbec) |

### solenoid — Control de riego

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `canal` | uint8 | Canal del solenoide asignado al nodo |
| `active` | bool | true si el solenoide está activo ahora |
| `reason` | string | `hsi` (automático) / `manual` / `off` |
| `ciclos_activo` | uint32 | Ciclos consecutivos con solenoide activo |

---

## Topics MQTT

| Topic | Dirección | Cuándo |
|-------|-----------|--------|
| `hydrovision/{node_id}/telemetry` | Nodo → Backend | Cada ciclo de medición |
| `hydrovision/{node_id}/alert` | Nodo → Backend | Cuando HSI >= umbral dinámico por estadio |
| `hydrovision/{node_id}/status` | Nodo → Backend | Cada N ciclos (heartbeat) |

---

## Valores de `calidad_captura`

| Valor | Significado | Acción backend |
|-------|-------------|----------------|
| `ok` | Captura válida | Procesar normalmente |
| `fumigacion` | PM2.5 > 200 µg/m³ detectado | Descartar frame térmico (aerosol interfiere IR) |
| `lluvia` | PM2.5 > 200 + humedad > 95% | Descartar frame térmico + MDS (agua en sensor) |
| `nocturno` | Sin radiación solar | CWSI no calculable (solo MDS y env) |
| `lente_sucio` | iso_nodo < 80 | Alertar mantenimiento, frame degradado |

---

## Estadios fenológicos (Malbec)

| Estadio | GDD aprox | CWSI umbral |
|---------|-----------|-------------|
| dormancia | 0 | — |
| brotacion | 0 (detección por convergencia térmica) | — |
| hojas_expandidas | 150 | 0.40 |
| floracion | 350 | 0.35 |
| cuajado | 500 | 0.35 |
| envero | 900 | 0.30 |
| maduracion | 1200 | 0.25 |
| cosecha | 1600 | — |
| post_cosecha | — | — |
| pre_dormancia | — | — |
