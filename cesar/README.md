# Prueba de Concepto Computacional — HydroVision AG
## TRL 3 · Colonia Caroya, Córdoba · Cultivo: Vid Malbec

---

## Qué demuestra esta prueba

Esta prueba de concepto computacional demuestra que los principios físicos del
**Crop Water Stress Index (CWSI)** y la **Dendrometría** —documentados en más
de 200 publicaciones desde Jackson et al. (1981)— pueden implementarse
correctamente en software y producir resultados coherentes con los rangos
publicados en literatura para condiciones climáticas de Colonia Caroya, Córdoba.

El módulo `combined_stress_index.py` implementa el **HSI (HydroVision Stress Index)**,
la innovación central del nodo: fusión de termografía foliar (CWSI, 35%) +
dendrometría de tronco (MDS, 65%), logrando R²≈0.90–0.95 vs ψ_stem frente a
R²≈0.65 (solo CWSI) o R²≈0.85 (solo MDS).

Los módulos `baseline.py` y `fusion_engine.py` (ML Engineer/03_fusion/) implementan la
**auto-calibración dinámica del baseline CWSI**: el extensómetro de tronco actúa como
referencia fisiológica de la cámara térmica — cada evento de lluvia con MDS≈0 provee
una calibración automática de Tc_wet sin visita humana, y la regresión online aprende la
relación local CWSI↔MDS_norm por nodo durante la temporada. Esta es la capa que hace
técnicamente justificable el R²=0.90–0.95 en condiciones reales de campo.

La validación es **analítica y computacional** (no experimental en campo).
El hardware integrado es el objetivo del TRL 4.

---

## Estructura de módulos

```
cesar/
├── cwsi_formula.py           # Módulo 1 — Fórmula CWSI + Índice Jones + ψ_stem
├── thermal_pipeline.py       # Módulo 2 — Pipeline imágenes MLX90640 (32×24 px)
├── gdd_engine.py             # Módulo 3 — Motor GDD + fenología automática
├── synthetic_data_gen.py     # Módulo 4 — Generador de frames térmicos sintéticos
├── sentinel2_fusion.py       # Módulo 5 — Fusión CWSI ↔ NDWI (Sentinel-2)
├── dendrometry.py            # Módulo 6 — Dendrometría MDS + ψ_stem desde tronco
├── combined_stress_index.py  # Módulo 7 — HSI: fusión CWSI (35%) + MDS (65%)
├── baseline.py               # Módulo 8 — Auto-calibración dinámica del baseline CWSI (EMA + eventos de campo)
├── fusion_engine.py          # Módulo 9 — Motor HSI con regresión online CWSI↔MDS y pesos adaptativos
├── field_config.py           # Módulo 10 — Configuración del campo, polígono del lote y nodos GPS
├── optical_health.py         # Módulo 11 — ISO_nodo: índice 0-100% de salud óptica del lente
├── pipeline_satelital.py     # Módulo 12 — Pipeline de extrapolación satelital: nodo → mapa de campo completo
├── gee_connector.py          # Módulo 13 — Conector Google Earth Engine (Sentinel-2, ERA5, Landsat)
├── tests/
│   ├── test_cwsi.py          # 24 tests — validación matemática del CWSI
│   ├── test_gdd.py           # Tests motor fenológico GDD
│   ├── test_pipeline.py      # Tests pipeline térmico
│   ├── test_sentinel2.py     # Tests fusión satelital
│   ├── test_dendrometry.py   # 31 tests — MDS, ψ_stem, clasificación, rescate
│   ├── test_combined_stress.py # 32 tests — fusión HSI, acuerdo, desacuerdo, rescate
│   ├── test_baseline.py      # Tests auto-calibración dinámica baseline
│   ├── test_fusion_engine.py # Tests motor HSI con regresión online
│   └── test_optical_health.py # Tests ISO_nodo
└── outputs/                  # Figuras generadas por los demos
```

---

## Módulo 1 — `cwsi_formula.py`

**Qué implementa:**
Fórmula CWSI según Jackson et al. (1981) con coeficientes empíricos
calibrados para Malbec por Bellvert et al. (2016).

**Ecuación central:**
```
CWSI = (ΔT_medido − ΔT_LL) / (ΔT_UL − ΔT_LL)

  ΔT_medido = T_foliar − T_aire
  ΔT_LL = −1.97 + 1.49 × VPD   [límite inferior — Bellvert 2016 Malbec]
  ΔT_UL = +3.50                  [límite superior — hoja sin transpiración]
  VPD   = presión de vapor saturación − presión actual [kPa]
```

**Índices implementados:**

| Índice | Referencia | Descripción |
|--------|-----------|-------------|
| CWSI | Jackson et al. (1981) | Índice principal. Escala 0 (sin estrés) a 1 (estrés máximo). |
| Ig (Jones) | Jones (1999), Gutiérrez et al. (2018) | Alternativa sin VPD modelado. Usa Twet/Tdry medidos en campo. |
| ψ_stem [MPa] | Pires et al. (2025), Zhou et al. (2022) | Convierte CWSI a potencial hídrico Scholander. |

**Clasificación CWSI para Malbec:**

| CWSI | Nivel | Acción recomendada |
|------|-------|-------------------|
| < 0.10 | Sin estrés | Sin acción |
| 0.10–0.30 | Estrés leve | Monitoreo intensificado |
| 0.30–0.55 | Estrés moderado | Programar riego próximas 48h |
| 0.55–0.85 | Estrés severo | Riego urgente |
| > 0.85 | Estrés crítico | Riego inmediato — riesgo de daño irreversible |

**Arquitectura multi-cultivo:** el módulo incluye coeficientes para otros
cultivos del portfolio (olivo con respaldo García-Tejero 2018; variedades
adicionales de vid interpoladas desde Bellvert 2016). Estos están preparados
para calibración futura en campo y **no son objeto de la prueba TRL 3**.

**Ejecutar demo:**
```bash
python cwsi_formula.py
```

**Resultado esperado:**
```
  Escenario                CWSI  psi_stem  Nivel hidrico
  Bien regada             0.041  -0.40 MPa  SIN_ESTRES
  Estres leve             0.334  -0.75 MPa  ESTRES_LEVE
  Estres moderado         0.483  -0.93 MPa  ESTRES_MODERADO
  Estres severo           0.903  -1.43 MPa  ESTRES_CRITICO
  ...
  Error CWSI por 100mK (MLX90640): +/-0.0185 por pixel
  Error efectivo 28 px promediados: +/-0.0035   [OK — << ±0.05]
```

---

## Módulo 2 — `thermal_pipeline.py`

**Qué implementa:**
Pipeline completo de procesamiento de imágenes térmicas:
frame MLX90640 (32×24 px) → segmentación de canopeo → CWSI por frame → CWSI de sesión.

**Pasos del pipeline:**
1. Validación de calidad del frame (NETD, saturación, gradiente de borde)
2. Validación de condiciones de captura (radiación ≥ 400 W/m², VPD ≥ 0.5 kPa, viento ≤ 4 m/s)
3. Segmentación foliar por percentiles P20–P75 de temperatura
4. Filtro morfológico (regiones ≥ 4×4 px)
5. CWSI del frame = f(T_canopeo_media, condiciones meteorológicas)
6. CWSI de sesión = promedio ponderado por fracción foliar entre ángulos

**Metodología multi-angular:**
7 posiciones de gimbal × 3 ventanas horarias (9h / 12h / 16h) (6 fijas + 1 condicional viento).
Flag `alta_variabilidad_angular` si std(CWSI entre ángulos) > 0.12.
Campo `canopy_side` registra cara norte/sur del canopeo (Pires 2025, Zhou 2022).

**Ejecutar demo:**
```bash
python thermal_pipeline.py
```

---

## Módulo 3 — `gdd_engine.py`

**Qué implementa:**
Motor de acumulación de Grados-Día (GDD) y detección automática de estadios
fenológicos para Malbec en Colonia Caroya.

**Método:** Winkler (1974) — base 10°C
```
GDD_i = max(0, (T_max_i + T_min_i) / 2 − 10)
GDD_acum = Σ GDD_i  desde reinicio anual (1° septiembre, hemisferio sur)
```

**Estadios fenológicos detectados automáticamente:**

| Estadio | GDD Malbec | Umbral CWSI alerta |
|---------|-----------|-------------------|
| Brotación | 50–130 | 0.35 (muy sensible) |
| Desarrollo foliar | 130–280 | 0.40 |
| Floración | 280–420 | 0.30 (crítico — aborto floral) |
| Cuaje | 420–560 | 0.35 |
| Crecimiento fruto | 560–820 | 0.50 |
| Envero | 820–1.050 | 0.60 (RDI intencional) |
| Maduración | 1.050–1.380 | 0.65 |
| Cosecha | 1.380–1.500 | 0.75 |

**Datos climáticos de referencia:**
Estadísticas mensuales calibradas contra datos reales de la estación
**INTA EEA Manfredi** (código A872907, 2012–2026, n=4.802 días,
coord: −31.857°, −63.749°). Corrección altitudinal de −2.2°C aplicada
(lapse rate 0.6°C/100m × 370m entre Manfredi ~330m y Colonia Caroya ~700m).

**Ejecutar demo:**
```bash
python gdd_engine.py
```

---

## Módulo 4 — `synthetic_data_gen.py`

**Qué implementa:**
Generador de frames térmicos MLX90640 (32×24 px) que emulan la salida de la
cámara térmica en un viñedo de Malbec bajo distintos regímenes hídricos.

**Modelo físico de la imagen:**
```
T_leaf_pixel = T_air + ΔT_LL(VPD) + CWSI × (ΔT_UL − ΔT_LL) + N(0, NETD)
  NETD = 0.10°C  (especificación MLX90640, sensor BAB, breakout Adafruit 4407)
```

**Uso en TRL 4:**
Este generador es el núcleo del simulador que producirá **1.000.000 de imágenes
sintéticas** para el pre-entrenamiento del modelo PINN (Physics-Informed Neural
Network), antes de fine-tuning con los 680 frames reales de campo.

---

## Módulo 5 — `sentinel2_fusion.py`

**Qué implementa:**
Modelo de correlación CWSI (nodo termográfico) ↔ NDWI (Sentinel-2) para
generar mapas de estrés de campo completo desde un único nodo de referencia.

**Principio:**
- El nodo proporciona CWSI preciso en un punto (±0.05 CWSI)
- Sentinel-2 proporciona cobertura espacial (10m/px, cada 5 días, gratuito)
- La correlación empírica calibrada en campo permite extrapolar el CWSI
  del nodo a todos los píxeles vegetados del lote

**Índices espectrales usados:**
```
NDWI = (Band8A − Band11) / (Band8A + Band11)   [contenido hídrico foliar]
NDVI = (Band8  − Band4)  / (Band8  + Band4)    [vigor vegetativo]
NDRE = (Band8A − Band4)  / (Band8A + Band4)    [estrés temprano]
```

**Modelo:** Regresión polinomial grado 2 (HuberRegressor) sobre [NDWI, NDVI, NDRE, VPD].
Mínimo 10 observaciones de calibración con distribución CWSI 0.1–0.9.

**Ejecutar demo:**
```bash
python sentinel2_fusion.py
# Genera: outputs/cwsi_ndwi_fusion.png
```

**Resultado esperado (datos sintéticos):**
```
Calibración (n=96): R²=0.97  MAE=0.018  RMSE=0.024
Test       (n=24):  R²=0.96  MAE=0.021
```

---

## Correr todos los tests

```bash
cd "prueba computacional"
python -m pytest tests/ -v
```

**Resultado esperado: 135 tests, 0 fallos.**

```
tests/test_cwsi.py               24 passed   validación matemática CWSI + Ig + ψ_stem
tests/test_gdd.py                xx passed   motor fenológico GDD
tests/test_pipeline.py           xx passed   pipeline térmico + segmentación
tests/test_sentinel2.py          xx passed   fusión CWSI↔NDWI
tests/test_dendrometry.py        31 passed   MDS, ψ_stem, clasificación, rescate, recuperación
tests/test_combined_stress.py    32 passed   HSI fusion, acuerdo/desacuerdo, señal única, rescate
```

---

## Módulo 6 — `dendrometry.py`

**Qué implementa:**
Motor de análisis dendrométrico: micro-contracciones del tronco (MDS) → ψ_stem.
El extensómetro de tronco (strain gauge + ADS1231 24-bit ADC, resolución 1 µm)
mide la variación diaria del diámetro. MDS = D_max − D_min correlaciona con
ψ_stem con R²=0.80–0.92 (vs R²=0.62–0.67 del CWSI térmico).

**Principio biofísico:**
```
MDS = D_max − D_min  [µm]   (Maximum Daily Shrinkage)
ψ_stem = −0.15 + (−0.0080) × MDS  [MPa]   (Fernández & Cuevas 2010)

Umbrales protocolo HydroVision AG (Malbec):
  < 60 µm  : sin estrés
  60–150   : estrés leve
  150–280  : estrés moderado
  280–400  : estrés severo
  > 400    : estrés crítico
```

**Corrección térmica:** elimina expansión del sensor por temperatura del tronco
(alpha = 2.5 µm/°C, Pérez-López 2008):
```
MDS_corr = MDS_raw − 2.5 × ΔT_tronco
```

**Recuperación nocturna:** planta debe recuperar ≥80% antes del amanecer.
Recuperación < 80% indica déficit acumulado o daño en raíces.

**Ejecutar demo:**
```bash
python dendrometry.py
```

---

## Módulo 7 — `combined_stress_index.py`

**Qué implementa:**
Motor de fusión HSI (HydroVision Stress Index): combina señal térmica (CWSI)
y señal dendrométrica (MDS) en un único ψ_stem estimado con menor incertidumbre.

**Lógica de fusión:**

| Situación | Estrategia | Pesos | R² esperado |
|-----------|-----------|-------|------------|
| Acuerdo (Δψ < 0.35 MPa) | Promedio ponderado | 35% CWSI + 65% MDS | 0.90–0.95 |
| Desacuerdo (Δψ ≥ 0.35 MPa) | MDS domina | 20% CWSI + 80% MDS | 0.85–0.90 |
| Solo térmico | CWSI × 1.0, unc × 1.4 | 100% CWSI | 0.62–0.67 |
| Solo dendro | MDS × 1.0, unc × 1.4 | 100% MDS | 0.80–0.92 |
| Sin datos | Error / NO_DATA | — | — |

**Protocolo de rescate:** cualquier señal individual ≤ −1.5 MPa activa
`rescue_required = True` independientemente del índice compuesto.

**Novedad global:** no se ha identificado en el mercado global ningún producto
comercial que combine termografía foliar continua + motor fenológico automático
+ fusión satelital + dendrometría integrada en un nodo autónomo de campo.
(Jones 2004; Fernández et al. 2011)

**Ejecutar demo:**
```bash
python combined_stress_index.py
```

**Resultado esperado:**
```
  Fila 5 (Control 100% ETc):  CWSI=0.xxx  MDS=55um   psi_HSI=-0.xx MPa  SIN_ESTRES
  Fila 1 (Sin riego 0% ETc):  CWSI=0.xxx  MDS=440um  psi_HSI=-x.xx MPa  ESTRES_CRITICO [RESCATE]
  HSI fusion: R2 ~0.90-0.95  vs  CWSI-solo ~0.65  vs  MDS-solo ~0.85
```

---

## Correr todos los tests

```bash
cd "prueba computacional"
python -m pytest tests/ -v
```

**Resultado esperado: 135 tests, 0 fallos.**

```
tests/test_cwsi.py               24 passed   validación matemática CWSI + Ig + ψ_stem
tests/test_gdd.py                xx passed   motor fenológico GDD
tests/test_pipeline.py           xx passed   pipeline térmico + segmentación
tests/test_sentinel2.py          xx passed   fusión CWSI↔NDWI
tests/test_dendrometry.py        31 passed   MDS, ψ_stem, clasificación, rescate, recuperación
tests/test_combined_stress.py    32 passed   HSI fusion, acuerdo/desacuerdo, señal única, rescate
```

---

## Referencias científicas

| Referencia | Uso en el código |
|-----------|-----------------|
| Jackson et al. (1981). *Water Resources Research*, 17(4), 1133–1138. | Fórmula CWSI — `cwsi_formula.py` |
| Bellvert et al. (2016). *Precision Agriculture*, 17(1), 62–78. | Coeficientes ΔT_LL/ΔT_UL Malbec — `cwsi_formula.py` |
| Jones, H.G. (1999). *Agric. Forest Meteorology*, 95(3), 139–149. | Índice Ig (Jones) — `cwsi_formula.py` |
| Gutiérrez et al. (2018). *PLoS ONE*, 13(2), e0192037. | Validación Índice Jones en vid — `cwsi_formula.py` |
| Pires et al. (2025). *Computers & Electronics in Agriculture*, 239, 110931. | Correlación CWSI→ψ_stem (R²=0.663 tarde) — `cwsi_formula.py` |
| Zhou et al. (2022). *Agronomy*, 12(2), 322. | CWSI↔ψ_leaf, canopy_side — `thermal_pipeline.py` |
| Araújo-Paredes et al. (2022). *Sensors*, 22(20), 8056. | CWSI aéreo vs ψ_stem; error NETD — `thermal_pipeline.py` |
| Winkler et al. (1974). *General Viticulture*. UC Press. | Motor GDD base 10°C — `gdd_engine.py` |
| INTA EEA Manfredi, estación A872907 (2012–2026). | Climatología Colonia Caroya — `gdd_engine.py` |
| Bellvert et al. (2015). *Precision Agriculture*, 16(4), 361–378. | Fusión CWSI↔satélite — `sentinel2_fusion.py` |
| Fernández, J.E. & Cuevas, M.V. (2010). *Agric. Forest Meteorology*, 150(2), 135–151. | MDS→ψ_stem (R²=0.80–0.92) — `dendrometry.py` |
| Ortuño et al. (2010). *Trees*, 24(4), 641–648. | Validación extensómetro en cítricos — `dendrometry.py` |
| Naor, A. (2000). *Acta Horticulturae*, 526, 498–506. | Umbrales ψ_stem Malbec — `dendrometry.py` |
| Pérez-López et al. (2008). *Agric. Water Management*, 95(2), 214–224. | Corrección térmica extensómetro — `dendrometry.py` |
| Jones, H.G. (2004). *J. Experimental Botany*, 55(407), 2427–2436. | Complementariedad indicadores — `combined_stress_index.py` |
| Fernández et al. (2011). *Irrigation Science*, 29(4), 297–305. | Fusión dendrometría+ψ_stem; base del HSI — `combined_stress_index.py` |
| Jackson et al. (1981) + Fernández & Cuevas (2010). | Baseline NWSB + coeficiente ψ_stem = −0.15 − 0.0080×MDS — `baseline.py`, `fusion_engine.py` |

---

## Módulo 8 — `ML Engineer/03_fusion/baseline.py` — Auto-calibración dinámica del baseline CWSI

**Qué implementa:**
Motor de calibración autónoma del baseline CWSI por eventos de campo. El CWSI es sensible al error en los parámetros Tc_wet y Tc_dry — un error de 0.5°C en el baseline puede traducirse en ±0.10–0.15 unidades de CWSI de error sistemático. Este módulo corrige esa deriva sin intervención humana.

**Clases principales:**

`CWSIBaseline`:
- `tc_wet_offset` / `tc_dry_offset`: correcciones aditivas al NWSB de Jackson (1981). Parten en 0.0°C (baseline de fábrica) y convergen al valor real del nodo.
- `update_rain(tc_measured, ta, vpd_kpa, mds_um, timestamp_iso)`: cuando llueve y MDS ≈ 0 (plant al máximo de hidratación), Tc medida = Tc_wet real → actualiza offset por EMA (lr=0.25). Retorna False si MDS > 50 µm (la planta no está suficientemente hidratada).
- `update_scheduled(...)`: actualización periódica por sesión Scholander; tasa de aprendizaje reducida proporcional a la confianza (MDS/500).
- `detect_drift(cwsi_history)`: detecta deriva del baseline en tres condiciones: (a) CWSI medio < 0.02 → Tc_wet sobreestimado; (b) CWSI medio > 0.98 → Tc_wet subestimado; (c) std < 0.01 con >10 muestras → posible falla de sensor.
- `save(path)` / `load(path)`: persiste el estado calibrado en JSON para recuperación ante reinicios.

**Mecanismo central — evento de lluvia como referencia:**
```
Lluvia ≥ 5mm → MDS ≈ 0 (D_min ≈ D_max, tronco al máximo)
    → Tc_medido = Tc_wet real del nodo
    → error = Tc_medido − NWSB(Ta, VPD)
    → tc_wet_offset ← 0.75 × tc_wet_offset + 0.25 × error
```
Este mecanismo provee múltiples calibraciones por temporada sin que el equipo visite el viñedo. La Tc_wet de Jackson 1981 se adapta al microclima real del nodo.

**Ejecutar demo:**
```bash
python ML\ Engineer/03_fusion/baseline.py
# (demo incluido al final del módulo)
```

---

## Módulo 9 — `ML Engineer/03_fusion/fusion_engine.py` — Motor HSI con aprendizaje online

**Qué implementa:**
Motor HSI avanzado con regresión lineal online por nodo, pesos dinámicos por madurez del historial dendrométrico, imputación de CWSI en días sin ventana solar, y detección automática de divergencia entre sensores.

**Clases principales:**

`OnlineLinearRegression`:
- Ajuste CWSI = α + β × MDS_norm con ventana deslizante de 60 muestras por nodo.
- Se activa a partir de 10 muestras (mínimo estadístico). Antes de eso, no predice.
- `update(mds_norm, cwsi)`: agrega muestra y reajusta por mínimos cuadrados.
- `predict_cwsi(mds_norm)`: retorna None si no hay suficientes muestras.

`HSIFusionEngine`:
- Mantiene un `CWSIBaseline` por nodo y una `OnlineLinearRegression` por nodo.
- `compute(cwsi, ta, vpd_kpa, cwsi_confidence, mds_override, timestamp_iso)`:
  1. Normaliza MDS: mds_norm = mds_um / 350 (MDS_MAX_REFERENCE)
  2. Actualiza la regresión online con el nuevo par (mds_norm, cwsi)
  3. Calcula pesos dinámicos: mds_maturity = min(1, n_sesiones/20) — el MDS gana peso gradualmente
  4. Si cwsi_confidence < 0.4 y regresión activa: imputa CWSI desde MDS (días nublados, viento fuerte)
  5. Calcula HSI = clip(w_cwsi × cwsi_usado + w_mds × mds_norm, 0, 1)
  6. Alerta de divergencia si |CWSI − MDS_norm| > 0.35
- `on_rain_event(tc_canopy, ta, vpd_kpa, timestamp_iso)`: delega la calibración al CWSIBaseline subyacente.

`FusionReport`:
Dataclass de resultado con: hsi, cwsi, mds_um, mds_norm, psi_stem_mpa, w_cwsi, w_mds, cwsi_confidence, mds_quality, divergence_alert, regression_r2, cwsi_predicted_from_mds, baseline_offset.
- `stress_level()`: SIN_ESTRÉS (<0.25), LEVE (<0.50), MODERADO (<0.75), SEVERO (≥0.75).

**Demo integrado:**
```bash
python ML\ Engineer/03_fusion/fusion_engine.py
# Simula 10 nodos × 30 días × 3 sesiones/día
# Muestra curva de R² de regresión, evolución de offset de baseline y HSI por zona
```

---

## Limitación documentada

> Esta validación es **analítica y computacional**. No se dispone aún de hardware
> integrado funcionando. La prueba experimental en condiciones reales de campo
> (TRL 4) se realizará en el viñedo propio de Malbec en Colonia Caroya (1/3 ha,
> acceso exclusivo) una vez obtenido el financiamiento ANPCyT.
>
> Los coeficientes de Bellvert (2016) fueron obtenidos en vid Malbec en
> condiciones mediterráneas (Cataluña). Serán recalibrados para las condiciones
> específicas de Colonia Caroya y Cuyo mediante protocolo Scholander bajo
> supervisión de la Dra. Mariela Monteoliva (INTA-CONICET).
