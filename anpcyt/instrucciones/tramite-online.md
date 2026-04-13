# Formulario TAD — HydroVision AG
## Convocatoria Startup 2025 TRL 3-4 — ANPCyT / FONARSEC

---

## A0) OBJETIVO:

Desarrollar y validar en campo (TRL 4) el prototipo integrado del nodo HydroVision AG: un sistema autónomo de detección temprana de estrés hídrico en cultivos de alto valor (vid, olivo, pistacho, cerezo, nogal) que combina termografía infrarroja (índice CWSI), dendrometría de tronco (índice MDS) y fusión satelital multi-fuente (Sentinel-2 / SAOCOM 1A-1B CONAE Argentina / Sentinel-1 / Planet) en un nodo permanente de campo con procesamiento 100% edge sin internet, generando el índice HSI (HydroVision Stress Index, R²=0.90–0.95) con alertas automáticas de rescate hídrico en tiempo real. El protocolo experimental se ejecutará en el viñedo propio de Colonia Caroya (Córdoba, 1/3 ha Malbec) bajo supervisión de la Dra. Mariela Monteoliva (INTA-CONICET), produciendo el dataset de calibración propio (≥800 frames térmicos con potencial hídrico de tallo medido simultáneamente por bomba de Scholander) requerido para el entrenamiento final del modelo PINN embebido (MobileNetV3-Tiny INT8) y para la validación comercial del motor de propuesta automatizada R15 con productores en Mendoza y San Juan.

---

## A) INNOVACIÓN

### A1) Explique qué hace única a su solución respecto de otras disponibles en el mercado.

HydroVision AG es la primera plataforma de América Latina que mide el estado hídrico fisiológico real de la planta —no el suelo, no el entorno— de forma continua, autónoma y en tiempo real, combinando termografía infrarroja y dendrometría de tronco en un nodo permanente de campo con procesamiento edge sin internet.

Cuatro diferenciadores únicos:

1. **Doble señal fisiológica directa + calibración física dual-referencia — índice HSI:** el sistema fusiona dos señales independientes de estrés hídrico en un solo índice (HydroVision Stress Index). CWSI térmico (cámara MLX90640, ventana solar): correlación R²=0.663 con ψ_stem. MDS dendrométrico (extensómetro de tronco 24/7, incluyendo horas nocturnas y días nublados): R²=0.80–0.92. Fusión HSI ponderada por R²: R²=0.90–0.95. La solución israelí más avanzada del mercado global (Phytech/Netafim) ofrece solo señal dendrométrica (R²=0.82) sin térmica. HydroVision supera técnicamente a Phytech a 1/10 del precio de implementación en escala pequeña. Diferencial de calibración exclusivo: el bracket de cada nodo incorpora dos paneles de referencia físicos dentro del FOV de la cámara — Dry Ref (aluminio negro mate, ε≈0.98) y Wet Ref (fieltro hidrofílico saturado por micro-bomba peristáltica desde reservorio 10L, autonomía 90–120 días) — que permiten calcular el Índice Jones/Ig = (T_canopeo − T_wet) / (T_dry − T_canopeo) directamente en píxeles fijos, 96 veces/día, sin necesidad de visita humana ni modelo meteorológico VPD. El extensómetro de tronco actúa como segunda capa de auto-calibración: cuando llueve y MDS≈0, la temperatura foliar medida confirma el Tc_wet real del nodo. Stack de calibración triple con degradación controlada: Nivel 1 (paneles físicos) → Nivel 2 (lluvia+MDS) → Nivel 3 (histórico NWSB). Sin esta arquitectura, el error del baseline acumula ±0.15–0.20 CWSI silenciosamente a lo largo de la temporada.

2. **Confianza dinámica por viento con mitigación multinivel:** el nodo implementa 9 capas de defensa contra el artefacto de viento (orientación a sotavento, shelter anti-viento SHT31, tubo colimador IR, termopar foliar, buffer térmico con filtro de calma, rampa gradual firmware 4-12 m/s / 14-43 km/h). El CWSI permanece útil hasta 12 m/s / 43 km/h (antes solo hasta 4 m/s). A partir de 12 m/s, el peso se transfiere automáticamente al 100% MDS dendrométrico. El sistema nunca da una alerta falsa por condición meteorológica adversa.

3. **Fusión satelital multi-fuente calibrada (70% menos costo por ha):** el nodo terrestre calibra imágenes satelitales de múltiples fuentes gratuitas y de pago según cultivo, región y condición climática. Fuente principal: Sentinel-2 ESA/Copernicus (10m/px, gratuito, revisita 2–3 días en Cuyo). Fallback en días de nubes: SAOCOM 1A/1B de CONAE Argentina (radar SAR L-band, atraviesa nubes 100%, acceso gratuito para proyectos de I+D argentinos — el único satélite argentino en el stack) y Sentinel-1 ESA (SAR C-band, gratuito). Alta resolución para cultivos compactos (olivo seto, arándano): Planet PlanetScope (3m/px, revisita diaria, compartido entre clientes de la misma zona). Análisis histórico del lote en el onboarding: Landsat 8/9 USGS/NASA (30m/px, gratuito, archivo desde 1972 — 50 años de variabilidad). Un nodo cubre hasta 20 ha en lotes homogéneos con CWSI extrapolado R²=0.63; a densidad óptima 1 nodo/2 ha entrega HSI completo R²=0.90–0.95. La densidad híbrida por zonas permite optimizar el costo sin sacrificar precisión en los sectores críticos.

4. **IA con física incorporada (PINN) sin internet:** el modelo MobileNetV3-Tiny INT8 corre 100% en edge (ESP32-S3) con la ecuación del balance energético foliar embebida en la función de pérdida. Sin nube, sin conectividad, sin suscripción a servidor externo. En zonas sin cobertura celular (Valle de Uco, San Juan, NOA) el sistema funciona igual. Phytech y Saturas dependen de internet 24/7 — si cae la red, cae el sistema.

No existe en Argentina ni en América Latina un sistema comercial que combine termografía foliar continua + dendrometría de tronco (HSI dual-señal) + confianza dinámica por viento + motor fenológico automático + fusión satelital en un nodo autónomo de campo sin dependencia de internet ni de operador.

---

### A2) Relevancia de la problemática — ¿Qué problema resuelve? ¿Por qué es relevante? ¿Tiene impacto regional o nacional?

Cada año, productores de vid, olivo, cerezo, pistacho, nogal y citrus pierden entre el 15% y el 35% de su rendimiento por estrés hídrico detectado demasiado tarde. En Argentina y Chile, el valor de producción en riesgo supera los USD 498 millones anuales. No existe en América Latina un sistema autónomo que detecte este fenómeno en tiempo real con precisión fisiológica.

El impacto es nacional y regional: Argentina cuenta con ~447.700 ha de cultivos de alto valor con riego tecnificado. El NOA y Cuyo concentran el 85% de esa superficie. La crisis hídrica estructural en Mendoza, San Juan y Neuquén hace que la eficiencia en el uso del agua sea una prioridad productiva y ambiental de primer orden. Chile atraviesa una megasequía con Ley de Riego subsidiando reconversión a sistemas presurizados — mercado de expansión directa en Año 2.

Impacto cuantificado: por cada dólar invertido en la suscripción anual, el productor recupera en promedio USD 9,6 en valor rescatado (pérdidas evitadas + bonificación por calidad de exportación). ROI Año 2+ en vid premium Tier 3: 1,24x anual. Payback: 2,4 años. Break-even del negocio HydroVision AG: 800 ha bajo contrato — el 0,18% del mercado nacional disponible.

---

### A3) ¿Nivel actual de desarrollo tecnológico (TRL)?

**TRL 3 — Prueba de concepto analítica y computacional completada.**

El proyecto acredita TRL 3 mediante evidencias documentadas en cinco frentes:

**[1] Prueba computacional (10 módulos Python, 135 tests automatizados, 0 fallos):**
Cultivo de validación: Vid Malbec — Colonia Caroya, Córdoba (~700m s.n.m.).
- `cwsi_formula.py`: CWSI (Jackson et al. 1981) con coeficientes Bellvert et al. (2016) para Malbec. Tres índices: CWSI, Jones/Ig (Jones 1999) y predicción ψ_stem [MPa] (Pires et al. 2025, R²=0.663). Error por NETD 50mK del MLX90640: ±0.019 CWSI, dentro del límite ±0.07 (Araújo-Paredes et al. 2022).
- `thermal_pipeline.py`: pipeline completo frame Y16 → segmentación foliar P20–P75 → CWSI multi-angular ponderado por fracción foliar. 7 ángulos gimbal × 3 ventanas horarias.
- `gdd_engine.py`: motor GDD (Winkler 1974, base 10°C) con detección automática de 9 estadios fenológicos para Malbec. Climatología calibrada con datos reales INTA EEA Manfredi (A872907, 2012–2026, n=4.802 días).
- `synthetic_data_gen.py`: generador de frames Y16 sintéticos (160×120 px) con modelo físico de NETD. Núcleo del simulador para 1.000.000 imágenes de pre-entrenamiento PINN.
- `sentinel2_fusion.py`: modelo de fusión multi-satélite — correlación CWSI↔NDWI/NDVI/NDRE + VPD con HuberRegressor polinomial grado 2 robusto. R²=0.97 en calibración sintética. Selección automática de fuente satelital por lote y fecha: Sentinel-2 (principal, gratuito) → SAOCOM/CONAE Argentina (fallback SAR sin nubes, gratuito para I+D) → Sentinel-1 ESA (SAR C-band) → Planet (3m/px para cultivos compactos, Tier Elite). Análisis histórico de onboarding: Landsat 8/9 (50 años de archivo, gratuito). Demuestra que 1 nodo cubre hasta 20 ha vía satélite en lotes homogéneos.
- `dendrometry.py` [NUEVO]: motor MDS (Maximum Daily Shrinkage = D_max − D_min) con corrección térmica del extensómetro (alpha=2.5 µm/°C, Pérez-López 2008), estimación ψ_stem con R²=0.80–0.92 (Fernández & Cuevas 2010), clasificación 5 niveles de estrés, protocolo de rescate automático si ψ_stem < −1.5 MPa.
- `combined_stress_index.py` [NUEVO]: motor HSI — fusión CWSI térmico (35%) + MDS dendrométrico (65%). Acuerdo de señales (Δψ < 0.35 MPa) → R²~0.90–0.95. Desacuerdo → MDS domina 80%. Señal única → incertidumbre ×1.4. Confianza dinámica por anemómetro (Jones 2004, Fernández et al. 2011).
- `baseline.py` [NUEVO — ML Engineer/03_fusion]: motor de fallback de calibración y detección de deriva del baseline CWSI. Jerarquía: (1°) el panel Wet Ref físico provee T_wet medida directamente en tiempo real — mecanismo primario, sin estimación; (2°) cuando Wet Ref no está disponible, baseline.py estima T_wet por NWSB(Ta,VPD) + offset_EMA actualizado con lluvia+MDS≈0 (learning_rate=0.25) sin visita humana; (3°) detección de deriva autónoma (CWSI <0.02 o >0.98 sostenido, std<0.01). Las sesiones Scholander ya no alimentan este módulo para calibración de T_wet — su rol es validar coeficientes MDS→ψ_stem y etiquetar el dataset PINN. Persiste el estado en JSON ante reinicios.
- `fusion_engine.py` [NUEVO — ML Engineer/03_fusion]: motor HSI con regresión lineal online CWSI=α+β×MDS_norm (ventana 60 muestras/nodo) que aprende la relación local entre señal térmica y dendrométrica durante la temporada. Pesos dinámicos por madurez del historial (mds_maturity=min(1,n_sesiones/20)). Imputación de CWSI desde MDS en días sin ventana solar útil (cwsi_confidence<0.4). Alerta de divergencia automática (|CWSI−MDS_norm|>0.35). Demo: 5 nodos × 30 días × 3 sesiones diarias.
- `optical_health.py` [NUEVO]: módulo de auto-diagnóstico de integridad óptica. Monitorea en cada frame: (1) desviación estándar del histograma térmico para detectar obstrucción por polvo/insecto/empañamiento; (2) validación de temperatura del panel Dry Ref contra curva teórica T(radiación, T_aire) — desviación >1.5°C indica lente contaminado; (3) Índice de Salud Óptica (ISO_nodo 0–100%) reportado al dashboard. Intervención del técnico de campo solo cuando ISO_nodo < 80% — elimina mantenimientos preventivos innecesarios.

**[2] Factibilidad hardware verificada:** MLX90640 breakout integrado (sensor BAB, 110° FOV) entrega frames 32×24 px en ESP32-S3 con NETD ~100 mK. Con 28 píxeles foliares promediados, el error efectivo de CWSI es ±0.008. Extensómetro de tronco (strain gauge + ADS1231 24-bit ADC, resolución 1 µm) es hardware comercial verificado para condiciones de campo en vid (Fernández & Cuevas 2010). Anemómetro RS485 copa (resolución 0.1 m/s) integrado al nodo vía Modbus RTU.

**[3] Análisis de datos públicos externos:** datos tabulares de CWSI y ψ_stem de viñedos (Gutiérrez-Gamboa et al., INIA Chile, cv. Carménère/Cabernet Sauvignon, Valle del Maule; Bellvert et al. 2016, cv. Pinot Noir, Cataluña; datos USDA ARS Ag Data Commons) procesados para verificar coherencia del gradiente térmico foliar bajo distintas condiciones de VPD. Complementados con datos de la Red Agrometeorologica INIA Chile (agrometeorologia.cl) — estaciones con T_air, HR, radiación y viento en zonas vitícolas chilenas — para calibrar los límites ΔT_LL/ΔT_UL bajo el régimen climático de Chile Central. NDVI Sentinel-2 histórico de viñedos chilenos disponible en SpiderWebGIS INIA Chile (sp3.spiderwebgis.org) — fuente de datos para la expansión satelital Año 2.

**[4] Acceso a sitio experimental propio:** 1/3 hectárea de Malbec en Colonia Caroya, Córdoba (propiedad de los padres del co-fundador César Schiavoni), trabajado por Javier y Franco Schiavoni (hermanos de César, productores residentes). Acceso exclusivo e irrestricto. Conversión de riego por canal a riego por goteo con 5 zonas hídricas independientes (solenoides Rain Bird) como contrapartida del equipo — ejecutado en Mes 1–2 del proyecto. Sistema de presión directa por bomba autocebante 0,75 HP: toma agua del canal (acequia) y presuriza el header directamente; tanque australiano 20.000 L como buffer de almacenamiento para turnos nocturnos sin flujo de canal. Sin estructura elevada — el tanque no actúa por gravedad.

**[5] Supervisión científica institucional:** Dra. Mariela Monteoliva (INTA-CONICET, MEBA-IFRGV-UDEA, Córdoba) confirmó participación como responsable del protocolo Scholander en TRL 4. Rol del Scholander en el sistema: no es para calibrar el baseline térmico (T_wet), que es resuelto autónomamente por el panel Wet Ref físico y el extensómetro de tronco (MDS≈0 tras lluvia); su propósito es (a) validar que los coeficientes MDS→ψ_stem de la literatura son correctos para este viñedo y temporada, (b) generar los pares etiquetados (frame térmico + ψ_stem real) indispensables para el entrenamiento del modelo PINN, y (c) medir el R²(HSI vs ψ_stem_Scholander) que es la métrica de validación central del TRL 4.

**Limitación documentada (TRL 3 → TRL 4):** no se dispone aún de hardware integrado funcionando. La validación actual es analítica y computacional. La prueba experimental en campo con el sistema completo es el objetivo de TRL 4.

---

### A4) Describa el estado actual de la tecnología ¿en qué fase está y qué avances ha logrado?

El proyecto se encuentra en **TRL 3 completado**, con todos los componentes del sistema modelados y validados computacionalmente, y el plan experimental de TRL 4 completamente definido.

**Avances logrados:**

**Modelo físico central (CWSI) — implementado y validado:**
La fórmula del Crop Water Stress Index (Jackson et al. 1981) está implementada en Python con coeficientes empíricos calibrados para Malbec (Bellvert et al. 2016, Precision Agriculture). Se validó que:
- Los resultados son coherentes con los rangos publicados en literatura para condiciones de alta insolación similares a Cuyo.
- El sensor MLX90640 (NETD < 50mK) es suficientemente preciso: el error de ±0.019 CWSI está 3,7 veces por debajo del límite de discriminación agronómica (±0.07).
- Se implementaron tres índices complementarios: CWSI (Jackson 1981), Índice Jones/Ig (Jones 1999, validado en vid por Gutiérrez et al. 2018, PLoS ONE) y predicción de potencial hídrico de tallo ψ_stem en MPa (Pires et al. 2025, Computers & Electronics in Agriculture; R²=0.663).

**Motor fenológico GDD — implementado y calibrado:**
Acumulación de grados-día (Winkler 1974, base 10°C) con detección automática de 9 estadios fenológicos para Malbec y umbrales CWSI de alerta diferenciados por estadio (0.30 en floración → 0.85 en pre-cosecha). Calibrado contra datos reales de la estación INTA EEA Manfredi (código A872907, 2012–2026, n=4.802 días), con corrección altitudinal de −2.2°C para Colonia Caroya (~700m).

**Dendrometría de tronco, índice HSI y auto-calibración cruzada — implementados:**
Motor MDS completo con corrección térmica del extensómetro, estimación ψ_stem (R²=0.80–0.92, Fernández & Cuevas 2010), 5 niveles de clasificación de estrés, evaluación de recuperación nocturna (umbral 80%) y protocolo de rescate automático. Motor HSI de fusión adaptativa validado contra 135 tests automatizados: acuerdo de señales → R²~0.90–0.95; desacuerdo (Δψ > 0.35 MPa) → MDS domina 80/20; rampa gradual viento 4-12 m/s (14-43 km/h) → reducción progresiva del peso CWSI, ≥12 m/s (43 km/h) → 100% MDS. Motor de auto-calibración dinámica del baseline CWSI implementado (baseline.py): el extensómetro de tronco actúa como referencia fisiológica de la cámara térmica — cada evento de lluvia con MDS≈0 genera una calibración automática del Tc_wet sin visita humana, y el sistema detecta deriva del baseline antes de que el error afecte las alertas de riego. Motor HSI con regresión online (fusion_engine.py): aprende la relación local CWSI↔MDS_norm por nodo durante la temporada, permitiendo imputar el CWSI en días sin ventana solar y detectar divergencias entre sensores de forma autónoma.

**Fusión satelital multi-fuente — principio demostrado:**
R²=0.97 en calibración con datos sintéticos. Arquitectura multi-satélite con selección automática por disponibilidad y cultivo: Sentinel-2 ESA (10m/px, gratuito, primario para vid/olivo/frutales) · SAOCOM 1A/1B CONAE Argentina (SAR L-band, gratuito I+D, fallback 100% penetración de nubes — satélite argentino, alineado con soberanía tecnológica FONARSEC) · Sentinel-1 ESA (SAR C-band, gratuito, fallback complementario) · Planet PlanetScope (3m/px, diario, para olivo superintensivo y arándano donde Sentinel-2 es insuficiente) · Landsat 8/9 USGS (30m/px, 50 años de archivo, análisis histórico de onboarding). Demuestra que 1 nodo cubre hasta 20 ha en lotes homogéneos (error CWSI ±0.12–0.15) o 1–2 ha con HSI completo (error ±0.07–0.09).

**Validación científica externa (Dra. Mariela Monteoliva, INTA-CONICET):**
"El monitoreo del estrés hídrico en vides a través de imágenes térmicas ya ha sido documentado en numerosos trabajos, incluyendo diversos cultivares y regiones. Además, se ha reportado previamente una correlación aceptable entre los parámetros termométricos de las imágenes con mediciones de conductancia (pérdida de agua foliar) y potencial hídrico (agua disponible en tallos y hojas), sustentando su validez para la aplicación de estos parámetros en este proyecto."

**Próximos pasos (TRL 4 — financiado por esta convocatoria):**
- Prototipo hardware integrado: MLX90640 + ESP32-S3 + SHT31 + anemómetro RS485 + extensómetro de tronco (strain gauge + ADS1231 + DS18B20) + GPS u-blox + SX1276 (EBYTE E32-900T20D) LoRa + panel solar. Autonomía objetivo ≥72 horas continuas.
- Validación en campo controlado: 4 filas Malbec 136m (544 vides), 5 zonas hídricas independientes (solenoides Rain Bird), 5 nodos permanentes (uno por zona), gimbal motorizado captura 7 ángulos cada 15 min en forma continua 24/7 — sin movilización del equipo entre capturas.
- Dataset de calibración propio: 800 frames reales bajo protocolo Scholander (Dra. Monteoliva). Target: error CWSI < ±0.10. Modelo PINN MobileNetV3-Tiny INT8, accuracy > 85% en 120 frames de validación independiente.

---

### A5) ¿Cuenta con propiedad intelectual registrada o en trámite?

No se cuenta con propiedad intelectual registrada a la fecha de presentación. La solicitud de patente de invención ante el INPI Argentina está prevista para el Mes 9 del proyecto financiado, una vez demostrado el sistema integrado en TRL 4 y generado el dataset de calibración propio. El objeto de protección será el método de detección de estrés hídrico en cultivos de alto valor mediante: (1) índice HSI — fusión adaptativa de termografía LWIR (CWSI) + dendrometría de tronco (MDS) con confianza dinámica por viento; (2) motor GDD fenológico automático con ajuste de umbrales por estadio; (3) fusión satelital multi-fuente calibrada por el nodo (Sentinel-2 / SAOCOM / Sentinel-1 / Planet) con selección automática por disponibilidad y tipo de cultivo; todo en nodo autónomo de campo con procesamiento 100% edge sin dependencia de internet. Se evaluará también la solicitud en USA (USPTO) para protección en el mercado chileno y peruano en TRL 5.

---

### A6) Propuesta de Valor

HydroVision AG permite al productor de cultivos de alto valor detectar el estrés hídrico fisiológico 5–10 días antes del síntoma visual, operando autónomamente 24/7 sin intervención humana ni conexión a internet. El índice HSI (fusión CWSI térmico + MDS dendrométrico) eleva la correlación con ψ_stem a R²=0.90–0.95, frente al R²=0.63 de soluciones de señal térmica única y al R²=0.82 de Phytech (Israel) sin señal térmica. Por cada dólar invertido en el servicio, el productor recupera en promedio USD 9,6 en valor rescatado (pérdidas evitadas + bonificación calidad exportación). ROI Año 2+ en vid premium: 1,24x anual sobre la suscripción (payback 2,4 años). El punto de equilibrio del negocio HydroVision AG se alcanza con 800 ha bajo contrato recurrente — el 0,18% del mercado nacional disponible. A escala comparable de implementación, HydroVision resulta entre 31% y 64% más barato que Phytech/Netafim en Argentina, con mayor precisión de señal y soporte local en 24 horas.

---

### A7) Compare con otras soluciones en el mercado

| Solución | Señal de estrés | Continuo 24/7 | Costo ha/año (arg.) | Limitación crítica |
|---|---|---|---|---|
| **HydroVision AG** | **CWSI térmico + MDS dendrométrico (HSI dual) · R²=0.90–0.95** | **Sí — edge, sin internet** | **USD 80–650** | Hardware en desarrollo (TRL 4) |
| Phytech / Netafim (Israel) | MDS dendrométrico solo · R²=0.82 | Sí — requiere internet 24/7 | USD 400–900 + suscripción + Starlink | Sin señal térmica. 10× más caro en escala pequeña. Sin soporte local. Coeficientes no calibrados para Argentina (calibrados en Israel/California). Calibración del baseline MDS por heurística post-lluvia sin verificación fisiológica real (no mide ψ_stem). Solo bodegas grandes. Si cae internet, cae el sistema. |
| Saturas (Israel) | Psicrometría de tallo · directo | Sí — requiere internet | USD 600–1.400 | Invasivo (perforación del tallo). Sin alertas automáticas. Sin soporte en Argentina. |
| Satélite solo (Sentinel-2) | NDVI/NDWI — indirecto | Cada 5 días | Gratuito | Nubes bloquean 8–15 días. No detecta cierre estomático. Sin calibración de campo → error alto. HydroVision usa Sentinel-2 + SAOCOM + Planet + Landsat como stack integrado calibrado por el nodo. |
| Dron con operador | Térmica puntual | 1–2 vuelos/semana | USD 800–2.000/vuelo | Requiere piloto ANAC. No opera con viento ni lluvia. |
| Tensiómetro de suelo | Tensión matricial suelo | Sí | USD 200–500 | Mide suelo, no planta. Desfase 2–5 días. |
| Observación visual | Síntoma visible | No | Sin costo | El daño ocurre 5–10 días antes del síntoma visible |

No existe en Argentina ni en América Latina ningún sistema comercial que combine termografía foliar continua + dendrometría de tronco (HSI dual-señal) + auto-calibración cruzada del baseline CWSI sin visita humana + confianza dinámica por viento + motor fenológico automático + fusión satelital en un nodo autónomo de campo sin dependencia de internet ni de operador.

**Sobre calibración del baseline — diferencia técnica clave con Phytech:** Phytech también necesita una referencia de "planta sin estrés" para anclar su MDS. La obtiene por heurística post-lluvia o post-riego abundante: asume que en esos días el MDS mínimo equivale a "sin estrés". No mide ψ_stem, no verifica fisiológicamente, y sus coeficientes de conversión MDS→ψ_stem están calibrados para variedades israelíes y californianas — no recalibrados para Malbec en Cuyo ni para ninguna variedad argentina. HydroVision hace exactamente lo mismo (lluvia → MDS≈0 → referencia de planta bien hidratada) pero con tres diferencias decisivas: (1) el extensómetro confirma que el MDS realmente llegó a cero, no lo asume; (2) cada sesión Scholander verifica fisiológicamente con ψ_stem real y actualiza el modelo; (3) los coeficientes son recalibrados para Malbec en Colonia Caroya/Cuyo por la Dra. Monteoliva (INTA-CONICET). El baseline de Phytech en Argentina es una extrapolación israelí sin validación local. El de HydroVision es específico del nodo, la variedad y el microclima.

---

### A8) ¿Existe una demanda real identificada?

Sí. La demanda está validada en dos dimensiones:

**Cuantitativa:** ~447.700 ha de cultivos de alto valor con riego tecnificado en Argentina (vid 200.000 ha · citrus 130.000 ha · olivo 70.000 ha · pistacho 25.000 ha · nogal 15.000 ha · otros 7.700 ha), más ~307.000 ha en Chile. Ninguna cuenta con monitoreo hídrico foliar autónomo. El valor de producción en riesgo supera USD 498 millones anuales. La solución israelí más avanzada (Phytech/Netafim) no penetró el mercado latinoamericano por precio prohibitivo, barreras de importación, dependencia de internet en zonas rurales y ausencia de soporte local — dejando el segmento mediano (20–200 ha) sin cobertura.

**Cualitativa:** entrevistas preliminares con productores de vid en Colonia Caroya y Mendoza confirman disposición a pagar por detección de estrés antes del síntoma visible. El principal freno identificado es el costo de implementación — que el modelo de fusión satelital con densidad híbrida reduce sustancialmente. El plan de validación comercial (Resultado R10) incluye entrevistas estructuradas con al menos 5 productores en Mendoza y San Juan durante la ejecución, más un motor de propuesta automatizado (R15) que genera el mapa de nodos y ROI del cliente en < 5 minutos con solo las coordenadas GPS del campo.

---

## B) ESCALABILIDAD

### B1–B2) Participación e Inversión Privada Recibida

No se ha recibido inversión privada externa a la fecha de presentación. El proyecto es financiado íntegramente por los socios fundadores (César Schiavoni 55% · Lucas Bergon 45%) mediante aporte en especie: (a) estación de trabajo IA — Intel Core i7-12700K + NVIDIA RTX 3070 8GB + 32GB RAM, valorización mercado secundario USD 2.500; (b) viñedo experimental Colonia Caroya 1/3 ha, acceso exclusivo con agua y electricidad y cooperación en protocolo de estrés hídrico, valorización USD 5.000; (c) horas de dedicación en especie — César Schiavoni Director IA 434 hs × USD 25/hs + Lucas Bergon COO/Hardware 116 hs × USD 40/hs, total USD 15.500; (d) material vegetal experimental — 1.360 vides Malbec establecidas, valorización USD 5.440; (e) merma experimental de cosecha por protocolo de déficit hídrico controlado, valorización USD 2.500; (f) herramientas de instalación y campo — kit propiedad de los fundadores cedido al proyecto (barrenador, taladro, cables, multímetro, etc.), valorización USD 400; (g) tablet Android 4G dedicada a monitoreo de campo Mes 4–9, valorización USD 450; (h) equipamiento técnico adicional — Lucas Bergon / MBG Controls, pendiente de definir, valorización USD 710. Total aportes en especie: USD 30.000 (cumple exactamente el mínimo del 20% requerido). Pacto de socios con vesting de 4 años, cliff de 12 meses — en redacción. HydroVision AG SAS se constituirá en el Mes 1 del proyecto financiado.

Inversores objetivo post-TRL 4: The Yield Lab LATAM (fondo AgTech LAC), Innventure (Argentina), Pampa Start, y convocatorias ANPCyT TRL 5-6. Los resultados del TRL 4 son el material de presentación para esas rondas.

---

### B3) Modelo de Negocios

**Fuentes de ingresos (modelo dual hardware + SaaS):**

- **Hardware (venta única, margen positivo):** USD 950/nodo Tier 1 Monitoreo (CWSI + MDS + anemómetro + fusión satelital) · USD 1.000/nodo Tier 2-3 (+ relé SSR + solenoide Rain Bird integrados en el nodo). COGS Tier 1-2: ~USD 149/nodo (lote 50, arquitectura modular TRL4); Tier 3: ~USD 165/nodo. Margen hardware: USD 801/nodo Tier 1 (84%). A escala de producción (500+ unidades, bare chip + PCB custom): COGS estimado ~USD 121/nodo — margen escala > 87%.
- **Software (suscripción anual recurrente):** USD 80–110/ha/año (Tier 1 Monitoreo) · USD 130–170/ha (Tier 2 Automatización) · USD 220–290/ha (Tier 3 Precisión). Servicios Elite (dron, consultoría) como add-ons sobre cualquier tier. Margen bruto recurrente: 58% (Año 1) → 72% (Año 2) → 81% (Año 3+).
- **Conectividad de campo:** LoRaWAN privado (gateway RAK7268, sin costo mensual). Starlink Mini solo para el equipo de investigación durante campañas en zonas sin cobertura — no trasladado al cliente en producción.

**Estructura de costos principales:**
- Manufactura de nodos TRL4: arquitectura modular (ESP32-S3 DevKit + breakouts I2C/SPI) ensamblada en MBG Controls (Colonia Caroya) — sin PCB custom, sin dependencia de fabricantes externos para el prototipo.
- Infraestructura cloud: FastAPI + PostgreSQL/PostGIS + stack satelital multi-fuente (Copernicus Data Space API para Sentinel-2/Sentinel-1 gratuito · Google Earth Engine para procesamiento en nube · convenio CONAE para SAOCOM · Planet API compartida por zona como add-on). USD 720–960/año en régimen inicial para las fuentes gratuitas; Planet API (~USD 300/zona/año) activada solo en cultivos que lo requieren (olivo superintensivo, arándano) y distribuida entre los clientes de esa zona.
- Soporte técnico de campo: Lucas Bergon (residente Colonia Caroya) cubre zona Córdoba; network de técnicos regionales para Mendoza y San Juan en Año 2+.
- Desarrollo de software: equipo técnico financiado por ANR + uso intensivo de Claude Code (reduce tiempo de desarrollo 40%).

---

### B4) Proyección de Rentabilidad

- **Punto de equilibrio:** 800 ha bajo contrato recurrente (USD 95/ha/año promedio Tier 1) = USD 76.000 ARR. Equivale al 0,18% del mercado nacional disponible. El hardware genera margen positivo (USD 146/nodo), cubriendo ~90% de los costos fijos en el año de venta — reduce el break-even respecto a modelos de hardware subsidiado.
- **Margen bruto recurrente:** 58% (Año 1, 500 ha) → 72% (Año 2, 2.500 ha) → 81% (Año 3, 10.000 ha).
- **Proyección post-ANPCyT:**
  - Año 1 (TRL 5): 500 ha · USD 47.500 ARR · COGS USD 20.000 · Margen 58%
  - Año 2 (TRL 6): 2.500 ha · USD 260.000 ARR · COGS USD 72.000 · Margen 72%
  - Año 3 (TRL 7): 10.000 ha · USD 1.100.000 ARR · COGS USD 210.000 · Margen 81%
- **ROI del productor:** 1,24x anual sobre la suscripción en Tier 3 (USD 31.500 beneficio / USD 25.500 suscripción en 100 ha vid premium). Payback total Año 1: 2,4 años. Churn rate esperado < 10% por alto ROI verificable desde la primera cosecha.

---

### B5) Mercado

- **TAM (Mercado Total):** 34,5 millones de hectáreas a nivel global en cultivos de alto valor con riego tecnificado.
- **SAM (Mercado Direccionable):** ~750.000 ha en Argentina y Chile con infraestructura de riego compatible (goteo/microaspersión). Mercado potencial ampliado a >1.150.000 ha al incorporar Perú (Año 3).
- **SOM (Objetivo Año 3):** 5.300 ha (~1,2% del SAM). Facturación proyectada: USD 583.000 ARR con mix vid premium, olivo y pistacho en Mendoza, San Juan y NOA. Estimación conservadora (doc-10-analisis-venture).

---

### B6) Clientes objetivo y canal de comercialización

**Clientes primarios:** productores de vid, olivo, cerezo, pistacho, nogal y citrus con riego tecnificado y superficie ≥5 ha. Perfil: mediano productor tecnificado (20–200 ha), riego por goteo instalado, acceso a smartphone. Exactamente el segmento que Phytech/Netafim no puede servir por precio y barreras de importación.

**Canal de acceso:**
- Año 1: venta directa — viñedo propio en Colonia Caroya como caso de demostración presencial. Red de contactos del equipo fundador en Córdoba y Mendoza.
- Año 2: red de advisors agronómicos (ing. agrónomos independientes con cartera de productores). Comisión por venta referida. Motor de propuesta automatizado (R15): el advisor ingresa coordenadas GPS del campo y entrega al cliente un mapa de nodos + ROI personalizado en < 5 minutos, sin depender del equipo técnico de HydroVision.
- Año 3+: distribuidores de insumos agrícolas y empresas de riego (Rain Bird, Netafim distribuidores locales) como canal B2B2C. Convenios con Sociedades Rurales regionales para despliegue masivo en lotes de productores asociados.
- Instalación: técnico de campo instala el primer nodo (2 horas, incluido en el precio). Los nodos adicionales los activa el productor con código QR — costo de instalación incremental USD 0.

---

### B7) Plan de Validación Técnica y Comercial

**Validación técnica (TRL 4 — financiado por esta convocatoria):**
- Mes 3–4 (pre-campaña): conversión del viñedo experimental (riego canal → goteo por fila con 5 zonas hídricas independientes, solenoides Rain Bird). Ejecutado por Javier y Franco Schiavoni como contrapartida del equipo.
- Prototipo hardware integrado: MLX90640 + ESP32-S3 + SHT31 + anemómetro RS485 + extensómetro de tronco (strain gauge + ADS1231 + DS18B20) + GPS u-blox + SX1276 (EBYTE E32-900T20D) LoRa + panel solar. Autonomía objetivo ≥72 horas continuas.
- 5 nodos permanentes en 4 filas experimentales de Malbec (544 vides), 5 regímenes hídricos independientes (100% ETc → sin riego). Captura continua 24/7: 7 ángulos gimbal × 96 ciclos/día × 5 nodos. Dataset etiquetado: 20 pares directos Scholander (4 sesiones OED × 5 zonas) + miles de frames con ψ_stem estimado por MDS dendrométrico.
- Potencial hídrico de tallo medido con bomba de Scholander bajo protocolo Dra. Monteoliva (INTA-CONICET). Target: error CWSI predicho vs. medido < ±0.10.
- Dataset de calibración propio: 800 frames reales. Modelo PINN MobileNetV3-Tiny INT8. Accuracy > 85% en set de validación independiente de 120 frames.
- Validación del índice HSI en campo: coherencia entre CWSI medido y MDS dendrométrico en las 5 zonas hídricas. Protocolo de desacuerdo de señales verificado con eventos de viento Zonda simulado.

**Validación comercial (TRL 4 — paralela a la técnica):**
- Entrevistas estructuradas con ≥5 productores de vid y olivo en Mendoza y San Juan (Resultado R10).
- Motor de propuesta automatizada (R15): análisis multi-satélite histórico de ≥3 campos de productores candidatos — Landsat 8/9 (10 años de variabilidad NDVI) + Sentinel-2 (últimas 3 temporadas) para estratificar homogeneidad del lote por zonas, calcular densidad híbrida recomendada y estimar ROI personalizado. Generación de mapa de nodos + propuesta en PDF en < 5 minutos. Validación del pipeline de pre-venta con al menos 2 productores candidatos en Mendoza y San Juan.
- Instalación del sistema en el viñedo propio como caso de demostración para visitas de potenciales clientes. Objetivo: 2 visitas de productores documentadas antes del Mes 12.

---

### B8) Riesgos principales y mitigación

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Calibración CWSI para Malbec en Córdoba — coeficientes Bellvert (2016) para Pinot Noir en Cataluña pueden tener error sistemático en condiciones de VPD cordobés | Alta | Protocolo experimental con Dra. Monteoliva: recalibración de ΔT_LL/ΔT_UL midiendo ≥30 pares (ΔT, VPD) en plantas bajo riego completo. Motor de auto-calibración dinámico (baseline.py): cada evento de lluvia con MDS≈0 provee una calibración automática del Tc_wet real del nodo, sin visita humana — el error sistemático se corrige progresivamente durante la temporada. Detección de deriva activa: si el CWSI se desplaza fuera de rango, el sistema alerta antes de que el error afecte decisiones de riego. Plan B: Dr. Facundo Calderón, INTA EEA Junín, Mendoza. |
| Baja adopción por productores conservadores | Media | Motor de propuesta automatizado (R15) entrega ROI personalizado del campo del cliente antes de la primera reunión. Primer nodo subsidiado como caso demo en Año 1. |
| Dependencia tecnológica (Melexis descontinúa MLX90640) | Baja | Arquitectura modular: footprint TO39 compatible con MLX90641 (16×12 px) y Heimann HMS-C11L (16×16 px). Config.h: cambiar `SENSOR_TERMICO` — sin cambios en PCB ni firmware. |
| Desacuerdo persistente entre señales CWSI y MDS | Media | El índice HSI tiene 5 modos de operación documentados (FULL_AGREEMENT, DISAGREEMENT, THERMAL_ONLY, DENDRO_ONLY, NO_DATA). El desacuerdo no detiene el sistema — activa el modo DISAGREEMENT con MDS dominante (80%) y alerta de revisión al agrónomo. |
| Demora en validación TRL 4 por estacionalidad | Alta | Cronograma ajustado a ventana fenológica Malbec (octubre–marzo). Buffer de 2 temporadas en el plan. El viñedo experimental es de acceso exclusivo — no hay dependencia de terceros para coordinar fechas. |
| Cobertura de campo (conectividad) | Baja | LoRaWAN privado (gateway RAK7268) como infraestructura principal — sin dependencia de operadoras celulares. Starlink Mini como backup en campañas de validación. |
| Nubosidad excesiva bloquea Sentinel-2 (Río Negro, Chile, Perú) | Media | Stack multi-satélite con fallback automático: SAOCOM 1A/1B CONAE (SAR L-band, atraviesa nubes 100%, gratuito para I+D argentino) → Sentinel-1 ESA (SAR C-band, gratuito). En días nublados, el MDS dendrométrico del nodo actúa como señal principal de ψ_stem sin dependencia satelital. |
| Sentinel-2 insuficiente para olivo superintensivo o arándano (píxel 10m > filas 1.5m) | Media | Stack complementado con Planet PlanetScope (3m/px, diario). Costo compartido entre clientes de la misma zona (~USD 300/zona/año ÷ productores). Activado como add-on para cultivos que lo requieren. |

---

### B9) Sostenibilidad

**Ambiental:** reducción proyectada del 15–25% en consumo de agua de riego por prescripción diferencial (RDI asistido por HSI). Habilitación de créditos de carbono por eficiencia hídrica cuantificada (Verra VCS, Gold Standard — Año 3+). Compatible con certificaciones de huella hídrica (ISO 14046) y exigencias de exportación a la UE (Farm to Fork). Alineado con ODS 6 (agua limpia) y ODS 2 (productividad agrícola). El uso de SAOCOM (satélite argentino CONAE) en el stack tecnológico refuerza la soberanía tecnológica nacional en observación de la Tierra aplicada al agro — objetivo explícito del FONARSEC.

**Económica:** margen bruto >78% en operación recurrente estable (Año 3+). Año 1: 58%. Hardware con margen positivo (USD 146–149/nodo) — sin subsidio de hardware. Modelo SaaS con churn rate bajo por alto ROI verificable del cliente (USD 9,6 recuperados por cada dólar invertido; ROI anual 1,24x en Tier 3). Break-even a 800 ha (0,18% del mercado). Manufactura local en Córdoba (MBG Controls) reduce exposición cambiaria y genera empleo técnico local.

**Organizativa:** equipo interdisciplinario con perfiles en IA/software (MercadoLibre), electrónica industrial embebida (MBG Controls, 15 años, 150+ proyectos), e investigación en fisiología vegetal del estrés hídrico (INTA-CONICET). Ambos socios fundadores residentes o con vínculo directo en Colonia Caroya — zona del sitio experimental. Pacto de socios con vesting de 4 años garantiza estabilidad del equipo durante la ejecución del proyecto.

---

### B10) Calidad Técnica y Organizativa del Proyecto — Perfil del líder (máx. 700 caracteres)

César Schiavoni (55%, Project Leader ANPCyT). Sr. Software Engineer BackEnd en MercadoLibre (Seller Central, 4 años). Fundador de OCUPA (plataforma de gestión, 2018). .Net Sénior en Grupo Prominente 2014–2022 — clientes Metrovías, BCRA, Benito Roggio. Prototipo IoT de monitoreo lumínico integrado a plataforma de gestión de incidentes (Grupo Prominente). Dispositivo médico embebido + app de seguimiento (bomba de infusión inteligente, UTN 2014–2016). Ingeniería en Sistemas UTN FRC. Responsable de la ejecución técnica con IA: implementa la arquitectura definida por el Technical Leader usando Claude Code como herramienta principal de construcción — generación de código, tests, documentación e integración con firmware. Project Leader y nexo con Dra. Monteoliva (INTA-CONICET).

---

### B11) Integrantes y experiencia del equipo

**Nota metodológica — Claude Code como herramienta de desarrollo:** el proyecto utiliza Claude Code (Anthropic) de forma intensiva para generación de código Python/backend/frontend, tests automatizados (135 tests, 0 fallos en TRL 3), documentación técnica y revisión de arquitectura. Esto reduce los requerimientos de horas humanas en backend y frontend un 60–70%, redirigiendo el esfuerzo humano hacia diseño de arquitectura, validación científica, trabajo experimental de campo y gestión del proyecto. La composición del equipo refleja esta realidad.

| Nombre | Rol en el proyecto | Formación / Empresa | Dedicación |
|---|---|---|---|
| César Schiavoni | Co-fundador · Director de Desarrollo IA · Project Leader ANPCyT | Sr. Software Engineer BackEnd — MercadoLibre (Seller Central, 4 años). Fundador OCUPA (plataforma de gestión, 2018–presente). .Net Sénior Grupo Prominente 2014–2022 (clientes: Metrovías, BCRA, Benito Roggio). Prototipo IoT de monitoreo lumínico integrado a plataforma de gestión de incidentes (Grupo Prominente). Adaptación de bomba de infusión inteligente + app web de seguimiento para tratamiento de diabetes (UTN 2014–2016). Stack: Java, C#, .Net Core, Azure, API REST, Angular, Blazor, SQL, MongoDB. Ingeniería en Sistemas UTN FRC. Ejecuta la construcción del sistema usando Claude Code como herramienta principal: implementa la arquitectura definida por el Technical Leader, genera código Python (módulos HSI, pipeline térmico, fusión satelital), revisa y valida el output de IA, mantiene los 135 tests automatizados y gestiona la integración con el firmware de Lucas. Project Leader ANPCyT: coordina hitos, interlocución con Dra. Monteoliva (INTA-CONICET). Accionista fundador 55%. Acceso exclusivo al viñedo experimental Colonia Caroya (1/3 ha Malbec, propiedad familiar). | 40 hs/semana (20 hs/sem facturadas al proyecto como Director de Desarrollo IA) |
| Lucas Bergon | Co-fundador · Líder técnico Hardware / PCB / Firmware / Embebidos | Fundador MBG Controls (2011–presente, 15 años) — empresa de ingeniería especializada en automatización y control industrial, robótica colaborativa, tableros de control y dispositivos especiales. 150+ proyectos industriales · 50+ proyectos electrónicos. Automatización PLC (Siemens, Rockwell, Schneider, Omron, Festo, Mitsubishi). Comunicaciones industriales: Modbus RTU/TCP, Profibus, ProfiNet, Ethernet/IP, CAN, I2C, RS232/422/485. Electrónica: PCB multicapa, ARM, FPGA, i.MX, sistemas embebidos, montaje superficial. Robótica industrial y colaborativa. Safety. Industry 4.0. SCADA. Diseño mecánico 2D/3D (Inventor). Inglés Full Professional. Dos ingenierías: Electrónica (UTN FRC, 2005–2012) + Sistemas (Siglo 21, 2013–2019). Técnico en Electricidad y Electrónica (IPEM 69). Infraestructura propia: osciloscopio, analizador lógico, soldadores de estación, fuentes reguladas, CAD/CAE PCB multicapa — elimina dependencia de fabricantes externos para el prototipo. Reside en Colonia Caroya — acceso directo al viñedo experimental y soporte técnico de campo en 24 horas. Accionista fundador 45%. | 50% Mes 1-6, 25% Mes 7-12 |
| Dra. Mariela Monteoliva | Asesora científica — protocolo Scholander, supervisión agronómica, calibración CWSI y MDS por variedad | Investigadora Adjunta INTA-CONICET (MEBA-IFRGV-UDEA, CCT Córdoba). Doctora en Ciencias Químicas. Tres posdoctorados en fisiología vegetal del estrés hídrico. Autora en capítulo "Estado hídrico" (libro 'Abordajes fisiológicos para el estudio del estrés abiótico en cultivos', 2025). Especialidad: potencial hídrico foliar con bomba de Scholander, tolerancia a sequía, calibración CWSI. | ~15 hs/mes promedio (12 meses): ~5h/mes diseño (Mes 1–3) · ~25h/mes capturas Scholander (Mes 4–6) · ~12h/mes validación (Mes 7–9) · ~18h/mes publicación (Mes 10–12). ~180 hs totales. |
| Javier Schiavoni | Técnico de campo principal — instalación sistema de riego diferencial (Mes 1–3), instalación y verificación extensómetro de tronco en 5 nodos (Mes 3), mantenimiento viñedo experimental, ejecución protocolo Scholander (4 sesiones OED Mes 4–9). ~208 hs totales con verificación D_max/D_min del extensómetro en cada sesión. Co-propietario del predio familiar. | Productor vitícola — Colonia Caroya, Córdoba. Residente en el sitio experimental. | ~6 hs/semana (Mes 1–9) — ~208 hs totales · USD 1.000/mes |
| Franco Schiavoni | Técnico de campo — asistencia en instalación de nodos y extensómetros, soporte en sesiones Scholander, operación del viñedo experimental. | Productor vitícola — Colonia Caroya, Córdoba. | 3 hs/semana (Mes 4–9) — sin costo adicional (aporte familiar) |
| Investigador Art. 32 (a incorporar — búsqueda activa CIII/G.In.T.E.A UTN FRC) | Investigador en Validación de Señales y Datos Agronómicos — análisis estadístico correlaciones CWSI↔MDS↔Ψstem, calibración sensores dendrómetro, diseño experimental óptimo (OED), co-autoría publicación científica | Perfil: procesamiento de señales, estadística aplicada o instrumentación (UTN FRC u equivalente). | ~5 hs/semana (~177 hs totales) |
| Matías Tregnaghi | Contador Público — rendiciones FONARSEC, contabilidad SAS, informes trimestrales de avance | Contador Público (CPA) + Diplomatura en Finanzas para Pymes. | 20% dedicación, 12 meses — 8 hs/semana. Carga alta en Mes 1–3 (setup financiero, SAS, AFIP) y Mes 10–12 (rendición final). |
| Ximena Crespo | Agente de la Propiedad Industrial — redacción y presentación de solicitud de patente de invención ante INPI Argentina (Mes 9). Incluye asesoramiento en protección legal del software y evaluación de viabilidad PCT/USPTO. Servicio externo contratado por honorario único; sin dedicación horaria semanal al proyecto. | Socia fundadora — Arteaga y Asociados, Profesionales en Marcas y Patentes (Córdoba, Argentina, 20+ años). Agente de la Propiedad Industrial registrada (INPI). Especialidad: patentes de invención, protección de software, modelos de utilidad, transferencia de tecnología. Sede en Córdoba (Av. Recta Martinoli 5133) y CABA. Corresponsalías nacionales e internacionales. | Servicio externo — honorario único a cotizar Mes 9 |

---

### B12) Dedicación al proyecto

El proyecto tiene una duración de 12 meses (Octubre 2026 – Septiembre 2027). El diagrama Gantt a continuación detalla la participación de cada integrante por fase y mes:

**Referencias:** XX = período activo | S1–S4 = sesión Scholander campo | G0–G3 = Gate Review ANPCyT | V1–V4 = campaña externa | PI = solicitud patente INPI | CF = congreso científico

| Tarea / Hito | Oct | Nov | Dic | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **FENOLOGÍA MALBEC — Colonia Caroya** | | | | | | | | | | | | |
| Brotación | XX | | | | | | | | | | | |
| Floración | | XX | | | | | | | | | | |
| Desarrollo del fruto | | | XX | | | | | | | | | |
| Envero / Pre-maduración | | | XX | XX | | | | | | | | |
| Cosecha (mediados febrero) | | | | XX | XX | | | | | | | |
| Dormancia invernal | | | | | | XX | XX | XX | XX | XX | XX | |
| Nueva brotación temporada 2027–28 | | | | | | | | | | | | XX |
| **LEGAL / ADMINISTRATIVO** | | | | | | | | | | | | |
| Constitución HydroVision AG SAS (IGJ) + AFIP | XX | XX | | | | | | | | | | |
| Pacto de socios + cláusulas vesting 4 años | XX | XX | | | | | | | | | | |
| Seguros (RC + equipos + ART campo) | XX | XX | XX | XX | XX | XX | XX | XX | XX | XX | XX | XX |
| Contaduría / rendiciones ANPCyT (trimestral) | XX | XX | XX | XX | XX | XX | XX | XX | XX | XX | XX | XX |
| **ADQUISICIÓN & RECEPCIÓN HARDWARE** | | | | | | | | | | | | |
| Pedido MLX90640 breakout Adafruit 4407 ×7 | XX | | | | | | | | | | | |
| Recepción MLX90640 breakout (lead time ~2-4 sem) | XX | XX | | | | | | | | | | |
| ESP32-S3 DevKit ×7 + LoRa SX1276 ×7 | XX | | | | | | | | | | | |
| Sensores: SHT31, GPS u-blox, IMU, SX1276 (EBYTE E32-900T20D) | XX | | | | | | | | | | | |
| Gateway RAK7268 + Router 4G Teltonika RUT241 + Starlink Mini X kit | XX | | | | | | | | | | | |
| Scholander + tensiómetros ×5 + Davis Vantage | XX | XX | | | | | | | | | | |
| HOBO MX2301 ×1 + maletin IP67 | XX | XX | | | | | | | | | | |
| Integración modular DevKit + breakouts (Lucas) | XX | XX | | | | | | | | | | |
| Montaje 5 nodos en carcasa Hammond IP67 (Lucas/MBG) | | XX | XX | | | | | | | | | |
| Carcasa Hammond IP67 + sistema montaje estaca/bracket | | XX | XX | | | | | | | | | |
| Drip 440m + solenoides ×20 + Rain Bird ESP-ME3 | XX | XX | | | | | | | | | | |
| Brackets acero ×32 + paneles emisividad ×32 | XX | XX | | | | | | | | | | |
| **INSTALACIÓN VIÑEDO EXPERIMENTAL (Técnico + Lucas)** | | | | | | | | | | | | |
| Tendido cinta drip 4 filas ×136m | XX | XX | | | | | | | | | | |
| Instalación 20 solenoides + controlador Rain Bird | XX | XX | | | | | | | | | | |
| Prueba caudales 5 regímenes hídricos (0–100% ETc) | | XX | | | | | | | | | | |
| Instalación 32 brackets en postes espaldera | | XX | | | | | | | | | | |
| Túneles exclusión lluvia zonas C y D | | XX | | | | | | | | | | |
| Instalación 8 tensiómetros + paneles + estacas | | XX | | | | | | | | | | |
| Mantenimiento rutinario viñedo (técnico campo) | XX | XX | XX | XX | XX | XX | XX | XX | XX | | | |
| **HARDWARE & FIRMWARE (Lucas Bergon — COO/HW+FW)** | | | | | | | | | | | | |
| Setup entorno desarrollo + Claude Code | XX | | | | | | | | | | | |
| Drivers C/C++: MLX90640 I2C (32x24, FOV 110°) | XX | XX | XX | | | | | | | | | |
| Drivers C/C++: SHT31, GPS u-blox, IMU | XX | XX | XX | | | | | | | | | |
| Drivers C/C++: servos MG90S gimbal pan-tilt | XX | XX | XX | | | | | | | | | |
| Firmware deep sleep RTC DS3231 + watchdog TPL5010 | | XX | XX | | | | | | | | | |
| Integración ChirpStack/LoRaWAN + protocolo MQTT | | XX | XX | XX | | | | | | | | |
| Sistema solar: panel 6W + LiFePO4 + regulador MPPT | | XX | XX | | | | | | | | | |
| Gimbal pan-tilt 2 ejes: 7 ángulos automáticos | | XX | XX | XX | | | | | | | | |
| Prueba autonomía solar 72h continuas | | | | XX | | | | | | | | |
| Testing banco: deep sleep, watchdog, autonomía | | | | XX | XX | XX | | | | | | |
| Integración completa nodo (todas las capas HW) | | | | | | | | | | XX | XX | |
| ~~Alertas físicas: LED tricolor + sirena 90dB~~ (REMOVIDO) | | | | | | | | | | XX | XX | |
| Control riego autónomo nodo (GPIO → SSR → solenoide Rain Bird) | | | | | | | | | | | XX | XX |
| Prueba autonomía 72h sistema completo integrado | | | | | | | | | | | | XX |
| **IA / MODELO PINN + VALIDACIÓN (Inv. Art. 32 — Validación de Señales y Datos Agronómicos)** | | | | | | | | | | | | |
| Motor GDD: acumulador + detección brotación auto | XX | XX | XX | | | | | | | | | |
| Pipeline CWSI funcional en laboratorio (Python) | XX | XX | | | | | | | | | | |
| Segmentación foliar U-Net++ ResNet34 | | XX | XX | XX | | | | | | | | |
| Recopilación datasets públicos 50.000+ imgs | | | | XX | XX | XX | | | | | | |
| Simulador físico: generador 1M imgs sintéticas | | | | XX | XX | XX | | | | | | |
| Correlación inicial CWSI-NDWI (Sentinel-2) | | | | | XX | XX | | | | | | |
| Pre-entrenamiento backbone (50K imgs públicas) | | | | | | | XX | | | | | |
| Fine-tuning PINN (1M imgs sintéticas, ~40h GPU) | | | | | | | XX | XX | | | | |
| Calibración real PINN (800 frames Scholander) | | | | | | | | XX | XX | | | |
| Cuantización INT8 + exportación TF Lite Micro | | | | | | | | XX | XX | | | |
| Validación set independiente 120 frames (>85%) | | | | | | | | | XX | | | |
| Validación motor GDD vs. fenología observada | | | | | | | | | XX | | | |
| Soporte técnico integración Fase 3 (25%) | | | | | | | | | | XX | XX | XX |
| **BACKEND & CLOUD (César + Claude Code)** | | | | | | | | | | | | |
| Setup AWS IoT Core (MQTT 3.1.1) | XX | XX | | | | | | | | | | |
| ChirpStack Network Server + PostgreSQL/PostGIS | XX | XX | XX | | | | | | | | | |
| Base de datos InfluxDB time-series CWSI + GDD | | XX | XX | XX | | | | | | | | |
| API Sentinel-2 Copernicus (NDVI/NDWI/NDRE auto) | | | | XX | XX | XX | | | | | | |
| API REST FastAPI + esquema OpenAPI | | | | | XX | XX | XX | XX | | | | |
| Fusión CWSI-NDWI vía Google Earth Engine | | | | | | XX | XX | XX | XX | | | |
| Pipeline CI/CD GitHub Actions + Docker | | | | | | XX | XX | XX | | | | |
| Hardening seguridad (OAuth2, rate limiting) | | | | | XX | XX | | | | | | |
| Motor reglas riego configurable (backend) | | | | | | | | | XX | XX | XX | |
| **FRONTEND & APP MÓVIL — diferido TRL 5** | | | | | | | | | | | | |
| Dashboard web (César + Claude Code) | | | | | | | | | XX | XX | XX | |
| **SESIONES SCHOLANDER (Monteoliva + Técnico campo)** | | | | | | | | | | | | |
| Diseño protocolo experimental (Monteoliva) | XX | XX | XX | | | | | | | | | |
| Sesión 1 — Brotación \| VPD<1.5kPa \| 60 vides | S1 | | | | | | | | | | | |
| Sesión 2 — Envero \| VPD>2kPa \| 20–25 vides AL | | | S2 | | | | | | | | | |
| Sesión 3 — Pre-cosecha \| validación \| AL | | | | S3 | | | | | | | | |
| Sesión 4 — Pre-cosecha final \| validación | | | | | S4 | | | | | | | |
| Validación simulador vs. datos Scholander reales | | | | | | | XX | XX | XX | | | |
| Co-autoría publicación científica | | | | | | | | | | XX | XX | XX |
| **CAMPAÑAS EXTERNAS (César + Lucas)** | | | | | | | | | | | | |
| Campaña Mendoza 1 (Valle de Uco / vinculación) | | | | | V1 | | | | | | | |
| Campaña Mendoza 2 (multi-varietal Cab/Torrentes) | | | | | | | | V2 | | | | |
| Campaña Bodega Las Cañitas (Gabriel Campaña) | | | | | | | | | | | V3 | |
| Campaña San Juan (olivo/pistacho) | | | | | | | | | | | | V4 |
| **PROPIEDAD INTELECTUAL (Ximena Crespo)** | | | | | | | | | | | | |
| Búsqueda formal anterioridad INPI+EPO+USPTO | XX | XX | XX | | | | | | | | | |
| Redacción reivindicaciones + descripción técnica | | | | | | | | | XX | XX | XX | |
| Presentación solicitud patente INPI Argentina | | | | | | | | | | | | PI |
| **GATE REVIEWS & HITOS ANPCyT** | | | | | | | | | | | | |
| G0 — Pipeline CWSI + nodo capturando (fin M3) | | | G0 | | | | | | | | | |
| G1 — Dataset validado + simulador OK (fin M6) | | | | | | G1 | | | | | | |
| G2 — Modelo >85% accuracy + INT8 OK (fin M9) | | | | | | | | | G2 | | | |
| G3 — TRL 4 demostrado + informe final (fin M12) | | | | | | | | | | | | G3 |
| **DIFUSIÓN & VINCULACIÓN** | | | | | | | | | | | | |
| Material técnico: manual + videos tutoriales | | | | | | | | | XX | XX | XX | XX |
| Diseño identidad corporativa + web MVP | | | | | | | | XX | XX | XX | | |
| Congreso Soc. Argentina Fisiología Vegetal | | | | | | | | | | CF | | |
| Publicación científica open access | | | | | | | | | | XX | XX | XX |
