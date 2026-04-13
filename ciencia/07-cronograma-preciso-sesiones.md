
# CRONOGRAMA PRECISO DE SESIONES SCHOLANDER
## Viñedo Experimental HydroVision AG — Colonia Caroya, Córdoba
## Elaborado por: Dra. Mariela Inés Monteoliva (INTA-CONICET)

---

## 1. PRINCIPIO DE DISEÑO: SESIONES VINCULADAS A FENOLOGÍA, NO AL CALENDARIO

Las 4 sesiones del protocolo Scholander están posicionadas según el estadio fenológico del Malbec, no según fechas fijas del calendario. La fecha exacta de ejecución se determina **2–4 días antes** cuando confluyen:

1. **Trigger fenológico**: el motor GDD del nodo detecta que se alcanzó el umbral de GDD acumulados del estadio
2. **Trigger meteorológico**: ventana de 48 h sin lluvia pronosticada (SMN Córdoba)
3. **Disponibilidad**: Dra. Monteoliva confirma asistencia presencial (S1, S2) o Javier/Franco confirman ejecución autónoma (S3, S4)

Este documento establece:
- Ventanas **objetivo** (rangos de fechas ideales por fenología)
- Fechas **tentativas** calculadas según GDD histórico de Colonia Caroya (2018–2024)
- Fechas de **respaldo** (backup) si la principal se cancela por lluvia o contingencia
- Criterios de **cancelación y reprogramación**

---

## 2. FENOLOGÍA MALBEC — COLONIA CAROYA — LÍNEA BASE HISTÓRICA

| Estadio | GDD acumulado | Fecha histórica promedio | Rango observado | Variabilidad (±) |
|---|---|---|---|---|
| Brotación | 80–120 GDD | 10 de septiembre | 1–25 sep | ±12 días |
| 4–6 hojas desplegadas | 150–200 GDD | 5 de octubre | 25 sep–15 oct | ±10 días |
| Floración (inicio) | 280 GDD | 28 de octubre | 15–10 nov | ±12 días |
| Cuaje | 420 GDD | 20 de noviembre | 5–30 nov | ±12 días |
| Pre-envero (inicio) | 500–550 GDD | 10 de enero | 28 dic–20 ene | ±15 días |
| Envero (50% bayas) | 650 GDD | 5 de febrero | 20 ene–20 feb | ±16 días |
| Post-envero (madurez) | 750–800 GDD | 25 de febrero | 10 feb–10 mar | ±14 días |
| Pre-cosecha | 850–900 GDD | 15 de marzo | 5–30 mar | ±12 días |

*Fuente: datos propios INTA EEA Córdoba (estación Colonia Caroya), temperatura base T=10°C.*

---

## 3. CALENDARIO DE LAS 4 SESIONES

### SESIÓN 1 — Post-brotación / Calibración de línea base

| Campo | Detalle |
|---|---|
| **Objetivo científico** | Establecer ΔT_LL baseline con plantas en plena hidratación (zona A, Ψ_stem > −0.5 MPa) |
| **Estadio requerido** | 4–6 hojas desplegadas. GDD: 150–200 acumulados desde 1 ago |
| **Fecha tentativa** | **Lunes 5 de octubre de 2026** |
| **Ventana objetivo** | 29 de septiembre — 12 de octubre de 2026 |
| **Fecha de respaldo** | **Lunes 12 de octubre de 2026** (2° respaldo: 19 oct) |
| **Presencia Monteoliva** | **Presencial — obligatoria** (capacitación Scholander a Javier y Franco) |
| **Horario** | Llegada 8:30 hs. Medición 10:00–13:00 hs. Revisión de datos 14:00–16:00 hs |
| **n plantas** | ≥ 5 por zona (25 plantas total) |
| **Actividades adicionales** | Capacitación 4–6 h en manejo de bomba Scholander |
| **Trigger automático** | Notificación push del nodo cuando GDD ≥ 140 AND pronóstico SMN = sin lluvia 48h |
| **Criterio de cancelación** | Lluvia > 2 mm en las 24 h previas → reprogramar a fecha de respaldo |

**Lista de materiales a llevar (Monteoliva):**
- Bomba de presión Scholander (INTA EEA Córdoba — reservar con 30 días de anticipación)
- 2 cilindros de N₂ comprimido (verificar presión mínima 120 bar)
- Bolsas de papel de aluminio para equilibrio de hojas (≥ 50 unidades)
- Lupa de bolsillo 10× para identificar puntos finales dudosos
- Planillas de campo impresas (del §8 del protocolo formal, doc 01)
- Lámina plastificada de síntomas visuales niveles 1–3 (para pegar en tablero de riego)

---

### SESIÓN 2 — Pre-envero / Máxima demanda hídrica

| Campo | Detalle |
|---|---|
| **Objetivo científico** | Calibrar CWSI durante el período de máxima demanda hídrica y sensibilidad al déficit (pre-envero). Validar umbrales de alerta R1 y R2 del doc 04 |
| **Estadio requerido** | Pre-envero (bayas < 10% coloreadas). GDD: 480–540 |
| **Fecha tentativa** | **Miércoles 7 de enero de 2027** |
| **Ventana objetivo** | 30 de diciembre de 2026 — 15 de enero de 2027 |
| **Fecha de respaldo** | **Miércoles 14 de enero de 2027** (2° respaldo: 21 ene) |
| **Presencia Monteoliva** | **Presencial — obligatoria** (primera sesión de campo real con estrés diferencial) |
| **Horario** | Llegada 8:00 hs. Medición 10:00–13:00 hs. El VPD típico en enero supera 3.5 kPa antes de las 12:30 hs en Córdoba — iniciar puntualmente |
| **n plantas** | ≥ 5 por zona (25 plantas total). Priorizar zonas D y E si hay limitación de tiempo |
| **Actividades adicionales** | Primera comparación cuantitativa CWSI (dashboard nodo) vs. Ψ_stem medido. Ajuste preliminar de coeficientes si el residuo > 0.15 unidades CWSI |
| **Trigger automático** | Notificación push cuando GDD ≥ 470 AND pronóstico SMN = sin lluvia 48h AND T_max > 28°C (alta demanda evaporativa) |
| **Criterio de cancelación** | Lluvia > 3 mm en las 48 h previas → reprogramar. Recordar: post-lluvia 3–10 mm = esperar 24–36 h; >10 mm = esperar 48–72 h |

**Alerta San Juan — enero:** si se programa visita paralela al viñedo San Juan, coordinar con las fechas de esta sesión para optimizar el viaje.

---

### SESIÓN 3 — Post-envero / Estrategia RDI enológica

| Campo | Detalle |
|---|---|
| **Objetivo científico** | Validar el cambio de umbrales entre el coeficiente Set B (pre-envero) y Set C (post-envero, umbral más alto tolerado bajo estrategia RDI enológica). Evaluar si el motor GDD del nodo hace la transición automáticamente en la fecha correcta |
| **Estadio requerido** | Post-envero (≥ 70% bayas coloreadas). GDD: 680–740 |
| **Fecha tentativa** | **Jueves 11 de febrero de 2027** |
| **Ventana objetivo** | 1–20 de febrero de 2027 |
| **Fecha de respaldo** | **Jueves 18 de febrero de 2027** |
| **Presencia Monteoliva** | **Remota** (Javier y Franco ejecutan autónomamente. Monteoliva disponible por videollamada durante la sesión) |
| **Horario** | Medición 10:00–13:00 hs solar. Javier reporta en tiempo real via WhatsApp los valores de Ψ_stem |
| **n plantas** | ≥ 5 por zona (25 plantas). Si el tiempo es limitado: n=3 por zona = 15 plantas mínimo |
| **Validación remota** | César Schiavoni envía a Monteoliva el CSV del nodo (últimas 48 h) antes de las 9:00 hs del día de la sesión. Monteoliva confirma condiciones adecuadas para proceder |
| **Trigger automático** | Notificación push cuando GDD ≥ 660 AND pronóstico SMN = sin lluvia 48h |

---

### SESIÓN 4 — Pre-cosecha / Cierre del dataset de calibración

| Campo | Detalle |
|---|---|
| **Objetivo científico** | Completar el dataset con el estadio de madurez (máximo °Brix, Ψ_stem en zona A ≈ −0.8 a −1.0 MPa bajo RDI moderado). Cerrar la regresión CWSI–Ψ_stem con n ≥ 80 pares totales |
| **Estadio requerido** | Pre-cosecha. GDD: 830–890. °Brix zona A: 22–24 (verificar con refractómetro) |
| **Fecha tentativa** | **Martes 16 de marzo de 2027** |
| **Ventana objetivo** | 8–25 de marzo de 2027 |
| **Fecha de respaldo** | **Martes 23 de marzo de 2027** |
| **Presencia Monteoliva** | **Remota** (idéntico procedimiento a S3) |
| **Actividades adicionales** | Medición de °Brix en ≥ 10 bayas por zona (refractómetro Javier) + foto del estado del canopeo por zona. Estos datos se incluirán en la tabla de resultados del paper (correlación CWSI–calidad enológica) |
| **Trigger automático** | Notificación push cuando GDD ≥ 810 AND pronóstico SMN = sin lluvia 48h |
| **Cierre del experimento** | Dentro de los 7 días post-sesión 4: exportar el dataset completo al pipeline de el investigador Art. 32 para análisis estadístico final |

---

## 4. VISTA CALENDARIO — TEMPORADA 2026–2027

```
AGO 2026   SEP 2026          OCT 2026         NOV 2026
│          │                 │                │
│ GDD=0    │ Brotación        │ 4–6 hojas      │ Floración
│ Reset    │ (GDD 80–120)     │ (GDD 150–200)  │ (GDD 280–420)
│          │                 │                │
│          │          [S1 tentativa: 5-oct] ──►│
│          │                 │                │
│          │                 │          [RESTRICCIÓN ZONA E]
│                                              │ 28-oct – 20-nov
│
DIC 2026         ENE 2027          FEB 2027          MAR 2027
│                │                 │                 │
│ Cuaje tardío   │ Pre-envero       │ Post-envero      │ Pre-cosecha
│ GDD 420–480    │ GDD 500–550      │ GDD 680–740      │ GDD 830–890
│                │                 │                 │
│                │ [S2 tentativa:   │ [S3 tentativa:   │ [S4 tentativa:
│                │  7-ene] ────────►│  11-feb] ───────►│  16-mar] ──►
│                │                 │                 │
│                │ MONTEOLIVA       │ Javier autónomo  │ Javier autónomo
│                │ PRESENCIAL       │ Monteoliva remota│ Monteoliva remota
```

---

## 5. CRITERIOS DE CANCELACIÓN Y REPROGRAMACIÓN

### 5.1 Criterios meteorológicos (automáticos)

| Condición | Acción |
|---|---|
| Lluvia < 2 mm en últimas 24 h | Sin restricción — sesión según plan |
| Lluvia 3–10 mm en últimas 48 h | Posponer sesión 24–36 h |
| Lluvia > 10 mm en últimas 48 h | Posponer sesión 48–72 h |
| T_max prevista > 38°C el día de la sesión | Iniciar medición a las 9:30 hs (30 min antes). Finalizar antes de las 12:30 hs. No hay cancelación por calor extremo salvo que T_foliar supere 48°C (fuera de rango MLX) |
| Pronóstico de tormenta eléctrica | Cancelar. No reprogramar antes de 24 h post-tormenta |
| Viento > 30 km/h durante la sesión | Continuar con Scholander (no afectado por viento). Anotar en planilla — los frames LWIR de ese día se marcarán como "alta incertidumbre" |

### 5.2 Criterios fenológicos (si la ventana se pierde)

Si una sesión se pierde completamente dentro de su ventana objetivo y las fechas de respaldo también se pierden:

- **S1 perdida**: Ejecutar lo antes posible dentro de GDD 200–250. Aceptable hasta 15 oct.
- **S2 perdida**: Ejecutar dentro de GDD 550–600 (hasta 20 ene). Pasado ese GDD, el envero puede comenzar y la sesión pierde representatividad del período pre-envero.
- **S3 o S4 perdidas**: Ejecutar en la siguiente semana disponible. El rango post-envero es más amplio (GDD 680–900).

### 5.3 Criterio de abandono del protocolo OED

Si se pierden 2 de las 4 sesiones sin posibilidad de recuperación, notificar a Monteoliva inmediatamente. El diseño D-óptimo requiere las 4 sesiones; perder 2 reduce el R² estimado del ajuste final de 0.75 a ~0.50. En ese caso, evaluar si se puede extender el protocolo a la temporada 2027–2028 con las sesiones perdidas.

---

## 6. DEPENDENCIAS OPERATIVAS

### 6.1 Dependencias que pueden demorar una sesión

| Dependencia | Responsable | Plazo de verificación previo a la sesión |
|---|---|---|
| Bomba Scholander disponible (INTA Córdoba) | Monteoliva | 30 días antes de S1; 15 días antes de S2 |
| Cilindros N₂ cargados | Monteoliva | 10 días antes de cada sesión |
| Nodo HydroVision AG funcionando (batería, comunicación) | César Schiavoni | 72 h antes de cada sesión |
| Tensiómetros de zona leídos y operativos | Javier Schiavoni | Semana previa a la sesión |
| Monteoliva con agenda libre (S1 y S2) | Monteoliva | Confirmar 21 días antes |
| Solenoides zonas D y E funcionando (verificar no hay falla electromecánica) | César Schiavoni | 72 h antes |

### 6.2 Sincronización con otros hitos del proyecto

| Sesión | Hito previo requerido | Hito posterior que habilita |
|---|---|---|
| S1 | Nodo instalado y calibrado en campo (≥ 2 semanas de operación previa) | Inicio de análisis de datos S1; primer reporte para ANPCyT (Mes 4) |
| S2 | Pipeline de procesamiento el investigador Art. 32 operativo (puede ingerir datos S1) | Primer ajuste CWSI–Ψ_stem preliminar |
| S3 | Dataset S1+S2 analizado; coeficientes provisionales actualizados | Validación del cambio de coeficientes post-envero (motor GDD Set C) |
| S4 | Fine-tuning PINN con datos S1+S2+S3 disponible | Dataset completo ≥ 80 pares → paper submission |

---

## 7. NOTIFICACIONES Y COMUNICACIÓN

### 7.1 Cadena de notificación ante trigger automático

```
Motor GDD del nodo detecta umbral alcanzado
              │
              ▼
  Notificación push automática a:
  • César Schiavoni (app del nodo)
  • Javier Schiavoni (app del nodo)
              │
              ▼
  César verifica pronóstico SMN para las 48 h siguientes
  (https://www.smn.gob.ar/pronostico-extendido — zona Córdoba Norte)
              │
        ┌─────┴─────┐
        │ Sin lluvia │ Lluvia prevista
        │           └──► Monitorear hasta ventana libre → reprogramar
        ▼
  César consulta agenda Monteoliva (S1 y S2)
  o confirma autonomía Javier/Franco (S3 y S4)
              │
              ▼
  Notificación WhatsApp a todos los involucrados:
  "SESIÓN [n] PROGRAMADA para [fecha] [hora]. 
   Confirmar asistencia / disponibilidad antes de [fecha-2]."
```

### 7.2 Grupo de WhatsApp recomendado

Crear grupo: **"HydroVision — Sesiones Campo"**
- Miembros: César Schiavoni, Javier Schiavoni, Franco Schiavoni, Dra. Monteoliva, el investigador Art. 32 (para coordinar exportación de datos post-sesión)

---

## 8. EXPORTACIÓN DE DATOS POST-SESIÓN

Dentro de las **6 horas** de cerrada cada sesión Scholander:

1. **Javier**: escanear planillas de campo (foto clara con celular) → subir a Google Drive carpeta "Sesiones Scholander / S[n]"
2. **César**: exportar CSV del nodo (ventana 6:00–15:00 hs del día de la sesión) → subir al mismo Google Drive
3. **Inv. Art. 32**: dentro de 24 h, correr el script de ingesta de datos y actualizar el dashboard de calibración (scatterplot CWSI vs. Ψ_stem, R² en tiempo real)
4. **Monteoliva**: revisar el scatterplot preliminar dentro de 48 h de la sesión y dar feedback por WhatsApp

---

## 9. RESUMEN EJECUTIVO — FECHAS CLAVE

| Sesión | Fecha tentativa | Respaldo | Presencia Monteoliva | GDD trigger |
|---|---|---|---|---|
| **S1** | **Lunes 5 oct 2026** | 12 oct 2026 | Presencial | ≥ 140 |
| **S2** | **Miércoles 7 ene 2027** | 14 ene 2027 | Presencial | ≥ 470 |
| **S3** | **Jueves 11 feb 2027** | 18 feb 2027 | Remota | ≥ 660 |
| **S4** | **Martes 16 mar 2027** | 23 mar 2027 | Remota | ≥ 810 |

**Milestone final:** Dataset completo exportado a pipeline PINN → **antes del 31 de marzo de 2027**.

---

*Dra. Mariela Inés Monteoliva — INTA EEA Córdoba / CONICET — Abril 2026*
