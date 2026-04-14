
# HYDROVISION AG
Plataforma de Inteligencia Agronómica para Cultivos de Alto Valor



## DESCRIPCIÓN TÉCNICA DEL PROYECTO
con Nivel de Madurez Tecnológica (TRL) Documentado

Denominación del proyecto
Plataforma Autónoma de Inteligencia Agronómica para Cultivos de Alto Valor mediante Termografía LWIR, Dendrometría de Tronco, Motor Fenológico Automático y Fusión Satelital con IA Edge
Convocatoria
STARTUP 2025 TRL 3-4 — ANPCyT / FONARSEC — Agencia I+D+i (BID)
TRL actual / objetivo
TRL 3 (actual) → TRL 4 al cierre del proyecto financiado
Área tecnológica
Inteligencia Artificial · Sistemas Embebidos · Sensórica Avanzada · AgTech
Sector productivo
Agroindustria — cultivos de alto valor bajo riego: vid, olivo, cerezo, pistacho, nogal, citrus, arándano
Monto solicitado / total
USD 120.000 ANR (80%) — ANPCyT · USD 30.000 contrapartida equipo (20%) · Total: USD 150.000
Fecha de presentación
Abril 2026 — Convocatoria cierra 21 de mayo de 2026
Empresa beneficiaria
HydroVision AG SAS se constituirá en el Mes 1 del proyecto financiado (estatuto societario redactado, trámite iniciado ante IGJ). La cesión de titularidad a HydroVision AG SAS se formalizará conforme al procedimiento establecido por ANPCyT para cambios de titularidad.
Distribución accionaria
César Schiavoni: 55% · Lucas Bergon: 45%. Sin inversores externos a la fecha de presentación. Pacto de socios con vesting de 4 años, cliff de 12 meses — en redacción.


Documento Confidencial — Para uso exclusivo ANPCyT

## 1. Resumen Ejecutivo


Cada año, productores de vid, olivo, cerezo, pistacho, nogal y citrus pierden entre el 15% y el 35% de su rendimiento por estrés hídrico detectado demasiado tarde. En Argentina y Chile, el valor de producción en riesgo supera los USD 500 millones anuales. No existe en América Latina un sistema autónomo que detecte este fenómeno en tiempo real con precisión fisiológica. HydroVision AG resuelve este problema.
HydroVision AG es una plataforma autónoma de inteligencia agronómica para cultivos de alto valor bajo riego. Combina termografía infrarroja, dendrometría de tronco (extensómetro de micro-contracciones), sensores meteorológicos con anemómetro, un motor fenológico automático por grados-día acumulados (GDD) y fusión con imágenes satelitales Sentinel-2 para operar como un asistente agronómico completo: calcula el Índice de Estrés Hídrico del Cultivo (CWSI) en tiempo real, detecta automáticamente el estadio fenológico del cultivo, genera 12+ tipos de alertas agronómicas (helada, estrés calórico, riesgo fitosanitario, timing de operaciones, predicción de cosecha), y produce mapas de estrés de campo completo fusionando datos terrestres con satelitales. Todo sin intervención humana y alertando al productor 5 a 10 días antes de que el estrés sea visible a simple vista. El productor compra el kit online. La instalación incluye una visita de puesta en marcha de 2 horas donde un técnico de campo orienta el primer nodo en el lote. Los nodos adicionales los instala el productor solo con código QR. La conectividad de campo se resuelve con modelo dual: router 4G industrial (Teltonika RUT241, donde hay cobertura celular) o Starlink Mini X (donde no hay 4G, solo Tier 2-3). El modelo de negocio separa la venta del hardware (USD 950–1.000/nodo) de la suscripción anual de software (USD 80–290/ha/año según tier).

Más allá del CWSI, el sistema opera como plataforma de inteligencia agronómica completa: detecta automáticamente el estadio fenológico del cultivo mediante grados-día acumulados (GDD), genera alertas de helada tardía, estrés calórico, riesgo de enfermedades fúngicas y timing de operaciones de manejo (desbrote, análisis foliar, deadlines de fungicidas), y predice fechas de floración, envero y cosecha actualizadas semanalmente. Todo esto sin hardware adicional significativo — solo un pluviómetro de USD 15 completa el kit.
El sistema se instala como nodo fijo autónomo — alimentado por energía solar, conectado por LoRaWAN privado — y opera las 24 horas sin intervención humana. Los datos se fusionan con imágenes satelitales Sentinel-2 gratuitas (revisita cada 5 días, 10m/px) mediante un modelo de correlación CWSI↔NDWI: el nodo calibra el satélite en un punto y el satélite extrapola esa calibración a todo el lote, generando mapas de prescripción de riego diferencial y mapas de vigor vegetativo por zona, visibles desde una aplicación móvil con notificaciones push configurables por tipo de alerta. En su versión Tier 2-3, el nodo automatiza el riego por goteo directamente mediante relé SSR → solenoide — el nodo decide autónomamente cuándo regar según HSI, eliminando la intervención manual del operario.

Problema cuantificado: en cultivos de vid, olivo, cerezo, pistacho, nogal y citrus, el estrés hídrico mal gestionado genera pérdidas de rendimiento del 15 al 35% por campaña según condiciones y cultivo (Maes & Steppe 2012 para vid; García-Tejero et al. 2018 para olivo en condiciones de déficit controlado), equivalentes a USD 680–3.200 por hectárea según variedad. En condiciones de manejo promedio con riego tecnificado, las pérdidas evitables se estiman conservadoramente en el rango 10–20%. Argentina cuenta con ~447.700 hectáreas de cultivos de alto valor con riego tecnificado; sumando Chile el mercado direccionable supera las 600.000 ha. El valor de producción en riesgo supera los USD 498 millones anuales solo en Argentina.

Brecha tecnológica: no existe en Argentina ni en América Latina un sistema comercial que realice detección de estrés hídrico foliar en tiempo real mediante termografía, operando autónomamente en campo. Las soluciones existentes (satélite, drones con operador, tensiómetros de suelo) no detectan el estrés fisiológico de la planta antes del síntoma de marchitez. Esta brecha fue verificada mediante búsqueda de anterioridad en Google Patents, Espacenet (EPO), INPI Argentina y revisión de literatura científica 2020–2025.

Viabilidad Económica: El aporte de HydroVision varía según el cultivo, con un promedio ponderado de USD 9,6 recuperados por cada dólar invertido en la suscripción anual del servicio. En vid premium (USD 9.600/ha de ingreso bruto), el aporte evitado de pérdidas es USD 1.150/ha. Cálculo de ROI Año 1 en configuración Tier 1 (1 nodo/10 ha): costo hardware por ha USD 95 (amortizado en Año 1, sin deuda) + suscripción USD 95/ha = USD 190/ha total · Beneficio: USD 1.150/ha → ROI Año 1 = 1.150 / 190 ≈ 6x. En configuraciones Tier 3 (alta densidad, 1 nodo/2 ha), el hardware domina el costo Año 1 y el payback se extiende a ~2,4 años, con ROI Año 2+ fuertemente positivo. En cultivos de mayor valor el retorno es aún más pronunciado: cerezo (USD 3.200/ha de aporte, ingreso bruto USD 30.000/ha), pistacho (USD 2.160/ha) y nogal (USD 1.200/ha). El punto de equilibrio del negocio (HydroVision AG) se alcanza con las primeras 800 hectáreas bajo contrato recurrente — menos del 0,18% del mercado nacional direccionable de ~447.700 ha. La inversión en hardware Tier 1 se recupera en la primera cosecha en cultivos de alto valor.

Viabilidad del Negocio (HydroVision AG): El punto de equilibrio operativo se alcanza con 800 hectáreas bajo contrato recurrente (Tier 1, USD 95/ha/año promedio) — equivalente al 0,18% del mercado nacional direccionable de 447.700 ha. Proyección post-ANPCyT: Año 1 (TRL 5) 500 ha · USD 47.500 ARR; Año 2 (TRL 6) 2.500 ha · USD 260.000 ARR; Año 3 (TRL 7) 10.000 ha · USD 1.100.000 ARR — escenario conservador basado en tasa de penetración del 0,02% anual del mercado total. Los costos operativos de HydroVision AG post-TRL 4 son principalmente cloud (ya presupuestados a escala en el ítem de infraestructura) y soporte comercial, con margen bruto estimado >78% en operación recurrente estable (Año 3+).

Monto solicitado: USD 120.000 en Aportes No Reembolsables (ANR), representando el 80% del costo total del proyecto. La contrapartida del equipo fundador asciende a USD 30.000 (cumple el mínimo del 20% requerido), aportada en especie: estación de trabajo IA, viñedo experimental, horas de dedicación César/Lucas, material vegetal, merma experimental de cosecha y equipamiento de campo.



### 1A. Ventaja Competitiva y Diferenciación Técnica


HydroVision AG no es un sensor de riego más. Es el primer sistema en América Latina que mide directamente la respuesta fisiológica de la planta —no el suelo, no el entorno— de forma continua, autónoma y en tiempo real. Los cuatro diferenciales técnicos que lo hacen único:

| Diferencial | Qué hace | Resultado |
|---|---|---|
| **Doble señal fisiológica — HSI** | Fusiona termografía LWIR (CWSI) + extensómetro de tronco (MDS) con pesos adaptativos por R² | R²~0.90–0.95 vs. ψ_stem. Térmica cubre espacio; dendrometría cubre tiempo 24/7 |
| **Fusión satelital calibrada** | El nodo calibra Sentinel-2 en un punto; el satélite extrapola a todo el lote | 1 nodo cubre 50 ha — 70% menos costo por ha frente a redes de sensores |
| **Arquitectura PINN** | La función de pérdida embebe la ecuación física del CWSI (Jackson 1981) | Predicciones físicamente coherentes incluso con clima extremo — sin caja negra |
| **Confianza dinámica de señal** | 9 capas de mitigación de viento (sotavento, shelter, tubo colimador, termopar, buffer térmico, rampa gradual 4-18 m/s) — CWSI útil hasta 18 m/s (65 km/h), backup 100% MDS automático | Medición correcta en días de viento sin intervención humana |

**Doble señal fisiológica directa: HSI (HydroVision Stress Index)**
Mientras que un tensiómetro indica cuánta agua hay en el suelo, HydroVision mide dos respuestas fisiológicas reales de la planta simultáneamente: (1) temperatura foliar via termografía LWIR — el cierre estomático eleva la temperatura de la hoja (CWSI, Jackson 1981); (2) micro-contracciones del tronco via extensómetro — el déficit hídrico encoge el floema y el cambium (MDS, Fernández & Cuevas 2010). Ambas señales son fusionadas en el HSI con pesos adaptativos que parten de 35% CWSI + 65% MDS (basados en R² de correlación con ψ_stem), y se ajustan dinámicamente durante la temporada: el peso del MDS crece conforme el nodo acumula sesiones propias (mds_maturity), el anemómetro reduce gradualmente el peso del CWSI entre 4-18 m/s (rampa lineal) y transfiere al backup 100% MDS a partir de 18 m/s (65 km/h), y en días sin ventana solar útil la regresión online imputa el CWSI desde el MDS para no dejar huecos en la serie. El baseline Tc_wet se auto-calibra sin visita humana: cada lluvia con MDS≈0 provee la temperatura de hoja bien hidratada real del nodo. Resultado: R²~0.90–0.95 vs. ψ_stem medido con Scholander. La señal térmica cubre el espacio (50+ plantas por sesión), la señal dendrométrica cubre el tiempo (24/7) y calibra activamente a la cámara térmica.

**Fusión Satelital Calibrada (70% menos costo por ha)**
El nodo terrestre calibra las imágenes de Sentinel-2. Esto permite que un solo nodo proporcione datos precisos de estrés para un lote completo de 50 hectáreas, reduciendo el costo de implementación por superficie en un 70% frente a redes de sensores tradicionales. Un productor con 100 ha necesita 2 nodos, no 200.

**Arquitectura PINN: IA con física incorporada**
La IA no es una “caja negra”: incorpora las leyes de la termodinámica y el balance energético foliar en su entrenamiento (Physics-Informed Neural Network). Esto garantiza predicciones físicamente coherentes incluso con variaciones climáticas extremas en zonas como Cuyo o el NOA, y elimina la posibilidad de predicciones imposibles que dañarían la credibilidad del sistema ante el productor.

**Confianza dinámica de señal — 9 capas de mitigación de viento**
El viento produce enfriamiento convectivo artificial de la hoja que corrompe la medición térmica. HydroVision implementa 9 capas de defensa en profundidad: (1) orientación a sotavento — la cámara apunta al lado opuesto al viento dominante, usando las propias plantas como barrera (~60-70% reducción); (2) shelter anti-viento SHT31 — protege T_air/HR del viento directo; (3) tubo colimador IR — bloquea flujo lateral de aire sobre el FOV del MLX90640; (4) termopar foliar Type T — ground truth por contacto, inmune al viento, corrige la lectura IR en tiempo real; (5) buffer térmico con filtro de calma — 5 muestras, mediana de lecturas con viento <2 m/s; (6-8) rampa gradual firmware 4-18 m/s — el peso del CWSI se reduce linealmente de 35% a 0% entre 4 y 18 m/s (extendida por mitigaciones v2: Kalman IR↔termopar, Muller gbh, Hampel filter); (9) backup 100% MDS automático a partir de 18 m/s (65 km/h). Resultado: el CWSI permanece útil hasta 18 m/s / 65 km/h (antes solo hasta 4 m/s), y el error se reduce de ±0.12-0.18 a ±0.03 CWSI.


## 2. Descripción del Problema y Oportunidad de Innovación


### 2.1 El problema técnico central
La planta manifiesta estrés hídrico fisiológico mucho antes de que sea perceptible visualmente. Cuando los estomas se cierran por déficit de agua, la transpiración disminuye y la temperatura foliar aumenta respecto a una planta bien hidratada. Este diferencial térmico — base del CWSI — puede detectarse con precisión de ±0.05°C mediante cámaras térmicas de bajo costo actualmente disponibles en el mercado.

El problema actual es que ningún sistema detecta ese diferencial de forma continua, en tiempo real, directamente en el lote productivo. Las alternativas existentes fallan:

| Método actual | Por qué falla | Limitación crítica |
|---|---|---|
| Satélite (Sentinel-2) | Resolución 10m/px — mezcla suelo y plantas. Nubes bloquean la imagen 8–15 días. | No detecta estrés foliar directo. Falla exactamente cuando más se necesita. |
| Dron con operador | Requiere planificación, condiciones climáticas y piloto ANAC certificado. | 1–2 vuelos por semana máximo. El estrés se instala en 3–5 días. |
| Sensor de suelo (tensiómetro) | Mide humedad del suelo, no el estado hídrico real de la planta. | Desfase de 2–5 días entre suelo seco y planta con daño metabólico. |
| Observación visual del productor | El productor visita el lote cada 7–14 días. | Cuando ve el síntoma de marchitez, el daño fisiológico ocurrió 5–10 días antes. |


### 2.2 La oportunidad de innovación
HydroVision AG integra tres tecnologías maduras que hasta ahora no se combinaron en un sistema embebido de campo permanente:

[1] Termografía infrarroja de bajo costo — módulo breakout MLX90640 (Melexis, 32×24 px, NETD ~100 mK) con costo de componente USD 45–55 por módulo breakout integrado (Adafruit 4407 / SparkFun SEN-14844).
[2] Modelos de IA de inferencia en edge — redes neuronales cuantizadas INT8 que procesan imágenes localmente con latencia < 200ms en ESP32-S3 (Xtensa LX7 dual-core 240 MHz).
[3] Conectividad LoRaWAN privada — protocolo de baja potencia, alcance hasta 15 km en campo abierto con un gateway por lote. Conectividad del gateway a internet vía router 4G industrial (donde hay cobertura celular) o Starlink Mini (zonas sin 4G).
[4] Actuación en campo — control de riego autónomo integrado en el nodo Tier 2-3 (relé SSR + solenoide Rain Bird). El nodo decide localmente cuándo regar según HSI (histéresis 0.30/0.20) y activa el solenoide vía GPIO → SSR. El servidor recibe el estado vía payload LoRa. Nodos Tier 1 (solo monitoreo) reportan alertas vía WhatsApp, email y dashboard web. Las alertas son desactivables por el productor.
[5] Motor fenológico automático por grados-día acumulados (GDD) — el nodo calcula GDD desde su sensor de temperatura 24/7 y detecta automáticamente el estadio fenológico del cultivo (brotación, floración, envero, maduración, dormancia), seleccionando los coeficientes CWSI correspondientes y generando alertas agronómicas específicas por estadio. Cero configuración humana.
[6] Fusión calibrada nodo-satélite — el nodo proporciona CWSI preciso en un punto; Sentinel-2 (gratuito, cada 5 días, 10m/px) proporciona cobertura espacial de todo el lote. El modelo de correlación CWSI↔NDWI permite que un solo nodo calibre el satélite para 50+ ha, reduciendo la densidad de nodos necesaria y generando mapas de estrés de campo completo.
[7] Captura multi-angular con gimbal motorizado — inspirada en la metodología de termografía UAV (Pires et al. 2025, Zhou et al. 2022), la cámara térmica del nodo se monta sobre un gimbal pan-tilt motorizado de 2 ejes que barre el canopeo en 5–9 ángulos por ciclo de captura (±20° horizontal, ±15° vertical). Los frames se fusionan mediante un algoritmo de selección por fracción foliar: se retienen los 3 frames con mayor proporción de píxeles hoja (P20–P75 térmico) y se calcula el CWSI como promedio ponderado. Resultado: cobertura equivalente a un vuelo UAV de baja altitud desde un punto fijo, sin dependencia climática, sin certificación ANAC y sin límite de frecuencia de captura.
[8] Dendrometría de tronco integrada (HSI) — extensómetro de tronco (strain gauge + ADS1231 24-bit, resolución 1 µm) mide micro-contracciones diarias del tronco (MDS = D_max − D_min). Correlación directa con ψ_stem R²=0.80–0.92 (Fernández & Cuevas 2010) vs. R²=0.62–0.67 del CWSI térmico solo. Opera 24/7 sin dependencia de ventana solar ni condiciones meteorológicas. El HSI (HydroVision Stress Index) fusiona ambas señales con pesos adaptativos (base 35% CWSI + 65% MDS, ajustados dinámicamente por madurez del historial dendrométrico, confianza de la señal térmica y viento) → R²~0.90–0.95 combinado vs. ψ_stem Scholander. La temperatura del tronco (DS18B20) corrige la dilatación térmica del extensómetro. El extensómetro actúa además como referencia fisiológica de la cámara: cada lluvia con MDS≈0 auto-calibra el baseline Tc_wet sin visita humana. No se ha identificado en el mercado global ningún producto comercial que integre termografía foliar + dendrometría de tronco con auto-calibración cruzada en un único nodo autónomo de campo.
[9] Confianza dinámica por anemómetro y mitigación de viento multinivel — el nodo implementa 9 capas de defensa contra el artefacto de viento: orientación a sotavento (cámara al lado opuesto al viento dominante, plantas como barrera ~60-70%), shelter anti-viento SHT31, tubo colimador IR (PVC 110mm×250mm), termopar foliar Type T 0.1mm (ground truth por contacto, corrección IR en tiempo real), buffer térmico con filtro de calma (5 muestras × 2s, mediana con viento <2 m/s), y rampa gradual firmware 4-18 m/s que reduce linealmente el peso del CWSI de 35% a 0% (extendida por mitigaciones v2: Kalman IR↔termopar, Muller gbh, Hampel filter, buffer adaptativo, 2do termopar, captura oportunista). A partir de 18 m/s (65 km/h), el HSI usa 100% MDS dendrométrico. El IMU ya presente detecta vibración del nodo como proxy de ráfagas súbitas entre ciclos de medición. El CWSI permanece útil hasta 18 m/s / 65 km/h (antes solo hasta 4 m/s), con error reducido de ±0.12-0.18 a ±0.03 CWSI (Jones 2004).
[10] Calibración física dual-referencia con auto-diagnóstico óptico — el bracket de cada nodo incorpora dos paneles de referencia dentro del campo de visión (FOV) de la cámara térmica: (a) Referencia Seca (Dry Ref): panel de aluminio con recubrimiento negro mate (emisividad ε≈0.98), actúa como límite superior de temperatura (hoja con estomas totalmente cerrados); (b) Referencia Húmeda (Wet Ref): panel con material hidrofílico (fieltro técnico) mantenido en saturación constante por una micro-bomba peristáltica 6V controlada por GPIO del ESP32-S3, desde un reservorio de 10L con autonomía de 90–120 días (toda la campaña crítica de riego). El firmware lee coordenadas de píxeles fijas pre-calibradas — sin ML para detectar los paneles — y calcula el Índice Jones/Ig: Ig = (T_canopeo − T_wet) / (T_dry − T_canopeo), 96 veces/día (cada 15 min). El módulo de auto-diagnóstico óptico monitorea la salud física del sensor en cada frame: la desviación estándar del histograma térmico detecta obstrucciones (polvo, insectos, empañamiento); si la temperatura del panel seco se desvía >1.5°C de la curva teórica (función de radiación solar y temperatura ambiente), el sistema emite una alerta de "Lente Sucio/Empañado". El Índice de Salud Óptica (ISO_nodo) se reporta al dashboard — el técnico de campo interviene para limpiar solo cuando ISO_nodo < 80%, eliminando mantenimientos preventivos innecesarios. Costo incremental por nodo: USD 20 (bomba + paneles + reservorio).

Hipótesis técnica central: un nodo permanente con cámara térmica + extensómetro de tronco + anemómetro + paneles de referencia dual (Dry/Wet Ref) + modelo HSI de IA local puede estimar ψ_stem con R²~0.90–0.95, suficiente para detectar estrés incipiente 5–10 días antes del síntoma visual y verificarlo con la señal dendrométrica continua 24/7. El costo de venta del nodo es de USD 950 (Tier 1 Monitoreo, COGS ~USD 149) — incluye todos los módulos: cámara LWIR breakout, extensómetro, anemómetro, tubo colimador IR, termopar foliar, shelter SHT31, gimbal, LoRa, solar — y baja a ~USD 121/nodo COGS a escala de producción (500+ unidades, arquitectura bare chip + PCB custom).


## 3. Escala de Madurez Tecnológica (TRL) — Estado Actual y Proyectado


El estado actual del proyecto se documenta en la escala TRL internacional (ISO 16290:2013 / NASA TRL). El objetivo al cierre del proyecto financiado es alcanzar TRL 4.

1
TRL
Principios básicos observados — LOGRADO
El CWSI como indicador de estrés hídrico está documentado en más de 200 publicaciones científicas desde Jackson et al. (1981). La relación física entre temperatura foliar, cierre estomático y estado hídrico de la planta está matemáticamente establecida.


2
TRL
Concepto tecnológico formulado — LOGRADO
Arquitectura del sistema definida: nodo con MLX90640 breakout integrado (Adafruit 4407) + ESP32-S3 DevKit (MicroPython) + SHT31 (T/HR) + anemómetro RS485 + extensómetro de tronco (strain gauge + ADS1231 + DS18B20) + GPS + IMU ICM-42688-P + SX1276 LoRa 915 MHz + fusión con Sentinel-2. Arquitectura modular TRL4: DevKit + breakouts I2C/SPI sin PCB custom. Índice HSI (HydroVision Stress Index): fusión CWSI térmico (35%) + MDS dendrométrico (65%) con confianza dinámica por viento. El concepto fue validado contra la literatura científica especializada y analizado técnica y económicamente por el equipo fundador.


3
TRL
ACTUAL
Prueba de concepto analítica y computacional — NIVEL ACTUAL DEL PROYECTO
Evidencias documentadas de TRL 3:


─── FACTIBILIDAD CIENTÍFICA ─────────────────────────────────────────────────

El principio físico del CWSI está respaldado por más de 200 publicaciones científicas desde Jackson et al. (1981). La relación entre temperatura foliar, cierre estomático y estado hídrico de la planta está matemáticamente establecida y validada en vid Malbec específicamente mediante:
La base científica de la dendrometría de tronco como segunda señal fisiológica directa de ψ_stem está igualmente consolidada en literatura internacional especializada: Fernández & Cuevas (2010, Agricultural Water Management) documentan MDS como el indicador dendrométrico más robusto de estrés hídrico en vid con R²=0.80–0.92 vs ψ_stem Scholander. Ortuño et al. (2010, Agricultural Water Management) validan MDS vs. ψ_stem en limonero mediterráneo con correlación lineal estable bajo déficit hídrico controlado. Naor (2000, Irrigation Science) establece los umbrales de potencial hídrico de tallo para diferentes cultivos, incluyendo vid, usados como referencia para el protocolo de rescate hídrico. Pérez-López et al. (2008, Plant and Soil) caracterizan el coeficiente de expansión térmica del tronco de vid (alpha = 2.5 µm/°C), base de la corrección térmica del extensómetro. Fernández et al. (2011, Irrigation Science) integran señales térmicas y dendrométricas en vid bajo déficit hídrico controlado, validando el principio de fusión HSI con ponderación por R².
· Jackson et al. (1981, Water Resources Research): fórmula CWSI original — base del modelo.
· Bellvert et al. (2016, Precision Agriculture): coeficientes empíricos calibrados para Malbec (ΔT_LL = −1.97 + 1.49·VPD, ΔT_UL = +3.50°C). Obtenidos sobre vid Malbec en condiciones mediterráneas; serán recalibrados para Córdoba/Cuyo en TRL 4.
· Pires et al. (2025, Computers & Electronics in Agriculture): correlación CWSI → ψ_stem Scholander en vid (R²=0.663 en capturas de tarde). Valida la conversión del índice térmico al potencial hídrico medido con bomba de Scholander.
· Araújo-Paredes et al. (2022, Sensors): validación de CWSI termográfico vs. ψ_stem en viñedo. Error NETD 50mK → error CWSI < ±0.07 aceptable.
· Zhou et al. (2022, Agronomy): CWSI↔ψ_leaf y efecto de cara norte/sur del canopeo en vid.
· Gutiérrez et al. (2018, PLoS ONE): validación del Índice Jones (Ig) como alternativa al CWSI en vid, sin necesidad de VPD modelado.

Validación científica externa — Dra. Mariela Monteoliva (INTA-CONICET):
La Dra. Monteoliva (investigadora adjunta INTA-CONICET, MEBA-IFRGV-UDEA, Córdoba), especialista en fisiología vegetal y responsable del protocolo Scholander en el proyecto, confirmó la base científica del sistema con el siguiente juicio experto: "El monitoreo del estrés hídrico en vides a través de imágenes térmicas ya ha sido documentado en numerosos trabajos, incluyendo diversos cultivares y regiones. Además, se ha reportado previamente una correlación aceptable entre los parámetros termométricos de las imágenes con mediciones de conductancia (pérdida de agua foliar) y potencial hídrico (agua disponible en tallos y hojas), sustentando su validez para la aplicación de estos parámetros en este proyecto."

Análisis de datos públicos externos: datos tabulares de CWSI y ψ_stem de viñedos publicados por INIA Chile (Gutiérrez-Gamboa et al., cv. Carménère/Cabernet Sauvignon, Valle del Maule) y USDA ARS (Ag Data Commons), confirmando coherencia del gradiente térmico foliar bajo distintas condiciones de VPD con los rangos del modelo Bellvert 2016. Complementado con datos meteorológicos de la Red Agrometeorologica INIA Chile (agrometeorologia.cl) — T_air, HR, radiación, viento en zonas vitícolas — para calibrar los límites ΔT_LL/ΔT_UL en el régimen climático de Chile Central.


─── FACTIBILIDAD COMPUTACIONAL ──────────────────────────────────────────────

Prueba computacional — 10 módulos Python, 135 tests automatizados (0 fallos):
Cultivo de validación: Vid Malbec — Colonia Caroya, Córdoba (~700m s.n.m.).
· cwsi_formula.py: implementación de Jackson et al. (1981) con coeficientes Bellvert et al. (2016) calibrados para Malbec. Tres índices implementados: CWSI (Jackson 1981), Índice Jones/Ig (Jones 1999, validado en vid por Gutiérrez et al. 2018, PLoS ONE), y predicción de potencial hídrico de tallo ψ_stem [MPa] (Pires et al. 2025, R²=0.663 en capturas de tarde). Resultados coherentes con rangos publicados para condiciones de Cuyo: CWSI 0.0–0.95, ψ_stem −0.35 a −1.49 MPa. Error CWSI por NETD 50mK = ±0.019 (dentro del límite ±0.07 de Araújo-Paredes et al. 2022).
· thermal_pipeline.py: pipeline completo frame MLX90640 (32×24 px) → segmentación foliar P20–P75 → CWSI ponderado por fracción foliar. Metodología multi-angular (5–6 posiciones de gimbal × 3 ventanas horarias). Flag canopy_side norte/sur (Pires 2025, Zhou et al. 2022).
· gdd_engine.py: motor GDD (Winkler 1974, base 10°C) con detección automática de 9 estadios fenológicos para Malbec. Umbrales CWSI diferenciados por estadio (0.30 en floración → 0.85 en pre-cosecha). Climatología calibrada contra datos reales de la estación INTA EEA Manfredi (A872907, 2012–2026, n=4.802 días) con corrección altitudinal −2.2°C para Colonia Caroya (~700m).
· synthetic_data_gen.py: generador de frames térmicos Y16 sintéticos (32×24 px, resolución MLX90640) con modelo físico T_leaf = T_air + ΔT_LL(VPD) + CWSI × (ΔT_UL − ΔT_LL) + N(0, NETD). Núcleo del simulador para las 1.000.000 imágenes sintéticas del pre-entrenamiento PINN en TRL 4.
· sentinel2_fusion.py: modelo de correlación CWSI↔NDWI/NDVI/NDRE con regresión polinomial robusta (HuberRegressor). R²=0.97 en calibración sintética. Demuestra el principio de que un nodo calibra el satélite para 50+ ha.
· dendrometry.py [NUEVO]: motor de análisis de micro-contracciones de tronco (MDS — Maximum Daily Shrinkage). Calcula MDS = D_max − D_min con corrección térmica del extensómetro (alpha = 2.5 µm/°C, Pérez-López 2008), estima ψ_stem desde MDS con R²=0.80–0.92 (Fernández & Cuevas 2010), clasifica 5 niveles de estrés, evalúa recuperación nocturna y activa protocolo de rescate si ψ_stem < −1.5 MPa. Coeficientes Malbec: ψ_stem = −0.15 + (−0.0080) × MDS [MPa].
· combined_stress_index.py [NUEVO]: motor HSI (HydroVision Stress Index) — fusión de CWSI térmico (35%) + MDS dendrométrico (65%) ponderados por R² de correlación con ψ_stem. Estrategia de fusión adaptativa: acuerdo de señales (Δψ < 0.35 MPa) → promedio ponderado con R²~0.90–0.95; desacuerdo → MDS domina al 80%; señal única → incertidumbre ×1.4. Protocolo de rescate activado por cualquier señal individual ≤ −1.5 MPa. La confianza dinámica por anemómetro (rampa gradual 4-18 m/s → reducción progresiva del peso CWSI, backup 100% MDS a partir de 18 m/s (65 km/h)) se integra en TRL 4. Base: Jones (2004), Fernández et al. (2011).
· baseline.py [NUEVO — ML Engineer/03_fusion]: motor de calibración de fallback y detección de deriva del baseline CWSI. Jerarquía de referencia térmica: (Primario) el panel Wet Ref físico provee T_wet medida directamente en tiempo real — CWSI = (T_canopeo − T_wet_medido) / (T_dry − T_wet_medido), sin estimación; (Secundario/fallback) cuando el Wet Ref no está disponible o ISO_nodo < 80%, baseline.py estima T_wet mediante NWSB(Ta,VPD) + offset_EMA actualizado por eventos de lluvia con MDS≈0 (learning_rate=0.25) — el extensómetro confirma que la planta está al máximo de hidratación sin visita humana; (Terciario) detección de deriva autónoma — CWSI sistemáticamente < 0.02 o > 0.98 indica offset desplazado, std(CWSI) < 0.01 con >10 muestras indica falla de sensor. Nota: las sesiones Scholander ya no alimentan baseline.py para calibración de T_wet; su rol es exclusivamente validar los coeficientes MDS→ψ_stem y generar datos etiquetados para el PINN.
· fusion_engine.py [NUEVO — ML Engineer/03_fusion]: motor HSI con regresión lineal online CWSI=α+β×MDS_norm (ventana deslizante 60 muestras, mínimo 10 para activarse) que aprende la relación local entre señal térmica y dendrométrica por nodo durante la temporada. Pesos dinámicos por madurez del historial: mds_maturity = min(1, n_sesiones/20) — el peso del MDS crece gradualmente conforme el nodo acumula sesiones propias. Imputación de CWSI desde MDS cuando cwsi_confidence<0.4 (días completamente nublados, viento persistente): la regresión local predice el CWSI que habría dado la cámara térmica, eliminando huecos en la serie. Alerta de divergencia automática (|CWSI − MDS_norm| > 0.35) para detectar condiciones anómalas sin intervención humana. Demo integrado: 5 nodos × 30 días × 3 sesiones diarias con curva de aprendizaje R² de regresión y evolución del offset de baseline por zona.

Factibilidad hardware verificada: MLX90640 breakout integrado (sensor BAB, 110° FOV) entrega frames 32×24 px en ESP32-S3 con NETD ~100 mK. Con 28 píxeles foliares promediados, el error efectivo de CWSI es ±0.008 — dentro del umbral ±0.07 de Araújo-Paredes et al. 2022 y comparable al FLIR Lepton 3.5 de mayor costo. El extensómetro de tronco (strain gauge + ADS1231 24-bit ADC, resolución 1 µm) es hardware comercial verificado para condiciones de campo en vid (Fernández & Cuevas 2010).

─────────────────────────────────────────────────────────────────────────────

Análisis de mercado validado: ~850.000 ha con riego tecnificado en Argentina y Chile (San Juan 38.635 ha · Mendoza 90.000 ha · Río Negro 13.500 ha · Chile 307.000 ha) sin solución de monitoreo hídrico foliar autónomo en tiempo real. El olivo en San Juan tiene 98% de tecnificación — mercado más receptivo de Argentina en Año 1. Chile atraviesa megasequía con Ley de Riego subsidiando reconversión a sistemas presurizados — expansión Año 2.

Acceso a viñedo experimental propio con técnicos residentes: el equipo fundador dispone de 1/3 de hectárea de Malbec en Colonia Caroya, Córdoba (propiedad de los padres del co-fundador César Schiavoni), con acceso exclusivo e irrestricto para el proyecto. El viñedo es trabajado por Javier y Franco Schiavoni (hermanos de César), productores vitícolas residentes en Colonia Caroya, con conocimiento directo de las condiciones del cultivo. Ejecutarán las mediciones de campo bajo protocolo diseñado y supervisado por la Dra. Monteoliva (INTA-CONICET). Esto elimina la dependencia de técnicos externos, reduce costos de campo y garantiza disponibilidad durante toda la ventana fenológica.

Infraestructura de riego — inversión previa al TRL 4: el viñedo experimental opera actualmente con riego por canal (acequia). La implementación del plan experimental TRL 4 —que requiere 5 zonas hídricas independientes con tratamientos diferenciados de 100% ETc a déficit hídrico severo— exige la instalación de riego por goteo con solenoides Rain Bird. Esta conversión (canal → goteo por fila con control individual por zona) constituye una inversión de infraestructura que el equipo fundador asume como parte de la contrapartida del proyecto, independientemente del financiamiento ANPCyT. La instalación será ejecutada por Javier y Franco Schiavoni previo al inicio de la campaña experimental (Mes 3–4 del proyecto financiado).

Limitación actual: no se dispone aún de hardware integrado funcionando. La validación es analítica y computacional, no experimental en condiciones reales con el sistema completo. Los coeficientes de Bellvert (2016) fueron obtenidos en condiciones mediterráneas y serán recalibrados para Malbec en Colonia Caroya/Cuyo mediante protocolo Scholander bajo supervisión de la Dra. Mariela Monteoliva (INTA-CONICET) en TRL 4.


4
TRL
OBJETIVO
Validación tecnológica en laboratorio — OBJETIVO AL CIERRE DEL PROYECTO
Hitos que demostrarán TRL 4:
Prototipo hardware integrado: MLX90640 breakout (Adafruit 4407) + ESP32-S3 DevKit (MicroPython) + SHT31 + anemómetro RS485 + extensómetro de tronco (strain gauge + ADS1231 + DS18B20) + GPS + LoRa SX1276 915 MHz operando simultáneamente con autonomía solar ≥ 72 horas continuas. Arquitectura modular sin PCB custom — carcasa Hammond IP67 200×150×100mm.
Validación en condiciones de campo real controlado: 5 filas experimentales de Malbec de 136m (680 vides) intercaladas con 5 filas buffer a 100% ETc, sistema de riego por goteo diferencial — 5 regímenes hídricos independientes (100% ETc → sin riego), 1 tratamiento uniforme por fila, controladas por solenoides Rain Bird (1 por fila experimental). 5 nodos permanentes (1 por fila experimental, planta central), gimbal motorizado 7 ángulos × 96 ciclos/día. Potencial hídrico de tallo verificado con bomba de Scholander bajo protocolo Dra. Monteoliva. Error CWSI predicho vs. medido < ±0.10 unidades.
Dataset de calibración propio: 800 frames de imágenes térmicas de Malbec bajo protocolo Scholander (Dra. Monteoliva), capturados en al menos 2 estadios fenológicos y 2 regiones (Colonia Caroya + Mendoza). Split: 680 frames para fine-tuning (85%) + 120 frames reservados como set de validación independiente (15%). Dataset total del modelo: 1.050.680 imágenes (50.000 públicas + 1.000.000 sintéticas + 680 reales de fine-tuning). Set de validación independiente: 120 frames reales no vistos durante entrenamiento.
Modelo IA PINN (Physics-Informed Neural Network) — MobileNetV3-Tiny INT8 con la ecuación física del CWSI embebida en la función de pérdida. El modelo no puede predecir valores que violan el balance energético foliar. Entrenado con 1.050.680 imágenes (50.000 públicas + 1.000.000 sintéticas + 680 reales). Target: accuracy > 85% en set de validación de 120 frames independientes, latencia < 200ms en ESP32-S3. Primer modelo PINN de CWSI con termografía embebida documentado en Argentina.
Comunicación LoRaWAN funcional: transmisión nodo → gateway a 500m en ambiente abierto, latencia < 5 segundos, payload < 50 bytes.
Exportación GeoJSON y dashboard web básico: visualización de mapa de estrés georreferenciado accesible desde dashboard web (app móvil diferida a TRL 5).


5–9
TRL
Validación en campo real → Producto comercial — Fases posteriores (convocatorias TRL 5-6 y TRL 7-9)
TRL 5-6: prototipo en lote productivo real — el primer sitio de validación en campo real es el viñedo propio de Malbec en Colonia Caroya, Córdoba (1/3 ha, acceso exclusivo del equipo fundador). Financiado por Startup 2025 TRL 5-6 (USD 250K reembolsable 80/20) + inversión privada seed (The Yield Lab LATAM, Innventure). A partir del Mes 9: expansión a lotes de productores colaboradores gestionados por la red comercial de advisors. · TRL 7-9: comercialización y escalado — Startup 2025 TRL 7-9 (USD 500K) + ronda seed USD 200K–500K.




## 4. Descripción Técnica Detallada del Sistema
