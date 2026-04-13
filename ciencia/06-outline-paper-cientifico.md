
# OUTLINE — ARTÍCULO CIENTÍFICO
## HydroVision AG — Calibración CWSI–Ψ_stem en *Vitis vinifera* cv. Malbec
## Elaborado por: Dra. Mariela Inés Monteoliva (INTA-CONICET)

---

## 1. DATOS DEL ARTÍCULO PROPUESTO

| Campo | Valor |
|---|---|
| **Título tentativo** | "Continuous fixed-node LWIR thermography fused with trunk diameter variation for real-time crop water stress index calibration in Malbec grapevines under regulated deficit irrigation" |
| **Título alternativo corto** | "CWSI calibration via LWIR+TDV fusion in Malbec under 5-level RDI" |
| **Tipo** | Artículo original (Original Research Article) |
| **Idioma de redacción** | Inglés (requerido por las revistas objetivo) |
| **Extensión estimada** | 7.000–9.000 palabras (cuerpo) + tablas + figuras |
| **Figuras** | 6–8 |
| **Tablas** | 4–5 |
| **Referencias estimadas** | 45–65 |

---

## 2. REVISTAS OBJETIVO (en orden de preferencia)

| # | Revista | Factor de impacto (2024) | Cuartil | Razón de preferencia |
|---|---|---|---|---|
| 1 | **Agricultural Water Management** (Elsevier) | 6.6 | Q1 | Referencia del campo — CWSI en vid tiene antecedentes publicados aquí |
| 2 | **Precision Agriculture** (Springer) | 6.2 | Q1 | Tecnología de precisión + sensores — perfil del sistema HydroVision AG |
| 3 | **Computers and Electronics in Agriculture** (Elsevier) | 8.3 | Q1 | IoT agrícola, edge computing — más técnico, menos fisiológico |
| 4 | **Irrigation Science** (Springer) | 3.8 | Q2 | Alternativa si rechazan Q1 — menos competitivo |
| 5 | **Journal of Experimental Botany** | 7.1 | Q1 | Solo si el énfasis fisiológico supera al tecnológico |

**Recomendación:** someter primero a *Agricultural Water Management*. Si rechazan sin revisión (desk rejection), *Precision Agriculture*. No someter simultáneamente.

---

## 3. AUTORÍA PROPUESTA

| Orden | Autor | Afiliación | Contribución (CRediT) |
|---|---|---|---|
| 1° (primer autor) | **Monteoliva, Mariela I.** | INTA EEA Córdoba / CONICET | Conceptualización, diseño experimental, metodología Scholander, escritura |
| 2° | **Inv. Art. 32 (a definir)** | HydroVision AG | Software (PINN, pipeline procesamiento), curación de datos |
| 3° | **Schiavoni, César** | HydroVision AG | Hardware, firmware, recursos, supervisión técnica |
| 4° (autor de correspondencia) | **Monteoliva, Mariela I.** | INTA-CONICET | Correspondencia con editores |

**Notas de autoría:**
- Javier Schiavoni (técnico de campo): reconocimiento en Acknowledgements — no califica como coautor por criterios ICMJE
- Si el paper se publica antes del TRL 4, revisar si incluir afiliación HydroVision AG puede comprometer la independencia científica del aval

---

## 4. ESTRUCTURA DETALLADA

### 4.1 Abstract (250 palabras)

- **Background**: Estado del arte: limitación de termografía UAV ocasional vs. monitoreo continuo. Gap: no existe sistema comercial de nodo fijo LWIR con extensometría de tronco en vid a escala de campo.
- **Objective**: Calibrar CWSI usando nodo fijo LWIR+extensómetro bajo 5 niveles de déficit hídrico (RDI 0–100% ETc) en Malbec, Córdoba, Argentina.
- **Methods**: Viñedo experimental Colonia Caroya, 5 zonas RDI, nodo HydroVision AG (MLX90640 LWIR 32×24, extensómetro 24 bits, SHT31, pluviómetro). 4 sesiones Scholander (Ψ_stem, cámara de presión). Ajuste lineal CWSI–Ψ_stem, R² y RMSE.
- **Key results** (a completar post-experimento): R²=X.XX entre CWSI y Ψ_stem; CWSI_alerta = X.XX corresponde a Ψ_stem = −X.X MPa.
- **Conclusion**: Primera calibración CWSI para Malbec argentina con monitoreo continuo fijo.
- **Keywords**: CWSI · stem water potential · Malbec · regulated deficit irrigation · LWIR · trunk diameter variation

### 4.2 Introduction (800–1.000 palabras)

**Párrafo 1 — La problemática:** Viñedos de alto valor en regiones áridas-semiáridas de Argentina (Mendoza, San Juan, Córdoba) enfrentan limitaciones crecientes de agua. RDI mejora calidad enológica pero requiere monitoreo preciso del estado hídrico.

**Párrafo 2 — Estado del arte termografía:** CWSI Jackson (1981). Correlaciones CWSI–Ψ_stem documentadas en vid (Bellvert 2016, Araújo-Paredes 2022, Pires 2025, Zhou 2022). Problema: datos de UAV (2 capturas/semana) o campañas manuales → no detectan inicio del estrés en escala horaria.

**Párrafo 3 — Estado del arte extensometría:** MDS (máxima contracción diaria) como indicador de Ψ_stem (Fernández & Cuevas 2010). Ventaja: no afectado por viento ni nubosidad. Limitación: único punto, no todo el canopeo.

**Párrafo 4 — Gap e hipótesis:** Ningún trabajo ha integrado LWIR fijo continuo + extensómetro de tronco en un único sistema de campo para generar un índice combinado (HSI). Hipótesis: la fusión aumenta R² de ~0.62 (CWSI solo) a >0.85.

**Párrafo 5 — Objetivos del trabajo:**
1. Calibrar línea base CWSI (ΔT_LL, ΔT_UL) para Malbec en Córdoba bajo condiciones de VPD variables
2. Establecer la relación cuantitativa CWSI–Ψ_stem en 5 niveles de déficit hídrico
3. Evaluar si la fusión CWSI+MDS (HSI) mejora la correlación con Ψ_stem respecto a CWSI solo
4. Definir umbrales operativos de alerta y rescate hídrico para Malbec Córdoba

### 4.3 Materials and Methods (1.500–2.000 palabras)

**2.1 Study site and plant material**
- Viñedo Schiavoni, Colonia Caroya, Córdoba (~700 m s.n.m., 31°S, 64°W)
- Malbec (*Vitis vinifera* L. cv. Malbec), espaldera, plantación 2010–2015
- Suelo: franco-limoso, capacidad de campo ~0.28 m³/m³, PMP ~0.12 m³/m³
- Clima: templado semi-árido, ETo media anual 850 mm, precipitación 600–700 mm (distribución estival)

**2.2 Experimental design — 5-zone RDI**
- 5 zonas de riego: A=100%, B=65%, C=40%, D=15%, E=0% ETc
- Rain Bird controller, solenoides por zona, tensiómetros a 30 cm
- ETo calculada por Penman-Monteith (datos SMN Córdoba + estación local)
- Tabla de zonas con número de plantas y replicas

**2.3 HydroVision AG monitoring node**
- Componentes: MCU ESP32-S3, cámara LWIR MLX90640 (32×24 px, NETD<0.1°C), extensómetro lineal 24 bits (resolución 0.5 μm), T+HR SHT31, pluviómetro basculante, anemómetro
- Frecuencia de captura: 15 min en horario 9:00–15:00 hs; hibernación nocturna
- Gimbal de ángulo variable (35–45°), instalación a 0.6–1.0 m del tronco
- Auto-calibración del offset Tc_wet por eventos de lluvia ≥5 mm + MDS≈0 (EMA, Nivel 2)

**2.4 CWSI calculation**
- Fórmula Jackson 1981: CWSI = (ΔT_medido − ΔT_LL) / (ΔT_UL − ΔT_LL)
- Línea base inferior: ΔT_LL = a + b·VPD (coeficientes calibrados en temporada)
- Línea base superior: ΔT_UL = media histórica de planta bajo estrés máximo (zona E)
- Segmentación foliar: máscara por rango de temperatura (exclusión suelo/madera)
- Filtro de viento: rampa gradual 4-12 m/s (14-43 km/h) → peso CWSI se reduce linealmente de 35% a 0%. Frames con v_viento ≥ 12 m/s (43 km/h) → descartados del análisis CWSI (ponderación HSI = 0 para termografía)

**2.5 Trunk diameter variation (TDV) measurement**
- Máxima Contracción Diaria (MDS): MDS = D_max_noche − D_min_día
- Normalización: MDSNORM = MDS / media_7_días
- Correlación MDS–Ψ_stem documentada: R²=0.71–0.85 (vid, Fernández & Cuevas 2010)

**2.6 HSI — HydroVision Stress Index**
- HSI = w_cwsi · CWSI + (1 − w_cwsi) · f(MDS_NORM)
- w_cwsi = max(0, 1 − v_viento/4)
- Cálculo a las 13:00 hs (máximo estrés diario)

**2.7 Scholander pressure chamber measurements (reference method)**
- Bomba de presión PMS Instrument Co. (Santa Barbara, CA)
- Ψ_stem: hoja penúltima madura, equilibrada en cámara de papel de aluminio 90 min antes de la medición
- Ventana: 10:00–13:00 hs solar
- n ≥ 5 plantas por zona por sesión
- 4 sesiones: Sep–Oct 2026, Ene 2027, Feb 2027, Mar 2027 (OED D-óptimo)
- Restricciones post-lluvia: <2 mm → sin restricción; 3–10 mm → esperar 24–36 h; >10 mm → esperar 48–72 h

**2.8 Statistical analysis**
- Regresión lineal simple y múltiple: Ψ_stem ~ CWSI, Ψ_stem ~ HSI
- R², RMSE, MAE para ambos modelos
- Comparación de pendientes por zona RDI (ANCOVA)
- Software: R 4.x (lm, ggplot2) o Python (statsmodels, sklearn)

### 4.4 Results (2.000–2.500 palabras)

**3.1 Microclimate characterization**
- VPD diario promedio por sesión (kPa), T_aire, HR
- Distribución de condiciones de viento y % de frames válidos para CWSI

**3.2 CWSI baseline calibration**
- Figura 1: ΔT_LL vs. VPD para 5 zonas — punto de corte zona A (plena hidratación)
- Tabla 1: Coeficientes a, b de la línea base inferior con IC 95%
- Resultado esperado: ΔT_LL_Malbec = −0.55 − 0.95·VPD (valores tentativos basados en bibliografía; a confirmar con datos)

**3.3 CWSI–Ψ_stem relationship**
- Figura 2: Diagrama de dispersión CWSI vs. Ψ_stem, todos los pares válidos (n esperado: 80–100)
- Tabla 2: R², RMSE, pendiente por sesión y global
- Resultado esperado: Ψ_stem = −0.4 − 1.8·CWSI (R² ≈ 0.60–0.75)
- Comparación con bibliografía: Araújo-Paredes 2022 (R²=0.49–0.65), Pires 2025 (R²=0.70–0.82)

**3.4 HSI vs. CWSI — improvement from fusion**
- Figura 3: Comparación R² (CWSI solo) vs. R² (HSI) por condición de viento
- Condición de alto viento (v > 3 m/s): esperado CWSI R²↓ 0.35, HSI R²↑ 0.72
- Condición sin viento: esperado CWSI R²=0.70, HSI R²=0.73 (mejora marginal)
- Tabla 3: RMSE (MPa) por índice y condición

**3.5 Operational thresholds**
- Tabla 4: Umbrales CWSI_alerta y CWSI_rescate calibrados para Malbec Córdoba
- Comparación con valores publicados para otras regiones
- Figura 4: Curva de riesgo — probabilidad de Ψ_stem < −1.5 MPa en función del CWSI

**3.6 Phenological modulation of CWSI thresholds (GDD)**
- Figura 5: CWSI vs. Ψ_stem por estadio fenológico (GDD sets A, B, C)
- Cambio de pendiente entre floración/cuaje vs. pre-cosecha

### 4.5 Discussion (1.200–1.500 palabras)

**Párrafo 1:** ¿El R² obtenido supera el estado del arte UAV (Araújo-Paredes, Pires)? Si sí → el monitoreo continuo fijo genera más datos para el ajuste. Si no → discutir limitaciones del MLX90640 (baja resolución vs. cámara UAV de laboratorio).

**Párrafo 2:** El viento como fuente de error en CWSI — justificación empírica del umbral 4 m/s. Comparar con Taghvaeian et al. 2014 (umbral 3 m/s en alfalfa).

**Párrafo 3:** La fusión HSI recupera la capacidad predictiva en condiciones de viento → relevancia práctica para regiones con viento Zonda (Mendoza) y viento Norte (Córdoba).

**Párrafo 4:** Limitaciones del trabajo: resolución espacial del MLX90640 (32×24 pixels → ¿suficiente para Malbec en espaldera?), n de plantas por zona, una sola variedad y sitio. Proyección a otras variedades (§5 — tabla de adaptación, doc 05).

**Párrafo 5:** Implicancias prácticas — ahorro de agua vs. monitoreo Scholander manual. Costo-beneficio del sistema HydroVision AG para el productor. *[PRECAUCIÓN: no mencionar cifras de ahorro de m³ sin el análisis del doc 08 — verificar consistencia]*

### 4.6 Conclusions (300–400 palabras)

1. Primera calibración cuantitativa CWSI–Ψ_stem para Malbec argentina en condiciones de campo real
2. Umbral operativo validado: CWSI > X.XX → Ψ_stem < −1.5 MPa con X% de correctas clasificaciones
3. La fusión LWIR+extensómetro (HSI) mejora R² en condiciones de viento de X.XX a X.XX
4. El motor GDD es necesario para mantener precisión del umbral a lo largo del ciclo
5. Los coeficientes son válidos para Colonia Caroya, Córdoba; se requieren calibraciones regionales para Valle de Uco y San Juan

### 4.7 Acknowledgements

"The authors thank Javier and Franco Schiavoni for field technical assistance and careful execution of irrigation protocols at the experimental vineyard. This research was supported by [ANPCyT STARTUP 2025 TRL 3-4, grant N°X]. M.I.M. acknowledges CONICET for doctoral and postdoctoral support."

### 4.8 Data Availability Statement

"The calibrated CWSI coefficient dataset for Malbec (Colonia Caroya, Córdoba) will be deposited in [Repositorio Digital INTA / Zenodo] upon acceptance. Raw LWIR frames and trunk extensometer time series are available from the corresponding author upon reasonable request."

**Nota para César:** Los coeficientes específicos por variedad y región son un secreto comercial de HydroVision AG. Lo que se publica son los coeficientes del experimento de Colonia Caroya con Malbec, que ya estarán documentados públicamente en la memoria de TRL. Los coeficientes derivados para otras variedades y regiones **no se publican** en este paper y quedan en el repositorio privado de la empresa.

---

## 5. CRONOGRAMA DE REDACCIÓN

| Hito | Fecha estimada | Responsable | Dependencia |
|---|---|---|---|
| Draft Methods (completo) | Julio 2026 | Monteoliva | Diseño experimental confirmado |
| Draft Introduction + Discussion (estructura) | Agosto 2026 | Monteoliva | — |
| Sesión 1 Scholander ejecutada | Octubre 2026 | Javier/Franco + Monteoliva | Brotación confirmada |
| Análisis preliminar datos S1 | Noviembre 2026 | el investigador Art. 32 | Pipeline PINN disponible |
| Sesión 2 Scholander ejecutada | Enero 2027 | Javier/Franco | GDD ≥ 450 (pre-envero) |
| Draft Results preliminar (S1+S2) | Febrero 2027 | Monteoliva + Inv. Art. 32 | — |
| Sesiones 3 y 4 completadas | Marzo 2027 | Javier/Franco | GDD ≥ 650 y ≥ 850 |
| Análisis estadístico final | Abril 2027 | el investigador Art. 32 | Dataset completo (≥80 pares) |
| Draft completo v1.0 | Mayo 2027 | Monteoliva (lead) | — |
| Revisión interna HydroVision AG | Junio 2027 | César Schiavoni | Chequeo de secretos comerciales |
| Submission | Julio 2027 | Monteoliva | — |
| Respuesta editorial esperada | Oct–Nov 2027 | — | — |

---

## 6. FIGURAS DEL PAPER (lista preliminar)

| Figura | Descripción | Datos fuente | Software |
|---|---|---|---|
| Fig. 1 | Diagrama esquemático del nodo y diseño experimental de las 5 zonas | Ilustración | Inkscape / Python matplotlib |
| Fig. 2 | ΔT_LL vs. VPD — línea base inferior calibrada para Malbec Córdoba | Datos sesión 1+2 | Python seaborn |
| Fig. 3 | Dispersión CWSI vs. Ψ_stem — todos los pares, coloreados por zona RDI | Datos 4 sesiones | R ggplot2 |
| Fig. 4 | Comparación R² CWSI vs. HSI por condición de viento | Datos 4 sesiones | Python matplotlib |
| Fig. 5 | Umbral de riesgo — P(Ψ<−1.5 MPa) ~ CWSI con bandas de confianza | Modelo logístico | R |
| Fig. 6 | Modulation de pendiente CWSI–Ψ_stem por estadio fenológico (GDD) | Datos 4 sesiones | Python |

---

## 7. TABLA DE BALANCE — PUBLICABLE vs. SECRETO COMERCIAL

| Elemento | ¿Publicar? | Razón |
|---|---|---|
| Coeficientes CWSI Malbec Córdoba (este experimento) | **SÍ** | Es el aporte científico principal — sin publicar, no hay paper |
| Coeficientes por variedad y región (tabla §2 del doc 05) | **NO** | Secreto comercial — ventaja competitiva HydroVision AG |
| Fórmula HSI general (w_cwsi con viento) | **SÍ** | Innovación publicable — diferenciación técnica |
| Parámetros específicos del modelo PINN (λ, arquitectura) | **NO** | Secreto comercial — protección de IP |
| Protocolo Scholander simplificado (sin el Excel del sistema) | **SÍ** | Aporta a comunidad científica |
| Diseño de hardware del nodo (componentes generales) | **SÍ** | Referencia de métodos |
| Firmware completo o código fuente del edge | **NO** | Repositorio privado HydroVision AG |

---

*Dra. Mariela Inés Monteoliva — INTA EEA Córdoba / CONICET — Abril 2026*
