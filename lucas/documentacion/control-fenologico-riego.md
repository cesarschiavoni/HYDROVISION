# Control Fenológico del Riego — HydroVision AG

## Resumen

El sistema inhibe automáticamente la activación del solenoide durante los periodos de
reposo/dormancia del cultivo. La decisión se toma en **tres niveles** (nodo, backend, dashboard)
para garantizar que no se riegue cuando es contraproducente.

Regar en dormancia favorece enfermedades fúngicas (Botrytis, oidio) y retrasa la
lignificación del sarmiento, reduciendo la resistencia a heladas (Keller 2010, Chapter 4).

---

## Tabla de periodos de riego por variedad

Basado en Ky (coeficiente de sensibilidad al rendimiento) de FAO-33 (Doorenbos & Kassam 1979).
Riego inhibido cuando **Ky ≤ 0.15**.

### Vid

| Mes | Malbec | Cabernet | Bonarda | Syrah | Etapa | Riego |
|-----|--------|----------|---------|-------|-------|-------|
| Ago | 0.20 | 0.20 | 0.20 | 0.20 | Brotación | Permitido |
| Sep | 0.20 | 0.20 | 0.20 | 0.20 | Brotación | Permitido |
| Oct | 0.70 | 0.70 | 0.70 | 0.70 | Desarrollo vegetativo | Permitido |
| Nov | 0.85 | 0.85 | 0.85 | 0.85 | Floración/cuaje | Permitido (CRITICO) |
| Dic | 0.85 | 0.85 | 0.85 | 0.85 | Floración/cuaje | Permitido (CRITICO) |
| Ene | 0.85 | 0.85 | 0.85 | 0.85 | Envero | Permitido |
| Feb | 0.40 | 0.85 | 0.40 | 0.40 | Maduración/vendimia | Permitido (RDI) |
| Mar | 0.40 | 0.40 | 0.40 | 0.40 | Vendimia | Permitido (RDI) |
| **Abr** | **0.10** | 0.40 | **0.10** | **0.10** | Reposo/vendimia Cab | **INHIBIDO** (excepto Cab) |
| **May** | **0.10** | **0.10** | **0.10** | **0.10** | Reposo | **INHIBIDO** |
| **Jun** | **0.10** | **0.10** | **0.10** | **0.10** | Dormancia | **INHIBIDO** |
| **Jul** | **0.10** | **0.10** | **0.10** | **0.10** | Dormancia | **INHIBIDO** |

### Olivo

| Mes | Ky | Etapa | Riego |
|-----|-----|-------|-------|
| Jun-Jul | 0.20 | Post-cosecha/reposo | Permitido (Ky > 0.15) |
| Ago-Sep | 0.20 | Brotación | Permitido |
| Oct-Nov | 0.65 | Floración/cuaje | Permitido (CRITICO) |
| Dic-Feb | 0.40 | Endurecimiento carozo | Permitido (RDI admite deficit) |
| Mar-May | 0.55 | Maduración/cosecha | Permitido |

> El olivo nunca entra en inhibición automática (Ky mínimo = 0.20 > 0.15).

### Cerezo

| Mes | Ky | Etapa | Riego |
|-----|-----|-------|-------|
| **May-Jul** | **0.10** | Dormancia | **INHIBIDO** |
| Ago | 0.20 | Pre-floración | Permitido |
| Sep-Oct | 1.10 | Floración/cuaje | Permitido (MUY CRITICO) |
| Nov-Ene | 0.70 | Crecimiento fruto | Permitido |
| Feb-Abr | 0.30 | Post-cosecha | Permitido |

---

## Implementación — Nivel 1: Firmware del nodo (ESP32-S3)

### Archivo: `firmware/driver_solenoide.h`

La función `solenoide_evaluar()` recibe el estadio fenológico del motor GDD (`driver_gdd.h`)
y lo evalúa como **Protección 0** (antes de cualquier otra decisión):

```cpp
// Protección 0: inhibir en dormancia y post-cosecha
if (estadio == FENOL_DORMANCIA || estadio == FENOL_POST_COSECHA) {
    if (rtc_solenoide_activo) _solenoide_cerrar("reposo");
    st.reason = "reposo";
    return st;
}
```

**Cadena de protecciones del solenoide (en orden de prioridad):**

| # | Protección | Razón reportada | Efecto |
|---|-----------|----------------|--------|
| 0 | Dormancia/post-cosecha | `reposo` | Cierra si estaba abierto, no permite abrir |
| 1 | Lluvia activa | `lluvia` | Cierra si estaba abierto |
| 2 | Fuera de ventana horaria | `fuera_ventana` | Solo riega entre 06:00-22:00 |
| 3 | Duración máxima (anti-fuga) | `max_ciclos` | 8 ciclos × 15 min = 120 min max |
| 4 | HSI con histéresis | `hsi_alto` / `hsi_bajo` | Umbral dinámico por estadio |

### Umbrales HSI dinámicos por estadio

En lugar de un umbral fijo (`RIEGO_HSI_ACTIVAR = 0.30`), el firmware ahora usa
`CWSI_UMBRAL_POR_ESTADIO[]` de `driver_gdd.h`:

| Estadio | Umbral activar | Umbral desactivar | Sensibilidad |
|---------|---------------|-------------------|-------------|
| Dormancia | 0.90 | 0.80 | Inhibido (nunca alcanza) |
| Brotación | 0.35 | 0.25 | Alta |
| Floración | 0.30 | 0.20 | Muy alta (etapa crítica) |
| Cuaje | 0.35 | 0.25 | Alta |
| Crecimiento fruto | 0.50 | 0.40 | Media (RDI tolerable) |
| Envero | 0.60 | 0.50 | Baja (RDI intencional) |
| Maduración | 0.65 | 0.55 | Baja |
| Post-cosecha | 0.85 | 0.75 | Inhibido (casi nunca alcanza) |

Histéresis = umbral_activar - 0.10 para evitar ciclos rápidos ON/OFF.

### Sleep adaptativo

En dormancia y post-cosecha, el nodo duerme **6 horas** en vez de 15 minutos
(definido en `SLEEP_ESTADIO[]` de `driver_gdd.h`). Esto extiende la autonomía
de batería ~20x durante el invierno.

---

## Implementación — Nivel 2: Backend FastAPI

### Archivo: `mvc/app.py`

#### Función `_zona_en_reposo(zona_id)`

Consulta la fenología de la zona (varietal + mes actual) y retorna `True` si Ky ≤ 0.15.

#### Endpoint `POST /api/irrigate/{node_id}` (override manual)

Si la zona está en reposo y el riego está apagado, retorna:
```json
{
  "status": "blocked",
  "reason": "reposo",
  "detail": "La variedad está en reposo/dormancia. Regar en este periodo es contraproducente."
}
```
Solo permite **apagar** un riego que ya estaba encendido (por seguridad).

#### Endpoint `POST /ingest` (reporte autónomo del nodo)

Si el nodo reporta `solenoid.active = true` y la zona está en reposo, el backend:
1. Fuerza `_NODE_IRRIGATION[node_id] = False` en memoria
2. Retorna un comando de apagado:
```json
{
  "status": "ok",
  "command": {"irrigate": false, "reason": "reposo_fenologico"}
}
```
En TRL 5+ este comando se envía al nodo vía MQTT/LoRa.

#### Simulación (`_sim_tick`)

Si el riego está activo en una zona en reposo, se apaga automáticamente y no se
aplica `_IRRIG_RATE` al balance hídrico.

---

## Implementación — Nivel 3: Dashboard

### Archivo: `mvc/templates/dashboard.html`

- **Badge "Reposo"** (gris) con tooltip explicativo en cada card de zona
- **Botón de riego deshabilitado** con texto "Riego inhibido (reposo)"
- **`sugerir_riego = False`** siempre en zonas en reposo (aunque CWSI > umbral)
- Si el usuario intenta activar riego manualmente, recibe un `alert()` con la explicación

---

## Datos Sentinel-2 reales — Modelo físico CWSI

Para zonas sin nodo, el backend estima CWSI desde bandas Sentinel-2 reales
(Microsoft Planetary Computer, sin API key):

| Indicador | Rango | Interpretación |
|-----------|-------|----------------|
| NDVI < 0.12 | Suelo desnudo | CWSI = null (sin cobertura) |
| NDVI 0.12-0.25 | Viñedo baja cobertura (pixel mixto) | CWSI atenuado (veg_factor 0.5-1.0) |
| NDVI 0.25-0.45 | Viñedo normal en espaldera | CWSI = 0.45 - 1.0 × NDWI |
| NDVI > 0.45 | Cobertura densa | CWSI pleno |

Ajustes: VPD (+0.06 por kPa sobre 1.5) y cobertura vegetal.

En abril (post-vendimia), NDVI típico = 0.11-0.19 (viñedo con hojas senescentes).
El sistema muestra "Sin cobertura vegetal" o CWSI bajo con fuente "Sentinel-2 real".

---

## Referencias

- Doorenbos & Kassam (1979). FAO Irrigation and Drainage Paper 33.
- Fereres & Soriano (2007). Deficit irrigation for reducing agricultural water use. J. Exp. Bot. 58:147.
- Bellvert et al. (2015). Mapping crop water stress index in a 'Pinot-noir' vineyard. Precision Agriculture 16(4).
- González-Dugo et al. (2013). Using high-resolution hyperspectral and thermal airborne imagery. Remote Sensing 5(3).
- Keller (2010). The Science of Grapevines: Anatomy and Physiology. Chapter 4: Water relations.
- García de Cortázar-Atauri et al. (2009). Grapevine phenology models. Int. J. Biometeorol.
- Schultz (2003). Differences in hydraulic architecture account for near-isohydric and anisohydric behaviour. Plant Cell & Env.
