

### 4.1 Arquitectura del sistema
El sistema opera en tres capas tecnológicas integradas:

Capa
Descripción
Tecnología clave
Capa 1Sensórica en campo
Nodo autónomo con cámara térmica, sensor meteorológico, GPS y módulo LoRa TX. Energía solar. Carcasa IP67. En Tier 1 el nodo es exclusivamente sensor — mide, calcula índices (CWSI, HSI, MDS) y transmite. En Tier 2-3, el nodo también actúa sobre el riego vía GPIO → relé SSR → solenoide Rain Bird (ver Capa 5).
MLX90640 32×24px · Sensirion SHT31 · Anemómetro RS485 copa · Extensómetro tronco (strain gauge + ADS1231 24-bit + DS18B20) · u-blox NEO-6M · SX1276 LoRa TX
Capa 2Procesamiento edge
Microcontrolador ESP32-S3 DevKit embebido en el nodo. Ejecuta el pipeline de procesamiento de imágenes térmicas y el modelo IA INT8 localmente, sin internet ni nube. Firmware en MicroPython. Consumo ~85% menor que RPi4, deep sleep 8µA.
ESP32-S3 DevKit · MicroPython · TFLite Micro INT8 · MobileNetV3
Capa 3Fusión y visualización
Servidor que recibe datos de todos los nodos, los fusiona con Sentinel-2 y genera mapas de prescripción de riego en formato GeoJSON visualizable en dashboard web (app móvil en TRL 5). Publica comandos de riego vía MQTT al controlador de campo.
FastAPI · SQLite/PostgreSQL · Sentinel-2 API · GeoPandas · MQTT (paho-mqtt)
Capa 4Intel. agronómica
Inteligencia que procesa los datos de las capas 1-3 para generar alertas de helada, estrés calórico, riesgo fitosanitario, predicción de fenología y cosecha, timing de operaciones de manejo, y fusión con Sentinel-2 para mapas espaciales de CWSI de todo el lote.
Motor GDD · Índices riesgo fitosanitario · Predicción cosecha · Fusión CWSI-Sentinel-2 · Notificaciones push configurables
Capa 5Actuación en campo (TRL 5+)
Control de riego autónomo integrado en nodo Tier 2-3. El nodo ESP32-S3 decide localmente cuándo regar según HSI (histéresis 0.30/0.20) y activa el solenoide vía GPIO → relé SSR. El servidor recibe el estado vía payload `/ingest`. Override manual disponible para emergencia/demo.
Relé SSR 24VAC 2A · Solenoide Rain Bird 24VAC 1" · driver_solenoide.h (firmware autónomo)

**Conectividad nodo → nube — modelo dual 4G / Starlink**
Los nodos transmiten por LoRaWAN al gateway RAK7268 (1 cada 10 nodos, antena omnidireccional 8 dBi). El gateway necesita internet para reenviar la telemetría al backend (~30–50 MB/mes para 10 nodos). Dos opciones según cobertura del campo:
- **Opción A — Router 4G industrial** (donde hay cobertura celular): Teltonika RUT241 (industrial, IP30, −40/+75°C), USD 155–190 una vez + chip M2M ~USD 3–5/mes. Failover automático y gestión remota vía Teltonika RMS. Opción por defecto — la mayoría de los campos en Mendoza, San Juan y Córdoba tienen cobertura 4G.
- **Opción B — Starlink Mini X** (donde NO hay cobertura celular): ~USD 215 hardware + USD 27/mes (plan Mini). Solo se ofrece en Tier 2-3 — el revenue de Tier 1 no justifica el costo. El gateway se conecta por Ethernet a cualquiera de las dos opciones. El nodo funciona autónomamente en edge durante períodos sin conectividad y sincroniza cuando se restablece el enlace.

### 4.2 Modelo físico — el CWSI
El Crop Water Stress Index (CWSI) es el índice agronómico central del sistema. Desarrollado por Jackson et al. (1981) y validado en más de 200 publicaciones científicas:

CWSI = (ΔT_medido − ΔT_LL) / (ΔT_UL − ΔT_LL)

Donde: ΔT = temperatura foliar − temperatura del aire · ΔT_LL = límite inferior (planta bien hidratada, función lineal del VPD) · ΔT_UL = límite superior (estoma cerrado, +3°C sobre el aire). Rango: 0 (sin estrés) a 1 (estrés severo). Umbrales de alerta: 0.30 (leve) / 0.55 (moderado) / 0.75 (severo). Discriminación de confounders: el sistema integra datos meteorológicos en tiempo real para diferenciar causas de temperatura foliar elevada. Si T° > 38°C y VPD > 4.5 kPa, el sistema activa flag 'estrés calórico probable' y ajusta los umbrales CWSI según protocolo Monteoliva. Si la temperatura foliar no correlaciona con el historial de riego del lote (riego reciente + CWSI alto), el sistema señala posible causa no hídrica (enfermedad foliar, estrés salino) y recomienda inspección visual. Esta lógica de discriminación causal se implementa como reglas en el motor de alertas del backend. Los coeficientes de Bellvert 2016 (vid Pinot Noir, Cataluña) se usan como punto de partida y serán recalibrados para Malbec en condiciones de Córdoba/Cuyo mediante el protocolo experimental diseñado con la Dra. Monteoliva — midiendo ΔT vs. VPD en plantas bajo riego completo en al menos 30 condiciones distintas de VPD durante el período experimental. Rango de VPD objetivo: 1.0–5.5 kPa, cubriendo las condiciones típicas del verano cordobés y cuyano (T° 28–40°C, HR 15–55%). Este rango es más amplio que el de Bellvert 2016 (1.5–3.0 kPa, Cataluña) y es el que determina la validez de los coeficientes para Malbec en Argentina.

#### 4.2.1 Motor fenológico automático (GDD) — detección de estadio sin configuración
El sensor meteorológico SHT31 del nodo mide temperatura cada 15 minutos, 24/7, los 365 días del año. Con esta información, el firmware calcula automáticamente grados-día acumulados — GDD = Σ max(0, (T_max + T_min)/2 - T_base) — y determina el estadio fenológico del cultivo sin intervención humana.
Punto de inicio y reinicio anual del acumulador GDD: La vid es un cultivo perenne, por lo que no existe un "día 0" natural equivalente al de un cultivo anual. La convención agronómica estándar en viticultura del hemisferio sur es iniciar la acumulación de GDD el 1 de agosto, fecha que corresponde al inicio del período post-dormancia invernal y es la adoptada por INTA para modelado fenológico de vid en Argentina (Catania & Avagnina, 2007). El firmware reinicia automáticamente el acumulador de GDD el 1 de agosto de cada año. Cuando el sistema detecta dormancia (T_media < T_base durante 14 días consecutivos), confirma el ingreso al período invernal y programa el próximo reinicio para el 1 de agosto siguiente. El GPS del nodo determina automáticamente el hemisferio: hemisferio norte → reinicio el 1 de febrero.
Detección automática de brotación: La brotación se confirma por convergencia de dos señales: (1) señal térmica — la desviación estándar de temperatura del frame térmico supera 0.8°C durante 3 días consecutivos (indica presencia de masa foliar emergente); (2) señal GDD — los grados-día acumulados desde el 1 de agosto superan 80–120 (umbral de brotación para Malbec según Catania & Avagnina, 2007). La convergencia de ambas señales elimina falsos positivos por días cálidos aislados en plena dormancia. El GPS del nodo determina automáticamente el hemisferio y ajusta la fecha de reinicio del acumulador.

Estadio
GDD Malbec
Acción automática del sistema
Vegetativo
0–350
Coeficientes Set A (hojas jóvenes). Alertas standard.
Floración
350–550
Coeficientes Set B. Umbrales más conservadores — estrés en floración causa caída irreversible de frutos.
Desarrollo
550–1.100
Coeficientes Set A (hojas maduras, máxima conductancia). Máxima precisión del modelo.
Envero
1.100–1.400
Coeficientes Set C. ΔT_LL ajustado hacia arriba — la conductancia baja naturalmente por redistribución al fruto, NO es estrés.
Pre-cosecha
1.400–1.900
Modo RDI automático: solo alerta si CWSI > 0.85 (daño irreversible) o si CWSI baja inesperadamente.
Dormancia
T_media < T_base × 14 días
Hibernación: 1 frame cada 6h, heartbeat LoRa semanal, consumo ~1µA. Despierta automáticamente en la siguiente temporada.


T_base por cultivo: Malbec T_base=10°C (Catania & Avagnina, INTA 2007); Cabernet Sauvignon T_base=10°C (Ortega-Farías et al. 2019); Olivo T_base=12.5°C; Arándano T_base=7°C. Los modelos GDD predicen brotación con RMSE de 3–7 días (García de Cortázar-Atauri et al. 2009).
Alertas agronómicas derivadas del motor GDD (sin hardware adicional): El sistema genera automáticamente 12+ tipos de alertas y predicciones además del CWSI: alerta de helada tardía (T° < 2°C con GDD indicando brotes presentes), estrés calórico (T° > 40°C), riesgo de mildiú (HR > 85% + T° 18–25°C + lluvia), riesgo de botrytis (HR > 90% + T° 15–25°C en envero), ventana de desbrote (GDD 150–200), momento de muestreo de pecíolos, predicción de fecha de floración/envero/cosecha actualizada semanalmente, deadlines de PHI de fungicidas, registro de horas de frío acumuladas en dormancia, y modo RDI automático en pre-cosecha. Todas configurables por el productor como notificaciones push.

#### 4.2.2 Sistema de notificaciones configurables
HydroVision AG permite al productor configurar qué alertas recibir y por qué canal (WhatsApp, email) desde el dashboard web. Las alertas son completamente desactivables por el productor:

Alerta
Urgencia
Canal default
CWSI > umbral (estrés hídrico)
Alta
Push inmediato + riego autónomo (Tier 2-3)
Helada inminente (T° < 2°C)
Crítica
Push + SMS
Estrés calórico (T° > 40°C)
Alta
Push
Riesgo mildiú / botrytis
Media
Push diario
Estadio fenológico detectado
Info
Push
Predicción floración/envero/cosecha
Info
Push semanal
Ventana de desbrote / análisis foliar
Media
Push
Deadline PHI fungicida
Alta
Push + email
Nodo sin datos / batería baja
Alta
Push + email
Heartbeat hibernación semanal
Info
Email
ψ_stem crítico — HSI ≤ −1.5 MPa (RESCATE hídrico)
Crítica
Push + SMS
Estrés hídrico MDS — ψ_stem MDS > umbral por estadio
Alta
Push inmediato
Recuperación nocturna insuficiente — tronco recuperó < 80% contracción antes del amanecer
Alta
Push + email
Desacuerdo señales HSI — Δψ entre CWSI y MDS > 0.35 MPa (revisar sensor o condición anómala)
Media
Push

El productor puede desactivar cualquier alerta, cambiar el canal y ajustar umbrales numéricos. La configuración se sincroniza con todos los nodos del lote.

#### 4.2.3 Auto-calibración dinámica del baseline CWSI — el sensor de tronco calibra a la cámara térmica
El CWSI requiere dos parámetros baseline por nodo: Tc_wet (temperatura de la hoja bien hidratada) y Tc_dry (temperatura sin transpiración). En la literatura, se usan los coeficientes NWSB de Jackson (1981) como punto de partida — pero en campo, cada planta, variedad y microclima produce un Tc_wet ligeramente diferente. Sin calibración de campo, el error sistemático del baseline se acumula silenciosamente durante la temporada y puede desplazar el CWSI ±0.15–0.20 unidades.

HydroVision AG resuelve este problema sin visitas de calibración humanas, usando el extensómetro de tronco como ancla fisiológica de la cámara térmica:

Evento de lluvia (calibración principal):
Cuando llueve ≥5mm y el extensómetro registra MDS≈0 (tronco al diámetro máximo — planta al máximo de hidratación), la temperatura foliar medida por la cámara térmica en ese momento ES el Tc_wet real del nodo para esas condiciones de Ta y VPD. El sistema captura ese par (Tc_medido, Ta, VPD) y actualiza el offset del baseline vía EMA (Exponential Moving Average, learning_rate=0.25):
  tc_wet_offset ← (1 − 0.25) × tc_wet_offset + 0.25 × (Tc_medido − NWSB(Ta, VPD))
Este mecanismo provee calibraciones reales múltiples por temporada sin que el equipo visite el viñedo — la lluvia genera automáticamente el evento de referencia hídrica.

Actualización periódica por sesión Scholander:
Cada sesión de medición Scholander aporta un par verificado (Tc_medido, ψ_stem). Las sesiones con MDS bajo (planta razonablemente hidratada, MDS < 200µm) actualizan el baseline con tasa de aprendizaje reducida (learning_rate × confianza × 0.5) — aprendizaje más conservador que el evento de lluvia.

Detección de deriva del baseline:
Si el CWSI histórico del nodo muestra: (a) media < 0.02 → Tc_wet está sobreestimado (el baseline inferior es demasiado alto); (b) media > 0.98 → Tc_wet está subestimado; (c) std < 0.01 con >10 muestras → señal sin variación, posible falla del sensor. Cualquiera de estas condiciones activa una alerta de "deriva de baseline" al agrónomo.

Persistencia ante reinicios:
Los offsets tc_wet_offset y tc_dry_offset de cada nodo se guardan en JSON local cada vez que cambian. Al reiniciar el ESP32-S3 (actualización de firmware, corte de energía, watchdog), el nodo carga el baseline calibrado de la temporada en curso sin perder el historial acumulado.

Resultado operativo: un nodo instalado en octubre inicia con el NWSB de Jackson (1981) como baseline de fábrica. Con cada evento de lluvia y cada sesión Scholander, el baseline converge al comportamiento real de las plantas de esa zona. Para fin de temporada, el sistema tiene el baseline específico de ese nodo/variedad/microclima, y lo carga automáticamente al inicio de la campaña siguiente. Esta calibración dinámica es la que hace técnicamente justificada la afirmación R²=0.90–0.95 del HSI: sin un baseline correcto para cada nodo, ese R² no es alcanzable en condiciones reales de campo.

**Stack de calibración de triple redundancia (niveles de degradación controlada):**
El sistema ordena sus fuentes de calibración en tres niveles. Ante la falla de un nivel, degrada la precisión de forma controlada sin interrumpir el servicio:

| Nivel | Fuente | Trigger de activación | Precisión | Disponibilidad |
|---|---|---|---|---|
| **1 — Paneles Dry/Wet Ref** (primario) | Panel Wet Ref físico: T_wet medida 96 veces/día | Siempre activo mientras el reservorio tenga agua | RMSE < 0.5°C — máxima | 100% campaña · recarga mensual por Javier |
| **2 — Eventos climáticos** (fail-safe) | Lluvia ≥5mm con MDS≈0 → T_wet real del nodo; viento validado por anemómetro | Reservorio Wet Ref agotado (T_wet ≈ T_aire) | Buena — evento fisiológico real | 8–12 eventos/campaña en Colonia Caroya/Cuyo |
| **3 — NWSB + offsets históricos** (emergencia) | Coeficientes Jackson (1981) ajustados por JSON de temporadas anteriores | Nodo < 2 semanas instalado o sin lluvia ni recarga reciente | Inferior — suficiente para alertas | Siempre disponible (offline) |

La degradación es explícita, trazable y reportada al dashboard como "Nivel de confianza de calibración activo" — el nodo nunca entrega datos corruptos silenciosamente.

#### 4.2.4 Mitigación de viento — 9 capas de defensa en profundidad y transición gradual al MDS

**El problema:** El viento afecta la medición de temperatura foliar de tres formas: (1) enfriamiento convectivo de la hoja (T_leaf baja artificialmente), (2) movimiento de la hoja dentro/fuera del FOV del sensor IR (ruido), (3) error en T_air y HR del sensor ambiental (propaga error al VPD y al CWSI). Sin mitigación, el CWSI solo es confiable hasta 4 m/s (14 km/h) — insuficiente en Cuyo donde el 60-80% de los días de temporada tienen viento > 4 m/s.

**Solución — 9 capas de mitigación (todas incluidas en todos los nodos, un solo SKU):**

| Capa | Tipo | Qué ataca | Reducción de error |
|------|------|-----------|-------------------|
| 0 — Orientación a sotavento | Física (instalación) | Convección directa. Cámara al lado este (sotavento del Zonda) — las plantas actúan como barrera, reduciendo ~60-70% la velocidad en la zona medida | ±0.08 → ±0.03 |
| 1 — Tubo colimador IR | Física (hardware) | Movimiento de hoja en FOV y flujo lateral. Tubo PVC 110mm × 250mm negro mate, concéntrico con lente MLX90640 | ±0.04 → ±0.01 |
| 2 — Shelter anti-viento SHT31 | Física (hardware) | Error en T_air/HR/VPD. Shelter tipo Gill 6 placas blancas, convección natural sin flujo forzado (estándar WMO Guide No. 8) | ±0.05-0.10 → ±0.01 |
| 3 — Termopar foliar de contacto | Física + firmware | Enfriamiento convectivo (fuente principal). Termopar tipo T 0.1mm al envés de hoja, inmune al viento. Corrección: `T_corr = T_IR + k × (T_tc - T_IR)`, k=0.6 calibrable | ±0.08 → ±0.02 |
| 4 — Compensación Tc_dry | Firmware | Baseline superior inflado por viento. `delta *= (1 - wind/20)` reduce el denominador del CWSI proporcionalmente | Elimina sesgo |
| 5 — Buffer térmico + filtro calma | Firmware | Ruido instantáneo. 5 lecturas/ciclo, selecciona mediana de lecturas con viento < 2 m/s (7 km/h) | Elimina outliers |
| 6 — Fusión HSI (65% MDS base) | Firmware | Inestabilidad del CWSI vs. estabilidad del MDS. El MDS ya domina por diseño — un error de +0.15 en CWSI impacta solo +0.053 en HSI | Atenuación 65% |
| 7 — Rampa gradual 4-18 m/s | Firmware | Pérdida progresiva de confianza del CWSI. Transición suave, nunca un salto abrupto (ver detalle abajo) | Degradación controlada |
| 8 — Fallback CWSI inválido | Firmware | CWSI = -1 (no calibrado, rango insuficiente). HSI = 100% MDS automáticamente | Red de seguridad |

**Transición gradual CWSI → MDS (rampa lineal 4-18 m/s / 14-65 km/h):**

El sistema NO usa un cutoff binario. El peso del CWSI se reduce linealmente a medida que el viento sube:

| Viento (anemómetro) | km/h | Viento real en hoja (con mitigaciones) | w_cwsi | w_mds | Estado |
|---|---|---|---|---|---|
| 0-4 m/s | 0-14 | 0-1.6 m/s | 0.35 | 0.65 | Normal — error ±0.02 |
| 6 m/s | 22 | ~2.4 m/s | 0.26 | 0.74 | Reducción 25% |
| 8 m/s | 29 | ~3.2 m/s | 0.18 | 0.82 | Reducción 50% |
| 10 m/s | 36 | ~4.0 m/s | 0.09 | 0.91 | MDS domina 91% |
| 12 m/s | 43 | ~3.6-4.8 m/s | 0.15 | 0.85 | CWSI residual con corrección v2 |
| 15 m/s | 54 | ~4.5-6.0 m/s | 0.08 | 0.92 | MDS domina 92% |
| ≥18 m/s | 65 | ~5.4-7.2 m/s | 0.00 | 1.00 | Backup total — solo MDS |

**Justificación de 18 m/s como umbral máximo (antes era 4 m/s):**

Con orientación a sotavento (Capa 0), el viento en la hoja medida es ~30-40% del medido en el anemómetro (que está en la punta del mástil, expuesto). A 18 m/s medidos, las hojas ven solo ~5.4-7.2 m/s. El firmware v2 extiende el rango útil de 12 a 18 m/s gracias a: fusión Kalman IR↔termopar [B5], paneles Muller gbh de referencia [C4], filtro Hampel para outliers [B2], buffer adaptativo [B1], segundo termopar [A3] y captura oportunista en calma [B3]. El tubo colimador (Capa 1) reduce el flujo lateral adicional, y el termopar (Capa 3) corrige el 60% del error restante por contacto directo. El resultado combinado: a 18 m/s medidos, el error del CWSI es ±0.05-0.07, dentro del umbral aceptable de ±0.07 (Araújo-Paredes et al. 2022). Antes de las mitigaciones, ese error era ±0.12-0.18 ya a 4 m/s. En la práctica: el CWSI pasa de ser útil el 20-40% de los días a ser útil el **95-98% de los días** de temporada en Cuyo.

**Calibración del factor de corrección TC_BLEND_K (termopar):**

El factor k=0.6 (default para Malbec Cuyo) se calibra mediante sesiones Scholander bajo viento moderado (5-10 m/s / 18-36 km/h). Se miden simultáneamente ψ_stem (Scholander), T_leaf_IR y T_termopar. Se calcula CWSI_blend(k) para distintos valores de k y se selecciona el que maximiza R² vs. ψ_stem. Valores típicos: Malbec 0.5-0.7, Olivo 0.6-0.8, Arándano 0.7-0.9. Recalibración solo necesaria si cambia varietal o estructura del canopeo. Procedimiento detallado en `lucas/documentacion/mitigacion-viento.md` y `lucas/documentacion/guia-instalacion-nodo-v1.md`.

**Cuándo entra en vigencia el backup total (100% MDS):**

El MDS incrementa su protagonismo de forma gradual — no es un switch on/off. En condiciones normales (≤4 m/s) ya tiene el 65% del peso. El backup total (w_mds=1.00) ocurre en dos situaciones: (1) viento ≥18 m/s / 65 km/h (Zonda severo, ~2-5 días/temporada en Cuyo), o (2) CWSI = -1 (sensor no calibrado o rango insuficiente). El MDS es inmune al viento (mide contracción del tronco con strain gauge), opera 24/7, y su única limitación es la respuesta más lenta (horas vs. minutos del CWSI).

Costo incremental de las 9 capas: USD 9 sobre COGS base (6.5%). Detalle completo en `lucas/documentacion/mitigacion-viento.md`.

### 4.3 Estrategia de datos y entrenamiento del modelo IA — arquitectura PINN
Fundamento de la arquitectura PINN: La arquitectura Physics-Informed Neural Network (PINN) fue elegida específicamente porque el CWSI está gobernado por una ecuación física exacta (Jackson et al., 1981) que el modelo no debe violar. A diferencia de un regresor de caja negra, la función de pérdida PINN incorpora un término de residuo físico adicional: L_total = L_datos + λ · L_física. El término L_física penaliza predicciones de ΔT_foliar que no sean consistentes con el balance energético foliar bajo las condiciones meteorológicas medidas en ese instante (T°, VPD, radiación). Esto actúa como regularización física — reduce el espacio de soluciones admisibles y mejora la generalización con pocos datos reales, que es exactamente la condición de TRL 4 (800 frames reales: 680 fine-tuning + 120 validación independiente). La factibilidad del enfoque está documentada en literatura reciente de 2024-2025: Ridder et al. (2025) aplican PINN a la absorción radicular con 2% de error en parámetros de estrés hídrico; Benkirane et al. (2025) demuestran PINN con Penman-Monteith para evapotranspiración en contextos de datos limitados; Hu et al. (2025) aplican PINN a estimación de humedad de suelo con Landsat 8 Thermal; y Rouholahnejad et al. (2024) implementan physics-informed yield loss forecasting con Sentinel-2. Ninguno aplica PINN al CWSI calculado desde termografía embebida en campo — ese es el aporte original de HydroVision AG.

El modelo de IA se entrena con una estrategia de tres capas que permite alcanzar un dataset efectivo de 1.050.680 imágenes sin necesidad de campañas de captura masivas en campo:

Capa
Fuente
Volumen y contenido
Propósito
1
Datasets públicos agrícolas y térmicos
50.000+ imágenes: INIA Chile (vid bajo riego deficitario con CWSI verificado) · IRTA Cataluña (olivo bajo déficit hídrico) · PlantVillage Thermal (hojas bajo estrés, Penn State) · FLIR ADAS (14.000 imágenes térmicas industriales para aprendizaje de representaciones térmicas generales)
Pre-entrenamiento del backbone. El modelo aprende a interpretar imágenes térmicas y detectar patrones de estrés sin datos propios.
2
Imágenes sintéticas — simulador físico propio
1.000.000 de imágenes generadas por simulador de balance energético foliar calibrado para Malbec en condiciones climáticas de Cuyo. Inputs del simulador: parámetros morfológicos de la hoja (área, emisividad, conductancia estomática por nivel de estrés), condiciones meteorológicas (T°, VPD, radiación solar) y nivel de CWSI objetivo. Output: imagen térmica sintética con ruido realista del sensor MLX90640 32×24px. Ejecutado en RTX 3070 — 1.000.000 imágenes en ~40 horas de GPU.
Fine-tuning específico para Malbec bajo condiciones de Cuyo. Permite entrenar con variedad de condiciones climáticas extremas sin depender de eventos naturales ni campañas de campo.
3
Frames reales calibrados — protocolo Monteoliva
800 frames de imágenes térmicas de plantas de Malbec bajo 5 regímenes hídricos controlados, capturados en al menos 2 estadios fenológicos y 2 regiones (Colonia Caroya + Mendoza). Cada frame etiquetado con CWSI verificado por potencial hídrico de tallo medido con bomba de Scholander. Split: 680 frames para fine-tuning + 120 frames para validación independiente (no vistos durante entrenamiento). Anclaje fisiológico real del modelo.
Calibración final del modelo a condiciones reales de campo. Con el backbone ya pre-entrenado en 50.000 imágenes públicas y 1.000.000 sintéticas, los 680 frames de fine-tuning son suficientes para una calibración precisa sobre Malbec en condiciones de Cuyo.
Total entrenamiento
1.050.680 imágenes (50.000 + 1.000.000 + 680) · Validación independiente: 120 frames reales
El simulador físico es un activo estratégico diferencial: permite generar datasets ilimitados para nuevas variedades (Cabernet, Chardonnay, Syrah) y nuevos cultivos (olivo, arándano) sin campañas de campo masivas. TRL 5 incorpora Sauvignon Blanc y olivo Arauco sin costo adicional de captura.
Target: accuracy > 85% en set de validación independiente de 120 frames reales no vistos durante entrenamiento.



#### 4.3.1 Pipeline 'Simulación Primero' — modelos para nuevas variedades sin calibración inicial
Para escalar a nuevas variedades más allá de Malbec, el simulador físico habilita un pipeline de tres etapas que permite generar un modelo funcional sin calibración de campo inicial:

Etapa
Tiempo / Costo
Descripción y precisión
1. Literature-Grade
Día 1 / $0
Parámetros morfológicos foliares publicados para todas las viníferas, olivo, citrus y arándano (Jones 1999, Bellvert 2016, García-Tejero 2018). Se extrapolan coeficientes ΔT_LL/ΔT_UL desde variedades similares. Error CWSI: ±0.20–0.35. Suficiente para detección gruesa de estrés severo.
2. Simulation-Grade
Semana 1–4 / ~USD 80 GPU
El simulador genera 1.000.000 imágenes sintéticas con los parámetros morfológicos de la nueva variedad y fine-tunea el modelo IA. Error CWSI: ±0.15–0.25. Suficiente para alertas de estrés moderado. El productor recibe valor desde el día 1 con indicación de precisión limitada.
3. Field-Grade
Mes 4–6 / USD 15K–25K
Calibración real con bomba de Scholander. Error CWSI < ±0.10. Habilita control automático de riego (Tier 2-3). Es el estándar de referencia del proyecto TRL 4 para Malbec.


Implicancia estratégica: El pipeline reduce el time-to-market para nuevas variedades de 6 meses a 4 semanas. La calibración real deja de ser el primer paso obligatorio y se convierte en una mejora incremental sobre un modelo que ya funciona. El simulador validado es el activo más escalable del proyecto.

### 4.4 Hardware del nodo — especificación TRL 4
Condiciones de operación en campo: Temperatura ambiente 0–45°C (picos de 55°C en carcasa al sol directo en Cuyo) · Humedad 10–95% RH · Exposición UV directa · Ciclos de riego por goteo/microaspersión · Viento hasta 80km/h · Polvo en NOA y San Juan. El diseño incorpora gestión térmica pasiva (disipador aluminio), protección de la ventana óptica HDPE (solapa mecánica entre capturas), conectores M12 IP67 y carcasa ABS/PC con tratamiento UV. El nodo es instalado por un técnico de campo en la primera puesta en marcha — los nodos adicionales los activa el productor solo con código QR.

Componente
Modelo
Costo USD
Función
Microcontrolador
ESP32-S3 DevKit (off-the-shelf, MicroPython) + EBYTE E32-900T20D (SX1276)
$15
CPU + RAM + LoRa TX (DevKit elimina PCB custom)
Cámara térmica
MLX90640 breakout integrado (Adafruit 4407, sensor BAB 110° FOV) 32×24px
$50
Imagen foliar LWIR (módulo plug & play I2C)
Sensor meteorológico
Sensirion SHT31-DIS-B + piranómetro BPW34
$8
T°, HR, radiación solar
GPS
u-blox NEO-6M con antena cerámica
$8
Georreferenciación
IMU + Gimbal motorizado
ICM-42688-P + servo pan-tilt 2 ejes (MG90S × 2)
$18
Escaneo activo multi-angular del canopeo: 7 capturas por ciclo (6 posiciones fijas + 1 condicional con viento > 20 km/h) a ±20° horizontal y ±15° vertical. IMU compensa vibración de viento durante cada captura. Inspirado en metodología de termografía UAV.
Panel solar + batería
Panel policristalino 6W + LiFePO4 6.000mAh + regulador
$27
Autonomía energética
Carcasa IP67 (sin PCB custom)
Hammond IP67 200×150×100mm + pasacables M16. Arquitectura modular: DevKit + breakouts I2C/SPI — sin PCB custom para TRL4.
$20
Protección IP67 + integración modular
~~Alertas físicas — LED tricolor + sirena~~ (REMOVIDO)
Eliminado del diseño: mercado objetivo = plantaciones con riego automatizado. Alertas vía WhatsApp, email y dashboard web (desactivables por el productor).
—
Ahorro USD 28/nodo
Control de riego — Tier 2-3 (integrado en nodo)
Relé SSR 24VAC 2A + solenoide Rain Bird 24VAC 1" integrados directamente en el nodo ESP32-S3 Tier 2-3. El nodo decide autónomamente cuándo regar según HSI local (histéresis 0.30/0.20) y activa el solenoide vía GPIO → SSR. El servidor solo recibe el estado vía payload `/ingest`.
USD 16 (adicional vs Tier 1)
Automatización riego por goteo autónoma en nodo
Sistema de montaje en campo
Estaca acero inoxidable 316 punta cónica 1.5m base (extensible a 3m para viñedo en espaldera) (se clava entre plantas, protege de tractor) · Bracket aluminio con abrazadera doble tornillo + tope angular mecánico + nivel de burbuja integrado · Conectores M12 IP67 para cables externos (estándar industrial, no dupont) · Kit cableado UV-resistente
USD 45
Instalación estable, orientación reproducible, protección industrial
Gestión térmica pasiva
Aleta disipadora de aluminio sobre pared lateral de la carcasa en contacto con el ESP32-S3 — conducción térmica sin ventilación activa. El ESP32-S3 genera ~85% menos calor que RPi4. Mantiene temperatura interna < 65°C a 45°C ambiente. Sin partes móviles ni entrada de polvo.
USD 12
Operación confiable en verano cordobés/cuyano (40–45°C ambiente)
Protección ventana óptica HDPE
Solapa mecánica de aluminio que cubre la ventana HDPE entre capturas — se abre solo durante la captura (15 seg cada 15 min) mediante servo de bajo consumo. Protege de polvo, barro de salpicaduras de riego y lluvia lateral. Cubierta UV-resistente exterior.
USD 18
Mantiene la ventana óptica limpia · Extiende vida útil en campo > 3 años
Anemómetro RS485 copa
Anemómetro de copa RS485 Modbus RTU, resolución 0.1 m/s, rango 0–60 m/s, carcasa ABS UV-resistente. Comunicación RS485 vía MAX485 en PCB.
USD 35
Detección de viento — transición gradual CWSI→MDS entre 4-18 m/s / 14-65 km/h (rampa lineal). A ≥18 m/s (65 km/h): HSI = 100% MDS. Confianza dinámica del índice HSI. Complementado por termopar foliar de contacto (ground truth inmune al viento) y tubo colimador IR que bloquea flujo lateral en el FOV del MLX90640.
Extensómetro de tronco — dendrometría MDS
Strain gauge de tronco + ADS1231 24-bit ADC (resolución 1 µm) + DS18B20 (corrección térmica ±0.5°C) + abrazadera de aluminio anodizado flexible (diámetro 10–25 cm, compatible con troncos adultos). Montaje permanente sobre tronco principal, a 30 cm del suelo, cara norte.
USD 45
Medición de micro-contracciones diarias del tronco (MDS = D_max − D_min). Estimación directa de ψ_stem con R²=0.80–0.92 (Fernández & Cuevas 2010). Segunda señal fisiológica del índice HSI — inmune a artefactos de viento.
TOTAL NODO TIER 1 (COGS a volumen prototipo x5)


~USD 149


TOTAL NODO TIER 3 (+ control riego SSR + solenoide)


~USD 164

> Nota: Precios COGS para prototipo x5 unidades. BOM detallado con proveedores y alternativas en `lucas/hardware/BOM-nodo-v1.md`. Precio de venta al cliente: USD 950 (Tier 1) / USD 1.000 (Tier 3).






Figura 2 — Nodo HydroVision AG instalado en viñedo de Malbec, Mendoza. Panel solar 6W, carcasa IP67 Hammond, relé SSR integrado para control autónomo de solenoide Rain Bird, líneas de goteo, gateway LoRaWAN + router 4G (o Starlink Mini en zonas sin cobertura celular) al fondo. El nodo Tier 2-3 decide autónomamente cuándo regar según HSI local. Andes al fondo. Simulación fotorrealista de condiciones reales de campo TRL 5.

#### 4.4.1 Balance energético del nodo — autonomía solar
ESP32-S3 con deep sleep RTC DS3231: Consumo activo ~0.5W, deep sleep 8µA (~0.03mW). Con ciclo de captura cada 15 minutos (90s activo + 810s dormido) incluyendo MLX90640, gimbal, sensores y LoRa, el consumo promedio ponderado es ~0.18W. Batería LiFePO4 6.000mAh a 3.2V = 19.2Wh. Autonomía sin sol: ~120 horas (~5 días). Panel 6W con 6h de sol efectivo/día genera 36Wh/día vs. consumo diario ~4.3Wh — balance energético positivo con amplio margen. El ESP32-S3 consume ~85% menos que RPi4 en el mismo ciclo de trabajo.
Nota sobre la protección de la ventana óptica: El sistema de limpieza usa un micro-soplador piezoeléctrico (Murata MZB1001T02, consumo 0.3W × 0.5s por pulso) que dispara un jet de aire sobre la ventana HDPE antes de cada captura. Con 96 capturas/día, el consumo diario es ~0.004Wh (despreciable). La ventana HDPE incorpora recubrimiento hidrofóbico nano-coating que minimiza la adherencia de polvo y gotas. Este diseño elimina completamente las partes móviles expuestas al ambiente (servos, solapas mecánicas), que son la principal causa de falla en dispositivos de campo a largo plazo.

#### 4.4.2 Sistema de captura multi-angular — termografía de campo inspirada en UAV

El principal diferencial técnico introducido por la investigación en termografía UAV (Pires et al. 2025, Zhou et al. 2022, Santesteban et al. 2017) es la captura desde múltiples ángulos sobre el canopeo, que reduce drásticamente el problema de mezcla espectral suelo/hoja/tallo inherente a una cámara fija. HydroVision AG incorpora esta metodología al nodo fijo mediante un gimbal pan-tilt motorizado, obteniendo los beneficios del UAV sin sus limitaciones operativas.

Secuencia de captura multi-angular (por ciclo de 15 minutos):
El firmware ejecuta la siguiente secuencia en ~8 segundos antes del procesamiento CWSI:

Posición
Ángulo horizontal
Ángulo vertical
Propósito
Centro
0°
0°
Referencia base — vista frontal del canopeo
Izquierda
−20°
0°
Captura zona de sombra de filas — reduce reflexión solar directa
Derecha
+20°
0°
Captura zona de exposición máxima
Arriba
0°
+15°
Vista superior — máxima cobertura foliar, mínima exposición de suelo
Abajo
0°
−10°
Validación de dosel inferior — detecta stress en zonas de menos exposición
Extra (viento > 20 km/h)
Aleatorio
Aleatorio
Frame adicional para validación estadística en condiciones de alta vibración

Algoritmo de fusión multi-frame (edge, ESP32-S3):
1. Para cada frame: calcular fracción foliar (píxeles en rango P20–P75 del histograma térmico / total de píxeles).
2. Seleccionar los 3 frames con mayor fracción foliar (típicamente Centro, Arriba y uno lateral según orientación de filas).
3. Calcular ΔT_foliar ponderado: promedio de los 3 CWSI individuales, ponderado por fracción foliar de cada frame.
4. Si la desviación estándar entre los 3 CWSI seleccionados supera 0.12 unidades → emitir flag 'alta variabilidad angular' e incluir el dato con advertencia.
Resultado: CWSI final con error estimado < ±0.07 unidades (vs. ±0.10 de captura fija), equivalente o superior a la precisión reportada en termografía UAV de baja altitud (Araújo-Paredes et al., 2022; Santesteban et al., 2017).

Comparación con alternativas:

Método
Resolución
Ángulos
Frecuencia
Costo
Regulación
CWSI error típico
Drone UAV térmico
640×512px
Múltiples (vuelo)
1–2/semana
USD 800–2.000/vuelo
ANAC requerida
±0.08–0.12
Nodo fijo ángulo único (TRL 4 base)
32×24px
1 fijo
96/día
USD 950 (hardware)
Sin regulación
±0.10–0.15
Nodo con gimbal multi-angular (TRL 4 mejorado)
32×24px × 7 frames fusionados (6 fijos + 1 condicional)
7 por ciclo
96/día
USD 980 (+USD 30 servo)
Sin regulación
±0.06–0.09

El sistema multi-angular no reemplaza un drone de alta resolución para mapeo de campo completo, pero sí iguala su precisión de CWSI puntual con captura continua — que es exactamente lo que necesita el productor para gestión de riego en tiempo real.

Costo del upgrade: La incorporación de dos servos MG90S (USD 8 c/u) más el bracket de montaje ajustado (USD 14) añade USD 30 al costo del nodo. El firmware de control del gimbal (PWM, secuencia angular, retorno a posición de reposo) se implementa en el Mes 1–2 del proyecto junto con los drivers de sensores.

#### 4.4.3 Diseño modular para escalabilidad multi-varietal
La PCB del nodo incorpora un conector I²C del MLX90640 como cámara base. Para escalar a cultivos de hoja pequeña (olivo, arándano) en TRL 5+, la PCB incluye un conector FFC de 24 pines que acepta un módulo adaptador para el FLIR Boson 320 (320×256px, USD 2.000) sin cambios en la PCB base. El firmware detecta automáticamente qué cámara está conectada y ajusta los parámetros de captura. El productor compra el 'nodo para vid' (MLX90640, USD 950) o el 'nodo para olivo/arándano' (Boson, USD 2.800) — nunca necesita saber qué cámara tiene adentro.
El sistema de montaje usa un kit modular de piezas combinables: estaca base 1.5m + extensiones + brazos específicos por cultivo (penetrante para olivo en seto, cenital para arándano, estaca alta para citrus). Todas las piezas comparten la misma rosca y sistema de ajuste. Un técnico reconfigura un nodo en 15 minutos.

Motor GDD multi-varietal — estrategia de reinicio por tipo de cultivo: La extensión del motor GDD a nuevos cultivos requiere adaptar dos parámetros: la temperatura base (T_base) y la estrategia de reinicio del acumulador. Todos los cultivos objetivo de HydroVision comparten el mismo sensor SHT31 — no se necesita hardware adicional.

Cultivo
Tipo
T_base
Reinicio acumulador GDD
Horas frío requeridas
Complejidad
Vid (todas las variedades)
Caducifolio
10°C
1 agosto (sur) / 1 febrero (norte) — detección dormancia por T_media < T_base × 14 días
Sí — registro automático
Baja — mecanismo base del proyecto
Cerezo
Caducifolio
4.5°C
1 agosto (sur) — misma lógica que vid
Sí — crítico (400–1.200 horas según variedad)
Baja — mismo mecanismo, alta sensibilidad al frío
Pistacho
Caducifolio
10°C
1 agosto (sur)
Sí — muy exigente (1.000+ horas)
Baja — especialmente relevante en San Juan/NOA
Nogal
Caducifolio
10°C
1 agosto (sur)
Sí — moderado (600–800 horas)
Baja — mismo mecanismo
Olivo (AOVE)
Semi-caducifolio
12.5°C
1 julio (sur) — calendar-based fijo (dormancia parcial e inconsistente)
No aplica
Media — reinicio fijo, no por detección de dormancia
Citrus (Limón)
Perennifolio
13°C
Sin reinicio anual — modelo por evento fenológico (floración, cuaje, maduración)
No aplica
Alta — múltiples ciclos de brotación; requiere modelo específico por evento. TRL 5+ dedicado.

Para los cultivos caducifolios (cerezo, pistacho, nogal), la extensión es directa: el mismo firmware carga una tabla de parámetros por cultivo sin modificaciones estructurales. El registro de horas de frío (horas con T° < 7°C durante la dormancia) se implementa en paralelo sobre el mismo sensor SHT31, habilitando alertas de déficit de frío crítico para pistacho y cerezo en zonas de clima cambiante.
Para el olivo, el reinicio es calendar-based fijo (1 de julio) dado que su dormancia es parcial e inconsistente entre variedades — no es detectable de forma confiable por señal térmica.
Para citrus, el motor GDD anual no aplica directamente: los ciclos de brotación son múltiples por año y dependen de eventos (post-helada, post-cosecha, irrigación). Su incorporación requiere un modelo por evento fenológico que se desarrolla en TRL 5 como variedad dedicada.
Watchdog de hardware: El nodo incorpora un watchdog timer externo (TPL5010, consumo 35nA) que reinicia automáticamente el ESP32-S3 si no recibe pulso heartbeat en 2 minutos. Esto garantiza la recuperación autónoma ante cuelgues de software sin intervención humana.

### 4.5 Fusión nodo-satélite para cobertura espacial completa

El nodo proporciona dos niveles de estimación de ψ_stem con distintas coberturas temporales: (a) CWSI térmico (±0.07–0.09) disponible solo durante la ventana solar (9–16hs) cuando la iluminación y el VPD son suficientes; (b) HSI dendrométrico (extensómetro de tronco + MDS) disponible 24/7, incluyendo horas nocturnas y días nublados, con R²=0.80–0.92 vs. ψ_stem Scholander. El MDS registra la contracción máxima diaria del tronco — indicador de estrés acumulado que el CWSI térmico instantáneo no puede capturar. La fusión HSI provee continuidad temporal completa: el extensómetro ancla la tendencia de estrés de 24 horas; la cámara térmica aporta la lectura de alta precisión en la ventana solar.

La cobertura espacial —que el nodo no puede proveer solo— la aporta Sentinel-2 de forma complementaria y gratuita. Esta fusión es el mecanismo que hace viable económicamente el sistema: sin ella, cubrir 100 ha con la misma precisión requeriría 50–100 nodos en vez de 2–10.

─── QUÉ ES SENTINEL-2 Y POR QUÉ ES LA FUENTE SATELITAL ÓPTIMA ───────────────

Sentinel-2 es la constelación de satélites de observación de la Tierra del programa Copernicus de la Agencia Espacial Europea (ESA), compuesta por dos satélites en órbita (S-2A lanzado 2015, S-2B lanzado 2017) en órbita heliosíncrona a 786 km de altitud. Es de acceso completamente gratuito y sin restricciones para usos comerciales — a diferencia de Landsat (menor resolución), Planet (pago) o SPOT (pago).

Características técnicas relevantes para el proyecto:

· Resolución espacial: 10 m/px en las bandas VIS/NIR (B2 Azul, B3 Verde, B4 Rojo, B8 NIR) · 20 m/px en las bandas Red Edge y SWIR (B5, B6, B7, B8A, B11, B12) · 60 m/px en bandas de corrección atmosférica (B1, B9, B10). En vid de Mendoza con filas de espaldera separadas 2–3 m, cada píxel de 10m cubre 3–4 filas — suficiente para discriminar zonas de vigor diferencial por sectores de 0.5 ha.
· Revisita: 5 días en el ecuador (2–3 días en latitudes medias como Mendoza −33°S / San Juan −31°S, por la superposición orbital de los dos satélites). En temporada activa de estrés (diciembre–febrero), se obtienen típicamente 10–12 imágenes útiles por mes.
· Latencia: las imágenes Level-2A (corrección atmosférica incluida) están disponibles en la API de Copernicus Data Space en < 3 horas desde la captura. El sistema consulta automáticamente si hay imagen nueva cada mañana.
· Cobertura de nubes: la fracción de nubosidad se reporta por escena. El sistema filtra automáticamente escenas con cloud_cover > 20%. En Cuyo (Mendoza, San Juan) la nubosidad media en verano es del 15–20% → típicamente disponibles 8–10 escenas útiles/mes en temporada crítica. En días nublados, el MDS dendrométrico actúa como señal principal mientras el satélite no entrega dato.
· Corrección atmosférica: el procesamiento Level-2A (producto BOA — Bottom Of Atmosphere) corrige el efecto de la atmósfera sobre la reflectancia, entregando valores de reflectancia de superficie comparables entre fechas y regiones. Esta corrección es fundamental para que la correlación CWSI↔NDWI sea estable entre campañas.
· Acceso: API RESTful de Copernicus Data Space (https://dataspace.copernicus.eu). Autenticación por token gratuita. Descarga directa de bandas individuales o productos completos. Sin costo. Sin cuota de uso para proyectos de investigación y desarrollo. Alternativa de procesamiento: Google Earth Engine (GEE) — plataforma de cómputo geoespacial en la nube con catálogo completo de Sentinel-2 ya disponible, accesible con cuenta gratuita para proyectos de investigación.

─── BANDAS UTILIZADAS Y SU JUSTIFICACIÓN AGRONÓMICA ─────────────────────────

HydroVision AG utiliza cinco bandas de Sentinel-2 para los tres índices principales:

Banda
Longitud de onda central
Resolución
Índice
Justificación agronómica
B3 — Verde
560 nm
10 m
NDVI (parcial)
Referencia de reflectancia en verde para cálculo NDVI
B4 — Rojo
665 nm
10 m
NDVI, NDWI
Absorción por clorofila — discrimina vegetación activa de suelo y material senescente
B8 — NIR
842 nm
10 m
NDVI, NDWI
Alta reflectancia en NIR correlaciona con biomasa foliar activa y contenido de agua en tejidos
B5 — Red Edge 1
705 nm
20 m
NDRE
Zona de transición rojo-NIR extremadamente sensible al contenido de clorofila y al estrés hídrico temprano. Detecta envero 3–5 días antes que NDVI en vid.
B11 — SWIR 1
1610 nm
20 m
NDWI
Absorción por agua líquida en tejidos foliares. Correlaciona directamente con el contenido hídrico de la hoja — el índice más sensible al estrés hídrico antes del síntoma visible.

Índices calculados:
· NDVI = (B8 − B4) / (B8 + B4). Rango −1 a +1. En vid Malbec: dormancia 0.10–0.15 · brotación 0.25–0.35 · plena hoja 0.55–0.75 · envero (inicio) 0.50–0.60 · senescencia 0.30–0.45.
· NDWI = (B3 − B8) / (B3 + B8) [Gao 1996, alternativa McFeeters para vegetación]. Sensible al contenido de agua foliar. En vid estresada: NDWI cae 0.08–0.15 unidades antes del síntoma visible de marchitez.
· NDRE = (B8A − B5) / (B8A + B5). Más sensible que NDVI al estrés hídrico temprano y al contenido de clorofila. En vid, el NDRE detecta el inicio del envero 3–5 días antes que el NDVI — crítico para activar el modo RDI automático en el momento preciso.

─── MODELO DE CORRELACIÓN CWSI↔NDWI — CÓMO FUNCIONA ───────────────────────

El principio central de la fusión satelital es: el nodo tiene alta precisión en un punto (1–2 ha), el satélite tiene baja–media precisión en toda la superficie (50+ ha). La fusión usa el nodo para calibrar el satélite — y el satélite para estimar el estrés en zonas donde no hay nodo.

Distinción fundamental: el nodo calibra la curva CWSI↔NDWI, pero NO ancla el resultado de la zona. Cada zona recibe su propia firma espectral Sentinel-2 (NDWI, NDVI, NDRE propios de sus píxeles), y el modelo predice el estrés propio de esa zona a partir de esos valores. Zonas con suelo más seco → NDWI bajo → CWSI estimado alto. Zonas con suelo húmedo → NDWI alto → CWSI estimado bajo.

Paso 1 — Nodo: ground truth puntual
El nodo mide CWSI real en su posición GPS (cámara térmica MLX90640, ±0.07–0.09 CWSI). También mide T°aire y HR, con lo que se calcula el VPD del día: VPD = e_s × (1 − HR/100), donde e_s = 0.6108 × exp(17.27·T / (T + 237.3)). El VPD es la variable meteorológica que aporta la dimensión temporal a la fusión (condiciones atmosféricas del día).

Paso 2 — Sentinel-2 en el punto del nodo: features espectrales
Cuando Sentinel-2 entrega una imagen útil (cloud_cover < 20%), el sistema extrae las bandas espectrales (B4, B8, B8A, B11, B12) del píxel de 10m que corresponde a la ubicación GPS del nodo. A partir de estas bandas se calculan los índices:
  NDWI = (B8A − B11) / (B8A + B11) → contenido hídrico foliar
  NDVI = (B8  − B4)  / (B8  + B4)  → vigor vegetativo
  NDRE = (B8A − B4)  / (B8A + B4)  → estrés temprano (Red Edge)
Se genera un par de calibración: (CWSI=0.45, NDWI=0.12, NDVI=0.58, NDRE=0.42, VPD=1.9). En una campaña estándar de 6 meses (octubre–marzo) en Cuyo, se acumulan 40–60 pares.

TRL 4 demo: las bandas S2 se generan sintéticamente con la relación empírica NDWI↔CWSI publicada por González-Dugo et al. (2013). TRL 5+: bandas reales de GEE (extraer_bandas_punto).

Paso 3 — Calibración del modelo
Con ≥ 10 pares acumulados, se ajusta la regresión polinomial robusta:
  CWSI = f(NDWI, NDVI, NDRE, VPD)
Modelo: HuberRegressor grado 2 (sklearn Pipeline) que minimiza el impacto de outliers (nubes parciales, sombras). El VPD se incluye porque la relación CWSI↔NDWI no es estable en condiciones de VPD extremo (> 4.5 kPa en San Juan). Implementación: CWSINDWICorrelationModel en sentinel2_fusion.py. R²=0.96 en calibración sintética TRL 4; la literatura reporta R²=0.70–0.85 en vid con datos reales (Poblete et al. 2017, Remote Sensing).

Paso 4 — Sentinel-2 en la zona sin nodo: firma espectral propia
Para cada zona de riego que no tiene un nodo dentro de sus límites, el sistema extrae las bandas espectrales de los píxeles de Sentinel-2 que caen dentro del polígono de esa zona. Estas bandas son INDEPENDIENTES de las del nodo — representan la reflectancia real de la vegetación en esa zona particular. Si la zona tiene suelo más arenoso, su NDWI será más bajo que el del punto del nodo; si tiene más vigor, su NDVI será más alto.

TRL 4 demo: las features S2 de cada zona se generan con una firma espectral determinística por zona_id (seed fijo → reproducible). TRL 5+: bandas reales de GEE (polígono de la zona).

Paso 5 — Predicción del CWSI de la zona
El modelo calibrado en Paso 3 se aplica a las features de la zona:
  CWSI_zona = f(NDWI_zona, NDVI_zona, NDRE_zona, VPD_día)
El resultado es el estrés PROPIO de esa zona, no una copia del CWSI del nodo. El nodo solo calibró la curva; la zona tiene sus propios índices espectrales. El VPD del día (medido por los nodos) es el único dato compartido — aporta la condición atmosférica actual.

Aplicado al lote completo (10m/px): el backend aplica la función a cada píxel de la máscara del lote (polígono GeoJSON del productor). El resultado es un mapa de CWSI estimado, disponible cada 2–5 días. El backend almacena la serie temporal de mapas y calcula la variabilidad histórica por zona.

Implementación en app.py (_SatelliteFusionService):
  • Calibración: calibrar_con_nodos(pares) recibe historial (cwsi, vpd) de la DB
  • Predicción: predecir_cwsi(zona_id, vpd) genera features S2 de la zona y aplica el modelo
  • Prioridad: zona con nodo dentro → dato directo; zona sin nodo → fusión S2; sin nodos → sin datos
  • TRL 5+: reemplazar _obs_from_cwsi() y _obs_for_zona() con bandas GEE reales

Límites de precisión de la extrapolación:
La precisión del CWSI extrapolado disminuye con la distancia al nodo y con la heterogeneidad del suelo. El error de extrapolación fue caracterizado en la sección 8.2.1A: ±0.10–0.12 a 1 nodo/10 ha en lotes homogéneos, degradándose a ±0.15 a 1 nodo/20 ha (límite práctico de prescripción diferencial). A esta densidad, el CWSI extrapolado por satélite tiene R²=0.55–0.63 vs. ψ_stem — útil para detección de estrés severo y tendencias, pero insuficiente para control automático de riego. El HSI dendrométrico no se extrapola por satélite: la señal de tronco es específica de la planta medida.

─── NIVEL 1 — CALIBRACIÓN ESPACIAL DEL CWSI ────────────────────────────────

El modelo establece la correlación CWSI↔NDWI en el punto del nodo (donde la señal es de máxima precisión: HSI R²=0.90–0.95), y la aplica al resto del lote donde solo llega la señal satelital. Cada nodo adicional agrega un punto de calibración independiente en una zona distinta del lote — si las zonas tienen suelos distintos, sus modelos de correlación pueden diferir y el sistema los ajusta por separado (un modelo por zona). Resultado: mapa de CWSI estimado de 50–100 ha con un solo nodo, o de 200+ ha con densidad híbrida de 3–5 nodos estratégicamente ubicados en cada tipo de suelo.

Frecuencia de actualización del mapa: cada imagen Sentinel-2 útil (cloud_cover < 20%) genera un nuevo mapa. Con revisita de 2–3 días en latitudes de Cuyo, el mapa se actualiza en promedio 2 veces por semana en temporada activa. El MDS dendrométrico del nodo actualiza el ψ_stem de referencia a las 6:00 AM todos los días (hora de D_min, contracción máxima nocturna) — ancla diario de la escala de estrés que el satélite interpola cada 2–3 días en el espacio.

─── NIVEL 2 — VERIFICACIÓN FENOLÓGICA ESPACIAL ─────────────────────────────

La serie temporal de NDVI Sentinel-2 permite detectar automáticamente eventos fenológicos a escala de campo completo, complementando el GDD del nodo que solo conoce la temperatura de un punto:

· Brotación: el NDVI sube de 0.10–0.15 (dormancia) a 0.25–0.35 en 7–10 días. El sistema confirma la brotación cuando convergencia GDD + NDVI supera el umbral. La ventaja satelital: detecta si brotó todo el lote o solo una parte (variabilidad de fecha de brotación por exposición solar, tipo de suelo, disponibilidad hídrica).
· Envero: el NDRE (Red Edge, 705nm) es más sensible que el NDVI al cambio de pigmentación que ocurre en el envero. Detecta el inicio del envero 3–5 días antes que el NDVI, permitiendo anticipar el cambio de coeficientes CWSI al modo RDI automático (pre-cosecha) con mayor precisión. El NDRE es el índice más usado en viticultura de precisión precisamente por esta sensibilidad al estado fisiológico de la baya (Hall et al. 2011, Australian Journal of Grape and Wine Research).
· Senescencia y defoliación: el NDVI cae de 0.55–0.75 a < 0.20 en 3–4 semanas en otoño. El sistema detecta si la defoliación fue homogénea (senescencia natural) o asimétrica (zona con estrés hídrico severo o daño por helada tardía).
· Variabilidad espacial de vigor: el coeficiente de variación (CV) del NDVI dentro del lote en plena hoja (GDD 600–1000) es el mejor proxy de la heterogeneidad del suelo y del manejo diferencial. Este CV es el input principal del motor de propuesta automatizada (R15): determina si el lote requiere densidad uniforme o densidad híbrida por zonas.

──────────────────────────────────────────────────────────────────────────────
  CRITERIO DE HOMOGENEIDAD DEL LOTE — definición operativa HydroVision AG
──────────────────────────────────────────────────────────────────────────────

Se usan dos métricas complementarias:

A) CV del NDVI Sentinel-2 (en plena hoja, GDD 600–1000):
   Fuente: Sentinel-2, 10m/px, gratuito. Calculado por pipeline_satelital.py.

   CV NDVI < 15 %   → HOMOGÉNEO   — suelo y vigor uniformes. 1 nodo puede
                                     representar 10–20 ha (Poblete et al. 2017).
   CV NDVI 15–25 %  → MODERADO    — variabilidad apreciable. Densidad mínima
                                     recomendada: 1 nodo / 5–10 ha.
   CV NDVI > 25 %   → HETEROGÉNEO — lote con zonas de suelo o manejo distintos.
                                     Densidad recomendada: 1 nodo / 1–2 ha o
                                     zonificación explícita.

B) CV del CWSI entre nodos (tiempo real, calculado por el dashboard):
   Fuente: lectura más reciente de cada nodo activo. Sin satélite requerido.

   CV CWSI < 15 %   → HOMOGÉNEO   — todos los nodos ven estrés similar.
                                     La fusión nodo-satélite es confiable con
                                     una sola calibración para todo el lote.
   CV CWSI 15–25 %  → MODERADO    — diferencias de estrés entre zonas. Revisar
                                     si hay problema puntual (emisor tapado,
                                     zona de suelo diferente).
   CV CWSI > 25 %   → HETEROGÉNEO — estrés muy diferente por zona. El riego
                                     debe ser diferencial. Cada zona con suelo
                                     distinto requiere su propia calibración
                                     CWSI↔NDWI (un modelo por tipo de suelo).

Relación entre métricas:
   · CV NDVI es el diagnóstico estructural del lote (evaluar al inicio de campaña).
   · CV CWSI es el diagnóstico operativo en tiempo real (varía día a día con el riego).
   · Un lote homogéneo (CV NDVI < 15%) puede mostrar CV CWSI alto si el riego fue
     mal aplicado en alguna zona. Ambas métricas se complementan.

Nota: el IDW (Inverse Distance Weighting) entre nodos fue eliminado en TRL 4.
   La estimación de CWSI por zona ahora usa exclusivamente fusión nodo-satélite
   (ver "MODELO DE CORRELACIÓN CWSI↔NDWI" arriba). Cada zona sin nodo recibe
   su propia firma espectral Sentinel-2 — no se interpola entre nodos.

──────────────────────────────────────────────────────────────────────────────

─── NIVEL 3 — DETECCIÓN DE ANOMALÍAS ESPACIALES ────────────────────────────

El satélite puede identificar patrones espaciales que el nodo (puntual) no detecta, y el nodo puede diagnosticar causas que el satélite (espectral) no puede distinguir. La combinación de ambos resuelve el diagnóstico completo:

Anomalía detectada por satélite
Causa posible
Diagnóstico diferencial del nodo
Parche de NDVI bajo en zona localizada (< 30% del lote)
Estrés hídrico localizado · Foco de enfermedad foliar · Problema de suelo (salinidad, compactación) · Falla de emisor de goteo
Si CWSI alto en el nodo de esa zona → estrés hídrico. Si CWSI bajo + T° nocturna < 0°C → daño por helada. Si CWSI bajo + HR > 85% en rango mildiú → enfermedad probable. Si CWSI bajo + historial de riego normal → problema de suelo o emisor.
NDVI bajo en todo el lote respecto a campaña anterior
Déficit hídrico generalizado · Año de menor vigor por carga · Defoliación precoz por enfermedad
Si ψ_stem MDS < −1.2 MPa acumulado → déficit hídrico. Si GDD indica baja carga → año de menor vigor esperado. El productor puede corroborar con inspección visual dirigida a la zona exacta.
NDWI cae abruptamente en zona de buen NDVI
Estrés hídrico sin pérdida de biomasa aún (etapa pre-síntoma)
Confirmado por CWSI térmico elevado en el nodo de esa zona. Es el escenario de mayor valor: detección 5–10 días antes del síntoma visual, cuando aún hay tiempo para actuar.
Zona de NDRE muy bajo en envero
Estrés en maduración · Deficiencia nutricional (N, Mg)
Si ψ_stem MDS en rango moderado → estrés hídrico en maduración. Si ψ_stem normal → posible deficiencia nutricional. Recomendar muestreo de pecíolos.

─── ACCESO A DATOS Y IMPLEMENTACIÓN TÉCNICA ─────────────────────────────────

Fuente de datos: Copernicus Data Space (https://dataspace.copernicus.eu) — plataforma oficial ESA de acceso a datos Sentinel-2. Acceso completamente gratuito mediante autenticación por token (OAuth2). La API REST permite descargar bandas individuales en formato GeoTIFF recortadas al polígono del lote (sin descargar la escena completa de 110×110 km). Un lote de 100 ha con píxeles de 10m = 10.000 píxeles útiles → GeoTIFF de ~200 KB por banda. Costo de almacenamiento: despreciable.

Alternativa Google Earth Engine: GEE ofrece el catálogo completo de Sentinel-2 Level-2A accesible mediante Python API (earthengine-api), con cómputo de índices en la nube sin necesidad de descargar las imágenes crudas. Ventaja: latencia de procesamiento < 30 segundos para cualquier lote. HydroVision evalúa GEE como backend principal para la fusión satelital en TRL 4, con Copernicus Data Space como fallback.

Pipeline de procesamiento (backend FastAPI):
1. Consulta diaria automática a la API de Copernicus/GEE: ¿hay imagen nueva con cloud_cover < 20% sobre el lote?
2. Si sí: descarga/calcula bandas B3, B4, B5, B8, B8A, B11 recortadas al polígono del lote.
3. Cálculo de NDVI, NDWI, NDRE por píxel sobre la máscara de vegetación (excluye bordes, caminos, construcciones — definida una vez al momento del onboarding por el polígono GeoJSON del productor).
4. Emparejamiento temporal con CWSI/HSI del nodo (±1 día). Actualización del modelo de correlación CWSI↔NDWI con el nuevo par (aprendizaje continuo incremental — el modelo mejora con cada imagen nueva).
5. Aplicación del modelo calibrado a todos los píxeles del lote → mapa de CWSI estimado (GeoJSON / GeoTIFF).
6. Detección de anomalías: píxeles con NDVI < percentil 10 del lote en la misma fecha de campaña anterior → flag "zona anómala" → alerta push al productor con ubicación GPS exacta.
7. Almacenamiento en PostGIS de la serie temporal de mapas. Visualización en dashboard web como capa sobre el mapa del lote (app móvil en TRL 5).

Costo operativo de la fusión satelital: USD 0 en datos (Copernicus gratuito). Cómputo: incluido en el servidor VPS FastAPI (USD 60/mes para todos los lotes). El backend procesa en < 5 segundos un lote de 100 ha. A 100 lotes activos: < 8 minutos de cómputo por imagen nueva disponible. Escala lineal con el número de lotes — no requiere infraestructura adicional hasta ~500 lotes activos simultáneos.

─── CASO PRÁCTICO: 100 HA MALBEC, VALLE DE UCO ─────────────────────────────

Sin fusión satelital (solo nodos Tier 2-3 a 1/2 ha): 50 nodos a USD 1.000 = USD 50.000 en hardware.
Con fusión satelital (densidad mínima, 1 nodo/10 ha): 10 nodos a USD 950 = USD 9.500 en hardware.
Ahorro en hardware: USD 40.500 (−81%). La precisión del CWSI cae de R²=0.92 (HSI completo) a R²=0.63 (CWSI+sat) — suficiente para alertas de estrés severo y mapa de tendencias, pero insuficiente para control automático de riego en modo Tier 2-3. El productor que quiere automatización completa necesita la densidad 1/2 ha; el que quiere solo monitoreo y alertas puede empezar con 1/10 ha y agregar nodos en los sectores críticos identificados por el satélite en la primera campaña.

Este mecanismo — el satélite le dice al productor dónde instalar más nodos con mayor ROI — es el motor de expansión orgánica del negocio: la primera campaña satelital con densidad mínima genera el mapa de variabilidad que justifica y dimensiona la densidad óptima para la segunda campaña.

#### 4.5.1 Stack satelital multi-fuente — optimización por cultivo, región y condición climática

Sentinel-2 es la fuente principal del sistema, pero no es la única. HydroVision AG implementa una arquitectura multi-satélite donde cada fuente resuelve una limitación específica de las demás: cobertura de nubes, resolución espacial insuficiente para ciertos cultivos, o profundidad de archivo histórico. El sistema selecciona automáticamente la fuente óptima por lote y fecha según disponibilidad y calidad.

─── LIMITACIONES DE SENTINEL-2 POR CULTIVO ────────────────────────────────

Sentinel-2 a 10m/px funciona con precisión suficiente para cultivos con canopeos de ≥3m de ancho o filas separadas ≥2.5m. En cultivos más compactos, la mezcla espectral suelo/vegetación por píxel degrada la calidad del índice:

Cultivo
Geometría típica
Sentinel-2 (10m)
Problema
Solución
Vid espaldera (Mendoza, Cuyo)
Filas 2.5–3m separación
Suficiente
3–4 filas por píxel — discrimina zonas de vigor diferencial
Primaria
Olivo tradicional (marco 7×7m)
Copa adulta 4–6m diámetro
Suficiente
Copa supera píxel en árboles adultos
Primaria
Cerezo / Nogal / Pistacho
Copa 6–10m diámetro adulto
Suficiente
Canopeo domina el píxel
Primaria
Olivo superintensivo seto (San Juan)
Filas 1.5m separación
Parcial
Alta mezcla suelo/verde — degradación en NDWI
Planet como complemento Tier Elite
Arándano (Patagonia, Perú)
Plantas 0.5–1m, filas 0.5m
Insuficiente
Píxel 10m = 95% suelo — NDVI inútil para estrés foliar
Planet obligatorio
Espárrago (Perú — Costa)
Estructura rastrera
Insuficiente
No resuelve estructura de cultivo
Planet + SAR

─── SATÉLITES COMPLEMENTARIOS ──────────────────────────────────────────────

SAOCOM 1A/1B — CONAE Argentina (radar SAR banda L, 24cm)
El componente más estratégico del stack multi-satélite, por dos razones simultáneas: es técnicamente complementario a Sentinel-2, y es un satélite operado por la Comisión Nacional de Actividades Espaciales (CONAE) — acceso gratuito para proyectos de I+D argentinos, exactamente la categoría que cubre este ANR.

Características técnicas: resolución 10m en modo StripMap (hasta 100km de franja), revisita ~8 días, radar de apertura sintética banda L. El radar no es afectado por nubes, lluvia ni condiciones de iluminación solar — opera igual de noche que de día, en invierno que en verano, con neblina costera o tormenta de polvo de San Juan.

Complementariedad con Sentinel-2: mientras Sentinel-2 mide la reflectancia espectral de la superficie del canopeo (señal óptica, bloqueada por nubes), SAOCOM banda L penetra el canopeo y detecta la estructura y contenido de humedad en tejidos leñosos (troncos, ramas gruesas) — una señal independiente y directamente relevante para el estado hídrico de la planta. Esta complementariedad es documentada en literatura reciente de teledetección agrícola (Ferrazzoli et al. 2018; Paloscia et al. 2013).

Aplicación en HydroVision AG:
· Fallback principal cuando Sentinel-2 está bloqueado por nubes en Río Negro (nubosidad media 40–60% en temporada activa de peras y manzanas), Chile zona central (neblina costera) y NOA (tormentas convectivas de verano).
· En San Juan, las tormentas de polvo (viento Zonda) pueden degradar las imágenes ópticas. SAOCOM opera con transparencia total en esas condiciones.
· Correlación SAOCOM backscatter ↔ contenido de agua en tejidos leñosos: valida y complementa la señal MDS dendrométrica del extensómetro de tronco — dos sensores de estructura leñosa, uno en tierra y uno en órbita.
· Argumento ANPCyT: HydroVision AG integra tecnología espacial argentina (SAOCOM/CONAE) como componente de su stack técnico — alineado con la política de soberanía tecnológica nacional y con los objetivos del FONARSEC de fortalecer el uso de infraestructura científica pública argentina.

Acceso: convenio de colaboración con CONAE para acceso a imágenes SAOCOM en el marco del proyecto ANPCyT — trámite estándar para proyectos de I+D nacionales, sin costo. TRL 4: integración de SAOCOM como fuente de fallback en el módulo sentinel2_fusion.py.

Sentinel-1 — ESA/Copernicus (radar SAR banda C, 5.6cm)
Mismo ecosistema gratuito que Sentinel-2 (programa Copernicus). Radar banda C con resolución 10m y revisita 6–12 días. Complementa a SAOCOM en zonas donde el convenio CONAE aún no está activo. Sensible a humedad de suelo superficial (0–5cm) — proxy de riego reciente que complementa el MDS dendrométrico. Integración directa en Google Earth Engine junto con Sentinel-2 sin overhead de implementación adicional.

Planet Labs — PlanetScope (óptico 3–5m/px, constelación ~200 satélites)
Resolución 3m/px en el modelo SuperDove de 8 bandas (incluye Red Edge). Revisita diaria sobre cualquier punto de la Tierra. Es la única fuente que resuelve filas individuales de olivo superintensivo y cultivos de arándano — donde Sentinel-2 es insuficiente.

Costo: USD 2.000–5.000/año por acceso API comercial — no trasladable a un productor individual. Modelo de negocio HydroVision para Planet: una suscripción zonal compartida entre todos los clientes de una misma zona (ej. todos los olivicultores superintensivos de Albardón, San Juan). Con 5 clientes de 50 ha cada uno = 250 ha compartidas → costo Planet amortizado en < USD 20/ha/año sobre los clientes. Activado como add-on para cultivos donde Sentinel-2 no es suficiente.

Satellogic — empresa argentina (1m/px multispectral + hiperspectral)
Startup argentina de observación satelital con presencia en Buenos Aires y convenios con CONAE. Resolución 1m/px en modo multispectral y capacidad hiperspectral (30 bandas) en modo de revisita programada. Los índices hiperespectrales de contenido de agua foliar (índices WBI — Water Band Index, NDWI de 970nm, índice DSWI) son más precisos que el NDWI de Sentinel-2 para detección de estrés hídrico temprano. Aplicación estratégica HydroVision: alianza de validación mutua — HydroVision provee ground truth fisiológico (ψ_stem Scholander + HSI) para calibrar los modelos de estrés de Satellogic; Satellogic provee resolución hiperspectral para mejorar los índices de fusión satelital de HydroVision. Activación: TRL 5+ con convenio de colaboración.

Landsat 8/9 — USGS/NASA (óptico 30m/px, archivo desde 1972)
Gratuito, 16 días de revisita, resolución 30m/px. Demasiado grueso para monitoreo puntual de estrés por sector — pero invaluable para el análisis histórico de largo plazo de un lote. El motor de propuesta automatizada (R15) usa el archivo Landsat de los últimos 10 años del lote para calcular la variabilidad histórica de NDVI por zona, identificar sectores de bajo rendimiento crónico (posible problema de suelo, salinidad, compactación) y estratificar la densidad de nodos recomendada antes de la primera temporada de monitoreo. Este análisis histórico está disponible para cualquier campo en cualquier región de Argentina sin costo adicional.

MODIS — NASA (250m/px, diario, global)
Resolución 250–500m/px — no resuelve lotes individuales. Útil a escala regional para: predicción de eventos climáticos extremos (anomalías de temperatura superficial de tierra que anticipan episodios de estrés masivo en toda una cuenca vitivinícola), y para la contextualización del CWSI del nodo dentro de la variabilidad regional de la campaña.

─── MATRIZ DE SELECCIÓN AUTOMÁTICA POR LOTE ────────────────────────────────

El backend HydroVision selecciona automáticamente la fuente satelital óptima para cada lote en cada fecha según la siguiente lógica de prioridad:

Condición
Fuente seleccionada
Razón
Sentinel-2 disponible, cloud_cover < 20%
Sentinel-2 (principal)
Mejor balance resolución/bandas/cobertura/costo para vid, olivo tradicional, frutales de carozo
Sentinel-2 bloqueado por nubes (Río Negro, Chile, NOA)
SAOCOM → Sentinel-1
SAR atraviesa nubes. SAOCOM L-band preferido por mayor penetración en canopeo
Olivo superintensivo o arándano (filas < 2m)
Planet PlanetScope (Tier Elite)
Resolución 3m resuelve filas individuales — Sentinel-2 insuficiente a 10m
Onboarding nuevo campo / propuesta automatizada R15
Landsat 8/9 (archivo histórico 10 años)
Análisis de variabilidad histórica del lote sin visita de campo
Escala regional (alerta macroclimática para zona)
MODIS
Cobertura diaria de temperatura superficial de tierra a nivel de cuenca

─── COBERTURA POR REGIÓN DE EXPANSIÓN ─────────────────────────────────────

Región
Cultivo prioritario
Fuente principal
Fuente fallback
Desafío específico
Mendoza — Valle de Uco
Malbec premium
Sentinel-2
Sentinel-1
Alta insolación, VPD extremo verano (>5 kPa) — ajuste de modelo CWSI↔NDWI por rango VPD
San Juan — Albardón
Olivo Arbequina superintensivo
Sentinel-2 + Planet (Tier Elite)
SAOCOM (tormentas polvo Zonda)
Filas 1.5m — mezcla espectral alta. Viento Zonda degrada óptica.
Río Negro — Valle Medio
Pera Williams + Manzana
SAOCOM (principal)
Sentinel-2
Nubosidad 40–60% — SAOCOM como primario, no fallback
NOA — Cafayate, Jujuy
Torrontés + Citrus premium
Sentinel-2
SAOCOM
Tormentas convectivas verano. Altitud 1.600–2.000m — corrección atmosférica especializada
Chile — Zona Central
Vid Sauvignon Blanc + Olivo
Sentinel-2
SAOCOM (neblina costera)
Neblina de advección costera frecuente. Megasequía → alta variabilidad de estrés interanual
Perú — Costa Norte
Arándano + Espárrago
Planet (obligatorio)
Sentinel-1
Estructura de cultivo no resuelta por Sentinel-2. Alta humedad costera → SAR como backup

### 4.6 Sistema dual CWSI+MDS vs. análisis de tallo solo — justificación técnica comparativa

Esta sección documenta en detalle por qué la arquitectura HSI de doble señal (CWSI térmico
+ MDS dendrométrico) es superior al análisis de tallo solo (MDS/dendrometría únicamente,
como en Phytech Israel), cuáles son sus limitaciones reales, y en qué condiciones la señal
única puede ser suficiente. El equipo debe conocer ambos lados de esta comparación para
responder con precisión ante evaluadores ANPCyT, inversores y clientes técnicos.

---

#### 4.6.1 Qué mide cada señal — diferencia fisiológica fundamental

Antes de comparar, es crítico entender que CWSI y MDS no miden lo mismo.
Son señales de dos procesos fisiológicos distintos con relación de causa-efecto entre ellos.

| Señal | Órgano medido | Proceso fisiológico | Ventana temporal | Sensible a |
|---|---|---|---|---|
| CWSI (temperatura foliar) | Hoja / canopeo | Apertura estomática → balance energético foliar | Instantáneo (< 15 min) | Demanda atmosférica actual (VPD, radiación, temperatura aire) |
| MDS (extensómetro tronco) | Tallo / xilema | Contracción hidráulica del tejido xilemático | Diario (ciclo 24h) | Estado hídrico acumulado del sistema suelo-planta |

**La relación causal:** El tallo pierde agua (MDS sube) porque las hojas transpiran
(CWSI sube) cuando la demanda atmosférica supera la capacidad de extracción del suelo.
El CWSI es la señal de demanda; el MDS es la respuesta estructural.

Medir solo el MDS es como medir la deuda acumulada sin saber cuánto se gasta por día.
Medir solo el CWSI es como saber el gasto diario sin saber si la cuenta bancaria está vacía.
Con ambas señales: se sabe cuánto se gasta (CWSI) y cuál es el saldo restante (MDS).

---

#### 4.6.2 Ventajas del sistema dual CWSI+MDS sobre el análisis de tallo solo

**V1 — Resolución temporal: intradiaria vs. un valor por día**

El MDS solo produce un valor útil por ciclo de 24 horas: la contracción máxima diaria
(D_max − D_min, medida al amanecer). Un evento de estrés que ocurre entre las 13:00 y
las 17:00 (pico de VPD en Cuyo) queda registrado como "el MDS fue alto ese día" — sin
saber si el estrés duró 4 horas (recuperable) o 8 horas (daño estomático).

El CWSI tiene resolución de 15 minutos. El mismo evento queda registrado como:
"CWSI cruzó 0.55 a las 13:42, llegó a 0.78 a las 15:10, bajó a 0.32 a las 17:30."
Esa diferencia es relevante para floración (donde 4 horas > 0.60 causa aborto floral) y
para pre-cosecha (donde el RDI intencional requiere controlar exactamente cuánto tiempo
la planta estuvo bajo estrés).

```
Capacidad de detección de eventos intradiarios:
  MDS solo:    ×  (detecta que "el día fue estresante" — no cuándo)
  CWSI solo:   ✓  (detecta hora de inicio, pico, recuperación)
  CWSI+MDS:    ✓✓ (el CWSI ubica el evento; el MDS confirma si hubo daño acumulado)
```

**V2 — Validación cruzada: reduce falsas alarmas a < 5%**

Cada señal por sí sola tiene sus confounders específicos. La doble señal los cancela:

| Condición de campo | Solo CWSI | Solo MDS | CWSI+MDS |
|---|---|---|---|
| Viento fuerte (Zonda) | ❌ FALSA ALARMA — enfriamiento convectivo artificial baja la Tc → "sin estrés" cuando puede haberlo | ✓ MDS no afectado por viento | ✓ Sistema aplica 9 capas de mitigación: orientación a sotavento, tubo colimador IR, shelter SHT31, termopar de contacto, buffer con filtro de calma, compensación Tc_dry, y rampa gradual 4-18 m/s (14-65 km/h) que transfiere peso progresivamente al MDS. A ≥18 m/s (65 km/h): 100% MDS. |
| Suelo saturado + VPD extremo (calor súbito) | ✓ CWSI detecta estrés real (estomático, no hídrico) | ❌ FALSA TRANQUILIDAD — MDS bajo porque el suelo está húmedo, pero la planta puede estar en estrés por demanda | ✓ CWSI detecta el estrés estomático; MDS indica reserva hídrica disponible |
| Crecimiento activo (envero, brotación) | ✓ CWSI correcto | ❌ ARTEFACTO — MDS puede subir por expansión celular activa, no por estrés | ✓ CWSI calibra la interpretación del MDS durante estadios de expansión |
| Noche o día muy nublado | ❌ Sin señal (requiere gradiente térmico solar) | ✓ MDS operativo 24/7 | ✓ MDS cubre los períodos sin señal CWSI |
| Contaminación del lente (fumigación) | ❌ Sin señal por 24-48h | ✓ MDS no afectado | ✓ MDS como respaldo durante el blackout óptico |

**Tasa de falsas alarmas estimada:**
- CWSI solo en condiciones de Cuyo: 18-25% (días de Zonda + eventos de VPD extremo)
- MDS solo: 12-18% (artefactos de crecimiento activo + variación seasonal)
- CWSI+MDS (HSI): < 5% (los confounders de una señal son corregidos por la otra)

Fuente metodológica: Fernández & Cuevas 2010, Jones et al. 2002; la tasa para Cuyo es
estimación del equipo basada en la frecuencia de Zonda (15-30 días/temporada) y los
períodos de crecimiento activo en Malbec (brotación + envero ≈ 45-60 días/temporada).
Validación empírica prevista en TRL 4 (experimento H6 del Módulo 6 del plan de negocio).

**V3 — Discriminación del tipo de estrés: atmosférico vs. edáfico**

Esta es la ventaja más importante para la decisión de riego — y la menos obvia.

Escenario real frecuente en Cuyo (San Juan, verano):
- 14:00hs: T_aire = 42°C, VPD = 5.2 kPa, suelo bien hidratado (riego hace 48h)
- CWSI = 0.68 (estrés moderado-severo)
- MDS = bajo (el tronco está turgente — el suelo tiene agua)

**¿Qué hace el sistema de solo-MDS (Phytech)?** No genera alerta — el MDS está bien.

**¿Qué hace CWSI+MDS?** El sistema detecta el desacuerdo entre señales:
CWSI alto + MDS bajo = estrés atmosférico por VPD extremo, no déficit de suelo.
La decisión correcta: **NO regar** — el suelo tiene agua, la planta recuperará cuando
baje el VPD al atardecer. Regar en esas condiciones desperdicia agua y puede causar
golpe hídrico si el suelo ya estaba húmedo.

Un sistema de solo-MDS nunca detecta este evento. Un sistema de solo-CWSI genera una
alerta de riego que es incorrecta. Solo la combinación puede hacer la distinción.

**V4 — Dimensión espacial del canopeo**

El extensómetro mide un punto: el tronco de una planta. Si hay 30 plantas en el radio
de acción del nodo, el MDS refleja el estado de esa planta específica.

El MLX90640 captura una imagen de 32×24 = 768 píxeles. Dentro de esa imagen, el
segmentador identifica múltiples plantas, detecta zonas con temperatura diferencial, y
puede señalar que "la planta del extremo norte está 1.8°C más caliente que el promedio
del canopeo" — indicando estrés localizado antes de que el tronco instrumentado lo registre.

```
Cobertura espacial de señal:
  MDS:      1 punto (el árbol instrumentado)
  CWSI:     32×24 píxeles → múltiples plantas en el campo visual
  CWSI+MDS: punto de alta confianza + contexto espacial del canopeo
```

**V5 — Auto-calibración del baseline CWSI por el MDS**

Descrito en detalle en sección 4.2.3. En síntesis: sin el MDS, el baseline Tc_wet del
CWSI deriva silenciosamente durante la temporada. El evento de lluvia con MDS≈0 es el
único mecanismo que permite actualizar el baseline sin visita técnica. Sin MDS, el error
sistemático del CWSI crece hasta ±0.15-0.20 unidades al final de temporada. Con MDS,
el error se mantiene < ±0.07 unidades.

**Un sistema de CWSI solo no tiene este mecanismo de auto-calibración disponible.**
Requeriría visitas técnicas periódicas — exactamente el problema de Phytech.

---

#### 4.6.3 Desventajas del sistema dual vs. análisis de tallo solo — y su estado de cierre

La honestidad técnica requiere documentar las limitaciones reales. Cada una se analiza
junto a su estado de cierre: si es estructural (irreducible) o si tiene solución concreta.

**D1 — Mayor costo de hardware: +USD 47 por nodo (lote 1) → reducible a +USD 22 con escala**

| Componente extra vs. MDS solo | Costo lote 1 | Costo lote 500+ |
|---|---|---|
| MLX90640 breakout integrado (Adafruit 4407) | USD 50 | USD 18-22 (bare chip + PCB custom a escala) |
| Panel de referencia emisividad (PTFE + anodizado) | USD 6 | USD 2 (fabricación interna) |
| Carcasa óptica (protector lente IP54) | USD 5 | USD 0 (integrar al molde principal) |
| OpticalHealthMonitor + ISO_nodo | USD 0 (software) | USD 0 |
| **Costo adicional total** | **USD ~47** | **USD ~22** |

Impacto real: COGS USD 149 en lote 50 (arquitectura modular TRL4) → USD ~121 con volumen 500+ (arquitectura bare chip + PCB custom). Ver BOM-nodo-v1.md.
La comparación relevante no es "dual vs. solo-MDS" sino "USD 149 HydroVision dual vs.
USD 300-800 Phytech solo-MDS" — el dual cuesta 3-4× menos y entrega más señales.

**Estado: desventaja estructural en lote 1, reducida a +USD 22 a escala.
Acción de hardware pendiente → ver `lucas/hardware/`. Ver también tarea HW-01.**

---

**D2 — Mayor consumo de energía: −20% autonomía sin solar → eliminable con firmware**

El MLX90640 consume ~4-6 mW activo durante los 8 segundos de captura.
Con ciclos cada 15 minutos: 96 activaciones/día → ~22 µA equivalente promedio.

```
Deep sleep base (ESP32-S3 + MDS + LoRa):  ~8 µA  → ~13 meses
Con MLX90640 ciclo 15 min (96×/día):      ~22 µA  → ~13-14 meses
Con activación adaptativa (solo 06-18h):  ~14 µA  → ~17 meses  ← mejora firmware
Con panel solar 6W (ya incluido en BOM):   recarga >> consumo → autonomía ilimitada
```

El CWSI requiere gradiente solar activo — capturar fuera de la ventana 07:00-18:30 es
energía desperdiciada. Reducir las activaciones de 96/día a ~46/día (solo ventana solar)
recupera ~4 meses de autonomía y prácticamente elimina la desventaja.

**Estado: eliminable con firmware de activación adaptativa.
Acción de firmware pendiente → ver tarea HW-02 en `lucas/README.md`.**

---

**D3 — Mayor complejidad de calibración → ya resuelta por el propio sistema**

El sistema dual requiere calibrar CWSI (Tc_wet, Tc_dry, coeficientes ΔT_LL/ΔT_UL) y
MDS (baseline D_min, relación MDS→ψ_stem). Con solo-MDS, la calibración es un único
baseline dendrométrico.

Sin embargo, ambas calibraciones son automáticas desde el firmware:
- Tc_wet: auto-calibrado por eventos de lluvia con MDS≈0 (sección 4.2.3)
- Baseline MDS: auto-ajustado por comparación temporal entre ciclos en dormancia
- Parámetros iniciales: pipeline "simulación primero" (sección 4.3.1) para variedades nuevas

El productor no calibra nada. La complejidad es interna al sistema, invisible al usuario.

**Estado: no es una desventaja operativa — es complejidad de ingeniería ya encapsulada.**

---

**D4 — Dependencia del proveedor único MLX90640 (Melexis) → eliminable con rediseño PCB**

Sin diversificación de proveedor, una escasez de MLX90640 (como ocurrió en 2021-2023,
precio de USD 28 a USD 68) bloquea la producción. Con solo-MDS, los strain gauges y
ADC 24-bit tienen múltiples proveedores.

La solución es de ingeniería de PCB, no de arquitectura del sistema:
- **MLX90641** (Melexis, 16×12 px, paquete TO39 idéntico al MLX90640) — mismo fabricante,
  misma familia, menor resolución pero mismo footprint físico. Permite producir nodos
  con resolución reducida sin cambiar la PCB.
- **Heimann HMS-C11L** (Heimann Sensor GmbH, Alemania, 16×16 px) — fabricante independiente,
  footprint TO39 compatible. Diversifica el proveedor completamente.

Ambas alternativas requieren ajuste de firmware (resolución distinta, protocolo I2C
ligeramente diferente) pero la PCB física no cambia si el footprint se diseña correctamente.

**Estado: eliminable con diseño PCB dual-footprint en la primera versión de PCB.
Acción de hardware pendiente → ver tarea HW-03 en `lucas/README.md`.**

---

**D5 — Mayor complejidad de explicación para el cliente no técnico → no existe si se aplica la guía de ventas**

"El sistema mide la temperatura de las hojas Y la contracción del tronco y los fusiona con
IA" requiere 3 minutos adicionales en el pitch. Para un productor Tier 1-2, esos 3 minutos
generan confusión, no convicción.

La solución es de comunicación, no de ingeniería: el pitch comercial no menciona el
dual-signal. La propuesta de valor se comunica como resultado — "datos correctos en
cualquier condición meteorológica, incluyendo viento y fumigación". El funcionamiento
interno es documentación de soporte técnico, no argumento de venta.

**Estado: no existe como desventaja si se sigue la guía de ventas del Módulo 5 (doc-10).
No requiere acción de hardware ni firmware.**

---

**Resumen de estado de cierre:**

| Desventaja | Estado | Acción concreta |
|---|---|---|
| D1 +USD 47 COGS | Estructural en lote 1 — reducible a +USD 22 con escala | HW-01: panel PTFE interno + integrar carcasa óptica en molde + negociar precio Melexis a volumen |
| D2 −20% batería | Eliminable con firmware | HW-02: activación adaptativa MLX solo en ventana solar 07:00-18:30 |
| D3 Calibración dual | No existe operativamente — ya encapsulada | Ninguna |
| D4 Proveedor único | Eliminable con diseño PCB | HW-03: footprint dual MLX90640/MLX90641 + pad compatible Heimann HMS-C11L |
| D5 Pitch complejo | No existe si se sigue guía de ventas | Ninguna |

---

#### 4.6.4 Cuándo es suficiente el análisis de tallo solo

Para ser completamente justos: hay escenarios donde el MDS solo puede ser suficiente.

| Escenario | ¿Solo MDS es suficiente? | Razón |
|---|---|---|
| Zona sin Zonda (viento < 2 m/s promedio) | Parcialmente | Sin viento, la principal ventaja de dual (corrección por viento) desaparece. Pero V2, V3, V5 siguen aplicando. |
| Cultivo con baja variabilidad temporal de estrés (riego totalmente automatizado con caudal constante) | Parcialmente | Si el riego ya es preciso y el suelo es homogéneo, el CWSI aporta menos información adicional. |
| Productor que solo quiere saber "¿regué bien ayer?" | Sí | Pregunta retrospectiva → el MDS del día siguiente responde. El CWSI no aporta información adicional para esa pregunta específica. |
| Etapa TRL 3-4 con recursos muy limitados (no puede permitirse el MLX90640) | Técnicamente sí | En una versión MVP de emergencia, el MDS solo permite validar la señal fisiológica. Pero pierde las ventajas V1-V5 y el producto sería inferior a la propuesta actual. |

**Conclusión de cuándo es suficiente:** el MDS solo es suficiente para un sistema de
monitoreo básico en condiciones ideales (sin viento, suelo homogéneo, riego ya preciso).
HydroVision opera en Cuyo, donde el Zonda ocurre 15-30 días/temporada, el suelo es
heterogéneo (texturas cambiantes por variación lateral), y la decisión de riego no es
trivial. En esas condiciones, el sistema dual es la arquitectura correcta.

---

#### 4.6.5 Tabla resumen — CWSI+MDS vs. MDS solo vs. CWSI solo

| Dimensión | CWSI+MDS (HydroVision HSI) | MDS solo (Phytech) | CWSI solo |
|---|:---:|:---:|:---:|
| Resolución temporal | ✓✓ 15 min (CWSI) + diario (MDS) | △ 1 valor/día | ✓ 15 min |
| Funcionamiento nocturno | ✓ MDS activo | ✓ MDS activo | ❌ Sin señal |
| Resistencia al viento (Zonda) | ✓✓ MDS corrige CWSI | ✓ No afectado | ❌ Error sistemático |
| Detección de fumigación blackout | ✓ MDS como respaldo | ✓ No afectado | ❌ Sin señal 24-48h |
| Tasa de falsas alarmas (Cuyo) | ✓✓ < 5% | △ 12-18% | △ 18-25% |
| Discriminación estrés atmosférico vs. edáfico | ✓✓ Solo posible con ambas | ❌ Invisible | △ Parcial (sin información de suelo) |
| Cobertura espacial del canopeo | ✓✓ 768 píxeles | ❌ 1 punto | ✓✓ 768 píxeles |
| Auto-calibración de baseline | ✓✓ MDS ancla el Tc_wet | △ Solo baseline dendrométrico | ❌ Sin mecanismo |
| Costo de hardware (COGS) | △ USD 149 | △ USD 75-90* | △ USD 90-95* |
| Complejidad de calibración | △ Alta | ✓ Media | △ Alta |
| Autonomía de batería sin solar | △ 13-14 meses | ✓✓ 18+ meses | △ 13-14 meses |
| Riesgo de proveedor | △ MLX90640 single-source | ✓ Múltiples proveedores | △ MLX90640 single-source |
| **Score total (✓✓=2, ✓=1, △=0, ❌=-1)** | **+16** | **+3** | **+4** |

*COGS estimado para versión hipotética HydroVision con sensor único.
Phytech precio de venta USD 300-800 por sensor; COGS propio desconocido.

**El sistema dual HSI tiene una ventaja de +13 puntos sobre solo-MDS** en las dimensiones
que más importan para la condición operativa real de Cuyo. Ese diferencial justifica
completamente la complejidad de hardware y calibración adicional.

---

#### 4.6.6 Implicación para el pitch competitivo frente a Phytech

El argumento técnico correcto cuando se compara con Phytech no es "somos más baratos"
(aunque es verdad). Es:

> "Phytech mide el tronco. Sabe si la planta estuvo estresada ayer. No sabe si el estrés
> ocurrió a las 13:00 o a las 17:00, ni si fue porque no había agua en el suelo o porque
> hubo un pico de VPD de 5.8 kPa que ningún riego puede resolver. En un día de Zonda en
> San Juan, el tronco de Phytech te va a decir que estuvo estresado. HydroVision te va a
> decir que el MDS fue alto porque el Zonda secó el aire — y que regar ese día habría sido
> un desperdicio. Esa diferencia es la que vale el sistema."

Y para el productor que ya tiene Phytech (win-back):

> "¿Cuántas visitas técnicas de recalibración pagaste el año pasado? ¿A cuánto te salió
> cada una? El sistema de HydroVision se auto-calibra con cada lluvia, sin técnico.
> En 3 años, eso paga la diferencia de precio."

---

## 5. Equipo de Trabajo
