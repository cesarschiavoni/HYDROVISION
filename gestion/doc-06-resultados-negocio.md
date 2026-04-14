

### 8.1 Resultados técnicos al cierre del proyecto
R1: Prototipo funcional nodo HydroVision AG — hardware integrado, software completo, documentación técnica y de usuario.
R2: Modelo IA PINN (Physics-Informed Neural Network) de CWSI — arquitectura que embebe la física del balance energético foliar en la función de pérdida. Entrenado con 1.050.680 imágenes, validado en 120 frames independientes con accuracy > 85%, exportado INT8. Contribución original: aplicación de arquitectura PINN al CWSI con termografía embebida en condiciones de campo argentinas.
R3: Dataset de 1.050.680 imágenes — 50.000 de fuentes públicas, 1.000.000 sintéticas del simulador físico propio, 800 frames reales de Malbec bajo protocolo Scholander (680 fine-tuning + 120 validación independiente). Data augmentation térmica (rotaciones, variaciones de ruido del sensor, ajustes de contraste) se aplica sobre los 680 frames de fine-tuning para ampliar la diversidad. Set de validación de 120 frames permanece sin augmentation para preservar la medición de accuracy. Activo estratégico diferencial.
R4: Solicitud de patente ante INPI Argentina — sistema de detección de estrés hídrico mediante termografía embebida con modelo de IA local.
R5: Documentación TRL 4 completa — informe técnico de validación en laboratorio con métricas, metodología reproducible y análisis de resultados.
R6: Empresa SAS constituida con pacto de socios — estructura legal lista para recibir inversión privada seed en la etapa posterior.
R7: ~~Sistema de alertas físicas en campo~~ → Reemplazado por control de riego autónomo integrado en nodo Tier 2. El nodo decide localmente cuándo regar según HSI y reporta vía WhatsApp, email y dashboard web. LED + sirena eliminados del diseño (mercado = riego automatizado). Las alertas son desactivables por el productor.
R8: Prueba de concepto de automatización de riego — Control autónomo integrado en nodo Tier 2-3 (relé SSR + solenoide Rain Bird). El nodo decide localmente cuándo regar según HSI (histéresis 0.30/0.20) y activa el solenoide vía GPIO → SSR. Validado con Rain Bird ESP-ME3 existente en viñedo experimental Colonia Caroya. Base tecnológica del Tier 2-3.
R9: Sistema de instalación asistida + activación QR — protocolo de puesta en marcha de 2 horas donde el técnico de campo instala la estaca, orienta el bracket y conecta el relé. El productor activa el nodo escaneando el código QR con su celular. Nodos adicionales los instala el productor solo siguiendo la app. Validado en el viñedo de Colonia Caroya.
R10: Informe de validación comercial — resultados de entrevistas estructuradas con al menos 5 productores de vid y olivo en Mendoza y San Juan, documentando disposición a pagar, objeciones principales, requisitos de usabilidad y sugerencias de mejora. Input directo para el plan comercial del proyecto TRL 5-6.
R11: Motor fenológico automático (GDD) — implementación del cálculo de grados-día acumulados con detección automática de brotación por convergencia de señal térmica y GDD, cambio automático de coeficientes CWSI por estadio fenológico (5 estadios), modo RDI automático en pre-cosecha, y modo hibernación invernal. Validado con datos históricos de temperatura de Colonia Caroya y Mendoza.
R12: Sistema de alertas agronómicas — 12+ tipos de alertas automáticas derivadas de los sensores existentes (helada tardía, estrés calórico, riesgo mildiú/botrytis, predicción de floración/envero/cosecha, ventana de desbrote, deadline PHI de fungicidas, horas de frío). Configurables por el productor con selección de canal (WhatsApp, email) y umbrales ajustables. El productor puede desactivar alertas en cualquier momento desde el dashboard.
R13: Modelo de fusión nodo-satélite — correlación CWSI↔NDWI validada con datos de Sentinel-2 sobre el viñedo de Colonia Caroya. Generación de mapa de CWSI estimado de todo el lote a partir de un solo nodo como punto de calibración. Prototipo de detección de anomalías espaciales por variación de NDVI.
R14: App móvil HydroVision AG beta — React Native con mapa de estrés georreferenciado, alertas push por umbrales de CWSI e historial por nodo. Motor de reglas de riego configurable incluido como funcionalidad base. Versión comercial completa se desarrolla en TRL 5.
R15: Motor de propuesta automatizada (pre-venta) — herramienta interna de pre-venta que genera automáticamente la propuesta de densidad de nodos para cualquier campo con solo las coordenadas GPS y el cultivo. El motor consulta Sentinel-2 histórico (3 temporadas), calcula el índice de variabilidad espacial del lote (coeficiente de variación NDVI), clasifica el lote en homogéneo / moderado / heterogéneo, y genera un mapa GeoJSON con la ubicación óptima de los nodos, la densidad recomendada por zona, el costo total de hardware + suscripción, y el ROI estimado según el ingreso bruto documentado por variedad. Output: PDF de una página listo para presentar al productor. Fundamento técnico: el análisis satelital previo permite dimensionar la implementación sin visita de campo — reduce el costo de adquisición comercial (CAC) y profesionaliza la primera conversación con el cliente. Base para la automatización comercial completa en TRL 5.
R16: Motor de auto-calibración dinámica del baseline CWSI (baseline.py + fusion_engine.py) — implementación completa del sistema de calibración autónoma del índice CWSI por nodo mediante eventos de campo: (1) CWSIBaseline con actualización EMA del offset tc_wet ante eventos de lluvia (MDS≈0 → Tc_wet real capturado sin visita humana) y detección de deriva del baseline (CWSI sistemáticamente fuera de rango → alerta de recalibración); (2) HSIFusionEngine con regresión lineal online CWSI=α+β×MDS_norm (ventana deslizante 60 muestras por nodo) que aprende la relación local entre sensores durante la temporada, pesos dinámicos por madurez del historial dendrométrico (mds_maturity), e imputación de CWSI desde MDS en días sin ventana solar útil. El sistema YA ES auto-calibrante desde TRL 3 computacional: el extensómetro de tronco actúa como referencia fisiológica de la cámara térmica, mejorando la precisión del CWSI activamente con el paso de la temporada sin intervención humana.
R17: Auto-diagnóstico de integridad óptica (optical_health.py) — módulo de monitoreo de salud física del sensor en cada ciclo de captura. Implementa tres mecanismos: (1) Detección de obstrucción por histograma: si la desviación estándar de temperaturas en el frame térmico cae por debajo del umbral mínimo configurable, se detecta pérdida de contraste por polvo/insecto/empañamiento → alerta "Lente Sucio/Empañado" al dashboard y al técnico de campo; (2) Validación de emisividad del panel Dry Ref: si T_dry_medido se desvía > 1.5°C de T_dry_esperado(radiación_solar, T_ambiente), indica contaminación del panel o pérdida de transparencia óptica; (3) Índice de Salud Óptica (ISO_nodo, 0–100%): métrica compuesta que integra la desviación del panel seco y la pérdida de contraste del histograma, actualizada en cada frame y reportada al dashboard. El técnico de campo (Javier Schiavoni) ejecuta limpieza de lente solo cuando ISO_nodo < 80% — el sistema elimina mantenimientos preventivos innecesarios y reduce el OPEX de personal técnico en campo estimado en ~85% respecto a protocolos de limpieza fija semanal. El módulo opera de forma autónoma: no requiere intervención humana para generar la alerta ni para determinar si el dato del frame es válido.

### 8.2 Hoja de ruta post-proyecto
Los resultados de este proyecto son la base directa de una secuencia de escalado en tres etapas. En TRL 5-6, el prototipo se valida en el viñedo propio de Malbec en Colonia Caroya y en lotes de productores colaboradores gestionados por la red comercial de advisors, financiado por Startup 2025 TRL 5-6 (hasta USD 250.000 reembolsable al 80%). En TRL 7-9, el producto se comercializa en Argentina y Chile con financiamiento Startup 2025 TRL 7-9 (hasta USD 500.000 reembolsable) complementado por ronda seed privada (The Yield Lab LATAM, Innventure, Pampa Start). La estrategia de mercado completa se detalla en la sección 8.3. En TRL 5-6 se implementa aprendizaje federado (federated learning) entre los nodos deployados: cada nodo entrena localmente con sus datos de campo reales y sube solo los gradientes al servidor central — no las imágenes. El modelo mejora con cada campaña sin etiquetado manual. Con 50+ nodos en campo, el sistema aprende de Malbec en Mendoza, olivo en San Juan y arándano en NOA simultáneamente. Este mecanismo crea un diferencial competitivo que se auto-refuerza: cada nodo instalado mejora el modelo para todos los clientes existentes.

Funcionalidades clave del producto en TRL 5 (sobre la base del TRL 4):
· Onboarding automatizado de cliente: el productor ingresa las coordenadas GPS de su campo en la app. El sistema consulta Sentinel-2 histórico (3 temporadas), analiza la variabilidad espacial (CV de NDVI por zona), clasifica el lote y genera automáticamente un mapa con la posición óptima de los nodos, la densidad recomendada por zona, el costo total y el ROI estimado. Output: propuesta lista en menos de 5 minutos, sin visita de campo ni intervención del equipo comercial. El motor de propuesta desarrollado como R15 en TRL 4 se integra a la app y al flujo de venta digital.
· Federated learning entre nodos deployados (ver arriba).
· Calibración de modelo para Sauvignon Blanc y Olivo Arauco — segunda variedad y segundo cultivo con coeficientes propios validados en campo.
· Dashboard de gestión multi-lote: el productor o asesor con múltiples campos visualiza el estado hídrico de todos sus lotes en un solo mapa, con filtros por cultivo, zona y nivel de alerta.
· Evaluación de arquitectura de calibración en escala comercial: los datos de la campaña TRL 4 (10 nodos, 10 meses) permitirán comparar la precisión del sistema Wet Ref físico vs. el sistema lluvia+MDS para determinar si la micro-bomba peristáltica es necesaria en despliegues comerciales de 50+ nodos o si el sistema lluvia+MDS (sin partes mecánicas adicionales) alcanza la misma precisión en condiciones reales de Cuyo. Esta decisión se tomará con datos propios antes de escalar el BOM de producción.

#### 8.2.1 Modelo de negocio — Tiers de servicio
Modelo: Hardware + suscripción de software separados. El productor adquiere el hardware del nodo (venta única o financiado en cuotas) y paga una suscripción anual por software, datos y plataforma. Este modelo es el más adecuado para el mercado argentino: elimina la barrera del capital de trabajo para HydroVision AG y reduce la cuota recurrente para el productor. Un nodo cubre 1–2 hectáreas según la geometría del lote.

| Tier | Nombre | Qué incluye | Hardware (venta única) | Suscripción / ha / año |
|------|--------|-------------|----------------------|----------------------|
| 1 | Monitoreo | Nodo sensor (sin relé) + gateway LoRa en comodato (compartido por lote) + alertas por WhatsApp / email (desactivables por el productor) + dashboard web con mapa GeoJSON de estrés + fusión Sentinel-2. Incluye índice HSI (CWSI térmico + MDS dendrométrico 24/7) y confianza dinámica por anemómetro. 1 nodo cubre 1–10 ha según densidad. El productor decide manualmente cuándo regar. | USD 950/nodo + visita instalación incluida (gateway en comodato) | USD 80–110/ha |
| 2 | Automatización | Tier 1 + riego autónomo: el nodo decide localmente cuándo regar según HSI (histéresis 0.30/0.20) y activa solenoide vía GPIO → SSR. Compatible con Rain Bird, Netafim, Irritrol. Sin intervención del servidor. Densidad recomendada: 1 nodo/2–5 ha. | USD 1.000/nodo + visita instalación incluida (gateway en comodato) | USD 130–170/ha |
| 3 | Precisión | Tier 2 + alta densidad (1 nodo/1–2 ha) + HSI dual completo (R²=0.90–0.95) + reporte compliance ISO 14046 huella hídrica + DaaS (datos exportables para auditorías) + SLA garantizado. Para bodegas premium, cereza/pistacho export, certificaciones UE. | USD 1.000/nodo + visita instalación incluida (gateway en comodato) | USD 220–290/ha |

**Nota:** Tier 4 "Elite" eliminado como tier separado. Los servicios adicionales (dron multiespectral tercerizado, consultoría agronómica mensual, calibración varietal prioritaria) se ofrecen como add-ons sobre cualquier tier, disponibles vía contrato plurianual.

**Cambio arquitectónico (abril 2026):** Se eliminó el LED tricolor + sirena del hardware. El mercado objetivo es exclusivamente plantaciones con riego automatizado (goteo/microaspersión). El nodo actúa autónomamente (Tier 2-3) o reporta vía WhatsApp, email y dashboard (Tier 1). Las alertas son desactivables por el productor. Alertas visuales/sonoras en campo no aportan valor a este segmento.


Ejemplo — 100 ha de vid, Tier 3
Año 1 (hardware + suscripción)
Año 2+ (solo suscripción)
ROI del productor
50 nodos Tier 3 × USD 1.000 = USD 50.000 · Gateway LoRa y conectividad en comodato (propiedad HydroVision, incluido en suscripción) · Suscripción software 100 ha × USD 255 = USD 25.500
USD 75.500
USD 25.500/año
Costo evitado con HSI (doble señal — mayor tasa de rescate que CWSI solo): recuperación del 12% de producción perdida por estrés hídrico no detectado (R²=0.90–0.95 vs. R²=0.63 single-signal; rango documentado 15–35% según Maes & Steppe 2012 y García-Tejero 2018) = USD 24.000 + ahorro en agua de riego (RDI 15-20%) USD 3.500 + ahorro jornales de inspección USD 4.000 = USD 31.500/año de beneficio recurrente · Costo total Año 1: USD 75.500 → Payback: USD 75.500 / USD 31.500 = 2,4 años · ROI Año 2+: USD 31.500 / USD 25.500 = 1,24x anual recurrente (24% de retorno sobre el costo de suscripción) · Nota: este ejemplo es Tier 3 alta densidad. En Tier 1 (1 nodo/10 ha), el payback Año 1 es positivo al reducir el costo total a ~USD 214/ha.


Densidad de nodos: En lotes homogéneos (suelo uniforme, pendiente mínima) 1 nodo cada 2 ha es suficiente. En lotes con alta variabilidad (distintos tipos de suelo, exposición solar) se recomienda 1 nodo por ha. El productor puede comenzar con densidad baja y agregar nodos en sectores críticos identificados en la primera campaña.

#### 8.2.1A Costo de instalación por hectárea — densidad mínima viable y aplicabilidad a cultivos extensivos

El costo total por hectárea depende de la densidad de nodos elegida y del objetivo de monitoreo. Existe una distinción crítica entre las dos señales del sistema: el CWSI térmico puede extrapolarse espacialmente vía Sentinel-2 (hasta 10–20 ha por nodo en lotes homogéneos), mientras que el MDS dendrométrico es una señal de planta única que no tiene proxy satelital. A densidades bajas, el sistema opera con CWSI + satélite (R²~0.63); a densidades altas, opera con HSI dual-señal completo (R²~0.90–0.95). La tabla incorpora ambas dimensiones: costo por ha y precisión real de estimación de ψ_stem:

Densidad
Señal activa
Precisión ψ_stem (R²)
Error CWSI extrapolado
Costo total/ha/año (Tier 1, amort. 5 años)
Uso recomendado
1 nodo / 1 ha
HSI completo (CWSI + MDS 24/7)
R²=0.90–0.95
±0.07–0.09 (directo)
USD 275
Investigación varietal, prescripción diferencial máxima, Tier 3 Precisión + add-ons
1 nodo / 2 ha
HSI completo (CWSI + MDS 24/7)
R²=0.90–0.95
±0.07–0.09 (directo)
USD 177
Lotes homogéneos — control automático de riego Tier 2-3. Densidad óptima para productor premium.
1 nodo / 5 ha
CWSI + MDS en zona del nodo · CWSI+sat en resto
R²=0.75–0.82 promedio lote
±0.10–0.12 (extrapolado)
USD 119
Mix HSI puntual + cobertura satelital. Identifica zonas de estrés con buena resolución.
1 nodo / 10 ha
CWSI térmico + Sentinel-2
R²=0.60–0.67
±0.12–0.15 (extrapolado)
USD 99
Monitoreo de tendencias y alertas de estrés severo. El satélite hace el 70% del trabajo. Punto de entrada recomendado para adopción gradual.
1 nodo / 20 ha
CWSI térmico + Sentinel-2 (límite práctico)
R²=0.55–0.63
±0.15 (límite aceptable)
USD 90
Límite de extrapolación útil en lotes muy homogéneos. Error CWSI ≥±0.15 hace la prescripción diferencial poco confiable.
1 nodo / 50 ha
Solo Sentinel-2 calibrado
R²<0.50 (solo tendencias)
±0.20+ (extrapolación gruesa)
USD 84
Detección de anomalías severas a escala de campo. No apto para decisiones de riego por sector.

Límite de extrapolación: más allá de 1 nodo / 20 ha en lotes homogéneos (o 1 nodo / 5 ha en lotes heterogéneos), el error de extrapolación CWSI supera ±0.15 unidades — umbral a partir del cual la prescripción diferencial de riego pierde confiabilidad agronómica. El MDS dendrométrico no extrapola en ningún caso: funciona como señal de referencia fisiológica exacta para la zona del nodo, y como ancla de calibración de confianza para validar el CWSI extrapolado en las zonas sin nodo.

Instalación adicional: el primer nodo requiere visita de puesta en marcha de 2 horas (incluida en el precio). Los nodos adicionales los activa el productor con código QR en menos de 5 minutos — costo de instalación incremental = USD 0.

Aplicabilidad a cultivos extensivos: Para cultivos de alto volumen y menor valor unitario (soja, maíz, trigo), la viabilidad económica depende de la densidad mínima posible gracias a la fusión satelital. Con 1 nodo cada 50 ha, el costo anual desciende a USD 84/ha — pero a esa densidad solo se detectan anomalías severas, sin precisión de prescripción diferencial, y el valor rescatado en cultivos extensivos (USD 80–120/ha en soja/maíz) genera un ROI marginal. Por este motivo, HydroVision AG no apunta a cultivos extensivos en TRL 4 ni TRL 5. Sin embargo, la arquitectura ya habilita esta expansión cuando los costos de hardware bajen a USD 100–120/nodo a escala (TRL 6+, COGS ya ~USD 112 en lote 500+, PCB con volumen).

Umbral económico mínimo: el sistema se justifica financieramente (ROI > 3x) cuando el ingreso bruto por hectárea supera USD 2.500/ha con densidad de 1 nodo/10 ha. Todos los cultivos de alto valor del portafolio actual (vid, olivo, cerezo, pistacho, nogal, citrus) superan ampliamente este umbral.

Validación con densidad mínima — adopción gradual en 3 pasos: (1) Temporada 1: 1 nodo / 10–20 ha — mapa de estrés satelital del lote completo con cobertura CWSI básica, alertas de estrés severo operativas desde el día 1, inversión mínima; (2) Temporada 2: agregar nodos en las zonas críticas identificadas → 1 nodo / 5 ha en sectores de mayor variabilidad — HSI completo en las zonas que más impactan el rendimiento; (3) Temporada 3: densidad plena 1 nodo / 2 ha en todo el lote si el ROI de la segunda campaña lo justifica. Este modelo reduce la inversión inicial en hardware hasta un 80% respecto a la densidad plena, con el máximo valor del sistema disponible de forma incremental.

#### 8.2.1B Casos de implementación — ejemplos hipotéticos por perfil de productor

Los siguientes cinco casos ilustran cómo se traduce la densidad de nodos a costo real, señal activa y ROI según el perfil del productor. Todos los valores de beneficio se calculan sobre el ingreso bruto documentado por variedad (Sección 8.3.3) y el aporte de rescate del sistema.

─────────────────────────────────────────────────────────────────
CASO 1 — Productor vitivinícola familiar, primer año
Valle de Uco, Mendoza · 20 ha Malbec premium · Riego por goteo instalado
Densidad: 1 nodo / 10 ha → 2 nodos Tier 1 + 1 gateway
─────────────────────────────────────────────────────────────────
Perfil: productor familiar de 20 ha, segunda generación, riego por goteo instalado hace 3 años, nunca monitoreó estrés foliar. Quiere evaluar el sistema antes de comprometerse.

Inversión:
· Hardware: 2 nodos × USD 950 = USD 1.900 (gateway LoRa en comodato — incluido en suscripción)
· Suscripción Año 1: 20 ha × USD 80/ha = USD 1.600
· Total Año 1: USD 3.500

Señal activa: CWSI térmico en 2 puntos del lote + Sentinel-2 cubre las 20 ha con R²=0.63. MDS dendrométrico activo en 2 plantas de referencia — no cubre el lote completo pero confirma si la señal térmica está captando estrés real.

Beneficio estimado:
· Ingreso bruto Malbec premium: USD 9.600/ha × 20 ha = USD 192.000
· Recuperación del 8% de rendimiento perdido por estrés no detectado (conservador para señal de baja densidad): USD 15.360
· Ahorro en agua de riego (2 eventos evitados por temporada): USD 1.200
· Total beneficio: USD 16.560

ROI Año 1: USD 16.560 / USD 3.500 = 4,7x · Payback: < 3 meses de campaña
ROI Año 2+ (solo suscripción USD 1.600): USD 16.560 / USD 1.600 = 10,4x

Valor estratégico: el productor identifica cuál de sus 2 sectores tiene mayor variabilidad de estrés. En la Temporada 2 agrega 2 nodos en el sector crítico → llega a 1/5 ha donde más importa, sin comprar densidad completa.

─────────────────────────────────────────────────────────────────
CASO 2 — Olivicultor San Juan, adopción intermedia
Albardón, San Juan · 50 ha Olivo Arbequina superintensivo (seto) · Goteo con fertirrigación
Densidad: 1 nodo / 5 ha → 10 nodos Tier 2 + 2 gateways
─────────────────────────────────────────────────────────────────
Perfil: productor de olivo superintensivo (1.600 plantas/ha), riego por goteo con fertirrigación automatizada. Ya tiene tensiómetros de suelo pero sabe que en seto las raíces absorben de manera heterogénea. Crisis hídrica severa en San Juan — cada m³ de agua tiene costo real de oportunidad.

Inversión:
· Hardware: 10 nodos × USD 950 = USD 9.500 (gateways LoRa en comodato — incluidos en suscripción)
· Suscripción Año 1: 50 ha × USD 130/ha (Tier 2 punto medio) = USD 6.500
· Total Año 1: USD 16.000

Señal activa: Mix HSI completo en 10 zonas (cobertura directa) + Sentinel-2 interpola entre nodos → R² promedio lote ~0.78. El anemómetro en cada nodo detecta el viento del Zonda (fenómeno frecuente en San Juan) y descarta automáticamente las lecturas térmicas corruptas → HSI se apoya en MDS durante eventos Zonda, que es exactamente cuando el estrés es más alto y más difícil de medir con térmica.

Beneficio estimado:
· Ingreso bruto AOVE Arbequina: USD 5.500/ha × 50 ha = USD 275.000
· Recuperación del 10% de rendimiento + bonificación rendimiento graso (HSI R²=0.78 > solo-térmica R²=0.63): USD 27.500
· Ahorro hídrico documentado (RDI 15-20% con control preciso): USD 4.200 (reducción costos de bombeo + cupo de agua disponible para más ha)
· Total beneficio: USD 31.700

ROI Año 1: USD 31.700 / USD 16.000 = 1,98x · Payback: 6 meses
ROI Año 2+ (solo suscripción USD 6.500): USD 31.700 / USD 6.500 = 4,9x

Valor estratégico: en San Juan el cupo de agua es un activo. El ahorro del 15-20% de agua no solo reduce costos — libera cupo para ampliar la superficie productiva. Un productor de 50 ha que ahorra 18% de agua puede regar 9 ha más sin nueva concesión.

─────────────────────────────────────────────────────────────────
CASO 3 — Bodega exportadora, implementación completa
Luján de Cuyo, Mendoza · 100 ha Malbec con certificación de sustentabilidad · Tier 3 Precisión
Densidad: 1 nodo / 2 ha → 50 nodos Tier 3 + 5 gateways + control automático de riego
─────────────────────────────────────────────────────────────────
Perfil: bodega premium exportadora a Europa y EE.UU. con protocolo de sustentabilidad ISO 14046. Necesita evidencia cuantificada de huella hídrica por parcela para certificación. Ya tiene solenoides Rain Bird instalados en las 5 zonas del lote. Quiere automatización completa del riego con IA fisiológica.

Inversión:
· Hardware: 50 nodos × USD 1.000 (Tier 3) = USD 50.000 (gateways LoRa en comodato — incluidos en suscripción)
· Suscripción Año 1: 100 ha × USD 255/ha (Tier 3 punto medio) = USD 25.500
· Total Año 1: USD 75.500

Señal activa: HSI completo en todo el lote (100% cobertura directa). CWSI térmico + MDS dendrométrico activos en cada zona. Confianza dinámica por anemómetro en cada nodo. R²=0.90–0.95 en toda la superficie. Automatización del riego: el sistema activa solenoides automáticamente cuando HSI cruza el umbral de estrés — sin intervención del enólogo. El productor configura las reglas de umbral; el sistema ejecuta y registra cada evento con timestamp georreferenciado.

Beneficio estimado:
· Ingreso bruto Malbec premium: USD 9.600/ha × 100 ha = USD 960.000
· Recuperación del 12% de rendimiento + bonificación calidad enológica (polifenoles, concentración) por RDI de precisión: USD 115.200
· Ahorro jornales de inspección y operación manual de riego: USD 8.000/temporada
· Acceso a mercados premium UE/USA con certificación huella hídrica (diferencial USD 0.50/botella × producción estimada): USD 18.000
· Total beneficio: USD 141.200

ROI Año 1: USD 141.200 / USD 75.500 = 1,87x · Payback: 6,4 meses de campaña
ROI Año 2+ (solo suscripción USD 25.500): USD 141.200 / USD 25.500 = 5,5x

Valor estratégico: la certificación de huella hídrica documentada por el sistema HydroVision (timestamp de cada evento de riego + ψ_stem en ese momento) es un activo de diferenciación en exportación que ningún competidor puede proveer hoy en Argentina.

─────────────────────────────────────────────────────────────────
CASO 4 — Productor de cereza, densidad máxima de precisión
Valle de Uco (Tunuyán), Mendoza · 12 ha Cereza Bing · Tier 3 Precisión + add-ons
Densidad: 1 nodo / 1 ha → 12 nodos Tier 3 + 2 gateways
─────────────────────────────────────────────────────────────────
Perfil: productor de cereza de exportación al mercado asiático. El valor de la cereza depende casi enteramente de la firmeza del fruto en el momento de cosecha — un déficit hídrico de 48 horas en el período crítico (engorde del fruto, 3 semanas antes de cosecha) reduce la firmeza un 15–25% y desclasifica el lote de exportación premium a industria (diferencia USD 4–8/kg). No tolera un solo evento de estrés no detectado. Opera con 1 nodo por ha.

Inversión:
· Hardware: 12 nodos × USD 1.000 = USD 12.000 (gateways LoRa en comodato — incluidos en suscripción)
· Suscripción Año 1: 12 ha × USD 290/ha (Tier 3 Precisión + add-on consultoría agronómica mensual) = USD 3.480
· Total Año 1: USD 15.480

Señal activa: HSI completo en cada hectárea de forma independiente. MDS dendrométrico detecta la contracción del tronco 12–24 horas antes de que el CWSI térmico supere el umbral visible — tiempo de anticipación clave para actuar antes del daño en la fruta. El protocolo de rescate hídrico (ψ_stem < −1.5 MPa) activa push + control automático de riego simultáneamente.

Beneficio estimado:
· Ingreso bruto cereza exportación: USD 30.000/ha × 12 ha = USD 360.000
· Prevención de un evento de desclasificación de lote completo (probabilidad documentada 1 cada 3 años sin monitoreo → 0 con HSI de precisión): USD 360.000 × 33% probabilidad × 20% desclasificación = USD 23.760/año equivalente
· Recuperación del 8% rendimiento adicional por manejo RDI fino en engorde: USD 28.800
· Total beneficio: USD 52.560

ROI Año 1: USD 52.560 / USD 15.480 = 3,4x · Payback: 4 meses
ROI Año 2+ (solo suscripción USD 3.480): USD 52.560 / USD 3.480 = 15,1x

Valor estratégico: un solo evento de desclasificación de lote completo (riesgo real 1 cada 3 temporadas sin monitoreo) cuesta más que 5 años de suscripción HydroVision. El productor de cereza premium no compra el sistema por el ROI — lo compra porque elimina el riesgo catastrófico.

─────────────────────────────────────────────────────────────────
CASO 5 — Gran operación pistachera, densidad híbrida por zonas
Caucete, San Juan · 200 ha Pistacho Kerman · 3 zonas de suelo distintas
Densidad híbrida: zona A 60 ha suelo arenoso homogéneo (1/10 ha) · zona B 80 ha suelo mixto (1/5 ha) · zona C 60 ha pendiente y salinidad variable (1/2 ha)
→ 6 + 16 + 30 = 52 nodos Tier 2-3 + 6 gateways
─────────────────────────────────────────────────────────────────
Perfil: empresa agroindustrial con 200 ha de pistacho en producción plena. El lote tiene tres zonas con comportamiento hídrico distinto identificadas en la primera campaña satelital. No tiene sentido — ni económico ni agronómico — instalar la misma densidad en todo el lote.

Inversión:
· Zona A (60 ha, 1/10 ha): 6 nodos × USD 950 = USD 5.700
· Zona B (80 ha, 1/5 ha): 16 nodos × USD 1.000 (Tier 3) = USD 16.000
· Zona C (60 ha, 1/2 ha): 30 nodos × USD 1.000 = USD 30.000
· Gateways LoRa (6 unidades): en comodato — incluidos en suscripción
· Total hardware: USD 51.700
· Suscripción: 60 ha × USD 80 + 80 ha × USD 220 + 60 ha × USD 255 = USD 4.800 + USD 17.600 + USD 15.300 = USD 37.700
· Total Año 1: USD 89.400

Señal activa por zona:
· Zona A: CWSI+sat R²=0.63 — suficiente porque el suelo es homogéneo y el comportamiento es predecible. El satélite extrapola bien.
· Zona B: Mix HSI+sat R²=0.78 — zonas de transición detectadas con mayor resolución.
· Zona C: HSI completo R²=0.90–0.95 — la salinidad y la pendiente generan heterogeneidad que solo se captura con señal directa planta por planta.

Beneficio estimado:
· Ingreso bruto pistacho: USD 18.000/ha × 200 ha = USD 3.600.000
· Recuperación de frutos vanos (caída sin relleno por estrés en floración) — reducción documentada 8% con monitoreo preciso en zona C: USD 288.000 × 8% = USD 23.040
· Ahorro hídrico por RDI preciso en zona A (donde se sobrerriegaba por falta de señal): USD 12.000
· Total beneficio estimado: USD 35.040

ROI Año 1: USD 35.040 / USD 89.400 = 0,39x (inversión de capital inicial alta)
ROI Año 2+ (solo suscripción USD 37.700): USD 35.040 / USD 37.700 = 0,93x · Payback total: ~2,6 años

Valor estratégico: el caso pistacho ilustra que la densidad híbrida reduce el costo de hardware total en ~48% respecto a cobertura uniforme 1/2 ha en todo el lote (que hubiera costado USD 100.000 en hardware), sin sacrificar precisión en las zonas críticas. La Zona A subsidia el overhead; la Zona C justifica toda la inversión.

─────────────────────────────────────────────────────────────────

Resumen comparativo de los 5 casos:

Caso
Cultivo / ha
Densidad
Total Año 1
Beneficio/año
ROI Año 2+
Perfil de riesgo
1 · Valle de Uco 20 ha Malbec
1/10 ha · Tier 1
USD 3.500
USD 16.560
10,4x
Entrada gradual — máxima eficiencia capital
2 · San Juan 50 ha Olivo
1/5 ha · Tier 2
USD 16.000
USD 31.700
4,9x
Ahorro hídrico como driver principal
3 · Luján de Cuyo 100 ha Malbec
1/2 ha · Tier 3
USD 75.500
USD 141.200
5,5x
Automatización + certificación exportación
4 · Tunuyán 12 ha Cereza
1/1 ha · Tier 3
USD 15.480
USD 52.560
15,1x
Eliminación riesgo catastrófico
5 · San Juan 200 ha Pistacho
Híbrida · Tier 2-3
USD 89.400
USD 40.160
1,07x (Año 2) — crece con adopción
Escala con optimización por zona

#### 8.2.2 Fuentes de ingreso secundarias — escalado de rentabilidad
Además del modelo SaaS por tiers, HydroVision AG proyecta cuatro fuentes de ingreso adicionales que se activan progresivamente a medida que escala la base de clientes:

Fuente
Descripción
Activación
Potencial anual
Monetización de datos agroclimáticos
Con 50+ lotes activos, los datos de CWSI georreferenciados por variedad, zona y fecha tienen valor para aseguradoras agrícolas (calibración de siniestros hídricos), bodegas premium (trazabilidad de estrés por campaña) y empresas de semillas (ensayos varietales de tolerancia). Datos anonimizados y agregados — sin comprometer la privacidad del productor.
Mes 18+ (50+ lotes activos)
USD 30.000–80.000/año
Seguro paramétrico hídrico
Alianza con aseguradoras para ofrecer seguros de rendimiento activados automáticamente por umbrales de CWSI verificados por el nodo. HydroVision actúa como proveedor del índice verificable y cobra una comisión por cada hectárea asegurada. El productor tiene cobertura objetiva sin peritaje manual.
Año 2
USD 40–120/ha asegurada
Créditos de carbono por eficiencia hídrica
La reducción cuantificada de consumo de agua mediante riego de precisión genera créditos de carbono en mercados voluntarios (Verra VCS, Gold Standard). HydroVision provee la metodología de medición y verificación del ahorro hídrico, actuando como agregador de créditos de múltiples productores para alcanzar volúmenes comercializables.
Año 3 (2027+)
USD 15–45/ha/año
Automatización del riego como servicio gestionado
En Tier 3, el productor puede contratar la gestión completa del riego: HydroVision define las reglas de activación, monitorea los resultados y ajusta los parámetros estacionalmente. Es un modelo de servicio gestionado con mayor stickiness que el SaaS puro — el productor delega una función crítica de su operación.
Año 2 (Tier 3+)
+USD 40–80/ha sobre precio base


#### 8.2.3 Impacto Ambiental y Sostenibilidad


HydroVision AG contribuye directamente a los objetivos de desarrollo sostenible, un criterio de evaluación crítico para financiamiento ANPCyT/BID. El proyecto genera impacto ambiental cuantificable y alineado con las políticas públicas de uso eficiente del agua en zonas áridas y semiáridas de Argentina y Chile:

Dimensión ambiental
Descripción y mecanismo
Impacto cuantificado
Eficiencia Hídrica
El Riego Deficitario Controlado (RDI) asistido por IA de HydroVision permite regar con precisión fisiológica, evitando tanto el déficit hídrico dañino como el exceso de agua. Cada alerta de CWSI evita un ciclo de riego innecesario o permite posponerlo con base en el estado real de la planta.
Reducción 15–20% en consumo de agua de riego + recuperación del 10–15% de producción perdida por estrés no detectado
Huella de Carbono
La optimización de los ciclos de bombeo eléctrico de riego —evitando riegos innecesarios— reduce el consumo energético y la huella de carbono del ciclo productivo. Las bodegas exportadoras requieren certificaciones de sustentabilidad para acceder a mercados europeos y norteamericanos; HydroVision provee la evidencia cuantificada.
Reducción consumo energético de bombeo + habilitación de certificaciones de sustentabilidad
Resiliencia Climática
Herramienta crítica para la adaptación de cultivos regionales frente a las megasequías y olas de calor recurrentes en Cuyo y el NOA. En contextos de restricción hídrica crónica, optimizar cada litro es una ventaja competitiva para el productor y una necesidad estratégica para la región.
Alineado con ODS 2 (hambre cero), ODS 6 (agua limpia) y ODS 13 (acción climática)


#### 8.2.4 Compliance UE y Certificación de Huella Hídrica — Oportunidad Regulatoria 2026

**Contexto regulatorio**: La Directiva ECGT (Empowering Consumers for the Green Transition, Directiva UE 2024/825) entra en vigor el **27 de septiembre de 2026** en toda la Unión Europea. A partir de esa fecha:

- Queda **prohibido** usar claims ambientales genéricos ("sustentable", "eco-friendly", "uso eficiente del agua") sin evidencia verificada por un tercero independiente.
- Las etiquetas de sustentabilidad deben estar basadas en un esquema de certificación que cumpla con los requisitos de la ECGT.
- Aplica a **cualquier producto vendido a consumidores europeos**, independientemente del país de origen.
- Los claims sobre desempeño ambiental futuro requieren un plan de implementación verificado por tercero.

**Impacto en el mercado de exportación argentino**: Las bodegas argentinas que exportan Malbec, Cabernet y otros varietales premium a la UE (principal mercado de exportación del sector) necesitarán evidencia verificada de su gestión hídrica para hacer cualquier claim ambiental en etiqueta. Bodegas de Argentina ya implementó la Huella Ambiental de Producto (HAP) verificada por SGS, y el PEVI 2030 tiene la sustentabilidad como eje — pero la **huella hídrica medida con datos reales de planta** es el eslabón más débil: la mayoría estima con modelos teóricos ET₀ (error 30-40% en eventos VPD extremo comunes en Cuyo).

**Estándares internacionales compatibles con HydroVision**:

| Estándar | Qué certifica | Cómo alimenta HydroVision |
|---|---|---|
| **ISO 14046** | Huella hídrica de producto/organización | Datos de m³/ha medidos con CWSI real cada 15 min, 365 días |
| **AWS v3.0** (Alliance for Water Stewardship, dic 2025) | Gestión responsable del agua a nivel de cuenca | Consumo real por zona, trazabilidad de decisiones de riego |
| **PEF/PEFCR** (UE) | Huella ambiental de producto — reglas específicas para vino ya publicadas | Los datos continuos del nodo alimentan directamente el cálculo PEF |
| **ECGT 2026** | Verificación de claims ambientales en UE | Sin datos verificados = prohibido hacer claims de sustentabilidad |

**Premium de mercado verificado**: Un meta-análisis publicado en 2025 (Food Quality and Preference, ScienceDirect) demuestra que los consumidores europeos pagan en promedio **+15% (IC 95%: 13-18%)** por vino con certificación de sustentabilidad verificada. El 88% de los consumidores de vino declara interés en comprar vino con certificación sustentable. Para una bodega que exporta Malbec a EUR 18/botella, +15% = EUR 2.70/botella adicional. En 100.000 botellas de exportación: **EUR 270.000 adicionales por año**.

**Producto derivado — HV-Water Certified**: Reporte mensual/anual de eficiencia hídrica auditable generado automáticamente por la plataforma HydroVision. El productor puede:
1. Adjuntarlo a su etiqueta de exportación para cumplir con ECGT 2026
2. Presentarlo ante certificadoras AWS/ISO 14046/SGS
3. Usarlo como evidencia verificada para claims de sustentabilidad ante importadores europeos
4. Acceder al premium de precio de +15% con datos reales (no estimaciones)

**Pricing**: USD 30-50/ha/año adicionales sobre el tier base (ya incluido en Tier 3 Precisión). Para Tier 1 y Tier 2, se ofrece como add-on.

**Ventaja competitiva diferencial**: HydroVision es la única solución en LATAM que mide estrés hídrico fisiológico real de planta (CWSI + MDS) de forma continua. La competencia (Phytech, CropX, estaciones meteorológicas) no puede generar reportes de huella hídrica con la misma resolución temporal (15 min vs. diario/semanal) ni con señal directa de planta (vs. modelos de suelo/atmosféricos).

**Argumento de venta al productor exportador**: "A partir de septiembre 2026, si no tenés datos verificados de huella hídrica, no podés hacer claims de sustentabilidad en la UE. Tus compradores europeos te lo van a exigir. HydroVision genera esos datos automáticamente, los 365 días del año, con la precisión que una auditoría ISO 14046 requiere."

**Implicación estratégica (D3 de doc-10 actualizado)**: El compromiso previo de 2-3 bodegas exportadoras para el módulo HV-Water Certified se vuelve más urgente con la ECGT entrando en vigor en septiembre 2026. Recomendación: iniciar conversaciones con Bodegas de Argentina y 2-3 bodegas del Valle de Uco en Mes 3-4 del TRL 4.

---

#### 8.2.5 Estrategia de Retención — Por qué los productores no cancelan

**Problema central**: La campaña de riego activa va de octubre a marzo (~6 meses). Sin estrategia de retención, el productor podría querer pagar solo los meses de riego y suspender el servicio en invierno.

**Investigación de mercado (abril 2026)**: Se analizaron las estrategias de retención de las industrias con mayor éxito en servicios que los clientes valoran solo una parte del tiempo:

| Industria | Problema | Estrategia clave | Retención promedio |
|---|---|---|---|
| **ADT / Alarmas** | El 99% del tiempo no pasa nada | Hardware en comodato + contrato 36 meses + "vendés tranquilidad, no monitoreo" | 15 años por cliente |
| **Gimnasios** | 67% no asiste en un mes dado | Desafíos estacionales + comunidad (56% más retención en grupales) + progreso visible en 90 días | 60% con progreso visible |
| **Control de plagas** | Plagas solo en verano | Billing flat mensual (costo anual ÷ 12) + prevención invernal que justifica el pago continuo | 80-90% anual |
| **Netflix/Spotify** | Usuarios inactivos 3+ semanas | Nudges personalizados + datos como ancla (historial, playlists) + hábito integrado | 90%+ con interacción social |
| **Seguros** | Puro gasto sin siniestro | Aversión a la pérdida: cancelar = quedar expuesto | Muy alta (inercia psicológica) |

**Estrategias aplicadas a HydroVision AG**:

1. **Hardware en comodato** (ADT): El nodo es propiedad de HydroVision AG. Si el productor cancela, devuelve los nodos. El switching cost de desinstalar + perder setup es alto. Densidad: 1 nodo/5 ha (Tier 1), 1 nodo/3 ha (Tier 2), 1 nodo/2 ha (Tier 3).

2. **Contrato anual obligatorio** (Control de plagas): No se ofrece opción mensual. El precio es anual (USD 95/150/250 por ha/año). Facturación plana — mismo monto todo el año.

3. **Valor real fuera de campaña de riego** (Control de plagas — prevención invernal):
   - Abril-Septiembre: monitoreo de heladas tardías (T foliar en tiempo real), acumulación de horas de frío para planificar brotación, detección de anegamiento por lluvias, historial continuo para planificación, datos dendrométricos de dormancia (MDS), fusión Sentinel-2 para anomalías de cobertura, alertas de fumigación (PM2.5) y viento extremo.
   - El nodo sigue midiendo y transmitiendo los 365 días.

4. **Datos como ancla** (Spotify/Netflix): El historial acumulado de CWSI, baselines calibrados y comparaciones interanuales no se pueden recrear — requieren temporadas completas de datos continuos. Cancelar = perder ventaja competitiva acumulada.

5. **Framing de protección** (Seguros): El producto no es "monitoreo de riego" — es **protección contra pérdidas catastróficas**. Un evento de desclasificación en cereza (USD 340.000) o pérdida de calidad enológica en vid (USD 192.000) supera años de suscripción.

6. **Progreso visible rápido** (Gimnasios): Primera alerta accionable en < 14 días post-instalación. El doc-10 ya documenta que si esto ocurre, la probabilidad de renovación sube a > 95%.

7. **Comunidad de productores** (Gimnasios — clases grupales): Benchmarking regional anonimizado, agrónomo conectado al dashboard, casos de éxito documentados por temporada. La retención social (el agrónomo adopta HydroVision como herramienta) hace que el contrato se renueve automáticamente.

**Precios fijos por tier (definidos abril 2026)**:

| Tier | Precio fijo | Nodo en comodato | Gateway LoRa en comodato | Margen neto/ha |
|---|---|---|---|---|
| 1 — Monitoreo | USD 95/ha/año | 1 cada 5 ha | 1 cada 10 nodos (compartido) | USD 83/ha (cloud USD 12/ha) |
| 2 — Automatización | USD 150/ha/año | 1 cada 3 ha | 1 cada 10 nodos (dedicado) | USD 138/ha |
| 3 — Precisión | USD 250/ha/año | 1 cada 2 ha | 1 cada 10 nodos + Starlink si necesario | USD 238/ha |

**Nota sobre comodato — nodos**: El nodo (COGS USD 149) se paga solo en ~4 meses de suscripción Tier 2 (3 ha × USD 150 = USD 450/año). A vida media del cliente de 7 años, el LTV del nodo en comodato es ampliamente positivo. El comodato elimina la barrera de entrada (el productor no paga USD 950+ de golpe) y aumenta la retención (devolver nodos = mayor fricción que renovar).

**Nota sobre comodato — gateway LoRa y conectividad**: El gateway RAK7268 (COGS USD 250) y la conectividad a internet (router 4G o Starlink Mini X según cobertura) son propiedad de HydroVision AG y se entregan en comodato junto con los nodos. El productor no paga hardware — solo la suscripción anual. Si cancela, HydroVision retira todo el equipo (nodos + gateway + router/Starlink).

#### 8.2.4A Conectividad del gateway — modelo dual 4G / Starlink

**Principio**: el gateway LoRa necesita internet para reenviar la telemetría al backend. El volumen de datos es ínfimo (~30–50 MB/mes para 10 nodos), por lo que no se requiere ancho de banda — solo cobertura. La conectividad se resuelve con dos opciones según la disponibilidad en el campo:

**Opción A — Router 4G industrial (donde hay cobertura celular)**

| Concepto | Costo |
|---|---|
| Router Teltonika RUT241 (industrial, IP30, -40/+75°C) | USD 155–190 (una vez) |
| Chip M2M IoT (Claro/Movistar, ~100 MB/mes) | USD 3–5/mes = USD 36–60/año |
| **COGS total Año 1** | **USD 195–250** |
| **COGS total Año 2+** | **USD 36–60/año** |

Ventajas: costo 6x menor que Starlink, sin antena visible, funciona con cualquier operador argentino, el RUT241 tiene failover automático y gestión remota (Teltonika RMS).

**Opción B — Starlink Mini X (donde NO hay cobertura celular)**

| Concepto | Costo |
|---|---|
| Kit Starlink Mini X (antena + router WiFi integrado) | ~USD 215 (una vez, al blue) |
| Plan Residencial Lite (38.000 ARS/mes) | ~USD 27/mes = USD 324/año |
| **COGS total Año 1** | **~USD 539** |
| **COGS total Año 2+** | **~USD 324/año** |

Ventajas: cobertura satelital en cualquier punto del territorio argentino, latencia 30–50 ms, suficiente para telemetría IoT.

**Regla de decisión por tier y cobertura:**

| Tier | Con 4G | Sin 4G | Quién absorbe el costo |
|---|---|---|---|
| T1 — Monitoreo | Router 4G incluido en comodato | **No se ofrece Starlink** — el revenue (USD 95/ha) no lo justifica. El campo necesita mínimo 4G o WiFi. | HydroVision AG |
| T2 — Automatización | Router 4G incluido en comodato | Starlink incluido en comodato (el revenue de USD 150/ha en 50+ ha lo absorbe) | HydroVision AG |
| T3 — Precisión | Router 4G incluido en comodato | Starlink incluido en comodato sin cargo adicional | HydroVision AG |

**Análisis de impacto en margen:**

| Campo | Revenue anual | Costo Starlink/año | % del revenue | Costo 4G/año | % del revenue |
|---|---|---|---|---|---|
| 20 ha T1 | USD 1.900 | USD 324 | **17% — NO rentable** | USD 50 | 2.6% |
| 50 ha T2 | USD 7.500 | USD 324 | 4.3% — aceptable | USD 50 | 0.7% |
| 100 ha T2 | USD 15.000 | USD 324 | 2.2% — bueno | USD 50 | 0.3% |
| 100 ha T3 | USD 25.000 | USD 324 | 1.3% — excelente | USD 50 | 0.2% |

**Conclusión**: Starlink solo se justifica en Tier 2-3 con campos de 50+ ha sin cobertura 4G. Para Tier 1 y campos chicos, el router 4G es la única opción rentable. En la práctica, la mayoría de los campos en Mendoza, San Juan y Córdoba tienen cobertura 4G — Starlink será la excepción, no la regla.

**Densidad de gateways LoRa por hectárea:**

| Superficie campo | Tier 1 (1 nodo/5 ha) | Tier 2 (1 nodo/3 ha) | Tier 3 (1 nodo/2 ha) |
|---|---|---|---|
| 20 ha | 4 nodos + 1 gateway | 7 nodos + 1 gateway | 10 nodos + 1 gateway |
| 50 ha | 10 nodos + 1 gateway | 17 nodos + 2 gateways | 25 nodos + 3 gateways |
| 100 ha | 20 nodos + 2 gateways | 34 nodos + 4 gateways | 50 nodos + 5 gateways |
| 200 ha | 40 nodos + 4 gateways | 67 nodos + 7 gateways | 100 nodos + 10 gateways |

Regla práctica: **1 gateway RAK7268 cada 10 nodos** (o 1 por lote físico, lo que sea mayor). El gateway tiene alcance teórico de 15 km en campo abierto con antena omnidireccional 8 dBi, pero en viñedos y frutales con vegetación densa el alcance práctico es 2–5 km. En campos extensos (200+ ha) se recomienda instalar gateways adicionales para redundancia y reducir latencia. Cada gateway lleva un router 4G o Starlink conectado por Ethernet — la conectividad es 1:1 con el gateway.

**Alertas desactivables**: todas las alertas por WhatsApp y email son configurables y desactivables por el productor desde el dashboard web. El productor puede elegir recibir alertas solo por email, solo por WhatsApp, ambos, o ninguno. El agrónomo asociado puede recibir copia de las alertas si el productor lo autoriza.

**Paquete piloto**: 20 ha mínimo × 1 temporada. Única concesión al compromiso temporal — diseñado para enganchar. Después de ver el ROI en una campaña (objetivo: 4.6x en vid Tier 1), renueva anual.

#### 8.2.6 Programa de Comunicación Lifecycle — Emails Automáticos de Valor

**Principio rector**: El productor nunca debe olvidar el valor que está recibiendo. La información de retención (datos acumulados, benchmarking, ROI medido) no pertenece a la landing page de adquisición — pertenece a comunicaciones post-venta dirigidas al cliente activo. Referencia: Spotify Wrapped, Tesla Annual Report, ADT Security Summary.

**Pieza 1 — Informe Anual Automático ("HydroVision Wrapped")**

Envío: email automático en noviembre (cierre de campaña) o en el aniversario de instalación del cliente.

Contenido del informe anual:
- **Eventos de estrés detectados y evitados**: lista con fecha, lote, severidad y acción tomada (riego automático o alerta manual). Ejemplo: "El 14 de enero detectamos estrés severo en Lote 3 — el sistema activó riego 6 horas antes de que el síntoma fuera visible."
- **Agua ahorrada**: m³ totales y % vs estimación de riego calendario para el mismo lote. Ejemplo: "Ahorraste 1.240 m³ — equivalente a 18% menos consumo que riego por calendario."
- **ROI estimado en USD**: rendimiento recuperado por detección temprana × precio de mercado del cultivo. Ejemplo: "Estimamos que la detección temprana protegió USD 8.640 en rendimiento sobre tus 60 ha de Malbec."
- **Datos acumulados**: total de mediciones, mejora del R² del modelo calibrado vs inicio de temporada. Ejemplo: "Tu modelo tiene 524.160 mediciones — precisión R² pasó de 0.82 a 0.91."
- **Benchmarking regional**: CWSI promedio del lote vs promedio anonimizado de la zona y variedad. Ejemplo: "Tu Malbec tuvo un CWSI promedio 0.08 menor que el promedio de Valle de Uco — tus plantas estuvieron mejor hidratadas que el 73% de los productores de la zona."
- **Compliance (Tier 3)**: resumen de huella hídrica del año con métricas ISO 14046, listo para adjuntar a documentación de exportación.
- **Recomendaciones para la próxima campaña**: basadas en los datos acumulados (zonas críticas, timing óptimo de RDI, ajuste de umbrales sugerido).

Objetivo de negocio: que el informe anual sea tan valioso que el productor lo comparta con su agrónomo y lo use como argumento para renovar ante su directorio o socio.

**Pieza 2 — Emails Lifecycle Mensuales**

Calendario de emails automáticos durante el año. Cada email demuestra valor concreto — no es marketing genérico.

| Mes | Trigger | Asunto del email | Contenido clave |
|---|---|---|---|
| **Octubre** | Inicio de campaña | "Tu sistema está activo — campaña [año] arrancó" | Nodos online, baseline CWSI calibrado, qué esperar en los primeros 14 días |
| **Diciembre** | Primer corte de datos | "Primer reporte: [X] eventos detectados" | Eventos de estrés del primer bimestre, litros ahorrados, comparación vs vecinos |
| **Febrero** | Pico de calor | "Alerta de temporada: tu sistema actuó [Z] veces esta semana" | Resumen de VPD extremo, golpes de calor evitados, dato de protección económica |
| **Abril** | Cierre de campaña | "Resumen de campaña: [X] alertas, [Y] m³ ahorrados" | Mini-informe de campaña, ROI parcial, anticipación del informe anual completo |
| **Junio** | Off-season value | "Tu campo en invierno: [X] heladas monitoreadas" | Horas de frío acumuladas, heladas detectadas, valor de los datos en reposo invernal |
| **Agosto** | Pre-campaña | "Tu modelo tiene [N] días de datos — predicción para la campaña que viene" | Insight predictivo basado en historial, sugerencia de ajuste de umbrales, invitación a subir de tier si aplica |
| **Noviembre** | Aniversario | "Hace [N] año(s) que monitoreas con HydroVision" | Informe anual completo (ver Pieza 1) |

**Principios de diseño de los emails:**
1. **Cada email tiene un dato concreto del campo del cliente** — no es newsletter genérica.
2. **Frecuencia**: máximo 1 email/mes. Nunca spam.
3. **Cada email refuerza una ancla de retención**: datos irremplazables (oct, ago), benchmarking (dic), protección económica (feb), valor off-season (jun), progreso visible (abr).
4. **Unsubscribe siempre visible** — mejor un email bien leído que 12 ignorados.
5. **El agrónomo recibe copia** — refuerza el canal de advisor y hace que la renovación sea decisión compartida.

**Implementación técnica (TRL 4-5):**
- Motor de emails integrado en la app FastAPI (módulo `services/email_service.py`).
- Templates HTML Jinja2 responsivos (`templates/emails/`).
- Scheduler con APScheduler o cron para triggers automáticos por fecha y por evento.
- Datos del informe: queries sobre tabla `telemetry` + `irrigation_log` agregados por cliente/período.
- Configuración SMTP vía variables de entorno (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_FROM`).

**Métricas de éxito del programa:**
- Open rate > 50% (benchmark agro B2B: 35-40%).
- El informe anual se comparte con al menos 1 persona (agrónomo, socio, directorio) en > 30% de los casos.
- Tasa de renovación anual > 90% en clientes que reciben el programa completo vs control.

---

### 8.3 Estrategia de Mercado por Región y Fase


El mercado objetivo de HydroVision AG es el segmento con riego tecnificado (goteo/microaspersión), donde el productor ya invirtió en eficiencia hídrica y está preparado para adoptar monitoreo fisiológico continuo de la planta. Este segmento alcanza ~850.000 hectáreas entre Argentina y Chile, con proyección a más de 1.250.000 ha al incorporar Perú en el Año 3.
Validación Gremial y Fortalecimiento Institucional
La estrategia comercial integra entidades gremiales del sector agroindustrial como canal de validación y despliegue acelerado. Se prevé la firma de convenios de colaboración con Sociedades Rurales regionales (ej. Sociedad Rural de Jesús María, Cámara Vitivinícola de Mendoza, Cámara del Olivicultor de San Juan) para el despliegue de unidades de prueba en lotes de productores asociados. Este mecanismo acelera la curva de confianza en el sector agroindustrial, reduce el costo de adquisición comercial y genera aval institucional ante evaluadores de ANPCyT y potenciales inversores seed.
El efecto de red (network effect) mediante aprendizaje federado refuerza esta estrategia: cada nuevo nodo instalado en una región mejora el modelo predictivo para el resto de los nodos, creando una barrera de entrada técnica que se auto-refuerza con la adopción gremial. Un convenio con una Sociedad Rural que representa 200 productores equivale a un pipeline comercial que ningún competidor externo puede replicar sin años de presencia local.

Fase
Región
Ha tecnif.
Cultivo prioritario
Tecnif. %
Razón estratégica
Año 1
Córdoba — Las Cañitas + viñedo propio
Piloto
Malbec / Sauvignon Blanc
Propio
TRL 5 en viñedo propio de Malbec en Colonia Caroya sin depender de terceros. Validación técnica inmediata con acceso exclusivo del equipo fundador.
Año 1
Mendoza — Valle de Uco
~90.000 ha
Malbec premium
~30%
Mayor valor por ha. Bodegas exportadoras con certificaciones de sustentabilidad. Red comercial de advisors con acceso directo a productores.
Año 1
San Juan
~38.600 ha
Olivo (98% tecnif.)
47%
Mercado más tecnificado de Argentina. Olivo ya en 98% goteo. Crisis hídrica severa como driver urgente de adopción.
Año 2
Chile — Zona Central
307.000 ha
Vid + Olivo
28%
Megasequía + Ley de Riego subsidiando reconversión a sistemas presurizados. Escala 3× mayor que Argentina. Mercado exportador de vino premium.
Año 2
Río Negro — Valle Medio
37.000 ha nuevas
Pera + Manzana
Obra nueva
Productores instalando riego presurizado en proyectos nuevos. Receptivos a tecnología complementaria desde el inicio de la infraestructura.
Año 3
Perú — Costa
400.000+ ha
Arándano + Espárrago
~17%
Modelo agroexportador de alta intensidad. Proyectos Majes-Siguas II y Chavimochic suman 100.000+ ha nuevas diseñadas 100% para riego presurizado.


8.3.1 Proyección de penetración de mercado — SAM y revenue estimado


Los ~850.000 ha con riego tecnificado en Argentina y Chile representan un valor de producción expuesto a pérdidas por estrés hídrico superior a USD 500 millones anuales. Esta cifra es el problema que HydroVision resuelve — no el TAM. El TAM se expresa en revenue anual capturable como servicio (suscripción + hardware), calculado en sección 8.3.4. El mercado servible (SAM) en el período TRL 5-7 se define como el segmento alcanzable con la red comercial de HydroVision AG en las regiones prioritarias:

Región / Cultivo
Ha tecnif.
Penetración Año 2
Nodos estimados
Revenue anual (Tier 2 avg.)
Mendoza — Malbec premium (Valle de Uco + Luján)
~90.000 ha
0.5% = 450 ha
~300 nodos
USD 226.500 (hardware) + USD 54.000 (suscripción)
San Juan — Olivo superintensivo
~38.600 ha
0.8% = 309 ha
~206 nodos
USD 155.900 (hardware) + USD 37.100 (suscripción)
Córdoba — Viñedos + ensayos varietales
Piloto propio
5 lotes (referencia)
~40 nodos
USD 30.200 (hardware) + USD 4.800 (suscripción)
TOTAL AÑO 2 — Argentina (conservador)


~1% del TAM
~546 nodos
USD 412.600 hardware + USD 95.900 suscripción recurrente


Supuestos del modelo: 1 nodo cada 1.5 ha promedio (mix lotes homogéneos/heterogéneos). Precio hardware Tier 2 USD 950/nodo (gateway LoRa en comodato — COGS USD 250, propiedad HydroVision). Suscripción USD 120/ha/año (punto medio Tier 2). Los nodos vendidos en Año 2 generan revenue de suscripción recurrente en Año 3 y subsiguientes — el modelo de ingresos se vuelve progresivamente más predecible a partir del Año 3.

8.3.2 Análisis por tipo de sistema de riego — dos mercados distintos


HydroVision AG opera en dos segmentos con lógicas de adopción y beneficio completamente distintas según el sistema de riego que ya tiene instalado el productor.



Con riego por goteo instalado
Con riego superficial / a manto
Mercado HydroVision
Principal — Tiers 1, 2 y 3 completos
Secundario — solo Tiers 1 y 2
Eficiencia del sistema base
90–95% (INTA, 2022) — pero con uniformidad de distribución del 70–80%, dejando un potencial de optimización del 10–20% sin aprovechar (INA Mendoza, 2015)
40–60% — pérdidas por evaporación, escurrimiento y percolación profunda. El estrés hídrico es estructural.
Beneficio inmediato con HydroVision
Recuperación del 10–20% de eficiencia no aprovechada + evitar pérdidas de rendimiento por estrés mal gestionado (15–35% del rendimiento). Para 100 ha de Malbec premium: USD 20.000–60.000 evitados por campaña.
Alerta temprana que permite intervención manual. No puede aprovechar el Tier 2-3 automático — sin electroválvulas que controlar.
Tier 2-3 — control automático
Sí — el nodo Tier 2-3 integra relé SSR + solenoide y decide autónomamente cuándo regar según HSI. Se conecta al sistema existente (Rain Bird, Netafim, Irritrol) sin obra hidráulica adicional.
No disponible — requiere reconversión previa del sistema de riego (USD 3.000–8.000/ha de inversión).
Barrera de adopción
Baja — ya tiene la mentalidad tecnológica, ya pagó por el goteo, ya tiene controlador instalado. HydroVision agrega inteligencia a la infraestructura existente.
Alta — antes de HydroVision necesita reconvertir el sistema. Chile ya subsidia esta reconversión con la Ley de Riego (mercado Año 2+).
Perfil del cliente Año 1
Bodega premium exportadora. Productores de Malbec Valle de Uco y olivo San Juan con goteo instalado y certificaciones de sustentabilidad.
No es el cliente Año 1. Mercado potencial para Año 3+ cuando haya subsidios de reconversión activos.


Por qué el mercado objetivo está definido como '~850.000 ha con riego tecnificado': Este segmento ya tiene la infraestructura hidráulica para usar HydroVision al máximo valor — detectar el estrés y actuar automáticamente en el mismo ciclo de 15 minutos, sin intervención humana. El productor con riego a manto puede recibir la alerta, pero debe actuar manualmente abriendo un compuerto — lo que reduce significativamente el valor del sistema. La estrategia comercial prioriza el segmento con mayor disposición a pagar y mayor beneficio inmediato verificable.

Fuentes: INTA EEA La Consulta (2022) — eficiencia riego por goteo >90%. INA-CRA Mendoza / Schilardi et al. (2015) — uniformidad de distribución 70–80%, potencial de optimización 10–20%. DGI Mendoza — el 81% del agua superficial va al agro, la mitad en riego a manto. Jackson et al. (1981) / García-Tejero et al. (2018) — pérdidas de rendimiento por estrés hídrico 15–35%.

8.3.2A Comparación de costos reales — HydroVision AG vs. solución israelí (Phytech/Netafim)

Los siguientes cinco casos comparan el costo total de implementación y mantenimiento de HydroVision AG frente a la solución tecnológicamente más cercana disponible en el mercado global: Phytech (Israel), distribuida por Netafim. Los casos usan los mismos perfiles de productor de la sección 8.2.1B. Todos los precios de Phytech incluyen el recargo por importación en Argentina (~35% de arancel sobre CIF) y conectividad rural requerida (Starlink Mini X). Precios en USD al tipo de cambio oficial.

Supuestos Phytech / Netafim en Argentina:
· Sensor de planta (tronco + fruto): USD 450–800 unidad (precio Israel USD 300–600 + 35% arancel + flete)
· Densidad: 1 sensor por zona de manejo (equivalente a ~1 sensor / 2 ha como mínimo práctico)
· Suscripción plataforma: USD 200–350/sensor/año (precio de catálogo internacional)
· Conectividad obligatoria a nube: Starlink Mini X ~USD 215 hardware + USD 27/mes (zonas sin 4G; modelo dual 4G/Starlink no disponible en Phytech)
· Instalación: técnico especializado externo (no hay distribuidores locales calificados en Argentina) → viaje + honorarios estimados USD 800–1.500 por visita
· Mantenimiento/reemplazo: sin repuestos locales → envío internacional USD 80–150 + demora 3–6 semanas
· Sin señal térmica: Phytech no calcula CWSI → no detecta estrés estomático intradiario → precisión limitada a señal dendrométrica sola (R²=0.80–0.85 vs. R²=0.90–0.95 del HSI dual-señal de HydroVision)
· Sin procesamiento edge: toda la lógica en servidores Netafim → si cae el internet, no hay datos ni alertas
· Calibración del baseline MDS: heurística post-lluvia sin verificación fisiológica real. Phytech asume que días post-lluvia = planta sin estrés, sin confirmar con ψ_stem ni con el extensómetro que el MDS realmente llegó a cero. HydroVision lo confirma. En condiciones de VPD extremo del verano cuyano (4–6 kPa), esa asunción puede estar equivocada — la planta puede no recuperarse completamente en 24h incluso tras lluvia si la temperatura sigue alta.
· Coeficientes israelíes/californianos — no recalibrados para Malbec en Cuyo ni para ninguna variedad argentina. El VPD de referencia israelí (2–3 kPa) es menos de la mitad del cuyano (4–6 kPa) → los umbrales MDS→ψ_stem sub-estiman el estrés real en Argentina.

─────────────────────────────────────────────────────────────────
CASO 1 — 20 ha Malbec, Valle de Uco · 2 nodos HydroVision vs. Phytech mínima viable
─────────────────────────────────────────────────────────────────

HydroVision AG (1/10 ha, Tier 1):
· Hardware: 2 nodos × USD 950 = USD 1.900 (gateway LoRa en comodato — incluido en suscripción)
· Suscripción Año 1: 20 ha × USD 80 = USD 1.600
· Instalación: incluida (2 horas técnico HydroVision, primer nodo)
· Conectividad: LoRaWAN — sin internet, sin costo mensual
· Total Año 1: USD 3.500
· Total Año 2+ (solo suscripción): USD 1.600/año
· Costo acumulado 5 años: USD 3.500 + (4 × USD 1.600) = USD 9.900
· Señal: CWSI + MDS + sat. R²=0.63 promedio lote (densidad baja)

Phytech / Netafim (1/2 ha mínimo viable, 10 sensores):
· Hardware: 10 sensores × USD 580 promedio = USD 5.800 + 35% arancel + flete = USD 7.830
· Suscripción plataforma: 10 sensores × USD 270/año = USD 2.700/año
· Instalación: 1 visita técnico externo = USD 1.200 (viaje Bs.As.–Mendoza + honorarios)
· Conectividad Starlink Mini X: ~USD 215 hardware + USD 324/año (USD 27/mes)
· Mantenimiento estimado: 1 sensor reemplazado cada 2 años → USD 580 + USD 130 flete = USD 355/año amortizado
· Total Año 1: USD 7.830 + USD 2.700 + USD 1.200 + USD 215 + USD 324 = USD 12.269
· Total Año 2+ (suscripción + conectividad + mant.): USD 3.379/año
· Costo acumulado 5 años: USD 12.269 + (4 × USD 3.379) = USD 25.785
· Señal: MDS solo (sin CWSI). R²=0.80–0.85. Sin detección de estrés intradiario.

Diferencia 5 años: Phytech cuesta USD 15.885 más (+160%) con menor precisión de señal y sin cobertura nocturna de CWSI.
Riesgo adicional Phytech: si en enero (estrés máximo) falla un sensor, la reposición tarda 3–6 semanas desde Israel — toda la temporada comprometida sin señal en esa zona.

─────────────────────────────────────────────────────────────────
CASO 2 — 50 ha Olivo San Juan · 10 nodos HydroVision vs. Phytech comparable
─────────────────────────────────────────────────────────────────

HydroVision AG (1/5 ha, Tier 2 · 10 nodos):
· Hardware: 10 × USD 950 = USD 9.500 (gateways LoRa en comodato — incluidos en suscripción)
· Suscripción: 50 ha × USD 130 = USD 6.500/año
· Conectividad: LoRaWAN — sin costo mensual
· Instalación: incluida
· Total Año 1: USD 16.000
· Total Año 2+: USD 6.500/año
· Costo 5 años: USD 16.000 + (4 × USD 6.500) = USD 42.000

Phytech / Netafim (25 sensores para misma densidad 1/2 ha):
· Hardware: 25 sensores × USD 580 = USD 14.500 + 35% = USD 19.575
· Suscripción: 25 × USD 270 = USD 6.750/año
· Conectividad Starlink Mini X: ~USD 215 + USD 324/año
· Instalación: USD 1.500 (distancia San Juan, 2 días técnico)
· Mantenimiento: ~2 sensores/año × USD 355 = USD 710/año amortizado
· Total Año 1: USD 19.575 + USD 6.750 + USD 215 + USD 324 + USD 1.500 = USD 28.364
· Total Año 2+: USD 7.784/año
· Costo 5 años: USD 28.364 + (4 × USD 7.784) = USD 59.500

Diferencia 5 años: Phytech cuesta USD 17.500 más (+42%) y no tiene señal térmica para detectar el efecto Zonda (viento cálido de San Juan que eleva la temperatura foliar artificialmente). HydroVision descarta automáticamente esas lecturas corruptas mediante el anemómetro — Phytech no puede hacerlo.

─────────────────────────────────────────────────────────────────
CASO 3 — 100 ha Malbec bodega exportadora · control automático completo
─────────────────────────────────────────────────────────────────

HydroVision AG (1/2 ha, Tier 3 · 50 nodos):
· Hardware: 50 × USD 1.000 = USD 50.000 (gateways LoRa en comodato — incluidos en suscripción)
· Suscripción: 100 ha × USD 255 = USD 25.500/año
· Control automático riego: incluido en hardware (relé SSR → solenoide)
· Conectividad: LoRaWAN — sin costo mensual
· Total Año 1: USD 75.500
· Total Año 2+: USD 25.500/año
· Costo 5 años: USD 75.500 + (4 × USD 25.500) = USD 177.500

Phytech / Netafim (50 sensores + integración riego separada):
· Hardware: 50 sensores × USD 650 (modelo premium con control riego) = USD 32.500 + 35% = USD 43.875
· Control de riego: Netafim vende la integración como módulo separado → USD 8.000–15.000 adicionales para 5 zonas (requiere controlador Netafim compatible)
· Suscripción: 50 × USD 320 = USD 16.000/año
· Conectividad Starlink Mini X: ~USD 215 + USD 324/año
· Instalación: USD 2.500 (sistema complejo, 3 días técnico especializado)
· Mantenimiento: ~4 sensores/año × USD 355 = USD 1.420/año
· Total Año 1: USD 43.875 + USD 12.000 (control riego) + USD 16.000 + USD 215 + USD 324 + USD 2.500 = USD 74.914
· Total Año 2+: USD 18.344/año
· Costo 5 años: USD 74.914 + (4 × USD 18.344) = USD 148.290

HydroVision cuesta más en 5 años (USD 177.500 vs. USD 148.290) — pero con diferencias estructurales críticas que justifican la inversión:
· Phytech no tiene señal térmica CWSI → menor precisión de estrés intradiario (R²=0.82 vs. 0.92)
· Phytech depende de internet 24/7 → si cae Starlink, cae el sistema de control de riego completo
· Phytech no genera mapa satelital del lote ni fusión Sentinel-2 → no hay prescripción espacial
· Phytech cobra suscripción por sensor, no por ha → al escalar a 200 ha el costo se duplica linealmente; HydroVision tiene economías de escala en suscripción por ha

─────────────────────────────────────────────────────────────────
CASO 4 — 12 ha Cereza premium · densidad máxima
─────────────────────────────────────────────────────────────────

HydroVision AG (1/1 ha, Tier 3 Precisión + add-ons · 12 nodos):
· Hardware: 12 × USD 1.000 = USD 12.000 (gateways LoRa en comodato — incluidos en suscripción)
· Suscripción: 12 ha × USD 290 (Tier 3 Precisión) = USD 3.480/año
· Total Año 1: USD 15.480
· Total Año 2+: USD 3.480/año
· Costo 5 años: USD 15.480 + (4 × USD 3.480) = USD 29.400

Phytech / Netafim (12 sensores tronco + fruto):
· Hardware: 12 sensores modelo cereza (fruto + tronco, USD 780/sensor) = USD 9.360 + 35% = USD 12.636
· Suscripción: 12 × USD 350 = USD 4.200/año
· Conectividad Starlink Mini X: ~USD 215 + USD 324/año
· Instalación técnico especializado: USD 1.000
· Mantenimiento: 1 sensor/año × USD 355 = USD 355/año
· Total Año 1: USD 12.636 + USD 4.200 + USD 215 + USD 324 + USD 1.000 = USD 18.375
· Total Año 2+: USD 4.879/año
· Costo 5 años: USD 18.375 + (4 × USD 4.879) = USD 37.891

Diferencia 5 años: Phytech cuesta USD 8.491 más (+29%). Pero la diferencia real es de funcionalidad:
· HydroVision detecta estrés 12–24 horas antes gracias al MDS nocturno + alerta push inmediata + control de riego autónomo. Phytech también tiene MDS pero sin la señal térmica intradiaria que confirma si el tronco ya está respondiendo en la ventana solar crítica.
· Si un sensor Phytech falla 2 semanas antes de cosecha (riesgo real) → no hay reposición en tiempo → lote sin monitoreo en el momento más crítico. Con HydroVision, Lucas Bergon (residente en Colonia Caroya) reemplaza el nodo en 24 horas.
· HydroVision genera el historial de ψ_stem verificado por temporada → datos para certificación de calidad premium exportación.

─────────────────────────────────────────────────────────────────
CASO 5 — 200 ha Pistacho San Juan · densidad híbrida
─────────────────────────────────────────────────────────────────

HydroVision AG (densidad híbrida 52 nodos Tier 2-3):
· Hardware: USD 51.700 (gateways LoRa en comodato — incluidos en suscripción)
· Suscripción: USD 37.700/año
· Total Año 1: USD 89.400
· Total Año 2+: USD 37.700/año
· Costo 5 años: USD 89.400 + (4 × USD 37.700) = USD 240.200

Phytech / Netafim (100 sensores para densidad equivalente 1/2 ha en todo el lote):
· Hardware: 100 sensores × USD 580 = USD 58.000 + 35% = USD 78.300
· Suscripción: 100 × USD 280 = USD 28.000/año
· Conectividad Starlink Mini X (zona remota Caucete): 2 unidades × (~USD 215 + USD 324/año) = USD 430 + USD 648/año
· Instalación: USD 3.000 (3 días técnico especializado + viaje)
· Mantenimiento: ~8 sensores/año × USD 355 = USD 2.840/año
· Total Año 1: USD 78.300 + USD 28.000 + USD 430 + USD 648 + USD 3.000 = USD 110.378
· Total Año 2+: USD 31.488/año
· Costo 5 años: USD 110.378 + (4 × USD 31.488) = USD 236.330

Costo 5 años casi idéntico — pero Phytech necesita densidad uniforme 1/2 ha en todo el lote (no puede hacer zonas diferenciadas sin múltiples contratos). HydroVision cubre las 200 ha con 52 nodos usando densidad híbrida; Phytech necesita 100 sensores para la misma cobertura. Phytech no ofrece fusión Sentinel-2 para interpolar las zonas sin sensor — HydroVision sí.

─────────────────────────────────────────────────────────────────
Resumen comparativo — costo acumulado 5 años:

Caso
Superficie / Cultivo
HydroVision 5 años
Phytech 5 años
Diferencia
Señal HydroVision
Señal Phytech
1
20 ha · Malbec (entrada)
USD 9.900
USD 25.785
−USD 15.885 (−62%)
CWSI+MDS+sat · R²=0.63
MDS solo · R²=0.82
2
50 ha · Olivo San Juan
USD 42.000
USD 59.500
−USD 17.500 (−29%)
HSI+sat · R²=0.78
MDS solo · R²=0.82
3
100 ha · Malbec bodega
USD 177.500
USD 148.290
+USD 29.210 (+20%)
HSI completo · R²=0.92
MDS solo · R²=0.82
4
12 ha · Cereza premium
USD 29.400
USD 37.891
−USD 8.491 (−22%)
HSI completo · R²=0.92
MDS solo · R²=0.83
5
200 ha · Pistacho híbrido
USD 240.200
USD 236.330
+USD 3.870 (+1.6%)
HSI+sat · R²=0.85 prom.
MDS solo · R²=0.82

Lectura estratégica de la tabla:
En los casos de menor escala (Casos 1, 2 y 4), HydroVision es 22–62% más barato. En los casos de gran escala con control de riego integrado (Casos 3 y 5), los costos convergen — pero HydroVision provee señal dual (CWSI térmico + MDS), fusión satelital, procesamiento edge sin internet, soporte local y calibración para variedades argentinas que Phytech no puede ofrecer en ninguna escala. La paridad de costo en escala grande no es una debilidad: significa que HydroVision compite de igual a igual en precio con la solución israelí líder global, pero con un producto técnicamente superior y sin las barreras de importación, soporte y conectividad que hacen a Phytech inviable en el mercado latinoamericano.

8.3.3 Factibilidad Económica por Variedad — Rescate de Valor


El valor generado por HydroVision AG se fundamenta en el concepto de "rescate de valor": la recuperación de pérdidas por estrés hídrico invisible (12–18% del rendimiento total) y la bonificación por calidad de exportación alcanzable cuando el estrés se gestiona con precisión fisiológica. Los siguientes datos cuantifican el aporte de la solución por cultivo objetivo:

| Variedad | Ingreso bruto (USD/ha) | Recuperación 12% (USD/ha) | Factor clave de éxito | Fuente de precio |
|----------|----------------------|--------------------------|----------------------|------------------|
| Cereza | USD 30.000 | USD 3.600 | Firmeza del fruto y ventana de cosecha | 15 ton/ha × USD 5.5/kg export promedio (USDA, Agrovalle 2025-26). Conservador — año bueno supera USD 50.000/ha. |
| Pistacho | USD 18.000 | USD 2.160 | Reducción de frutos vanos (cáscara vacía) | 3.000-3.500 kg/ha × USD 5.7/kg mayorista AR (Selinawamucii 2025). Rango real USD 17.000-20.000/ha. |
| Nogal (Nuez) | USD 10.000 | USD 1.200 | Maximización de calibre y peso | 1.500 kg/ha promedio × USD 5-8/kg (INTA 2024, Alimentos Argentinos). Plantaciones maduras pueden alcanzar USD 12.000/ha. |
| Vid Premium (Malbec, Cabernet) | USD 9.600 | USD 1.152 | Calidad enológica (polifenoles, concentración) | Bodega integrada, vino premium exportación. Precio uva bruta Valle de Uco $65/kg (AVM 2025) equivale a ~USD 500/ha — el valor se captura en la cadena vitivinícola. |
| Citrus (Limón) | USD 8.500 | USD 1.020 | Prevención de caída de fruta joven | Mix fresco+industria. Exportaciones Tucumán USD 408M / 40.000 ha ≈ USD 10.200/ha (Federcitrus 2025). Valor conservador. |
| Olivo (AOVE) | USD 5.500 | USD 660 | Rendimiento graso y ahorro energético de bombeo | Olivar tradicional 5-6 ton/ha. Superintensivo (10 ton/ha) alcanza USD 9.500/ha. Precio AOVE EUR 4.500/ton (2025). |


Metodología de validación: Los valores de aporte por variedad resultan de aplicar el CWSI (Jackson et al., 1981) como índice de rescate. La detección infrarroja del canopeo permite precisión superior al 90% en la detección de estrés antes del síntoma de marchitez, habilitando acciones preventivas que salvan el rendimiento. El costo del servicio HydroVision representa menos del 2% del margen bruto en todos los cultivos de la tabla — lo que sitúa la barrera de adopción por debajo del umbral de decisión de cualquier productor tecnificado.

Punto de equilibrio del negocio: El break-even operativo de HydroVision AG se alcanza con las primeras 800 hectáreas bajo contrato recurrente — menos del 0,18% del mercado nacional direccionable. La mejora respecto al modelo previo (1.000–1.100 ha) se explica por dos factores: (1) el hardware ahora genera margen positivo (USD 146/nodo Tier 1 vs. pérdida anterior), cubriendo ~90% de los costos fijos en el año de venta; (2) el incremento de suscripción (+USD 20/ha) justificado por el HSI dual-señal mejora la contribución marginal por ha de USD 77 a USD 90. Retorno promedio por dólar invertido por el productor: USD 9,6 en valor rescatado (promedio ponderado entre cultivos) — validado por el ROI Año 2+ de 1.24x en Tier 3 (USD 31.500 beneficio / USD 25.500 suscripción), lo que garantiza churn rate mínimo y renovación automática de suscripción.

8.3.4 Dimensionamiento de Mercado — TAM / SAM / SOM Multi-cultivo


La tabla siguiente muestra la superficie y el valor de producción en riesgo por cultivo — la magnitud del problema que HydroVision resuelve. El TAM como revenue capturable se calcula por separado al pie de la tabla.

Cultivo
Has. Argentina
Has. Globales
Valor de producción en riesgo Argentina (USD M)*
Vid (Vino + Premium)
200.000
7.100.000
USD 230,0 M
Citrus
130.000
10.000.000
USD 117,0 M
Olivo
70.000
11.500.000
USD 47,6 M
Pistacho
25.000
1.200.000
USD 61,2 M
Nogal
15.000
1.250.000
USD 27,7 M
Cereza / Palta / Otros
7.700
3.500.000
USD 14,9 M
TOTALES
447.700 ha
34.550.000 ha
USD 498,4 M

*Valor de producción en riesgo: estimación del ingreso bruto expuesto a pérdidas por estrés hídrico no detectado (15–35% del rendimiento según Jackson et al. 1981 y García-Tejero et al. 2018). Esta cifra representa el problema, no el TAM. El mercado no paga USD 498M/año por software de monitoreo — paga una fracción de ese valor como servicio.

TAM (revenue capturable como servicio):
· TAM software global: USD 4.146 M/año (34,5 M ha × USD 120/ha/año precio promedio mix Tier 1-2)
· TAM hardware global amortizado: USD 4.376 M/año (23 M nodos / ciclo 5 años × USD 950/nodo)
· TAM LATAM combinado (software + hardware + datos): USD 465 M/año

SAM (Mercado Direccionable Año 3): 665.900 hectáreas en Argentina, Chile y Perú con riego tecnificado y condiciones de adopción verificadas — filtrado por: (1) solo riego por goteo/microaspersión; (2) superficie ≥ 5 ha; (3) cultivos en portfolio HydroVision; (4) regiones con canal comercial activo. Revenue SAM software: USD 66,1 M/año.

SOM (Mercado Objetivo Año 3, proyección conservadora): 5.300 hectáreas. Revenue total Año 3: USD 2,17 M (USD 583.000 ARR suscripción + USD 1,59 M hardware). Break-even operativo: 800 ha — alcanzado en Q2 del Año 2.

8.3.5 Proyección Financiera — HydroVision AG Post-ANPCyT (Años 1–3)

La proyección de ingresos asume penetración conservadora del mercado SAM (~450.000 ha) a partir del cierre del TRL 4:

Año
Período
Hectáreas bajo contrato
ARR (USD)
COGS estimado (USD)
Margen bruto
1 (TRL 5)
Mes 1–12 post-ANPCyT
500 ha · Tier 1 promedio USD 95/ha
USD 47.500
USD 20.000 (cloud + soporte)
58%
2 (TRL 6)
Mes 13–24
2.500 ha · precio promedio USD 104/ha
USD 260.000
USD 72.000
72%
3 (TRL 7)
Mes 25–36
10.000 ha · precio promedio USD 110/ha
USD 1.100.000
USD 210.000
81%
Break-even operativo HydroVision AG: ~800 ha bajo contrato recurrente (antes del cierre del Año 1). Los costos fijos operativos post-TRL 4 son principalmente infraestructura cloud (USD 15.000/año a 10.000 ha) y equipo comercial (incorporado progresivamente con ARR). El hardware genera margen positivo (USD 146–149/nodo) que cubre ~90% de los costos fijos en el año de instalación. Margen bruto >78% en régimen estable (Año 3+) justifica escalado sin nueva ronda de deuda. Nota: el COGS incluye cloud + soporte técnico + actualizaciones de modelo; no incluye costos de adquisición comercial (CAC) que se incorporan gradualmente con el ARR.

La incorporación de cerezo, pistacho y nogal al portafolio de cultivos en TRL 5+ no requiere inversión adicional en hardware de campo (mismo nodo, mismo sensor SHT31, parámetros GDD actualizados vía firmware OTA). El valor de mercado adicional por hectárea es 2–3× mayor que el de vid estándar, con productores de mayor disposición a pagar dado el valor unitario del producto.

### 8.4 Análisis Competitivo — Brecha de Mercado


Ninguna solución disponible en el mercado detecta el estrés hídrico foliar de forma continua, autónoma y en tiempo real desde un nodo fijo en campo. La totalidad de los competidores actuales mide el suelo o el entorno — no la planta:

Solución existente
Qué mide
Limitación crítica
Ventaja diferencial HydroVision
Phytech / Netafim (Israel) — solución dendrométrica y de sensores en planta más avanzada del mercado global
Sensor de tronco (dendrometría), temperatura de fruto, flujo de savia. Plataforma en la nube con alertas agronómicas. Distribuida por Netafim como parte de paquetes de riego premium.
(1) Precio: USD 300–800 por sensor de planta + suscripción anual USD 150–400. Un viñedo de 10 ha con 3 zonas = USD 1.500–3.000 solo en hardware. Fuera del alcance del productor mediano latinoamericano. (2) Sin señal térmica foliar: el sistema de Phytech mide tronco y fruto pero NO tiene cámara térmica. No calcula CWSI. No detecta estrés estomático instantáneo. Pierde la lectura intradiaria de alta resolución del canopeo. (3) Calibración del baseline MDS por heurística, sin verificación fisiológica real: Phytech también necesita una referencia de "planta sin estrés" para anclar el MDS. La obtiene asumiendo que los días post-lluvia o post-riego abundante el MDS mínimo equivale a "sin estrés" — sin medir ψ_stem, sin confirmación fisiológica. HydroVision confirma con el extensómetro que el MDS realmente llegó a cero (no lo asume) y verifica con ψ_stem Scholander. (4) Coeficientes calibrados para condiciones israelíes y californianas — no recalibrados para Malbec en Cuyo ni para ninguna variedad argentina. El VPD del verano cuyano (4–6 kPa) duplica al mediterráneo israelí (2–3 kPa); los coeficientes MDS→ψ_stem derivados en Israel sub-estiman el estrés real en Argentina. HydroVision recalibra para Malbec en Colonia Caroya con la Dra. Monteoliva (INTA-CONICET) y el sistema se auto-ajusta nodo a nodo durante la temporada. (5) 100% dependiente de conectividad a nube: sin 4G/WiFi, sin datos. Zonas remotas de San Juan, NOA y Valle de Uco tienen cobertura intermitente. (6) Sin procesamiento edge: toda la lógica corre en servidores de Netafim. El productor no controla los datos ni el algoritmo. (7) Barreras de importación en Argentina: aranceles 35%+, sin distribuidores locales calificados, sin repuestos disponibles, sin soporte en español. (8) Modelo comercial B2B corporativo: Netafim vende a bodegas grandes como parte de un paquete de riego completo. El productor mediano de 20–100 ha no está en su canal. (9) Sin integración satelital: no fusiona con Sentinel-2 para extrapolar a lote completo. (10) Sin motor fenológico: no detecta estadio automáticamente, no ajusta umbrales por fenología.
HSI (CWSI térmico + MDS dendrométrico, pesos adaptativos) en un solo nodo a USD 804. Procesamiento 100% edge — sin nube, sin internet, sin suscripción. Calibración del baseline superior: el extensómetro confirma MDS=0 fisiológico (no lo asume), el Scholander verifica ψ_stem real, y el sistema se auto-ajusta nodo a nodo durante la temporada sin visita humana. Coeficientes recalibrados para Malbec en Cuyo por Dra. Monteoliva (INTA-CONICET) — no extrapolados desde Israel. Conectividad LoRaWAN — opera en zonas sin celular. Motor fenológico automático. Fusión Sentinel-2 para todo el lote. Control de riego autónomo integrado en nodo (Tier 2-3). 1/10 del precio total de Phytech.
Saturas (Israel) — microtensiometría de tallo (stems psychrometers)
Potencial hídrico de xilema mediante psicrométro embebido en el tallo. Señal directa de ψ_stem sin modelos indirectos.
Hardware de laboratorio adaptado a campo. Precio: USD 500–1.200 por punto de medición. Requiere técnico calificado para instalación (perforación del tallo). Degradación mecánica en campo (cavitación del sensor). Sin soporte en Argentina. Sin integración con sistema de riego ni alertas automáticas. Monitoreo puntual, sin extrapolación espacial a lote completo.
HSI ofrece estimación de ψ_stem equivalente (R²~0.90–0.95 vs. ψ_stem Scholander) combinando dos señales no-invasivas. Sin perforación del tallo. Instalación por el propio productor. Hardware 10× más barato.
Satélite Sentinel-2
NDVI / reflectancia multiespectral
Resolución 10m/px. Nubes bloquean 8–15 días. No detecta estrés foliar directo.
Temperatura foliar con ±0.05°C. Sin dependencia de condiciones climáticas. Alerta disponible en horas. El nodo calibra el satélite para extrapolación a 50+ ha.
Dron con operador (como servicio independiente)
Imagen térmica o multiespectral periódica
1–2 vuelos/semana máximo. El estrés se instala en 3–5 días. Requiere piloto certificado ANAC. No opera con viento >25 km/h ni lluvia.
HydroVision incorpora la metodología de captura multi-angular de termografía UAV directamente en el nodo fijo (gimbal motorizado pan-tilt 2 ejes), eliminando la dependencia climática y regulatoria. Monitoreo continuo 96 ciclos/día con precisión equivalente a drone de baja altitud (CWSI ±0.07–0.09 vs. ±0.08–0.12 en UAV según Zhou et al. 2022).
Tensiómetros digitalizados (IrroCloud, Watermark)
Tensión matricial del suelo
Mide el suelo, no la planta. Desfase de 2–5 días entre suelo seco y estrés foliar visible.
Mide directamente temperatura foliar + contracción de tronco. Correlación fisiológica directa con ψ_stem. Sin desfase temporal.
Sensores meteorológicos IoT
T°, HR, precipitación ambiental
Informan el entorno, no el estado hídrico de la planta. No predicen estrés foliar.
Fusiona datos meteorológicos con imagen térmica foliar y señal dendrométrica para calcular HSI con coeficientes calibrados por variedad.
HydroVision AG
CWSI térmico (MLX90640) + MDS dendrométrico (extensómetro de tronco) fusionados en índice HSI
TRL 3 actual → TRL 4 al cierre de este proyecto financiado
Único sistema autónomo, continuo, sin operador y sin internet que detecta estrés fisiológico foliar real con doble señal fisiológica (térmica + dendrométrica), IA calibrada por variedad, motor fenológico automático y fusión satelital para lote completo. A 1/10 del precio de la solución israelí equivalente.


#### 8.4.1 Diferenciales estructurales — barreras de entrada


La solución tecnológicamente más cercana a HydroVision AG a nivel global es Phytech (Israel, adquirida por Netafim), que combina sensores en planta con plataforma de datos agronómicos. Sin embargo, Phytech no penetró el mercado latinoamericano por razones estructurales: precio prohibitivo (USD 300–800/sensor + suscripción), dependencia de conectividad a nube en zonas rurales sin cobertura celular, ausencia de distribuidores locales y respaldo técnico, barreras de importación en Argentina, y un modelo comercial B2B corporativo orientado a grandes bodegas. El segmento mediano del mercado (productores 20–100 ha) quedó sin cobertura tecnológica viable — que es exactamente el hueco que HydroVision AG cierra.

Más allá de la brecha tecnológica actual, HydroVision AG construye tres diferenciales estructurales que se vuelven progresivamente más difíciles de replicar a medida que el sistema escala en el mercado:

Diferencial
Por qué es difícil de copiar
Cómo se acumula con el tiempo
Coeficientes CWSI calibrados por variedad y región
Los coeficientes ΔT_LL/ΔT_UL para Malbec en Cuyo son el resultado de un protocolo experimental de 6 meses con bomba de Scholander y respaldo de INTA-CONICET. Un competidor que quiera replicarlos necesita repetir el protocolo completo — tiempo, instrumentación y un investigador calificado que acepte colaborar. Con cada variedad calibrada (Cabernet, Sauvignon Blanc, olivo Arauco, arándano) la barrera crece.
Año 1: Malbec. Año 2: + Sauvignon Blanc + Olivo. Año 3: + Cabernet + Arándano. Cada calibración es una exclusividad de 12–18 meses antes de que cualquier competidor pueda publicar resultados equivalentes.
Red de datos propios del campo argentino
Con 50+ lotes activos, HydroVision AG acumula datos de temperatura foliar, CWSI, VPD y eventos de riego de Mendoza, San Juan, Córdoba y NOA — una base de datos que no existe en ninguna fuente pública. Esto habilita modelos predictivos (no solo reactivos): 'el Sector Norte entrará en estrés moderado el jueves en base a los últimos 7 días y el pronóstico meteorológico'. Ningún competidor puede construir ese modelo sin años de datos propios en campo.
El network effect de los datos es el moat más fuerte a largo plazo. A mayor cantidad de lotes, mayor precisión del modelo predictivo — lo que atrae más lotes, en un ciclo que se auto-refuerza.
Publicación científica indexada como referencia del sector
La publicación científica derivada del proyecto (Monteoliva et al., Agricultural Water Management o Precision Agriculture) establece a HydroVision AG como la referencia técnica del CWSI con termografía embebida en Argentina. Cualquier competidor que use los coeficientes calibrados cita el paper — y a sus autores. Combinado con el respaldo institucional del INTA-CONICET, crea una autoridad científica que ninguna startup extranjera puede replicar en el corto plazo.
Una publicación en revista indexada con co-autoría INTA-CONICET es prácticamente imposible de superar en credibilidad en el mercado agronómico argentino.
Simulador físico de imágenes térmicas
El simulador de balance energético foliar calibrado para Malbec genera datasets ilimitados para nuevas variedades sin campañas de campo masivas. La arquitectura PINN (Physics-Informed Neural Network) del modelo es un diferencial adicional: embebe la física del balance energético directamente en la red neuronal, lo que impide predicciones físicamente imposibles y mejora la generalización. Un competidor necesita replicar ambos activos simultáneamente para competir en calidad de predicción.
El simulador es reutilizable para cualquier cultivo con parámetros morfológicos conocidos. Cada nueva variedad calibrada amplía el activo sin costo marginal significativo.


### 8.5 Gestión de Riesgos Técnicos


Se identificaron once riesgos técnicos principales, todos con estrategias de mitigación concretas incorporadas al diseño del proyecto. Los riesgos macroeconómicos del entorno argentino se documentan en la sección 8.6:

Riesgo
Probabilidad
Mitigación
Plan B
Calibración CWSI para Malbec en Córdoba — coeficientes Bellvert (2016) calculados para Pinot Noir en Cataluña pueden tener error sistemático de ±0.15–0.25 en CWSI bajo condiciones de VPD cordobés.
Alta
Protocolo experimental con Dra. Monteoliva: recalibración de coeficientes ΔT_LL/ΔT_UL para Malbec midiendo ≥30 pares (ΔT, VPD) en plantas bajo riego completo durante el período experimental.
Si Monteoliva no confirma: contactar Facundo Calderón — INTA EEA Junín, Mendoza (publicó CWSI en Bonarda 2025).
Riesgo residual de overfitting geográfico — mitigado por estrategia de tres capas de datos.
Alta
Estrategia de tres capas: (1) pre-entrenamiento en 50.000 imágenes públicas agrícolas y térmicas; (2) fine-tuning con 1.000.000 imágenes sintéticas del simulador físico calibrado para Malbec; (3) calibración final con 680 frames reales etiquetados con Scholander (de los 800 capturados, 120 se reservan para validación independiente). Dataset total de entrenamiento: 1.050.680 imágenes.
Con 1.050.680 imágenes de entrenamiento y 120 frames de validación independiente, el objetivo de accuracy > 85% es alcanzable. Si no se llega, el simulador permite generar datos adicionales ilimitados sin costo de campo.
~~Riesgo resuelto — plataforma migrada a ESP32-S3.~~ El ESP32-S3 consume ~0.5W activo y 8µA en deep sleep (vs 2.7W del RPi4). Autonomía sin sol: ~5 días (~120 horas) con sistema completo operativo. Riesgo eliminado.
Segmentación foliar en 32×24px — mezcla espectral entre hojas, suelo y madera contamina el cálculo del CWSI.
Media
Máscara de temperatura relativa por percentiles (hojas = P20–P75 del frame) + filtro morfológico de regiones conectadas ≥4×4px. Captura fija en ventana horaria 10–14hs solar.
Aumentar distancia focal a 1.5m y enfocar en zona del dosel con mayor densidad foliar. Usar mounting bracket fijo para reproducibilidad.
Disponibilidad del equipo part-time — Lucas Bergon (COO/HW+FW, MBG Controls) y el investigador Art. 32 tienen compromisos laborales paralelos que pueden generar cuellos de botella.
Media
César Schiavoni (Project Leader) coordina sprints bi-semanales con tablero de tareas visible. Sesión presencial semanal de 3–4h en MBG Controls (Colonia Caroya) para integración hardware. Claude Code reduce el tiempo de implementación en ~50–60% por perfil. El cronograma incorpora buffer implícito de 2 semanas distribuidas entre Gates.
Si hay retraso por baja disponibilidad en cualquier capa: César reasigna tareas y ajusta el alcance del Gate dentro del buffer. Claude Code puede absorber tareas adicionales de backend directamente.
Importación del MLX90640 desde USA — posible retención aduanera o demora de 4–8 semanas.
Baja-Media
Importar a través de MBG Controls (empresa con experiencia en importación de componentes electrónicos). Hacer el pedido en la Semana 1 del proyecto, no en el Mes 1.
Contactar distribuidores locales de Melexis/MLX90640 en Argentina para verificar stock disponible.
Confusión de causa del estrés — temperatura foliar elevada puede deberse a déficit hídrico, estrés calórico (T°>40°C) o enfermedades foliares.
Media
El sistema integra datos meteorológicos en tiempo real. Si T° > 38°C y HR < 20%, activa flag 'condición extrema' que diferencia estrés calórico de déficit hídrico. Correlación con historial de riego y precipitaciones del lote.
El productor recibe la alerta con el contexto meteorológico completo. Agrónomo y protocolo Monteoliva definen umbrales contextualizados por variedad y fenología.
Nubosidad parcial durante la captura — una nube que pasa en los 15s de captura puede reducir T° foliar 0.5–1°C generando un falso CWSI bajo.
Media
Validación del frame por radiación solar: el piranómetro integrado mide la radiación en el momento exacto de la captura. Frames con radiación < 70% del máximo solar esperado para esa hora son excluidos automáticamente del cálculo del CWSI y marcados como 'condición sub-óptima'.
Si la nubosidad persiste más de 3 capturas consecutivas, el sistema emite alerta de 'datos insuficientes' en lugar de un CWSI potencialmente erróneo.
Drift estacional del modelo — el Malbec tiene fisiología diferente en verano (activo, alta transpiración) vs. envero vs. dormancia. Los coeficientes ΔT_LL/ΔT_UL varían por estadio fenológico.
Alta
El modelo se entrena y valida durante el período de máxima demanda hídrica (diciembre–marzo). Los umbrales CWSI se definen como específicos por estadio fenológico: vegetativo, envero, maduración. El protocolo Monteoliva incluye capturas en al menos 2 estadios fenológicos durante el período experimental.
Si el modelo muestra drift estacional, se recalibra con datos de cada estación usando el simulador para generar condiciones observadas. En TRL 5 se amplía el dataset real a múltiples estadios.
Representatividad geográfica — Colonia Caroya tiene condiciones climáticas diferentes a los mercados objetivo (Valle de Uco, San Juan). Altitud, HR y amplitud térmica difieren.
Media
El proyecto concentra la validación primaria en el viñedo experimental de Colonia Caroya (5 filas de calibración + 5 filas de producción × 136m con drip diferencial, 10 nodos permanentes) complementada con 3 campañas de validación cruzada en Mendoza y 2 en San Juan. Estas campañas capturan datos meteorológicos y térmicos en condiciones reales de Cuyo para verificar la transferibilidad del modelo.
Si los datos de Colonia Caroya resultan no representativos, las 3 campañas a Mendoza (Valle de Uco) proporcionan datos de recalibración. El simulador permite interpolar entre condiciones de ambas regiones.
Disponibilidad de tiempo del Inv. Art. 32 — ~5 hs/semana promedio (~177 hs totales), con obligaciones paralelas en su institución de investigación.
Baja
La arquitectura PINN, pipeline de entrenamiento, cuantización INT8 y fusión Sentinel-2 ya están implementados con Claude Code. El rol del investigador se concentra en validación, fine-tuning con datos reales (Mes 5–8) y exportación edge (Mes 9) — no es el cuello de botella del cronograma.
Si hay retraso en el fine-tuning (Gate 2 → Gate 3): el pipeline corre en la RTX 3070 de César sin necesidad de presencia física del investigador. Las decisiones arquitectónicas se documentan en repo Git con revisión asíncrona.


### 8.6 Gestión de Riesgos Macroeconómicos


Además de los riesgos técnicos documentados en la sección 8.5, el proyecto contempla riesgos del entorno macroeconómico argentino con estrategias de mitigación específicas:

Riesgo
Impacto
Estrategia de Mitigación
Importación de Insumos (sensores MLX90640, microcomputadoras)
Alto
Uso de la estructura de MBG Controls SAS para la gestión de licencias de importación de sensores MLX90640 y microcomputadoras. Pedido en Semana 1 del proyecto para absorber posibles demoras aduaneras de 4–8 semanas. Stock de repuestos críticos incluido en el presupuesto (MLX90640 ×2 de reserva). Alternativa: distribuidores locales de Melexis/MLX90640 en Argentina.
Conectividad en Campo (zonas sin cobertura celular)
Medio
Modelo dual de conectividad (ver sección 8.2.4A): donde hay cobertura 4G, el gateway se conecta vía router industrial Teltonika RUT241 (USD 190 + chip M2M USD 50/año). Donde no hay 4G, se usa Starlink Mini X (~USD 215 + USD 324/año). El gateway se conecta por Ethernet a cualquiera de las dos opciones. El nodo funciona autónomamente en edge durante períodos sin conectividad y sincroniza cuando se restablece el enlace.
Curva de Adopción (brecha digital del productor agropecuario)
Bajo
Interfaz basada en alertas por WhatsApp/email y dashboard web (todas desactivables por el productor). El sistema monitorea (Tier 1) o actúa autónomamente (Tier 2-3): cero configuración manual. Instalación guiada con QR. Canal de validación a través de agronomos e ingenieros de la red comercial que actúan como prescriptores de confianza.
Inestabilidad cambiaria y tipo de cambio (precios en USD, costos en ARS)
Medio
El presupuesto y el modelo de negocio están denominados en USD, lo que alinea ingresos y costos de componentes importados. El contingente del 14.2% del presupuesto absorbe variaciones de costos. La expansión hacia Chile (mercado en dólares) desde el Año 2 reduce la exposición al riesgo cambiario argentino.


### 8.7 Gestión de Riesgos de Ciberseguridad


El sistema HydroVision AG combina nodos IoT de campo, comunicación LoRaWAN, gateway con enlace satelital y backend cloud. Cada capa tiene superficie de ataque específica. Los riesgos de ciberseguridad se documentan por separado de los técnicos y macroeconómicos porque requieren mitigaciones de ingeniería de software y criptografía, no de diseño agronómico o de hardware.

Riesgo
Probabilidad
Impacto
Mitigación implementada / planificada
Inyección de telemetría falsa — endpoint POST /ingest sin autenticación permite que cualquier cliente envíe datos con node_id arbitrario.
Alta
Alto — datos falsos corrompen dashboard, generan alertas espurias y pueden disparar riego innecesario.
Implementar HMAC-SHA256 en cada payload: el nodo firma el JSON con un shared secret pre-cargado en NVS del ESP32; el backend verifica la firma antes de aceptar el ingreso. Planificado para Mes 3 (Gate 1).
Comunicación LoRa en texto plano — los paquetes JSON entre nodo y gateway se transmiten sin cifrado en banda 915 MHz, visibles para cualquier receptor LoRa en un radio de 1–3 km.
Media
Medio — un atacante puede capturar patrones de estrés hídrico (información comercial sensible) o hacer replay de paquetes para confundir al sistema.
Cifrado AES-128-CTR del payload antes de LoRa.write(). Clave de 128 bits derivada del eFuse unique_id de cada ESP32 + master key en NVS. Contador de secuencia de 2 bytes para prevenir replay. Gateway descifra antes de reenviar por MQTT/TLS. Planificado para Mes 3 (Gate 1).
Comandos downlink sin verificación de integridad — el nodo acepta cualquier JSON de downlink sin firma ni nonce, permitiendo que un atacante en rango LoRa active solenoides.
Media
Alto — activación no autorizada de riego puede dañar cultivos por exceso hídrico o agotar reserva de agua.
Firma HMAC en comandos downlink + nonce incremental. El nodo rechaza comandos con nonce ≤ último recibido. Alerta al backend si se detectan comandos rechazados (posible intento de ataque). Planificado para Mes 3 (Gate 1).
API sin rate limiting — endpoint /ingest acepta requests ilimitados, permitiendo DoS por inundación.
Baja
Medio — saturación de base de datos y degradación del servicio.
Rate limiting con SlowAPI: máximo 100 requests/minuto por node_id. Bloqueo temporal de 5 minutos al superar el límite. Logs de IPs bloqueadas para auditoría. Planificado para Mes 2.
Validación insuficiente de inputs — campos numéricos (CWSI, MDS, temperaturas) no tienen restricciones de rango; valores absurdos pasan sin filtro.
Media
Bajo — datos fuera de rango contaminan visualizaciones y pueden generar alertas falsas.
Validación Pydantic estricta: CWSI ∈ [0.0, 1.0], temperatura ∈ [−10, 60]°C, MDS ∈ [0, 2000] µm, HSI ∈ [0.0, 1.0]. Enum para calidad_captura: "ok", "lluvia", "post_lluvia", "fumigacion", "post_fumigacion". Planificado para Mes 2.
Secrets hardcodeados en firmware — frecuencia LoRa, spreading factor y power están en config.h; si el firmware se filtra, todos los nodos quedan expuestos.
Baja
Medio — no se pueden rotar credenciales sin reflashear físicamente cada nodo.
Migración de parámetros sensibles a NVS cifrado del ESP32 (Non-Volatile Storage con cifrado flash nativo). Generación de clave AES per-device desde eFuse unique_id. Implementación de OTA firmado con ECDSA para poder actualizar credenciales remotamente. NVS en Mes 3; OTA planificado para Mes 9–12.
Base de datos sin cifrado — SQLite almacena telemetría, decisiones de riego e historial de zonas en texto plano.
Baja
Medio — acceso al filesystem expone datos agronómicos propietarios del productor.
Migración a PostgreSQL con TLS + autenticación en producción. Credenciales de conexión en variables de entorno (no hardcodeadas). Backups cifrados con AES-256. SQLite solo para desarrollo local. Planificado para Mes 4–6.
Sin audit logging — no hay registro inmutable de quién accedió, comandó o modificó datos en el backend.
Baja
Medio — imposibilidad de investigar incidentes de seguridad; riesgo de compliance ante auditoría ANPCyT.
Tabla AuditLog: (timestamp, user_id, action, resource, old_value, new_value, ip_address). Log de todos los POST/PUT/DELETE en /admin y de payloads sospechosos en /ingest. Encadenamiento criptográfico hash(log_n) = SHA256(log_n-1 + contenido) para inmutabilidad. Planificado para Mes 6.
Sin redundancia de gateway — un solo RAK7268 + Starlink Mini X como punto único de fallo de conectividad.
Baja
Bajo (operación edge continúa) — los nodos siguen operando autónomamente con RTC memory; los datos se encolan hasta que el gateway se recupere. El riesgo es pérdida de datos si la cola excede la capacidad de NVS.
Monitoreo de heartbeat del gateway (el backend espera al menos 1 paquete/hora por nodo activo; si falta → alerta "gateway offline"). En TRL 5+: segundo gateway como failover automático. Para TRL 4: Lucas Bergon (residente Colonia Caroya) reemplaza gateway en <24h.
Sin verificación de estado real del solenoide — el nodo reporta el estado comandado del relé, pero no verifica si el solenoide realmente activó.
Baja
Medio — un relé trabado falla silenciosamente y el riego no se ejecuta cuando es necesario.
Diseño de feedback por current-sense en el relé: detectar si el solenoide realmente consumió corriente al activarse. Si falla 3 verificaciones consecutivas → alerta "Solenoide malfunction" + inhibición automática de esa zona. Planificado para TRL 5 (requiere revisión de PCB).


## 9. Análisis de Anterioridad — Búsqueda de Patentes
