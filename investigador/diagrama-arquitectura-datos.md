# Arquitectura de Datos — HydroVision AG TRL 4
## Flujo completo: nodo de campo → modelos ML → mapa satelital

---

## 1. Diagrama de flujo de datos

```
╔══════════════════════════════════════════════════════════════════════╗
║  NODO DE CAMPO (ESP32-S3)  — cada 15 min                            ║
║                                                                      ║
║  MLX90640 → thermal[]     SHT31 → t_air, rh                        ║
║  ADS1231  → mds_mm        Anemómetro → wind_ms                     ║
║  PMS5003  → pm2_5         Pluviómetro → rain_mm                    ║
║  GPS      → lat, lon      RTC → ts                                  ║
║                                                                      ║
║  firmware/hsi.h → cwsi, mds_norm, hsi_value, w_cwsi, w_mds         ║
║  firmware/nodo_main.ino → calidad_captura ("ok"|"lluvia"|...)       ║
╚══════════════════════════════════════════════════════════════════════╝
                    |
                    | LoRa SX1276 915MHz
                    |
         ┌──────────▼──────────┐
         │  GATEWAY LoRaWAN    │
         │  RAK7268            │
         └──────────┬──────────┘
                    |
                    | MQTT sobre TCP/IP (4G Teltonika RUT241 / Starlink Mini X)
                    | topic: hydrovision/{node_id}/telemetry
                    |
╔═══════════════════▼════════════════════════════════════════════════╗
║  BACKEND — FastAPI mínima TRL 3-4 (César / Claude Code)           ║
║                                                                    ║
║  POST /ingest                                                      ║
║    ├── valida calidad_captura == "ok"  → descarta si no           ║
║    ├── persiste raw payload → PostgreSQL tabla telemetry          ║
║    └── publica evento → cola interna                              ║
║                                                                    ║
║  PostgreSQL                                                        ║
║    telemetry(node_id, ts, cwsi, hsi, mds_mm, t_air, rh,          ║
║              wind_ms, rain_mm, pm2_5, lat, lon, calidad)          ║
╚═══════════════════╦════════════════════════════════════════════════╝
                    ║
          ┌─────────╩──────────┐
          │                    │
          ▼                    ▼
╔══════════════════╗  ╔════════════════════════════════════════════╗
║  MÓDULOS HSI     ║  ║  PIPELINE SATELITAL (César)               ║
║  (Inv. Art. 32)  ║  ║  cesar/pipeline_satelital.py              ║
║                  ║  ║                                            ║
║  cwsi.py         ║  ║  1. procesar_payload(payload)             ║
║  dendrometry.py  ║  ║     └── calidad_captura == "ok"?          ║
║  hsi_fusion.py   ║  ║     └── extraer_bandas_punto() via GEE    ║
║  phenology.py    ║  ║     └── obtener_vpd_era5()                ║
║  alerts.py       ║  ║     └── Sentinel2Observation(             ║
║                  ║  ║           B4,B8,B8A,B11,B12,VPD,cwsi)    ║
║  input:          ║  ║     └── acumular par calibración          ║
║    telemetry row ║  ║                                            ║
║  output:         ║  ║  2. _recalibrar(node_id)                  ║
║    hsi_index     ║  ║     └── cuando ≥ 10 pares                 ║
║    stress_level  ║  ║     └── CWSINDWICorrelationModel          ║
║    alerts[]      ║  ║           .calibrate(obs)                 ║
║    phenostage    ║  ║                                            ║
╚══════════════════╝  ║  3. generar_mapa(fecha)                   ║
          |           ║     └── extraer_bandas_campo() via GEE    ║
          |           ║     └── Sentinel2Observation × N_pixels   ║
          |           ║     └── mejor_modelo.generate_field_map() ║
          |           ║     └── output: cwsi_mean, cwsi_p90,      ║
          |           ║           cwsi_all[], n_pixels_veg        ║
          |           ╚════════════════════╦═══════════════════════╝
          |                                |
          └──────────────┬─────────────────┘
                         |
╔════════════════════════▼═══════════════════════════════════════════╗
║  MODELOS ML — investigador/                                             ║
║                                                                    ║
║  01_datos/                                                         ║
║    synthetic_thermal_dataset.py  → 1.000.000 imgs sintéticas      ║
║    real_field_dataset/           → 680 frames Scholander-labeled  ║
║                                                                    ║
║  02_modelo/                                                        ║
║    unet_segmentation.py          → segmenta canopeo 32×24 px      ║
║      input:  thermal frame [1×120×160]  (upscaled MLX90640)       ║
║      output: mask foliar [120×160]      (píxeles válidos)         ║
║                                                                    ║
║    pinn_cwsi.py                  → predice CWSI con física        ║
║      input:  [tc_mean, tc_wet, tc_dry, t_air, vpd, wind,         ║
║               solar_rad, valid_pixels, mds_norm]                  ║
║      output: cwsi_pred ∈ [0,1]                                    ║
║      loss:   MSE + λ·physics_residual                             ║
║        physics: CWSI = (Tc - Tc_wet) / (Tc_dry - Tc_wet)        ║
║                                                                    ║
║  03_validacion/                                                    ║
║    validate_pinn.py              → MAE, RMSE vs ψ_stem Scholander ║
║    target: error CWSI < ±0.10                                     ║
╚════════════════════════════════════════════════════════════════════╝
                         |
                         | resultados validados
                         ▼
╔═══════════════════════════════════════════════════════════════════╗
║  OUTPUTS TRL 4                                                    ║
║                                                                    ║
║  mapa_{fecha}.json                                                ║
║    cwsi_mean, cwsi_std, cwsi_p90                                  ║
║    n_pixels_veg, n_pixels_total                                   ║
║    modelo_nodo, modelo_r2, vpd_dia                                ║
║                                                                    ║
║  dataset propietario                                              ║
║    680 frames Malbec Colonia Caroya + ψ_stem Scholander          ║
║    → insumo patente + publicación científica                      ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## 1b. Flujo inverso — comando de riego (servidor → campo)

```
BROWSER (dashboard.html)
  click "Activar riego" en nodo con solenoide
    → POST /api/irrigate/{node_id}
╔═══════════════════════════════════════════════════════════════════╗
║  BACKEND — FastAPI (app.py)                                       ║
║                                                                    ║
║  POST /api/irrigate/{node_id}                                     ║
║    ├── verifica NodeConfig.solenoid IS NOT NULL                   ║
║    ├── toggle _NODE_IRRIGATION[node_id]                           ║
║    ├── IrrigationLog INSERT (node_id, zona, active)               ║
║    └── [TRL 5+] MQTT publish                                      ║
║          topic:   hydrovision/{node_id}/command/irrigate          ║
║          payload: {node_id, solenoid, active: bool, ts: unix}     ║
╚═══════════════════════════════╦═══════════════════════════════════╝
                                ║ MQTT (4G / Starlink Mini X)
                         ┌──────▼──────┐
                         │  GATEWAY    │
                         │  RAK7268    │
                         └──────┬──────┘
                                │ LoRa SX1276 915 MHz (downlink)
                    ┌───────────▼───────────────────────┐
                    │  NODO TIER 2-3 (riego integrado)  │
                    │  ESP32-S3 + SSR integrado en nodo  │
                    │                                    │
                    │  Parsea {node_id, solenoid, active}│
                    │  GPIO → SSR → solenoide ON/OFF     │
                    └───────────┬───────────────────────┘
                                │ 24VAC
                    ┌───────────▼───────────────────────┐
                    │  Solenoide Rain Bird (canal N)     │
                    │  → válvula hidráulica abre/cierra  │
                    │  → agua fluye en zona del nodo     │
                    └───────────────────────────────────┘
```

**Nota TRL 4:** El control de riego es directo desde el nodo Tier 2 via GPIO → SSR → solenoide.
No existe controlador de riego independiente. La activación se registra en `IrrigationLog`.
El riego se controla por nodo (no por zona) — solo nodos Tier 2-3 con SSR pueden activar riego.

---

## 2. Contratos de datos entre módulos

### Payload JSON del nodo (entrada al sistema)

```python
payload = {
    "v": 1,
    "node_id": "HV-A4CF12B3E7",   # str — MAC ESP32
    "ts": 1743980400,               # int — Unix timestamp UTC
    "cycle": 1024,                  # int — contador de ciclos
    "env": {
        "t_air":   28.3,            # float °C
        "rh":      42.1,            # float %
        "wind_ms": 2.7,             # float m/s
        "rain_mm": 0.0              # float mm acumulado ciclo
    },
    "thermal": {
        "tc_mean":     31.2,        # float °C — temperatura media canopeo
        "tc_max":      34.8,        # float °C
        "tc_wet":      26.1,        # float °C — panel Wet Ref
        "tc_dry":      38.5,        # float °C — panel Dry Ref
        "cwsi":        0.47,        # float [0-1]
        "valid_pixels": 28          # int — píxeles foliares válidos
    },
    "dendro": {
        "mds_mm":   0.112,          # float mm — Maximum Daily Shrinkage
        "mds_norm": 0.224           # float [0-1] — normalizado vs baseline
    },
    "hsi": {
        "value":        0.313,      # float [0-1] — HydroVision Stress Index
        "w_cwsi":       0.35,       # float — peso térmico
        "w_mds":        0.65,       # float — peso dendrométrico
        "wind_override": False      # bool — True si viento >= 12 m/s (43 km/h) → w_cwsi=0 (rampa gradual 4-12 m/s)
    },
    "gps":    {"lat": -31.2018, "lon": -64.0927},
    "bat_pct": 82,                  # int %
    "pm2_5":   14,                  # int µg/m³
    "calidad_captura": "ok"         # str — "ok"|"lluvia"|"post_lluvia"|
                                    #        "fumigacion"|"post_fumigacion"
}
```

### Sentinel2Observation (entrada a CWSINDWICorrelationModel)

```python
# cesar/sentinel2_fusion.py
obs = Sentinel2Observation(
    fecha     = "2025-01-15",   # str YYYY-MM-DD
    B4_red    = 0.0812,         # float [0-1] reflectancia roja
    B8_nir    = 0.3240,         # float [0-1] reflectancia NIR
    B8A_nir   = 0.3180,         # float [0-1] reflectancia NIR banda angosta
    B11_swir  = 0.1950,         # float [0-1] reflectancia SWIR1
    B12_swir  = 0.1120,         # float [0-1] reflectancia SWIR2
    VPD_kPa   = 2.35,           # float kPa — desde ERA5 DAILY
    cwsi_nodo = 0.47,           # float [0-1] — None si es píxel de campo
)
# Propiedades calculadas automáticamente:
# obs.NDWI  = (B8_nir - B11_swir) / (B8_nir + B11_swir)
# obs.NDRE  = (B8A_nir - B4_red)  / (B8A_nir + B4_red)
# obs.NDVI  = (B8_nir - B4_red)   / (B8_nir + B4_red)
```

### Mapa de campo (salida del pipeline satelital)

```python
mapa = {
    "fecha":              "2025-01-15",
    "cwsi_mean":          0.42,        # float [0-1]
    "cwsi_std":           0.11,        # float
    "cwsi_p90":           0.61,        # float — zona más estresada
    "cwsi_all":           [...],       # list[float] — un valor por píxel 10m
    "n_pixels_total":     320,
    "n_pixels_veg":       285,         # NDVI >= 0.30
    "field_coords":       [...],       # list[(lat,lon)] — coordenadas píxeles
    "modelo_nodo":        "HV-A4CF12B3E7",
    "modelo_r2":          0.87,
    "vpd_dia":            2.35,
    "n_nodos_calibrados": 5,
}
```

---

## 3. Dependencias entre archivos

```
nodo_main.ino
    ├── config.h              (umbrales, pines)
    ├── driver_mlx90640.h     (cámara térmica)
    ├── driver_mds.h          (extensómetro ADS1231)
    ├── driver_pms5003.h      (PM2.5 fumigación/lluvia)
    ├── hsi.h                 (cálculo CWSI + HSI + fenología)
    └── → payload JSON

investigador/
    ├── 01_datos/synthetic_thermal_dataset.py
    ├── 02_modelo/unet_segmentation.py   (segmentación canopeo)
    ├── 02_modelo/pinn_cwsi.py           (predicción CWSI con física)
    ├── 03_validacion/validate_pinn.py
    └── install_gpu.bat / verify_gpu.py  (setup RTX 3070 CUDA 12.1)

cesar/
    ├── field_config.py        (FIELD_BOUNDARY, NODES, OUTPUT_DIR)
    ├── gee_connector.py       (GEE: S2 images, ERA5 VPD)
    ├── sentinel2_fusion.py    (Sentinel2Observation, CWSINDWICorrelationModel)
    ├── pipeline_satelital.py  (PipelineSatelital — orquestador)
    └── requirements.txt       (earthengine-api, sklearn, numpy...)
```

---

## 4. Variables de entorno requeridas

```bash
# GEE (autenticación una sola vez por máquina)
earthengine authenticate
earthengine set_project hydrovision-ag

# Backend FastAPI
DATABASE_URL=postgresql://user:pass@localhost:5432/hydrovision
MQTT_BROKER=localhost
MQTT_PORT=1883

# Modelos ML (configurado por install_gpu.bat)
# PyTorch CUDA 12.1 — RTX 3070 8GB VRAM
# batch_size PINN: 256-512
# batch_size U-Net: 4-8
```

---

## 5. Criterios de aceptación TRL 4

| Módulo | Métrica | Target |
|--------|---------|--------|
| PINN CWSI | MAE vs ψ_stem Scholander | < ±0.10 |
| U-Net segmentación | IoU canopeo | > 0.80 |
| CWSINDWICorrelationModel | R² calibración | > 0.75 |
| Pipeline satelital | cobertura campo completo | ≥ 1 mapa/semana en temporada |
| HSI fusion | correlación HSI vs ψ_stem | R² > 0.88 |
