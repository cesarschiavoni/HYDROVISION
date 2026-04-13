# Oportunidad de Investigación — HydroVision AG / ANPCyT 2026

**Convocatoria:** STARTUP 2025 TRL 3-4 — ANPCyT/FONARSEC (BID)
**Plazo de incorporación:** antes del 21 de mayo de 2026
**Contacto:** César Schiavoni — schiavonicesar@gmail.com · 3525448154

---

## El proyecto

**HydroVision AG** desarrolla una plataforma autónoma de detección de estrés hídrico en cultivos de alto valor (vid, olivo, cerezo, citrus) usando termografía infrarroja de bajo costo embebida en nodos IoT de campo.

El núcleo del sistema es un nodo autónomo que:
1. **Captura imágenes térmicas del dosel** con una cámara MLX90640 (32×24 px) montada en gimbal motorizado
2. **Segmenta las hojas** del fondo (suelo, cielo, madera) y calcula la **temperatura media del canopeo**
3. **Estima el CWSI** (Crop Water Stress Index) en tiempo real usando un modelo PINN en el propio ESP32-S3 — sin nube
4. Activa el riego de forma autónoma cuando el CWSI supera el umbral de estrés

Como señal complementaria, el nodo incorpora un extensómetro de tronco (dendrómetro) que registra la variación de diámetro entre sesiones térmicas.

El proyecto cuenta con financiamiento ANPCyT por **USD 120.000 ANR** + contrapartida privada, y dispone de un viñedo experimental propio en Colonia Caroya (4 filas de Malbec × 5 regímenes hídricos controlados).

---

## La pregunta científica

El sistema ya está construido e instrumentado. Lo que define si el producto funciona — y lo que constituye el **aporte científico original del proyecto** — es responder con datos reales de campo:

> *¿El CWSI calculado por el nodo a partir de la temperatura del dosel (cámara 32×24 px, segmentación automática de hojas) predice con precisión el potencial hídrico foliar real de la planta?*

El gold standard para medirlo es la **bomba de Scholander** (Ψstem en MPa): instrumento de referencia en fisiología vegetal que mide directamente la tensión del agua en la hoja. La Dra. Mariela Monteoliva (INTA-CONICET) ejecuta el protocolo en el viñedo experimental.

La validación tiene tres niveles:

| Señal del nodo | vs. referencia | Métrica objetivo |
|---|---|---|
| CWSI (cámara térmica) | Ψstem Scholander | R² ≥ 0.75, MAE ≤ 0.08 CWSI |
| MDS (dendrómetro) | Ψstem Scholander | R² ≥ 0.65 |
| HSI = 0.35·CWSI + 0.65·MDS | Ψstem Scholander | R² ≥ 0.80 (índice integrado) |

---

## El problema técnico

El CWSI se calcula como:

```
CWSI = (T_canopy − T_LL) / (T_UL − T_LL)
```

donde `T_canopy` es la temperatura media de los píxeles foliares segmentados, `T_LL` es la temperatura de planta sin estrés (función del VPD) y `T_UL` es la temperatura de planta sin transpiración. Los parámetros de la línea base (`T_LL`, `T_UL`) varían por cultivar, estadio fenológico y condiciones locales.

Las complicaciones reales que hacen el problema interesante para un investigador de señales:

- **Segmentación en 32×24 px**: la resolución baja mezcla hojas, tallos, suelo y cielo en el mismo píxel — la calidad de la máscara foliar afecta directamente el CWSI calculado
- **Calibración de la línea base CWSI**: los parámetros `a` y `b` de `T_LL = a·VPD + b` son específicos del cultivar y la región — la Sesión 1 de Scholander los ancla experimentalmente
- **Deriva del dendrómetro**: la señal de tronco se mezcla con dilatación térmica (~0.01 mm/°C) e histéresis de rehidratación — requiere corrección y calibración por regresión (`Ψstem = a·ADC + b`) individual por planta
- **Diseño de las sesiones**: 4 sesiones Scholander óptimas (OED) pueden reemplazar 10 uniformes con igual información estadística — la elección de fechas y condiciones de VPD determina la calidad del modelo final

El análisis combina las tres señales (CWSI, MDS, Ψstem) con regresión, correlación cruzada, corrección de deriva y plots Bland-Altman para producir las métricas de validación TRL 4 publicables.

---

## Perfil buscado

**Formación:** Ingeniería electrónica, sistemas, mecatrónica, o afín con orientación en mediciones, señales o estadística aplicada.

**Conocimientos útiles:**
- Regresión lineal/no lineal, análisis de correlación, tests de hipótesis
- Python o R para análisis de datos (pandas, scipy, statsmodels o equivalente)
- Diseño de experimentos (DOE/OED) — deseable, no excluyente
- Experiencia con datos de sensores físicos (calibración, corrección de offset/deriva)

**Perfil institucional (requisito ANPCyT Art. 32°):** investigador, docente-investigador o becario de posgrado con afiliación en universidad, CONICET, INTA u organismo equivalente. La persona debe desarrollar actividades de investigación y/o formación de recursos humanos.

**No se requiere** experiencia previa en agricultura de precisión, visión por computadora ni modelos de IA. El sistema de inferencia está implementado — el investigador trabaja con las correlaciones estadísticas entre señales de campo y el gold standard Scholander.

---

## Condiciones

| Ítem | Detalle |
|------|---------|
| **Honorarios** | USD 6.000 — USD 500/mes × 12 meses, financiados íntegramente por ANR ANPCyT (~USD 34/hora) |
| **Dedicación** | ~4–5 horas/semana promedio (~177 horas totales en 12 meses) |
| **Modalidad** | Mayormente remota + 4 jornadas de campo en Colonia Caroya (Mes 4–9) |
| **Publicación** | Co-autoría garantizada en revista indexada Q1/Q2 — APC ya presupuestado (Agricultural Water Management / Biosystems Engineering) |
| **Inicio estimado** | Octubre 2026 (sujeto a aprobación ANPCyT) |

---

## Lo que ya está implementado

El investigador se incorpora a un proyecto con infraestructura técnica completa:

| Componente | Estado |
|---|---|
| Pipeline de captura térmica + segmentación foliar + cálculo CWSI en nodo | ✅ Implementado |
| Modelo PINN PyTorch + pipeline de entrenamiento | ✅ Implementado + pre-entrenamiento corrido |
| Simulador físico (1M imágenes sintéticas de dosel generadas) | ✅ Corrido (6-abr-2026) |
| Protocolo experimental Scholander + viñedo instrumentado | ✅ Diseñado por Dra. Monteoliva (INTA-CONICET) |
| Scripts de validación estadística (estructura + métricas TRL 4) | ✅ Implementados — requieren datos reales |
| Parámetros NWSB calibrados para 14 cultivares (vid, olivo, citrus, etc.) | ✅ Implementados |
| Backend IoT + API REST + base de datos de campo | ✅ Operativo |

El aporte del investigador es irreemplazable: los datos reales de campo con Scholander — que el sistema no puede generar sin un experimentalista — y la validación estadística que los convierte en evidencia publicable.

---

## Equipo

| Persona | Rol |
|---|---|
| **César Schiavoni** | Director Técnico / Project Leader ANPCyT. Ing. Sistemas UTN FRC. Sr. Software Engineer (MercadoLibre). |
| **Lucas Bergon** | COO / Hardware Lead. Fundador MBG Controls (150+ proyectos industriales). Ing. Electrónica + Ing. Sistemas UTN FRC. |
| **Dra. Mariela Monteoliva** | Investigadora Adjunta INTA-CONICET (IFRGV-UDEA, CCT Córdoba). Doctora Cs. Químicas. Especialista en CWSI y potencial hídrico foliar con bomba de Scholander. |
| **Javier Schiavoni** | Técnico de Campo. Residente en Colonia Caroya, a metros del viñedo experimental. Entrenado por Dra. Monteoliva en protocolo Scholander. Ejecuta las sesiones de campo, instala y mantiene los nodos y dendrómetros. |
| **Matías Tregnaghi** | CFO. Contador Público. Responsable de rendiciones ANPCyT. |

---

## Por qué participar

- **Dato escaso**: dataset de campo con gold standard Scholander + termografía sincronizada — raramente disponible en Argentina a esta escala para vid
- **Publicación con APC cubierto**: co-autoría en revista Q1/Q2, el proyecto cubre el costo de publicación
- **Problema metodológico real**: calibración de señales con deriva, histéresis, bajo número de píxeles y variabilidad inter-planta
- **Financiamiento sólido**: honorarios USD 500/mes pagados por ANPCyT/FONARSEC (BID) — no dependen del flujo de caja de la startup
- **Equipo de perfil UTN FRC**: César Schiavoni y Lucas Bergon son egresados Ing. Sistemas / Ing. Electrónica UTN FRC

---

## Contacto

Escribir a **César Schiavoni** con asunto **"Investigador Art. 32 — HydroVision AG"**:

- Email: schiavonicesar@gmail.com
- Tel: 3525448154

Adjuntar CV o perfil de Google Scholar / ResearchGate. **Plazo límite: 16 de mayo de 2026.**

---

## Anexo — Declaración de Participación Científica

**Proyecto HydroVision AG — Convocatoria STARTUP 2025 TRL 3-4 — ANPCyT/FONARSEC**

Córdoba, ______ de ____________ de 2026

Yo, **___________________________**, DNI ____________, declaro:

**1.** Que participo voluntariamente como **Investigador en Validación de Señales y Datos Agronómicos (Perfil científico-tecnológico Art. 32)** del proyecto *"Plataforma Autónoma de Inteligencia Agronómica para Cultivos de Alto Valor mediante Termografía LWIR, Dendrometría de Tronco, Motor Fenológico Automático y Fusión Satelital con IA Edge"*, presentado por HydroVision AG ante ANPCyT en el marco de la Convocatoria STARTUP 2025 TRL 3-4.

**2.** Que mi perfil científico-tecnológico comprende:
- Área de formación: ___________________________
- Afiliación institucional / grupo de investigación: ___________________________
- Publicaciones o ponencias relevantes: ___________________________

**3.** Que mis compromisos en el proyecto son: calibración experimental de la línea base CWSI con datos Scholander (Mes 4–6), diseño experimental óptimo (OED) para las sesiones de campo, análisis estadístico de correlaciones CWSI↔MDS↔Ψstem (Mes 5–9), calibración de sensores dendrómetro por regresión, validación de métricas TRL 4 (R²≥0.75 CWSI vs Ψstem) y co-autoría en publicación científica.

**4.** Que mi dedicación es de aproximadamente **4–5 horas semanales promedio (~177 horas)** en 12 meses, compatible con mi actividad actual.

**5.** Que la propuesta técnica es, a mi criterio, metodológicamente sólida y científicamente fundada.

---

Firma: ___________________________

Nombre completo: **___________________________**
DNI: ____________
Institución / Grupo de investigación: ____________________________
Email: ____________________________
Tel.: ____________________________

---

*HydroVision AG — Córdoba, Argentina — Abril 2026*
