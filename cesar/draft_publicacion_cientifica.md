# DRAFT -- Publicacion Cientifica HydroVision AG
## Para revision de Dra. Monteoliva y el investigador Art. 32

> **Target:** Congreso SAFV (Sociedad Argentina Fisiologia Vegetal) o revista indexada (Computers and Electronics in Agriculture / Precision Agriculture)
> **Autores:** Monteoliva, M.; Inv. Art. 32 (a definir); Schiavoni, C.; Bergon, L.
> **Estado:** Estructura IMRaD con placeholders. Se completa con datos reales Mes 10-12.

---

## TITULO

**Autonomous Field Estimation of Grapevine Stem Water Potential Using a Physics-Informed Neural Network with Fused Thermal and Dendrometric Signals: Validation in Malbec under Differential Irrigation in Cordoba, Argentina**

### Titulo alternativo (mas corto):

**HydroVision Stress Index (HSI): Fusing LWIR Thermography and Trunk Dendrometry with a PINN for Real-Time Vine Water Status in the Field**

---

## ABSTRACT (250 palabras max)

Real-time assessment of vine water status remains a critical challenge for precision irrigation management. We present the HydroVision Stress Index (HSI), a novel composite index that fuses low-cost long-wave infrared (LWIR) thermography with trunk micro-dendrometry using a Physics-Informed Neural Network (PINN) to estimate stem water potential (psi_stem) in grapevine (Vitis vinifera cv. Malbec) under field conditions.

An autonomous sensor node (ESP32-S3 + MLX90640 32x24 px thermal sensor + ADS1231 24-bit strain gauge dendrometer + meteorological sensors) was deployed in an experimental vineyard in Colonia Caroya, Cordoba, Argentina (31.20 S, 64.09 W, 520 m a.s.l.) during the [SEASON] growing season. Four rows of Malbec vines (136 m each, 544 vines) were subjected to five differential irrigation regimes (100% ETc to no irrigation) via drip system with Rain Bird solenoid valves. Ground truth was obtained from [N] pressure chamber (Scholander) measurements of psi_stem following the protocol of [Monteoliva et al.].

The PINN architecture embeds the CWSI energy balance equation (Jackson et al. 1981) as a physics constraint in the loss function, preventing physically impossible predictions. The model was trained on [1,050,680] images (50,000 public + 1,000,000 synthetic + [680] field-calibrated frames) and validated against [120] independent Scholander measurements.

Results: HSI achieved R^2 = [X.XX] (RMSE = [X.XX] MPa) against Scholander psi_stem on the independent validation set, compared to R^2 = [X.XX] for CWSI alone and R^2 = [X.XX] for MDS alone. The optimal fusion weights were [XX]% CWSI + [XX]% MDS. Inference latency was [XXX] ms on the edge device. The system operated autonomously for [XX] consecutive days with solar power.

**Keywords:** CWSI, PINN, dendrometry, MDS, precision viticulture, thermal imaging, water stress, Malbec, Argentina

---

## 1. INTRODUCTION

### 1.1 Problem statement

- Estres hidrico en vid: impacto economico (15-35% perdida rendimiento, Maes & Steppe 2012)
- Limitaciones de metodos actuales: satelite (nublado, resolucion), drones (operador, ANAC), tensiometros (suelo != planta), visual (tardio)
- Gap: no existe sistema autonomo de campo que mida respuesta fisiologica de la planta en tiempo real

### 1.2 CWSI -- estado del arte

- Jackson et al. (1981): fundamento fisico CWSI
- Bellvert et al. (2016): coeficientes vid, Cataluna
- Pires et al. (2025): framework escalable termografia en vinedo
- Jones (2004): efecto del viento en CWSI — principal artefacto
- Limitacion: CWSI termico solo alcanza R^2 = 0.62-0.67 vs psi_stem (literatura)

### 1.3 Dendrometria de tronco (MDS)

- Fernandez & Cuevas (2010): MDS correlaciona con psi_stem R^2 = 0.80-0.92
- Ventajas: opera 24/7, sin dependencia de ventana solar, no afectado por viento
- Limitacion: respuesta lenta a cambios rapidos, sensible a temperatura del tronco

### 1.4 Physics-Informed Neural Networks (PINN) en agricultura

- Ridder et al. (2025): PINN para absorcion radicular
- Benkirane et al. (2025): PINN + Penman-Monteith para ET
- Hu et al. (2025): PINN + Landsat para humedad de suelo
- **Gap: ningun trabajo aplica PINN al CWSI con termografia embebida en campo**

### 1.5 Hipotesis y objetivos

**Hipotesis:** La fusion de CWSI termico y MDS dendrometrico mediante una PINN que embebe el balance energetico foliar permite estimar psi_stem con R^2 > 0.85 en condiciones de campo real, superando a cada senal individual.

**Objetivos:**
1. Validar el HSI (CWSI + MDS fusionado por PINN) contra Scholander en Malbec bajo 5 regimenes hidricos
2. Determinar los pesos optimos de fusion CWSI/MDS
3. Demostrar operacion autonoma del nodo en campo por >72h continuas
4. Evaluar el efecto del viento en la precision del CWSI y la eficacia de la conmutacion automatica a MDS

---

## 2. MATERIALS AND METHODS

### 2.1 Sitio experimental

- Ubicacion: Colonia Caroya, Cordoba, Argentina (31.20 S, 64.09 W, 520 m a.s.l.)
- Cultivo: Vitis vinifera cv. Malbec sobre pie americano
- Diseno: 4 filas x 136 m = 544 vides
- 5 zonas hidricas por fila (27 m cada una): 100% ETc, 75% ETc, 50% ETc, 25% ETc, sin riego
- Sistema de riego: goteo con solenoides Rain Bird 24VAC controlados por nodo HydroVision
- Temporada: [MES INICIO] a [MES FIN] 2026/2027

### 2.2 Nodo sensor HydroVision AG

| Componente | Especificacion | Funcion |
|------------|---------------|---------|
| MCU | ESP32-S3 | Control, procesamiento, LoRa |
| Camara termica | MLX90640 32x24 px, NETD ~100 mK, FOV 110x75 | CWSI -- temperatura foliar |
| Dendrometro | Strain gauge + ADS1231 24-bit, resolucion 1 um | MDS -- micro-contracciones tronco |
| Correccion termica dendrometro | DS18B20, alpha = 2.5 um/C | Elimina dilatacion termica |
| Meteorologico | SHT31 (T_air, HR) | VPD, CWSI denominador |
| Viento | Anemometro RS485 Modbus | Confianza dinamica CWSI |
| Radiacion | Piranometro BPW34 ADC | Balance energetico |
| GPS | u-blox NEO-6M | Geolocalizacion |
| Gimbal | 2x MG90S, 5 posiciones | Captura multi-angular |
| Referencia termica | Dry Ref (aluminio negro e=0.98) + Wet Ref (feltro hidrofilico) | Calibracion Jones Ig |
| Comunicacion | SX1276 LoRa 915 MHz | Transmision a gateway |
| Energia | LiFePO4 6Ah + panel solar 6W + MPPT | Autonomia >72h |

### 2.3 Protocolo de medicion Scholander (ground truth)

- Instrumento: bomba de presion tipo Scholander
- Protocolo: Dra. M. Monteoliva (INTA-CONICET)
- Ventana de medicion: 10:00-14:00 hs (maximo estres diurno)
- Condicion previa: >48h sin lluvia significativa
- N sesiones: [10] | N mediciones totales: [XXX]
- Variables registradas: psi_stem [MPa], hora, T_air, HR, viento, estadio fenologico

### 2.4 Modelo PINN -- arquitectura y entrenamiento

**Arquitectura:** MobileNetV3-Tiny backbone + cabeza de regresion HSI

**Funcion de perdida PINN:**

```
L_total = MSE(CWSI_pred, CWSI_real) + lambda * ||CWSI_pred - f(dT_pred, VPD)||^2
```

donde f() es la ecuacion de Jackson et al. (1981):
```
f(dT, VPD) = (dT - dT_LL(VPD)) / (dT_UL - dT_LL(VPD))
```

**Dataset de entrenamiento:**

| Capa | Fuente | Volumen | Uso |
|------|--------|---------|-----|
| 1 | Datasets publicos (INIA Chile, IRTA, PlantVillage, FLIR ADAS) | 50,000 | Pre-entrenamiento backbone |
| 2 | Simulador fisico (balance energetico foliar Malbec) | 1,000,000 | Fine-tuning sintetico |
| 3 | Frames reales Colonia Caroya con Scholander | 680 | Calibracion final |
| Val | Frames reales independientes | 120 | Validacion (no vistos en entrenamiento) |

**Cuantizacion:** INT8 via TensorFlow Lite / PyTorch quantization

**Fusion HSI:**
```
HSI = w_cwsi * CWSI + w_mds * MDS_norm
```
Rampa gradual 4-12 m/s (14-43 km/h): w_cwsi se reduce linealmente de 0.35 a 0. Si viento ≥ 12 m/s (43 km/h): w_cwsi = 0, w_mds = 1 (conmutacion automatica)

### 2.5 Analisis estadistico

- Regresion lineal: HSI vs psi_stem Scholander (R^2, RMSE, MAE)
- Bland-Altman plot: sesgo y limites de concordancia
- Comparacion de modelos: CWSI solo vs MDS solo vs HSI fusionado
- Analisis por regimen hidrico (5 niveles) y estadio fenologico
- Test de significancia: ANOVA o Kruskal-Wallis segun normalidad

---

## 3. RESULTS

> **[PLACEHOLDER -- completar con datos reales Mes 10-12]**

### 3.1 Condiciones experimentales

- Tabla: T_air promedio, HR, VPD, radiacion, viento, lluvia acumulada por mes
- Rango de psi_stem observado: [X.XX] a [X.XX] MPa
- N total de mediciones Scholander: [XXX]

### 3.2 Performance del modelo

| Metrica | CWSI solo | MDS solo | HSI (CWSI+MDS) | Target |
|---------|-----------|----------|----------------|--------|
| R^2 vs psi_stem | [X.XX] | [X.XX] | [X.XX] | > 0.85 |
| RMSE [MPa] | [X.XX] | [X.XX] | [X.XX] | -- |
| MAE [MPa] | [X.XX] | [X.XX] | [X.XX] | -- |

### 3.3 Efecto del viento

- R^2 CWSI con viento < 2 m/s: [X.XX]
- R^2 CWSI con viento 2-4 m/s: [X.XX]
- R^2 CWSI con viento 4-12 m/s (rampa gradual): [X.XX]
- R^2 CWSI con viento > 12 m/s: [X.XX] (degradado — backup 100% MDS)
- R^2 HSI con conmutacion automatica a MDS: [X.XX] (recuperado)

### 3.4 Performance por regimen hidrico

- Tabla: R^2 y RMSE por cada uno de los 5 regimenes (100% ETc a sin riego)

### 3.5 Performance por estadio fenologico

- Tabla: R^2 por estadio (vegetativo, floracion, envero, pre-cosecha)

### 3.6 Operacion autonoma

- Dias continuos de operacion: [XX]
- Tasa de uptime: [XX]%
- Consumo promedio: [XX] mW

### Figuras

- Fig. 1: Scatter plot HSI vs psi_stem con linea 1:1 y R^2
- Fig. 2: Bland-Altman plot HSI vs Scholander
- Fig. 3: Serie temporal CWSI + MDS + HSI + psi_stem por regimen
- Fig. 4: Efecto del viento en CWSI vs HSI
- Fig. 5: Mapa de estres (frame termico segmentado + CWSI calculado)

---

## 4. DISCUSSION

### 4.1 Ventaja de la fusion CWSI+MDS

- Comparacion con literatura: Fernandez & Cuevas (2010) R^2=0.80-0.92 MDS solo; nuestro HSI fusionado [X.XX]
- El PINN physics constraint mejora generalizacion con pocos datos reales (680 frames)

### 4.2 Conmutacion automatica por viento

- Primera implementacion documentada de confianza dinamica CWSI/MDS basada en viento
- Elimina el principal artefacto de medicion (Jones 2004)

### 4.3 Limitaciones

- Sensor MLX90640 (NETD ~100 mK) vs FLIR Lepton 3.5 (~50 mK): implicancias en precision
- Validacion en un solo sitio y una variedad (Malbec, Colonia Caroya)
- Necesidad de validacion multi-varietal y multi-regional (TRL 5)

### 4.4 Implicancias practicas

- Costo del nodo (~USD 950) vs alternativas (drones, estaciones comerciales)
- Escalabilidad: fusion con Sentinel-2 permite 1 nodo / 50 ha

---

## 5. CONCLUSIONS

1. El HSI alcanza R^2 = [X.XX] vs psi_stem Scholander, superando CWSI solo (R^2 = [X.XX]) y MDS solo (R^2 = [X.XX])
2. La arquitectura PINN con physics constraint mejora la generalizacion con datos limitados
3. La conmutacion automatica CWSI -> MDS por viento elimina el principal artefacto de medicion
4. El sistema opera autonomamente por [XX] dias con energia solar
5. Primer sistema documentado en Argentina que integra termografia foliar + dendrometria de tronco en un nodo autonomo de campo

---

## ACKNOWLEDGEMENTS

This work was funded by ANPCyT (Agencia Nacional de Promocion de la Investigacion, el Desarrollo Tecnologico y la Innovacion) through the STARTUP 2025 TRL 3-4 program (FONARSEC / BID). The authors thank INTA-CONICET (MEBA-IFRGV-UDEA, CCT Cordoba) for laboratory access and the Schiavoni family for providing the experimental vineyard in Colonia Caroya.

---

## REFERENCES

- Bellvert, J., Marsal, J., Girona, J. & Zarco-Tejada, P.J. (2016). Precision Agriculture, 17(1), 62-78.
- Benkirane, H. et al. (2025). PINN + Penman-Monteith for evapotranspiration. [ref completa]
- Catania, C.D. & Avagnina, S. (2007). Modelado fenologico de vid en Argentina. INTA.
- Ciliberti, N. et al. (2015). Conditions for Botrytis bunch rot. EPPO Bull.
- Fernandez, J.E. & Cuevas, M.V. (2010). Agricultural Water Management, 97(4), 519-530.
- Garcia de Cortazar-Atauri, I. et al. (2009). Int J Biometeorol, 53, 317-326.
- Hu, S. et al. (2025). PINN + Landsat 8 Thermal for soil moisture. [ref completa]
- Jackson, R.D. et al. (1981). Water Resources Research, 17(4), 1133-1138.
- Jones, H.G. (1999). Agric. Forest Meteorol., 95(3), 139-149.
- Jones, H.G. (2004). Irrigation scheduling: advantages and pitfalls. J. Exp. Bot., 55(407), 2427-2436.
- Maes, W.H. & Steppe, K. (2012). Trends in Plant Science, 17(10), 606-615.
- Pires, A. et al. (2025). Computers and Electronics in Agriculture, 239, 110931.
- Ridder, N. et al. (2025). PINN for root water uptake. [ref completa]
- Rouholahnejad, E. et al. (2024). Physics-informed yield loss forecasting with Sentinel-2. [ref completa]
