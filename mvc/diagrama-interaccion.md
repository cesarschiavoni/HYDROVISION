# Diagrama de interacción — HydroVision AG TRL 4
## Flujo completo: nodo → MVC → browser → nodo Tier 2 (riego integrado)

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  CAMPO — Demo Colonia Caroya (campo configurable desde /admin)               ║
║                                                                              ║
║   ESP32-S3  [×N nodos]                                                      ║
║   ─────────────────────────────────                                          ║
║   MLX90640  → temperatura canopeo                                            ║
║   SHT31     → T° aire / HR                                                  ║
║   ADS1231   → dendrómetro (MDS)                                              ║
║   GPS       → posición                                                       ║
║                                                                              ║
║   Calcula: cwsi · hsi · mds_mm                                               ║
║   Tier 1: solo sensor · Tier 2-3: GPIO → SSR → solenoide Rain Bird          ║
╚════════════╦═══════════════════════════════════════╦════════════════════════╝
             │ payload JSON (LoRa TX)                │ orden riego (LoRa RX)
             ▼                                       │ {zona: N, active: bool}
╔══════════════════════════╗                         │
║  COMUNICACIÓN            ║                         │
║                          ║                         │
║  LoRa SX1276 915 MHz     ║                         │
║        ↓                 ║                         │
║  Gateway RAK7268         ║─────────────────────────┘
║        ↓         ↑       ║  (bidireccional)
║  MQTT (4G Teltonika RUT241 / Starlink Mini X)    ║
╚════════════╦═════════════╝
             │ HTTP POST /ingest
             ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║  CONTROLLER — app.py (FastAPI)                                               ║
║                                                                              ║
║  POST /ingest               ←── nodo vía MQTT/Gateway                       ║
║    └── valida calidad_captura == "ok"                                        ║
║    └── persiste en Telemetry                                                 ║
║    └── auto-crea NodeConfig si es nodo nuevo                                 ║
║                                                                              ║
║  GET  /api/status           ←── browser (cada 30 s)                         ║
║    └── última lectura por nodo                                               ║
║    └── calcula stress: Bajo / Medio / Alto                                   ║
║                                                                              ║
║  GET  /api/history/{node_id} ←── browser (click fila)                       ║
║    └── CWSI · HSI últimas 48 h                                               ║
║                                                                              ║
║  POST /api/irrigate/{zona}  ←── browser (toggle)                            ║
║    └── toggle zona 1–5                                                       ║
║    └── persiste en IrrigationLog                                             ║
║    └── [TRL 5] publica MQTT → Gateway → LoRa → Controlador riego            ║
║                                                                              ║
║  GET  /api/zones            ←── browser (init + refresh)                    ║
║  GET  /                     ←── browser → dashboard.html                    ║
║  GET  /admin                ←── browser → admin.html                        ║
╚════════════╦══════════════════════════════╦═══════════════════════════════════╝
             │ SQLAlchemy ORM               │ HTML directo (Path.read_text)
             ▼                              ▼
╔══════════════════════════╗   ╔═════════════════════════════════════════════╗
║  MODEL — models.py       ║   ║  VIEW — dashboard.html / admin.html        ║
║                          ║   ║                                             ║
║  Telemetry               ║   ║  dashboard.html                             ║
║    node_id               ║   ║    Cards: CWSI prom · nodos · zonas activas ║
║    cwsi / hsi / mds      ║   ║    Tabla nodos con siglas y tooltips        ║
║    t_air / rh / wind     ║   ║    Control zonas: toggle on/off             ║
║    bat_pct / calidad     ║   ║    Mapa Leaflet: zonas coloreadas por CWSI  ║
║    origen (real/sim)     ║   ║    Gráfico CWSI/HSI 48 h por nodo          ║
║    lat / lon             ║   ║    Auto-refresh 30 s                        ║
║         ↕                ║   ║                                             ║
║  IrrigationLog           ║   ║  admin.html                                 ║
║    zona / active / ts    ║   ║    Layout 2 col: panel + mapa full          ║
║         ↕                ║   ║    Dibujar zonas: rectángulo / polígono     ║
║  ZoneConfig              ║   ║    Editar zona: handles arrastrables        ║
║    id / name             ║   ║    Nodos: nombre + zona asignada            ║
║    lat / lon (centroide) ║   ║    Config campo: umbrales CWSI              ║
║    sw/ne bounds          ║   ║    Alpine.js · Leaflet.draw · Tailwind      ║
║    vertices (polígono)   ║   ║                                             ║
║    solenoid ← zona tiene ║   ╚═════════════════════════════════════════════╝
║      el N° de canal del  ║
║      controlador Rain Bird║                    │ HTTP
║         ↕                ║                    ▼
║  NodeConfig              ║        ╔══════════════════════╗
║    node_id / name        ║        ║  BROWSER             ║
║    zona_id               ║        ║  localhost:8000      ║
║         ↕                ║        ║                      ║
║  AppConfig               ║        ║  César /             ║
║    field_name/varietal   ║        ║  Evaluador ANPCyT    ║
║    cwsi_medio / alto     ║        ╚══════════════════════╝
║         ↕                ║
║  hydrovision.db (SQLite) ║
╚══════════════════════════╝


══════════════════════════════════════════════════════════════════════
  ARQUITECTURA DE RIEGO — DECISIÓN DE DISEÑO
══════════════════════════════════════════════════════════════════════

  Tier 1: el NODO es exclusivamente sensor. No actúa sobre ningún solenoide.
  Tier 2-3: el NODO integra control de riego (GPIO → SSR relay → solenoide Rain Bird).
             No existe controlador de riego independiente; el nodo mismo abre/cierra.

  El SOLENOIDE pertenece a la ZONA:
    - Zona 1 → nodo Tier 2-3 zona 1 → SSR → solenoide 1 → sector Norte
    - Zona 2 → nodo Tier 2-3 zona 2 → SSR → solenoide 2 → sector Centro-Norte
    - ...

  ~~DEPRECATED — CONTROLADOR DE RIEGO INDEPENDIENTE (diseño anterior):~~
  ~~El siguiente diseño fue reemplazado por la integración directa en nodos Tier 2-3.~~
    - ~~Hardware:  ESP32 + módulo LoRa SX1276 + 5 relés + fuente 24V~~
    - ~~Firmware:  escucha mensajes LoRa del Gateway~~
    - ~~Protocolo: {zona: N, active: bool, ts: unix}~~
    - En TRL 4:  la activación queda registrada en IrrigationLog (simulada)
    - En TRL 5+: el nodo Tier 2-3 recibe comando MQTT → Gateway → LoRa → nodo → SSR → solenoide

  Flujo de activación (TRL 5+):
    usuario click "Activar Zona 2"
      → POST /api/irrigate/2
        → IrrigationLog INSERT (zona=2, active=true)
        → MQTT publish: topic="hydrovision/irrigate", payload={zona:2, active:true}
          → Gateway RAK7268
            → LoRa 915 MHz
              → Nodo Tier 2 (zona 2)
                → GPIO → SSR cierra → solenoide 2 abre → agua fluye


══════════════════════════════════════════════════════════════════════
  ESTIMACIÓN CWSI POR ZONA — FUSIÓN NODO-SATÉLITE
══════════════════════════════════════════════════════════════════════

  ¿Cómo se determina el CWSI de cada zona de riego?

  CASO 1 — Zona con nodo dentro de sus límites:
    El nodo mide CWSI directamente (ground truth).
    fuente: "nodo:{node_id}"

  CASO 2 — Zona sin nodo (fusión nodo-satélite):
    No se puede medir CWSI directamente, pero sí se puede estimar
    usando la correlación entre el nodo y Sentinel-2.

    FLUJO (5 pasos):

    ┌───────────────────────────────────────────────────────────────┐
    │ PASO 1 — NODO (ground truth)                                 │
    │   El nodo mide CWSI = 0.45 en su posición GPS.               │
    │   También mide T°aire y HR → calcula VPD = 1.9 kPa.          │
    └───────────────────────────┬───────────────────────────────────┘
                                │
    ┌───────────────────────────▼───────────────────────────────────┐
    │ PASO 2 — SENTINEL-2 EN EL PUNTO DEL NODO                    │
    │   Sentinel-2 captura una imagen cada 5 días (10m/px).         │
    │   Se extraen las bandas espectrales en el píxel del nodo:     │
    │     NDWI = (B8A − B11) / (B8A + B11)  contenido hídrico      │
    │     NDVI = (B8  − B4)  / (B8  + B4)   vigor vegetativo       │
    │     NDRE = (B8A − B4)  / (B8A + B4)   estrés temprano        │
    │   Resultado: par (CWSI=0.45, NDWI=0.12, NDVI=0.58, VPD=1.9) │
    │                                                               │
    │   TRL 4 demo: features S2 sintéticas consistentes con CWSI    │
    │   TRL 5+: bandas reales de GEE (extraer_bandas_punto)         │
    └───────────────────────────┬───────────────────────────────────┘
                                │  se acumulan ≥ 10 pares
    ┌───────────────────────────▼───────────────────────────────────┐
    │ PASO 3 — CALIBRACIÓN DEL MODELO                              │
    │   Con ≥ 10 pares (CWSI_nodo, NDWI, NDVI, NDRE, VPD),        │
    │   se ajusta una regresión polinomial grado 2 (HuberRegressor):│
    │                                                               │
    │   CWSI = f(NDWI, NDVI, NDRE, VPD)                            │
    │                                                               │
    │   El modelo aprende: "cuando NDWI es bajo y VPD es alto,     │
    │   el CWSI es alto (la planta está estresada)".                │
    │   R² típico ≈ 0.95   MAE ≈ 0.04 unidades CWSI               │
    │                                                               │
    │   Implementación: CWSINDWICorrelationModel (sentinel2_fusion.py)│
    └───────────────────────────┬───────────────────────────────────┘
                                │  modelo calibrado
    ┌───────────────────────────▼───────────────────────────────────┐
    │ PASO 4 — SENTINEL-2 EN LA ZONA (sin nodo)                   │
    │   La zona tiene su PROPIA firma espectral (sus propios       │
    │   píxeles S2), independiente del nodo:                        │
    │     NDWI_zona = 0.28  (por ej. más agua que el punto del nodo)│
    │     NDVI_zona = 0.65  (más vigor que el punto del nodo)       │
    │   El VPD del día viene de los nodos (dato meteorológico).     │
    │                                                               │
    │   TRL 4 demo: features S2 sintéticas por zona_id (seed fijo) │
    │   TRL 5+: bandas reales de GEE (polígono de la zona)          │
    └───────────────────────────┬───────────────────────────────────┘
                                │
    ┌───────────────────────────▼───────────────────────────────────┐
    │ PASO 5 — PREDICCIÓN                                          │
    │   CWSI_zona = modelo( NDWI_zona, NDVI_zona, NDRE_zona, VPD ) │
    │                                                               │
    │   → El resultado es el estrés PROPIO de la zona.              │
    │   → El nodo solo calibró la curva — NO ancla el resultado.    │
    │   → Zonas con suelo más seco → NDWI bajo → CWSI alto.        │
    │   → Zonas con suelo húmedo → NDWI alto → CWSI bajo.          │
    │                                                               │
    │   fuente: "satelite_s2"                                       │
    └───────────────────────────────────────────────────────────────┘

  CASO 3 — Sin nodos activos:
    No hay datos para calibrar ni estimar.
    fuente: "sin datos"

  Prioridad de selección (GET /api/zones → campo "fuente"):
    1. Nodo asignado (NodeConfig.zona_id)      → "nodo:{id}"
    2. Nodo dentro de los bounds de la zona     → "nodo:{id}"
    3. Hay nodos activos, modelo calibrado      → "satelite_s2"
    4. Sin nodos                                → "sin datos"


══════════════════════════════════════════════════════════════════════
  MÓDULOS EXTERNOS (integración futura / paralela)
══════════════════════════════════════════════════════════════════════

  investigador/02_modelo/
    PINN (pinn_model.py)     → entrena en RTX 3070 → INT8 → firmware ESP32
    U-Net (segmentación)     → máscara canopeo → firmware ESP32

  cesar/
    pipeline_satelital.py   → Sentinel-2 + ERA5 → mapa CWSI campo
    sentinel2_fusion.py     → CWSINDWICorrelationModel (calibración y predicción)
                              usado por app.py (_SatelliteFusionService) para
                              estimar CWSI en zonas sin nodo


══════════════════════════════════════════════════════════════════════
  RESUMEN DE RESPONSABILIDADES
══════════════════════════════════════════════════════════════════════

  Rol              Componente            Responsabilidad
  ───────────────  ────────────────────  ──────────────────────────────────
  Sensor           ESP32-S3 + sensores   medir · calcular · transmitir
  Transporte       LoRa + RAK7268        llevar datos al servidor y órdenes al campo
  Controller       app.py (FastAPI)      validar · persistir · calcular · responder
  Model            models.py (SQLAlchemy) persistir telemetría · zonas · logs
  View             dashboard/admin.html  visualizar · configurar · controlar
  Actuador         Nodo Tier 2-3         abrir/cerrar solenoide via GPIO→SSR
```

---

## Modelo fenológico GDD — determinación automática de Ky FAO-56

### Principio

El factor Ky (Doorenbos & Kassam 1979, FAO Paper 33) cuantifica la sensibilidad de un cultivo al déficit hídrico en relación con la reducción de rendimiento:

```
(1 - Ya/Ym) = Ky × (1 - ETa/ETc)
```

Ky varía con la etapa fenológica: en floración es alto (mayor penalización por estrés), en brotación y madurez post-cuaje es bajo. Por ello **no puede ser un valor fijo configurado por el usuario**.

### Responsabilidades

```
  El NODO transmite t_air y t_air solamente — no calcula fenología.
  El SERVIDOR acumula t_air, calcula GDD y determina la etapa.

  Nodo             → t_air [°C] en cada transmisión
  app.py (servidor) → consulta histórico 365 días
                    → calcula GDD acumulados
                    → determina etapa fenológica
                    → devuelve ky, etapa, metodo en /api/report/
```

### Algoritmo GDD (hemisferio sur)

```
  1. Consultar t_air de los últimos 365 días para la zona.
     (Nodos dentro de la zona; fallback: todos los nodos del campo)

  2. Detectar inicio de temporada:
       pivot = 1° de julio (día más frío del año calendario en HS)
       Para cada día desde pivot hasta hoy:
         si T_media_día ≥ T_base → inicio_temporada = ese día; PARAR
       Si no se encontró → inicio = 1° de julio

  3. Acumular GDD desde inicio_temporada:
       para cada día desde inicio hasta hoy:
         GDD += max(0,  T_media_día − T_base)

  4. Mapear GDD → etapa fenológica → Ky:
       buscar la etapa donde gdd_inicio ≤ GDD < gdd_fin
       devolver (ky, nombre_etapa)
```

### Cadena de fallback

```
  ¿Hay ≥ 14 días de t_air para esta zona?
    SÍ → GDD model   → metodo = "gdd"
    NO  → ¿se conoce el mes del año?
            SÍ → tabla _KY_FAO56 por mes   → metodo = "mes"
            NO  → Ky = 0.85 (default alto) → metodo = "default"
```

### T_base por variedad

| Variedad / grupo              | T_base (°C) | Referencia         |
|-------------------------------|:-----------:|--------------------|
| Vid (todas las variedades)    | 10.0        | FAO-33, Winkler     |
| Olivo                         | 12.5        | Rallo & Cuevas 1999 |
| Cerezo / Guindo               |  4.5        | Richardson 1974     |
| Pistacho                      | 10.0        | Ferguson et al.     |
| Arándano                      |  7.0        | Spiers 1978         |
| Nogal                         | 10.0        | Polito & Pinney     |
| Citrus (naranja, limón, man.) | 13.0        | García-Tejero 2011  |

### Ejemplo: umbrales GDD — Vid Malbec

| Etapa                | GDD inicio | GDD fin | Ky   |
|----------------------|:----------:|:-------:|:----:|
| Brotación            |      0     |   150   | 0.20 |
| Desarrollo vegetativo|    150     |   450   | 0.70 |
| Floración / cuaje    |    450     |   750   | 0.85 |
| Envero / maduración  |    750     |  1300   | 0.85 |
| Vendimia             |   1300     |  1600   | 0.40 |
| Reposo               |   1600     |  9999   | 0.10 |

### Campos expuestos por la API

Los endpoints `/api/report/zone-performance` y `/api/report/summary` incluyen:

```json
"fenologia": {
  "etapa":   "floracion_cuaje",
  "gdd":     512.3,
  "ky":      0.85,
  "metodo":  "gdd",
  "n_dias":  38
}
```

| Campo    | Descripción |
|----------|-------------|
| `etapa`  | nombre de la etapa fenológica activa |
| `gdd`    | GDD acumulados desde inicio de temporada |
| `ky`     | factor de respuesta Ky FAO-56 correspondiente |
| `metodo` | `"gdd"` / `"mes"` / `"default"` — indica cómo se obtuvo |
| `n_dias` | días de datos t_air disponibles para el cálculo |

---

## Homogeneidad del lote — criterio operativo

| Métrica | Fuente | Homogéneo | Moderado | Heterogéneo |
|---------|--------|-----------|----------|-------------|
| **CV NDVI** (Sentinel-2, plena hoja GDD 600–1000) | `pipeline_satelital.py` | < 15% | 15–25% | > 25% |
| **CV CWSI** entre nodos (tiempo real) | Dashboard, calculado de `/api/status` | < 15% | 15–25% | > 25% |

**Implicancias para densidad de nodos:**
- Homogéneo (CV < 15%): 1 nodo / 10–20 ha — la fusión nodo-satélite es confiable en todo el lote
- Moderado (CV 15–25%): 1 nodo / 5–10 ha — revisar zonas con CWSI outlier
- Heterogéneo (CV > 25%): 1 nodo / 1–2 ha — riego diferencial obligatorio, cada zona necesita su propia calibración (suelos distintos → correlaciones CWSI↔NDWI distintas)

**CV NDVI** = diagnóstico estructural del lote (evaluar al inicio de campaña, no cambia a corto plazo).
**CV CWSI** = diagnóstico operativo diario (cambia con el riego y las condiciones meteorológicas).

---

## Contratos de datos

| Endpoint | Método | Entrada | Salida |
|----------|--------|---------|--------|
| `/ingest` | POST | payload JSON nodo v1 | `{status, node_id}` |
| `/api/status` | GET | — | `[{node_id, cwsi, hsi, stress, hace_min, ...}]` |
| `/api/history/{id}` | GET | — | `[{ts, cwsi, hsi}]` últimas 48 h |
| `/api/irrigate/{zona}` | POST | — | `{zona, active}` |
| `/api/zones` | GET | — | `[{id, name, active, cwsi, fuente, solenoid, ...}]` |
| `/api/admin/zones` | GET/POST/PUT/DELETE | ZoneIn JSON | zona o lista |
| `/api/admin/nodes` | GET | — | nodos con telemetría |
| `/api/admin/nodes/{id}` | PUT | `{name, zona_id}` | `{status}` |
| `/api/admin/config` | GET/PUT | ConfigIn JSON | configuración campo |

## Payload nodo v1

```json
{
  "v": 1,
  "node_id": "ESP32-A1B2C3",
  "ts": 1712345678,
  "cycle": 42,
  "env":     { "t_air": 28.5, "rh": 45.2, "wind_ms": 1.8, "rain_mm": 0.0 },
  "thermal": { "cwsi": 0.42, "calidad_captura": "ok" },
  "dendro":  { "mds_mm": 0.087 },
  "hsi":     { "value": 0.38 },
  "gps":     { "lat": -31.2012, "lon": -64.0927 },
  "bat_pct": 87,
  "pm2_5":   12,
  "calidad_captura": "ok"
}
```
