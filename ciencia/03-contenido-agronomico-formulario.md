
# CONTENIDO AGRONÓMICO PARA EL FORMULARIO ANPCyT
## Secciones redactadas desde la perspectiva de la Dra. Mariela Inés Monteoliva
## HydroVision AG — Convocatoria STARTUP 2025 TRL 3-4

*Este documento contiene los textos agronómicos que deben incorporarse en las secciones correspondientes del formulario/Plan de Trabajo. Cada sección indica dónde debe insertarse.*

---

## SECCIÓN A — Para incluir en §2 "Descripción del Problema y Oportunidad de Innovación"

### A.1 Por qué el CWSI termográfico es la variable correcta para viticultura de precisión

*[Insertar después del párrafo "El problema técnico central"]*

La vid (*Vitis vinifera* L.) es un cultivo isohedronómico — esto es, mantiene su potencial hídrico relativamente constante durante el día a expensas de cerrar sus estomas y sacrificar la fotosíntesis (Schultz 2003). Este comportamiento fisiológico hace que la planta responda al déficit hídrico **antes** de que el suelo esté seco, anticipando el cierre estomático para proteger la hidratación celular. En consecuencia, cualquier sistema que mida únicamente la humedad del suelo —como los tensiómetros o las sondas capacitivas— detecta el estrés con un desfase de 2 a 5 días respecto del momento en que la planta ya está fisiológicamente afectada.

La temperatura foliar capta esa respuesta en tiempo real: cuando el estoma se cierra, cae la transpiración y aumenta la temperatura de la hoja por encima de la temperatura del aire en más de lo esperado bajo condiciones sin estrés. Este diferencial térmico puede llegar a 3–6°C en condiciones de VPD alto (1.8–4.5 kPa), perfectamente detectable con cámaras de microbolómetro LWIR de bajo costo (NETD ≤ 150 mK). La traducción de esa diferencia térmica al CWSI de Jackson et al. (1981) provee un valor adimensional entre 0 y 1 que es comparado con umbrales agronómicos validados: 0.30 para estrés moderado, 0.55 para estrés alto, en vid Malbec bajo las condiciones de Cuyo y Córdoba.

### A.2 El impacto del estrés hídrico sobre la calidad enológica del Malbec

*[Insertar en §2 como subsección nueva o en el párrafo de cuantificación del problema]*

En vid de alta calidad, el manejo del estrés hídrico no es solo una decisión de conservación del cultivo: es una herramienta enológica activa. El Riego Deficitario Regulado (RDI) aplicado con precisión en momentos críticos del ciclo vegetativo tiene efectos documentados sobre la calidad de la baya:

- **Déficit moderado post-cuaje a pre-envero (CWSI 0.35–0.55, Ψ_stem −1.0 a −1.3 MPa):** reduce el tamaño del grano y concentra los sólidos solubles (°Brix), los polifenoles totales y las antocianinas, mejorando el perfil organoléptico del vino tinto premium. Es la estrategia estándar en producción de Malbec de alta gama en Mendoza Valle de Uco (ingreso bruto > USD 9.600/ha).

- **Déficit severo en floración (Ψ_stem < −1.3 MPa durante GDD 280–420):** provoca corrimiento y millerandage con pérdida de cuaje de hasta el 35–60% del potencial productivo. Es irreversible para esa temporada. Este es el evento de mayor impacto económico que el sistema HydroVision AG debe detectar y prevenir.

- **Déficit en pre-cosecha (GDD > 1.600):** cualquier aporte de agua en las últimas 2–3 semanas antes de cosecha diluye los mostos y reduce °Brix, acidez y color. El sistema debe suspender el riego automáticamente en este estadio, independientemente del CWSI.

La capacidad del sistema HydroVision AG de ajustar los umbrales de alerta y los criterios de riego según el estadio fenológico (motor GDD) es el elemento diferencial que permite al productor implementar estas estrategias enológicas de precisión sin depender del agrónomo en el lote.

---

## SECCIÓN B — Para incluir en §4 "Descripción Técnica" — Validación de umbrales CWSI por varietal

*[Insertar como §4.2.3 o como nota técnica dentro de §4.2 "Modelo físico — CWSI"]*

### B.1 Coeficientes CWSI para las variedades del proyecto — Estado actual y plan de calibración

Los coeficientes ΔT_LL y ΔT_UL de la fórmula CWSI de Jackson et al. (1981) son específicos de varietal, sistema de conducción, microclima y estadio fenológico. El uso de coeficientes de una región diferente o de una variedad diferente introduce errores sistemáticos que pueden desplazar el CWSI calculado en ±0.15–0.20 unidades, equivalente a diagnosticar una planta moderadamente estresada como si no tuviera estrés, o viceversa.

**Estado actual (TRL 3):**  
El sistema usa como punto de partida los coeficientes de Bellvert et al. (2016) para Pinot Noir en Cataluña (ΔT_LL = a + b·VPD, con rangos de VPD 1.5–3.0 kPa). Estos coeficientes son la mejor referencia disponible en la literatura para vid en espaldera, pero no han sido calibrados para Malbec en Argentina.

**Plan de calibración en TRL 4:**  
El protocolo experimental de Colonia Caroya generará los primeros coeficientes CWSI calibrados para *Vitis vinifera* cv. Malbec en condiciones de Córdoba (700 m s.n.m., suelo franco-limoso, ETP 850 mm/año, VPD típico 1.8–4.5 kPa en diciembre–febrero). El método de calibración es el estándar NWSB (Non-Water-Stressed Baseline) de Jackson et al. (1981):

1. Medir Ψ_stem de 4–6 plantas de Zona A (100% ETc, sin estrés) en ≥ 30 condiciones distintas de VPD durante la temporada (objetivo: cubrir el rango completo 1.0–5.5 kPa del verano cordobés).
2. Registrar simultáneamente (T_foliar, T_aire, VPD) para cada medición.
3. Ajustar por regresión lineal la línea base ΔT_LL vs. VPD: coeficientes a (intercepto) y b (pendiente).
4. Verificar que las plantas de Zona A mantienen Ψ_stem > −0.8 MPa durante todas las sesiones (condición de "sin estrés" para la calibración del ΔT_LL).

**Varietal vs. Coeficientes provisionales (hasta calibración TRL 4):**

| Varietal | Fuente coeficientes actuales | Rango VPD cubierto | Error estimado ΔT_LL |
|---|---|---|---|
| Malbec | Bellvert et al. (2016) — Pinot Noir, Cataluña | 1.5–3.0 kPa | ±0.10–0.15 CWSI |
| Syrah | Bellvert et al. (2016) | 1.5–3.0 kPa | ±0.12–0.18 CWSI |
| Cabernet Sauvignon | Bellvert et al. (2016) | 1.5–3.0 kPa | ±0.10–0.15 CWSI |
| Olivo | García-Tejero et al. (2018) | 1.5–3.5 kPa | ±0.08–0.12 CWSI |
| Cerezo | Estimado por analogía | — | ±0.20 CWSI (provisional) |

**Meta TRL 4:** ΔT_LL calibrado para Malbec en Córdoba/Cuyo con error < ±0.07 CWSI (umbral agronómico de Araújo-Paredes 2022). Los coeficientes calibrados se protegen como secreto comercial.

---

## SECCIÓN C — Para incluir en §5 "Equipo de Trabajo" — Perfil Monteoliva

*[Completar o reemplazar el perfil existente de la asesora científica]*

### C.1 Dra. Mariela Inés Monteoliva — Asesora científica / Investigadora INTA-CONICET

**Rol en el proyecto:** Supervisión científica del protocolo experimental de campo, diseño del protocolo de medición Scholander, validación de los coeficientes CWSI para Malbec, revisión de los resultados de correlación CWSI–Ψ_stem.

**Filiación:** Investigadora Adjunta, INTA EEA Córdoba / CONICET — Centro de Investigaciones Agropecuarias (CIAP), Córdoba.

**Especialidad:** Fisiología vegetal bajo estrés abiótico en cultivos. Relaciones hídricas en vid y frutales. Protocolo de medición de potencial hídrico (bomba de Scholander). Respuesta fisiológica del Malbec a condiciones de Riego Deficitario Regulado (RDI) en el pedemonte cordobés.

**Publicación de referencia:** Espinosa Herlein, M.A.; Monteoliva, M.I. (2025). Estado hídrico. En: *Abordajes fisiológicos para el estudio del estrés abiótico en cultivos*. Editorial UCC, Córdoba, Argentina.

**Aporte específico al proyecto:**
- Elaboró el protocolo de medición Scholander adaptado al viñedo experimental de Colonia Caroya
- Diseñó los criterios de post-lluvia y los umbrales de rescate hídrico del protocolo RDI
- Confirmó la validez científica del método CWSI termográfico para la aplicación en vid Malbec
- Aportará los primeros coeficientes CWSI calibrados para Malbec en condiciones de Córdoba
- Capacitará al técnico de campo local en el manejo de la bomba de presión Scholander, permitiendo que las sesiones 3 y 4 sean ejecutadas sin su presencia física

**Vínculo con el proyecto:** Asesora científica voluntaria, sin participación accionaria ni relación comercial con HydroVision AG. Carta de participación y aval científico adjuntos.

---

## SECCIÓN D — Para incluir en §6 "Plan de Trabajo" — Actividades con participación de Monteoliva

*[Insertar en el plan de trabajo de los meses correspondientes]*

### Mes 4 — Sesión 1 Scholander (post-brotación):

**Actividad 6.1 — Calibración inicial del sistema en viñedo experimental**
- **Responsable principal:** Dra. M. Monteoliva (INTA-CONICET)
- **Co-ejecutores:** César Schiavoni, Javier Schiavoni, Franco Schiavoni
- **Duración:** 2 días de trabajo en campo (incluye desplazamiento desde Córdoba)
- **Descripción:** La Dra. Monteoliva conduce la primera sesión de medición Scholander sobre las 5 zonas hídricas del viñedo experimental. Simultáneamente, realiza la calibración inicial de los dendrómetros de tronco (primera lectura de referencia de todos los sensores) y capacita a Javier Schiavoni en el manejo de la bomba de presión para las sesiones posteriores. Se obtienen los primeros pares calibrados (Ψ_stem, CWSI) del dataset de entrenamiento. Los coeficientes CWSI provisionales (Bellvert 2016) se ajustan con los primeros datos de la línea base sin estrés (Zona A, 100% ETc) bajo las condiciones de VPD del pedemonte cordobés.
- **Entregable:** Dataset de calibración Sesión 1 (5 pares Scholander + frames LWIR sincronizados). Informe de instalación verificada.

### Mes 8 — Sesión 2 Scholander (pre-envero):

**Actividad 6.2 — Sesión de estrés máximo y ajuste de coeficientes CWSI**
- **Responsable principal:** Dra. M. Monteoliva (INTA-CONICET)
- **Co-ejecutores:** César Schiavoni, Javier Schiavoni
- **Duración:** 1 día de trabajo en campo
- **Descripción:** Sesión en la ventana de mayor VPD del ciclo (mediodía de verano, enero). Se obtienen los pares calibrados en el rango de estrés máximo del gradiente (Zonas D y E), el más informativo para el límite superior del CWSI. La Dra. Monteoliva valida visualmente el estado de las vides, verifica el funcionamiento del protocolo de rescate, y ajusta los criterios de los coeficientes ΔT_UL con las mediciones de Zona E bajo condiciones de VPD > 2.0 kPa.
- **Entregable:** Dataset Sesión 2 (5 pares). Ajuste preliminar de coeficientes ΔT_LL / ΔT_UL para Malbec Colonia Caroya. Informe de validación de la línea base NWSB con primeros 15+ pares acumulados.

### Mes 12 — Validación final:

**Actividad 6.3 — Revisión científica de resultados de calibración**
- **Responsable:** Dra. M. Monteoliva (remoto)
- **Descripción:** La Dra. Monteoliva revisa el dataset completo acumulado (≥ 800 frames, 4 sesiones Scholander), valida la función de calibración CWSI–Ψ_stem resultante, y emite informe técnico de validación científica del sistema para el informe final ANPCyT.
- **Entregable:** Informe de validación científica firmado por Dra. Monteoliva. Input para el artículo científico en preparación.

---

## SECCIÓN E — Para incluir en §8 "Resultados Esperados" — Validación agronómica

*[Insertar como subsección nueva en §8.1 "Resultados técnicos al cierre del proyecto"]*

### E.1 Resultados agronómicos esperados al cierre del TRL 4

**Calibración CWSI para Malbec en Argentina:**  
El proyecto producirá los primeros coeficientes CWSI (ΔT_LL vs. VPD) calibrados para *Vitis vinifera* cv. Malbec bajo condiciones del pedemonte cordobés y, por extensión, adaptables a condiciones similares de Mendoza y San Juan. Estos coeficientes constituyen un activo de propiedad intelectual de primer orden: no existen datos equivalentes publicados para la región, y su obtención requirió 9 meses de protocolo de campo con supervisión INTA-CONICET.

**Correlación CWSI–Ψ_stem documentada:**  
Al cierre del proyecto se dispondrá de la función de calibración CWSI = f(Ψ_stem) con su intervalo de confianza, basada en ≥ 50 pares directos (Scholander + frame LWIR sincronizado) cubriendo el rango completo −0.3 a −1.5 MPa. Esta función es la base científica de la precisión del sistema y el argumento principal ante productores y compradores institucionales (INTA, universidades, empresas de riego) que requieran validación experimental para su adopción.

**Protocolo RDI validado para Malbec en Colonia Caroya:**  
El viñedo experimental habrá completado el ciclo vegetativo completo bajo el protocolo de 5 zonas hídricas con supervisión de la Dra. Monteoliva (INTA-CONICET). Los datos de rendimiento (kg/planta por zona), calidad de mosto (°Brix, acidez total, índice de polifenoles) y estado sanitario de las plantas al final de la temporada constituirán la primera evidencia experimental de la respuesta productiva del cv. Malbec al RDI en el pedemonte cordobés bajo el sistema de riego por goteo.

---

## SECCIÓN F — Glosario agronómico para el formulario

*[Agregar como sección de glosario al final del formulario o como nota al pie en las secciones correspondientes]*

**CWSI (Crop Water Stress Index):** Índice de estrés hídrico del cultivo. Valor adimensional entre 0 (sin estrés) y 1 (estrés severo), calculado a partir de la temperatura foliar medida por cámara infrarroja y dos temperaturas de referencia: la hoja bien hidratada (T_wet) y la hoja sin transpiración (T_dry). Definido por Jackson et al. (1981); validado en vid en más de 200 trabajos científicos.

**Ψ_stem (potencial hídrico de tallo):** Medida de la tensión del agua en el xilema de la planta, expresada en megapascales (MPa). Valores más negativos indican mayor estrés. El valor de equilibrio del mediodía solar (Ψ_stem,md) es el indicador fisiológico estándar para el manejo hídrico de viñedos de calidad. Se mide con la bomba de presión Scholander.

**MDS (Máxima Contracción Diaria del tronco):** Diferencia entre el diámetro máximo del tronco (amanecer, máxima hidratación) y el mínimo diario (mediodía, máximo estrés). Medida con extensómetro de alta resolución. Correlaciona con Ψ_stem con R² = 0.80–0.92. No depende de ventana solar ni se ve afectado por viento.

**VPD (Vapor Pressure Deficit — Déficit de Presión de Vapor):** Diferencia entre la presión de vapor de saturación y la presión de vapor real del aire. Expresa la "sed" de la atmósfera. A VPD alto (> 2.5 kPa), la demanda evaporativa es alta y los estomas tienden a cerrarse para regular la pérdida de agua, aumentando la temperatura foliar independientemente del estado hídrico del suelo.

**GDD (Grados-Día Acumulados):** Unidad de calor acumulado calculada como el promedio de temperatura diaria menos una temperatura base (T_base = 10°C para vid). Permite predecir y detectar automáticamente el estadio fenológico del cultivo sin depender de observaciones visuales de campo.

**RDI (Riego Deficitario Regulado):** Estrategia de manejo hídrico en la que se aplica deliberadamente menos agua que la ETc durante ciertos estadios del ciclo vegetativo para inducir respuestas fisiológicas que mejoran la calidad del fruto (concentración de azúcares, antocianinas, polifenoles en vid) sin reducir el rendimiento por debajo del umbral de viabilidad económica.

**ETc (Evapotranspiración del cultivo):** Cantidad de agua que un cultivo evapotranspira bajo condiciones sin estrés hídrico. Se calcula como ETc = ETo × Kc, donde ETo es la evapotranspiración de referencia (calculada con datos meteorológicos) y Kc es el coeficiente del cultivo según el estadio fenológico.

**Protocolo Scholander:** Método estándar internacional para la medición directa del potencial hídrico foliar y de tallo mediante la aplicación de presión de nitrógeno a una hoja o tallo cortado en una cámara hermética, hasta que la savia reaparece en el corte. La presión aplicada en ese punto es numéricamente igual al Ψ_stem (con signo negativo). Nombrado por el fisiólogo Per Scholander que lo describió en 1965.
