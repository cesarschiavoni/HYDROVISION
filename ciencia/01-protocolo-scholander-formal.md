
# PROTOCOLO EXPERIMENTAL DE MEDICIÓN DE POTENCIAL HÍDRICO DE TALLO (Ψ_stem) MEDIANTE BOMBA DE PRESIÓN (MÉTODO SCHOLANDER) EN VIÑEDO EXPERIMENTAL
## HydroVision AG — Convocatoria STARTUP 2025 TRL 3-4 — ANPCyT/FONARSEC

**Elaborado por:** Dra. Mariela Inés Monteoliva  
**Filiación:** Investigadora Adjunta CONICET — IFRGV-UDEA, INTA CIAP, CCT Córdoba  
**Especialidad:** Fisiología vegetal bajo estrés abiótico — Relaciones hídricas en cultivos  
**Publicación de referencia:** Espinosa Herlein, M.A.; Monteoliva, M.I. (2025). Estado hídrico. En: *Abordajes fisiológicos para el estudio del estrés abiótico en cultivos*. Editorial UCC, Córdoba.  
**Viñedo experimental:** Predio familiar Schiavoni, Colonia Caroya, Córdoba (31°12' S, 64°05' O, ~700 m s.n.m.)  
**Cultivo:** *Vitis vinifera* L. cv. Malbec en espaldera — 1/3 ha — 10 filas de 136 m (1.360 vides): filas 1–5 de calibración (5 regímenes hídricos) + filas 6–10 de producción (100% ETc)  
**Versión:** 1.0 — Abril 2026

---

## 1. FUNDAMENTO CIENTÍFICO

### 1.1 El potencial hídrico de tallo como variable central

El potencial hídrico de tallo (Ψ_stem, en MPa) es el indicador fisiológico más robusto y de mayor aceptación científica para cuantificar el estado hídrico interno de la planta. A diferencia de los sensores de humedad de suelo —que informan sobre la disponibilidad de agua en el perfil edáfico—, el Ψ_stem refleja directamente la demanda hídrica real de los tejidos conductores (xilema), integrando simultáneamente la oferta del suelo, la demanda evaporativa de la atmósfera y la resistencia hidráulica de la propia planta.

En vid (*Vitis vinifera* L.), el Ψ_stem medido al mediodía solar en hojas adultas sin sombra, previamente ocluidas, correlaciona con la tasa de fotosíntesis neta, la conductancia estomática, la elongación de brotes y la calidad de la baya (acumulación de antocianinas, síntesis de terpenos, concentración de azúcares) con coeficientes de correlación reportados de R² = 0.62–0.82 en distintos trabajos de campo en regiones semiáridas (Schultz 2003, Chaves et al. 2010, Pires et al. 2025).

El método Scholander (bomba de presión, Scholander et al. 1965) es el procedimiento estándar en fisiología vegetal para la determinación directa del Ψ_stem. Su validez y reproducibilidad están ampliamente documentadas en la literatura vitivinícola y en manuales de referencia de INIA Chile, CONICET y el USDA-ARS.

### 1.2 Relación entre Ψ_stem y el CWSI termográfico

El Índice de Estrés Hídrico del Cultivo (CWSI) calculado a partir de termografía infrarroja (Jackson et al. 1981) estima indirectamente el estado hídrico de la planta a través de su temperatura foliar. La hipótesis central es: **cuando la planta cierra sus estomas por déficit hídrico, disminuye la transpiración y aumenta la temperatura foliar por encima de la temperatura del aire** más allá de lo esperado bajo condiciones de balance energético foliar sin estrés.

La correlación directa Ψ_stem ↔ CWSI establece la función de calibración que permite al sistema HydroVision AG:
1. Usar el CWSI termográfico como proxy en tiempo real del Ψ_stem
2. Expresar los resultados en unidades fisiológicamente interpretables por el agrónomo
3. Definir umbrales de alerta calibrados para Malbec en las condiciones edafoclimáticas de Colonia Caroya / Cuyo

La correlación CWSI–Ψ_stem reportada en vid oscila entre R² = 0.49–0.67 para sistemas de termografía aérea (Araújo-Paredes et al. 2022, Pires et al. 2025). El sistema HydroVision AG busca superar ese rango mediante la fusión HSI (CWSI + MDS dendrométrico), alcanzando R² estimado de 0.90–0.95, consistente con los valores combinados reportados por Fernández & Cuevas (2010) para extensometría de tronco.

---

## 2. DISEÑO EXPERIMENTAL

### 2.1 Viñedo experimental — Régimen de Riego Deficitario (RDI)

El protocolo aplica el paradigma de Riego Deficitario Regulado (RDI, Regulated Deficit Irrigation) documentado en la literatura vitivinícola argentina y chilena para la obtención de datos de entrenamiento del modelo IA con gradiente completo de estrés.

El viñedo experimental tiene 10 filas de 136 m (1.360 vides, espaciado 1 m entre plantas, 3 m entre filas), dividido en dos zonas contiguas con funciones complementarias:

- **Zona de calibración (filas 1–5):** 5 regímenes hídricos controlados por solenoides independientes Rain Bird 24 VAC (1 solenoide por fila). Cada fila recibe un **único régimen hídrico** (la fila entera se riega igual). Los regímenes se ordenan con el estrés máximo en el extremo (fila 1) y el control pleno en la fila 5, que actúa como transición natural hacia la zona de producción.
- **Zona de producción (filas 6–10):** 5 filas a 100% ETc (riego normal) con nodos configurados en **modo producción** — ejecutando el pipeline comercial completo (CWSI → HSI → alerta → recomendación de riego) de forma autónoma, exactamente como lo haría un productor real.

| Fila | Régimen | ETc aplicada | Zona | Rango CWSI esperado | Función |
|---|---|---|---|---|---|
| 1 | Sin riego | 0% ETc | Calibración | 0.85–1.00 | Estrés máximo — límite del sistema |
| 2 | RDI severo | 15% ETc | Calibración | 0.65–0.85 | Zona de impacto productivo |
| 3 | RDI moderado | 40% ETc | Calibración | 0.45–0.60 | Umbral de alerta agronómica |
| 4 | RDI leve | 65% ETc | Calibración | 0.25–0.40 | Estrés incipiente — máxima sensibilidad del sistema |
| 5 | Control pleno | 100% ETc | Calibración | 0.05–0.20 | Referencia — línea base sin estrés. Transición natural hacia zona de producción |
| 6–10 | Riego normal | 100% ETc | Producción | 0.05–0.20 | Validación del producto final — nodos en modo comercial autónomo |

**Diseño del gradiente:** el gradiente de estrés decreciente (fila 1 → fila 5) minimiza el riesgo de contaminación hídrica lateral entre la zona de calibración y la zona de producción. La fila 5 (100% ETc) comparte el mismo régimen que las filas 6–10, eliminando cualquier efecto de borde entre zonas. El riego por goteo localizado (cinta drip) limita la migración lateral de agua entre filas adyacentes dentro de la zona de calibración.

El gradiente de 5 niveles en la zona de calibración permite obtener pares calibrados (Ψ_stem, CWSI) que cubren el rango operativo completo del sistema en una sola sesión de medición. Cada fila de calibración lleva un nodo permanente (planta central ~68) que monitorea un régimen hídrico uniforme, eliminando variabilidad intra-fila.

**Validación dual — calibración científica + producto final en el mismo viñedo:**

La zona de producción (filas 6–10) opera como banco de prueba del producto comercial. Los 5 nodos de producción ejecutan el pipeline completo de forma autónoma bajo riego normal (100% ETc). Esto permite:

1. **Validación cruzada directa:** los nodos de producción generan recomendaciones de riego que se contrastan con el Ψ_stem medido en la zona de calibración adyacente (fila 5 al mismo régimen 100% ETc). El nodo de producción dice "CWSI = 0.12, sin estrés"; la fila 5 de calibración (con Scholander) confirma cuantitativamente esa lectura.
2. **Reproducibilidad del sistema:** 5 nodos idénticos bajo las mismas condiciones (100% ETc) demuestran la consistencia del producto — las lecturas de los 5 nodos deben concordar (CV < 10%), evidencia directa de que el prototipo es reproducible y escalable.
3. **Demostración de producto para TRL 4:** los nodos de producción generan alertas, dashboards y recomendaciones reales durante toda la campaña, sin intervención humana — evidencia directa del TRL 4 ("prototipo escalable, con ventajas competitivas medibles").
4. **Separación limpia de datos:** los nodos de calibración (filas 1–5) generan el dataset científico (800 frames + Scholander); los nodos de producción (filas 6–10) generan datos de validación operativa independientes, con `node_id` separados.

### 2.2 Varietal y fenología del viñedo experimental

**Cultivo:** *Vitis vinifera* L. cv. Malbec  
**Sistema de conducción:** Espaldera doble con carga de poda de 8–12 yemas por planta  
**Marco de plantación:** 3,0 m entre filas × 1,0 m entre plantas  
**Portainjerto:** No especificado (planta propia en suelo franco-limoso)  
**Altitud:** ~700 m s.n.m. — precipitación media anual ~700 mm concentrada en verano (Nov–Mar)  
**Temperatura media anual:** 17°C — amplitud térmica diaria en verano: 12–18°C  
**VPD típico en ventana de medición (10–14 hs, Dic–Feb):** 1.8–4.5 kPa

**Estadios fenológicos relevantes y sus efectos sobre la respuesta hídrica del Malbec:**

| Estadio | GDD acumulados (T_base 10°C) | Período calendario | Sensibilidad al déficit hídrico |
|---|---|---|---|
| Brotación (E-C Baggiolini) | 80–120 GDD (desde 1-ago) | Sep–Oct | Moderada — déficit en brotación puede reducir número de brotes |
| Floración (F) | 280–420 GDD | Oct–Nov | **Crítica** — déficit severo causa corrimiento y millerandage con pérdida de cuaje irreversible |
| Cuaje y desarrollo de baya (G–H) | 420–800 GDD | Nov–Dic | Alta — fase de mayor sensibilidad al déficit post-antesis |
| Envero (I) | 1.100–1.350 GDD | Ene–Feb | Moderada en inicio — el RDI post-envero concentra azúcares y antocianinas (estrategia enológica) |
| Maduración (J) | 1.350–1.900 GDD | Feb–Mar | Estratégica — RDI moderado mejora calidad; déficit severo detiene maduración |
| Pre-cosecha (K) | >1.700 GDD | Mar | Cualquier riego en esta fase diluye mostos — suspender |

**Temperatura base Malbec:** T_base = 10°C (referencia INTA, Catania & Avagnina 2007)

### 2.3 Umbrales Ψ_stem de referencia para Malbec

Los siguientes umbrales se utilizan tanto para la definición de los regímenes hídricos experimentales como para la calibración de los umbrales CWSI del sistema HydroVision AG. Se adoptarán como referencia los valores de la literatura para vid cv. Malbec en Argentina y se ajustarán mediante el protocolo de campo:

| Estado hídrico | Ψ_stem (MPa) al mediodía | CWSI equivalente estimado | Acción recomendada |
|---|---|---|---|
| Sin estrés | > −0.8 MPa | 0.0–0.20 | Mantener régimen actual |
| Estrés leve | −0.8 a −1.0 MPa | 0.20–0.35 | Verificar pluviómetro — posible riego en 24–48 h |
| Estrés moderado | −1.0 a −1.3 MPa | 0.35–0.60 | Riego en el próximo turno programado (HydroVision alerta activo) |
| Estrés severo | −1.3 a −1.5 MPa | 0.60–0.80 | **Riego inmediato** — riesgo de daño fisiológico |
| Estrés crítico | < −1.5 MPa | > 0.80 | **Protocolo de rescate** — riego de emergencia — notificar a Monteoliva |
| Daño irreversible | < −2.0 MPa | — | Embolia xilemática documentada en Malbec (Schultz 2003) — evitar en todo caso |

**Umbral de rescate del protocolo:** Ψ_stem < −1.5 MPa en cualquier planta de fila 2 (15% ETc) o fila 1 (0% ETc) activa el protocolo de riego de emergencia automático. Este umbral tiene un margen de seguridad de 0.5 MPa sobre el umbral de daño irreversible documentado para Malbec en condiciones de Cuyo y Córdoba.

---

## 3. PROTOCOLO DE MEDICIÓN — PASO A PASO

### 3.1 Equipo y materiales

| Ítem | Especificación | Verificación previa |
|---|---|---|
| Bomba de presión Scholander | Cámara de presión tipo PMS Instruments mod. 1005, Soil Moisture o equivalente | Sello de goma íntegro, manómetro calibrado (± 0.02 MPa), válvula de purga operativa |
| Cilindro de N₂ | Gas nitrógeno comprimido ≥ 99.5% pureza, válvula reguladora de presión | Presión ≥ 50 bar antes de cada sesión. Con presión < 50 bar, no iniciar sesión |
| Lupa de campo | Aumento 10× | Lente limpio |
| Tijera de podar | Hoja de acero inox, afilada | Limpiar con algodón con alcohol 70% entre plantas |
| Bolsas plásticas zip | Cierre hermético, capacidad 15 × 10 cm | Verificar que cierran sin fuga antes de llevar a campo |
| Planilla de campo | Impresa o digital con celdas: fecha, hora, zona, vid ID, Ψ_stem, observaciones | Completar encabezado antes de salir |
| Reloj (celular o reloj) | Segundero visible | Sincronizado con la app del dashboard (±1 min) |
| Linterna | — | Baterías cargadas |

### 3.2 Condiciones ambientales de validez del protocolo

La medición de Ψ_stem de tallo para calibración del CWSI solo es válida bajo las siguientes condiciones. **Si alguna condición no se cumple, la sesión debe cancelarse o posponerse:**

**Condiciones de lluvia (pluviómetro automático del nodo, verificar en app):**
- < 5 mm en las últimas 48 h: sin restricción
- 5–10 mm en las últimas 48 h: procede si T° media post-lluvia > 30°C (suelo drenado); caso contrario, esperar 48 h completas
- > 10 mm en las últimas 48 h: reprogramar mínimo +48 h
- > 20 mm en las últimas 48 h: reprogramar mínimo +72 h (adaptado a suelo franco-limoso de Colonia Caroya con ETP alta)

*Fundamento: la lluvia reciente reequilibra el Ψ_stem de todas las zonas hacia valores cercanos a cero, eliminando el gradiente hídrico artificial sobre el que se calibra el sistema. Una medición post-lluvia entregaría todos los valores de Ψ_stem concentrados en el rango −0.2 a −0.5 MPa independientemente del régimen de riego asignado, generando un dataset de calibración sin variación útil.*

**Condiciones meteorológicas durante la ventana de medición:**
- Viento < 20 km/h sostenido (verificar en app del nodo)
- Temperatura ambiente < 38°C a las 9:30 hs de inicio
- Nubosidad < 70% durante los 30 min previos a cada lectura Scholander (nubosidad densa altera VPD y la temperatura foliar puede descender 1–2°C en minutos, afectando la correlación CWSI–Ψ_stem de ese frame)

**Condición de estabilización del potencial hídrico de tallo:**  
La medición debe realizarse **estrictamente entre las 10:00 y las 13:00 horas solares** (no horario oficial en verano argentino = 09:00–12:00 UTC−3). Fuera de ese rango, el Ψ_stem de tallo no ha alcanzado el equilibrio del mediodía solar y los valores no son comparables entre sesiones ni con los frames térmicos del nodo (que capturan el período de máximo estrés diurno).

*Fundamento: el potencial hídrico de tallo medido al mediodía solar (ψ_stem,md) en hojas ocluidas representa el estado de equilibrio hídrico del xilema, integrando la demanda de la totalidad de la planta. Es la referencia fisiológica estándar en viticultura de precisión (Scholander et al. 1965, Naor 2000, Fernández & Cuevas 2010). Mediciones fuera de la ventana del mediodía pueden diferir hasta 0.4 MPa del valor de equilibrio.*

### 3.3 Protocolo de medición por planta — secuencia operativa

**Selección de la hoja para la medición:**

La hoja para Ψ_stem debe cumplir todos los criterios siguientes:
- Hoja adulta completamente expandida, sin daño físico ni síntomas de enfermedad
- Ubicada en la parte media del dosel (evitar hojas terminales y basales extremas)
- Expuesta a radiación solar directa o semisombra durante al menos 30 min previos al corte (no hoja sombreada profunda — su Ψ no refleja el estado hídrico del tallo)
- Misma vid de referencia en cada sesión: vid de la posición central de cada fila de calibración (~planta 68 de cada fila, marcada con estaca numerada desde la Semana 2 de instalación)

**Procedimiento paso a paso:**

**Paso 1 — Oclusión previa (15–30 min antes de cada lectura):**  
No aplica para Ψ_stem de tallo en este protocolo. La hoja se corta directamente sin oclusión previa. *Nota: la oclusión previa es necesaria para Ψ_hoja; para Ψ_stem se requiere hoja sin ocluir cortada rápidamente.*

**Paso 2 — Corte de la hoja:**  
Con la tijera limpia, cortar el pecíolo de la hoja seleccionada con un movimiento único y limpio (no secciones sucesivas). El corte debe realizarse a 5–8 mm de la inserción con el raquis. Inmediatamente — en menos de 5 segundos — introducir el pecíolo cortado en la bolsa plástica zip y cerrarla. No exponer el corte al aire.

*Fundamento: la exposición del corte al aire inicia inmediatamente el proceso de cavitación del xilema, que cierra los vasos conductores y genera lecturas artificialmente más negativas. La bolsa plástica mantiene la atmósfera saturada de vapor y detiene ese proceso.*

**Paso 3 — Introducción en la cámara:**  
Abrir la cámara de presión. Extraer la hoja de la bolsa e introducirla con el pecíolo atravesando el orificio central del sello de goma, cuidando que el pecíolo quede centrado y que la lámina foliar quede dentro de la cámara. Cerrar la tapa del sello apretando hasta que quede hermético — verificar que el pecíolo no queda aplastado ni doblado.

**Paso 4 — Presurización controlada:**  
Abrir lentamente la válvula del cilindro de N₂ a una tasa de presurización de **no más de 0.02–0.03 MPa por segundo** (equivalente aproximadamente a 1 vuelta completa del regulador de caudal en ~10 segundos). Aplicar presión continua y uniformemente creciente.

*Fundamento: una presurización rápida puede generar burbujas en el xilema o desplazar la savia por efectos hidrodinámicos antes de que aparezca en el extremo del corte, produciendo una sobreestimación del Ψ (valor menos negativo de lo real).*

**Paso 5 — Detección del punto final:**  
Con la lupa 10× apuntada al extremo cortado del pecíolo, observar el corte en posición de buena iluminación (natural o con linterna). El punto final se define como **la primera aparición de savia brillante o el humedecimiento visible del corte** (no la aparición de gotas de gran tamaño — la primera señal de humedad es el punto correcto). Cerrar la válvula del N₂ de inmediato en ese instante.

*Fundamento: el "punto de la gota" (aparición de savia presionada por el gas) marca el momento en que la presión aplicada equilibra exactamente la tensión negativa que el xilema ejercía sobre la columna de agua — ese es el Ψ_stem. Si se continúa presionando más allá, se obtiene un valor artificialmente menos negativo. Si se para antes, el valor es artificialmente más negativo. La precisión del operador en este paso define directamente la precisión del dato.*

**Paso 6 — Lectura y registro:**  
Leer el manómetro con el eje visual perpendicular al dial (evitar error de paralaje). Anotar inmediatamente en la planilla:
- Fila de calibración (1 = 0% ETc / 2 = 15% / 3 = 40% / 4 = 65% / 5 = 100% ETc)
- Número de vid (ej. F1-046)
- Hora exacta (HH:MM)
- Valor de Ψ_stem en MPa (convertir si el manómetro está en bar: 1 bar = 0.1 MPa; si está en PSI: 1 PSI = 0.00689 MPa)
- El valor es **siempre negativo**: ej. "−0.85 MPa" o "−8.5 bar"
- Observaciones: condiciones anómalas, señales de enfermedad en la hoja, presencia de goteo previo al punto final, etc.

**Paso 7 — Liberación de presión y limpieza:**  
Abrir la válvula de purga lentamente para despresurizar. Abrir la cámara, retirar la hoja. Limpiar el sello de goma con paño húmedo. Limpiar la tijera con algodón + alcohol 70% antes de la siguiente medición (evitar transmisión de patógenos entre plantas).

**Paso 8 — Respaldo fotográfico:**  
Fotografiar cada hoja medida junto a la planilla con el valor anotado visible. Compartir inmediatamente a la carpeta del proyecto en Google Drive (carpeta "Sesión #N — Fotos Scholander").

### 3.4 Secuencia de medición por sesión

Medir en orden: Fila 5 → Fila 4 → Fila 3 → Fila 2 → Fila 1 (de menor a mayor estrés). Siempre las mismas vides de referencia (plantas 28 y 68 de cada fila):

| Fila | Tratamiento | Plantas ref. | Ventana horaria |
|---|---|---|---|
| 5 (100% ETc — control) | Sin estrés | F5-028, F5-068 | 10:00–10:20 |
| 4 (65% ETc) | RDI leve | F4-028, F4-068 | 10:25–10:45 |
| 3 (40% ETc) | RDI moderado | F3-028, F3-068 | 10:50–11:10 |
| 2 (15% ETc) | RDI severo | F2-028, F2-068 | 11:15–11:35 |
| 1 (0% ETc — secano) | Estrés máximo | F1-028, F1-068 | 11:40–12:00 |

Si el cronograma se desfasa por más de 20 minutos, anotar la hora real de cada medición con precisión de ±2 min — los frames térmicos del nodo se sincronizarán con la hora exacta del dato Scholander en el procesamiento posterior.

### 3.5 Protocolo de rescate hídrico — criterios obligatorios

El diseño experimental induce estrés hídrico severo en las filas 2 (15% ETc) y 1 (0% ETc, secano). Para garantizar la integridad del viñedo experimental durante los 9 meses del protocolo, se establecen los siguientes criterios de rescate de aplicación obligatoria e inmediata:

**Criterio 1 — Ψ_stem crítico:**  
Ψ_stem < −1.5 MPa medido en cualquier planta de fila 2 o fila 1 → activar riego de emergencia en esa fila en las siguientes 2 horas. Notificar a Monteoliva y Schiavoni por WhatsApp con el valor y la hora.

**Criterio 2 — Temperatura foliar extrema:**  
Temperatura foliar > 42°C sostenida > 30 min en condiciones de VPD normal (verificar en dashboard del nodo) → riego de emergencia inmediato en la fila afectada.

**Criterio 3 — Plazo máximo sin agua:**  
14 días consecutivos sin precipitación ni riego en fila 1 (0% ETc) durante Diciembre–Febrero → riego de recuperación mínimo de 24 h antes de continuar el protocolo, independientemente del Ψ_stem medido.

**Restricción permanente — Fila 1 (0% ETc) en floración:**  
La fila 1 (0% ETc, secano) **no aplica régimen sin riego durante el estadio de floración** (GDD 280–420 para Malbec, aprox. Oct–Nov). El aborto floral por estrés severo en floración es irreversible para esa temporada. Durante la floración, la fila 1 recibe 15% ETc (mismo régimen que la fila 2 en condiciones normales).

**Rotación de filas de estrés entre temporadas:**  
Las filas 1 y 2 (estrés severo) rotan entre distintas filas del viñedo en temporadas sucesivas para que ninguna línea de plantas acumule daño permanente por la repetición del protocolo.

---

## 4. PLANILLA DE REGISTRO — MODELO

```
PLANILLA SESIÓN SCHOLANDER — HydroVision AG
Fecha: ___/___/2026    Sesión #: ___    Hora inicio: ___:___    Operador: ___________________

CONDICIONES PREVIAS:
  Lluvia últimas 48h: ___ mm (app nodo)    Viento al inicio: ___ km/h    T° ambiente 9:30hs: ___°C
  D_max registrado anoche (extensómetros):  F5=___µm  F4=___µm  F3=___µm  F2=___µm  F1=___µm
  Observaciones condición previa: __________________________________________________

LECTURAS TENSIÓMETROS (8:45hs):
  Fila 5: ___ cb    F4: ___ cb    F3: ___ cb    F2: ___ cb    F1: ___ cb

MEDICIONES Ψ_stem (10:00–13:00hs):
  ┌────────────────────────┬─────────────┬──────────┬────────────────┬──────────────────────────────────┐
  │ Fila / Régimen         │ Vid (F-N°)  │ Hora     │ Ψ_stem (MPa)   │ Observaciones                    │
  ├────────────────────────┼─────────────┼──────────┼────────────────┼──────────────────────────────────┤
  │ Fila 5 (100% ETc)      │ F5-068      │ ___:___  │ −___.___ MPa   │                                  │
  │ Fila 4 (65% ETc)       │ F4-068      │ ___:___  │ −___.___ MPa   │                                  │
  │ Fila 3 (40% ETc)       │ F3-068      │ ___:___  │ −___.___ MPa   │                                  │
  │ Fila 2 (15% ETc)       │ F2-068      │ ___:___  │ −___.___ MPa   │ ¿>−1.5?: RESCATE ___ □           │
  │ Fila 1 (0% ETc)        │ F1-068      │ ___:___  │ −___.___ MPa   │ ¿>−1.5?: RESCATE ___ □           │
  └────────────────────────┴─────────────┴──────────┴────────────────┴──────────────────────────────────┘

LECTURAS TENSIÓMETROS (12:00hs):
  Fila 5: ___ cb    F4: ___ cb    F3: ___ cb    F2: ___ cb    F1: ___ cb

D_min del día (16:00hs — leer en app):
  F5=___µm    F4=___µm    F3=___µm    F2=___µm    F1=___µm
  MDS calculado:  F5=___µm  F4=___µm  F3=___µm  F2=___µm  F1=___µm

LECTURAS TENSIÓMETROS (16:00hs):
  Fila 5: ___ cb    F4: ___ cb    F3: ___ cb    F2: ___ cb    F1: ___ cb

CIERRE:
  Fotos subidas a Drive: SÍ □ / NO □ (motivo: _______________)
  Notificación a César y Monteoliva enviada: SÍ □ / NO □
  Incidencias: ________________________________________________________________
  Firma operador: ____________________________
```

---

## 5. CRONOGRAMA DE SESIONES

Se planifican **4 sesiones Scholander optimizadas** según el criterio de Diseño Óptimo de Experimentos (D-Optimal Design, Kiefer 1959), maximizando la cobertura del gradiente fenológico con el mínimo de visitas de campo especializadas:

| Sesión | Estadio fenológico objetivo | Período estimado | Condición de VPD objetivo | Responsable medición |
|---|---|---|---|---|
| **1 — Post-brotación** | 4–6 hojas desarrolladas (GDD 150–200) | Sep–Oct 2026 | VPD < 1.5 kPa (mañana fresca) | Dra. Monteoliva en persona |
| **2 — Pre-envero** | Envero incipiente (GDD 1.000–1.100) | Ene 2027 | VPD > 2.0 kPa (mediodía verano) | Dra. Monteoliva en persona |
| **3 — Post-envero** | Maduración inicial (GDD 1.200–1.400) | Feb 2027 | VPD variable | Javier Schiavoni (capacitado por Monteoliva) |
| **4 — Pre-cosecha** | 2–3 semanas antes cosecha (GDD >1.600) | Mar 2027 | VPD moderado | Javier Schiavoni |

**Sesiones 1 y 2:** La Dra. Monteoliva participa en persona. En la Sesión 1 se realiza la calibración inicial de todos los dendrómetros de tronco y se capacita a Javier Schiavoni en el manejo de la bomba de presión para las sesiones 3 y 4.

**Sesiones 3 y 4:** Ejecutadas por Javier Schiavoni bajo supervisión remota (WhatsApp + foto de cada lectura). Monteoliva revisa las planillas y aprueba los datos antes de cargarlos en el sistema.

---

## 6. CRITERIOS DE CALIDAD DE DATOS

Un par calibrado (Ψ_stem, CWSI) es **válido** para entrenamiento del modelo si cumple:

1. Hora de medición Scholander: entre 10:00 y 13:00 hs solar
2. Lluvia en 48 h previas: < 5 mm (o < 10 mm con T° > 30°C)
3. Viento en el momento de captura del frame LWIR: < 20 km/h
4. El frame LWIR asociado fue capturado dentro de los 15 min anteriores o posteriores a la lectura Scholander
5. No hubo lluvia, fumigación ni PM2.5 > 200 µg/m³ durante las 3 h previas al frame (flag de invalidación automático del nodo)
6. La presurización Scholander fue a tasa ≤ 0.03 MPa/s (registrar si hubo anomalía)
7. El sello de la cámara era íntegro (sin fuga audible)
8. La tijera fue limpiada con alcohol entre plantas

Pares que no cumplan todos los criterios serán marcados como "datos de baja confianza" en la planilla y excluidos del dataset de entrenamiento primario, aunque podrán usarse como datos de validación secundaria.

**Target de dataset al cierre del proyecto:**
- ≥ 800 frames térmicos etiquetados con Ψ_stem (captura continua 24/7 del nodo + 4 sesiones Scholander = ~50 pares directos + estimación vía MDS dendrométrico continuo)
- ≥ 120 frames de validación independiente (fuera del período de entrenamiento)
- Cobertura del rango completo: al menos 15 pares por zona hídrica (A–E) a lo largo de la temporada

---

## 7. REFERENCIAS CIENTÍFICAS DEL PROTOCOLO

Scholander, P.F., Hammel, H.T., Bradstreet, E.D., Hemmingsen, E.A. (1965). Sap pressure in vascular plants. *Science*, 148(3668), 339–346.

Naor, A. (2000). Midday stem water potential as a plant water stress indicator for irrigation scheduling in fruit trees. *Acta Horticulturae*, 537, 447–454.

Jackson, R.D., Idso, S.B., Reginato, R.J., Pinter, P.J. (1981). Canopy temperature as a crop water stress indicator. *Water Resources Research*, 17(4), 1133–1138.

Fernández, J.E., Cuevas, M.V. (2010). Irrigation scheduling from stem diameter variations: a review. *Agricultural and Forest Meteorology*, 150, 135–151.

Schultz, H.R. (2003). Differences in hydraulic architecture account for near-isohydric and anisohydric behaviour of two field-grown *Vitis vinifera* L. cultivars during drought. *Plant, Cell & Environment*, 26(8), 1393–1405.

Chaves, M.M., Zarrouk, O., Francisco, R., Costa, J.M., Santos, T., Regalado, A.P., Rodrigues, M.L., Lopes, C.M. (2010). Grapevine under deficit irrigation: hints from physiological and molecular data. *Annals of Botany*, 105(5), 661–676.

Araújo-Paredes, C., Portela, F., Mendes, S., Valín, M.I. (2022). Using Aerial Thermal Imagery to Evaluate Water Status in *Vitis vinifera* cv. Loureiro. *Sensors*, 22, 8056.

Pires, A., Bernardino, A., Victorino, G., Costa, J.M., Lopes, C.M., Santos-Victor, J. (2025). Scalable thermal imaging and processing framework for water status monitoring in vineyards. *Computers and Electronics in Agriculture*, 239, 110931.

Espinosa Herlein, M.A.; Monteoliva, M.I. (2025). Estado hídrico. En: *Abordajes fisiológicos para el estudio del estrés abiótico en cultivos*. Editorial UCC, Córdoba.

Catania, C.D., Avagnina, S. (2007). La interpretación sensorial del vino. *Curso superior de degustación de vinos*. INTA EEA Mendoza.

---

*Protocolo elaborado por la Dra. Mariela Inés Monteoliva en el marco de su participación como asesora científica del proyecto HydroVision AG. El protocolo está basado en metodología estándar internacional adaptada a las condiciones edafoclimáticas del viñedo experimental de Colonia Caroya, Córdoba, Argentina.*

**Dra. Mariela Inés Monteoliva**  
Investigadora Adjunta CONICET — IFRGV-UDEA, INTA CIAP, CCT Córdoba  
Colonia Caroya, Córdoba — Abril 2026
