
# PROTOCOLO OPERATIVO DE RESCATE HÍDRICO
## Viñedo Experimental HydroVision AG — Colonia Caroya, Córdoba
## Elaborado por: Dra. Mariela Inés Monteoliva (INTA-CONICET)

---

## 1. OBJETO Y ALCANCE

Este documento establece el procedimiento de escalada, decisión e intervención ante situaciones de estrés hídrico severo en las filas 2 (15% ETc) y 1 (0% ETc, secano) del viñedo experimental. Complementa el §3.5 del Protocolo Scholander formal y es de cumplimiento obligatorio para Javier Schiavoni, Franco Schiavoni y César Schiavoni durante toda la campaña (Mes 4–12).

**Principio rector:** el experimento sacrifica agua — nunca el viñedo. Las plantas son el patrimonio productivo de la familia Schiavoni y el activo que financia el ensayo. Cualquier criterio de rescate activa riego de emergencia sin necesidad de autorización previa.

---

## 2. CRITERIOS DE ACTIVACIÓN — CUADRO DE REFERENCIA RÁPIDA

### 2.1 Criterios automáticos (accionan sin consulta, en el momento)

| # | Indicador | Umbral | Quién detecta | Acción inmediata |
|---|---|---|---|---|
| R1 | Ψ_stem medido | < −1.5 MPa en fila 2 (15% ETc) o fila 1 (0% ETc) | Javier/Franco (Scholander) | Riego de emergencia esa fila en ≤ 2 h |
| R2 | Temperatura foliar | > 42°C sostenida ≥ 30 min con VPD normal | App del nodo (alerta push) | Riego de emergencia esa fila en ≤ 1 h |
| R3 | Días sin agua | 14 días consecutivos sin lluvia ni riego en fila 1 (0% ETc, Dic–Feb) | Javier (control manual) | Riego mínimo 6 horas antes de continuar el ciclo |
| R4 | Síntomas visuales severos | Marchitez persistente a las 8:00 hs en fila 2 o fila 1 | Javier/Franco (inspección) | Rescate inmediato + foto + notificación Monteoliva |

### 2.2 Criterio de suspensión del protocolo (consultar a Monteoliva antes de actuar)

| # | Condición | Umbral | Acción pendiente de consulta |
|---|---|---|---|
| S1 | Ψ_stem en fila 3 (40% ETc) | < −1.3 MPa (zona de control moderado) | Verificar falla de solenoide fila 3 + notificar Monteoliva |
| S2 | Daño visual en fila 5 (100% ETc) | Cualquier síntoma de marchitez o clorosis en la fila de control | Notificar Monteoliva inmediatamente — revisar falla de riego |
| S3 | Falla total del sistema Rain Bird | Todas las filas sin riego por > 48 h en período Nov–Feb | Riego manual de emergencia en todas las filas + notificar |

---

## 3. SÍNTOMAS VISUALES DE REFERENCIA

Javier y Franco deben reconocer los síntomas progresivos para anticipar el criterio R4 antes de que sea necesario el Scholander:

**Nivel 1 — Estrés moderado (normal en filas 1 y 2, sin acción):**
- Hojas con leve ondulación de bordes al mediodía (13–15 hs)
- Ángulo del pecíolo más vertical (la hoja "baja")
- Zarcillos marchitos pero el tallo principal firme
- Recuperación total a las 8:00 hs del día siguiente

**Nivel 2 — Estrés severo (activar monitoreo intensivo, medir Ψ_stem):**
- Hojas con pliegue longitudinal pronunciado a partir de las 11 hs
- Coloración verde más pálida o grisácea en el canopeo superior
- Zarcillos secos y quebradizos
- La hoja comienza a recuperarse recién a las 6:00–7:00 hs (no a las 4:00–5:00 hs como normalmente)

**Nivel 3 — Pre-embolia / RESCATE OBLIGATORIO (criterio R4):**
- Marchitez visible a las 8:00 hs antes de que suba la temperatura
- Hojas con quemado de bordes (necrosis marginal)
- Hojas caídas o colgantes sin turgencia aun en la madrugada
- Brotes terminales secos o colapsados
- **Estos síntomas corresponden a Ψ_stem < −1.8 a −2.0 MPa. Actuar inmediatamente.**

**Fotografías de referencia:** Adjuntar fotos de los niveles 1–3 impresas en una lámina plastificada en el tablero de riego. [César Schiavoni: obtener de bibliografía INTA o de Monteoliva en Sesión 1]

---

## 4. PROCEDIMIENTO DE ESCALADA

```
JAVIER/FRANCO detecta indicador de rescate
            │
            ▼
    ┌───────────────────────────────────┐
    │  ¿Es criterio R1, R2, R3 o R4?   │
    └──────────────┬────────────────────┘
                   │ SÍ
                   ▼
    ┌─────────────────────────────────────────────┐
    │  ACCIÓN INMEDIATA:                          │
    │  1. Abrir solenoide de la fila afectada     │
    │     (override manual en Rain Bird)          │
    │  2. Regar hasta que tensiómetro baje        │
    │     a < 30 centibares (aprox. 3–6 horas)   │
    │  3. Registrar en planilla: hora inicio,     │
    │     duración, causa del rescate             │
    └──────────────┬──────────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────────────┐
    │  NOTIFICACIÓN (dentro de las 2 horas):      │
    │  • WhatsApp a César Schiavoni               │
    │  • WhatsApp a Dra. Monteoliva               │
    │  Mensaje estándar (ver §5 de este doc)      │
    └──────────────┬──────────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────────────┐
    │  MONITOREO POST-RESCATE (ver §6):           │
    │  Verificar recuperación a las 24 h,         │
    │  48 h y 72 h — tensiómetro + visual         │
    └─────────────────────────────────────────────┘
```

---

## 5. MENSAJES DE NOTIFICACIÓN ESTÁNDAR

### 5.1 Mensaje de activación de rescate (copiar y completar)

```
🚨 RESCATE FILA [número] — [fecha] [hora]

Criterio activado: [R1 / R2 / R3 / R4]
Ψ_stem medido: −___.__ MPa  (solo si Scholander disponible)
Temperatura foliar: ___°C  (si R2)
Días sin agua: ___  (si R3)
Síntomas visuales: [descripción breve]

Acción tomada: Riego abierto fila [número] a las [hora]
Duración prevista: [horas]

Foto adjunta: [SÍ / NO]
```

### 5.2 Mensaje de cierre de rescate (cuando tensiómetro < 30 cb)

```
✅ RESCATE FILA [número] COMPLETADO — [fecha] [hora]

Duración total del riego: ___h ___min
Lectura tensiómetro al cierre: ___ cb
Estado visual plantas: [normal / recuperando / requiere seguimiento]

Próxima medición Scholander programada: [fecha]
```

---

## 6. PROTOCOLO POST-RESCATE

Una vez que finaliza el riego de emergencia, el experimento no continúa automáticamente. Javier debe:

**A las 24 hs post-rescate:**
- Leer tensiómetro de la fila afectada → objetivo: < 30 centibares
- Inspección visual: ¿las hojas recuperaron turgencia nocturna?
- Si tensiómetro > 40 cb a las 24 h: extender riego hasta alcanzar < 30 cb

**A las 48 hs post-rescate:**
- Verificar en el dashboard que el extensómetro registra D_max normal (expansión nocturna completa). Si D_max post-rescate es < 80% del promedio histórico del nodo: notificar a Monteoliva
- Foto general de la zona rescatada mostrando el dosel

**A las 72 hs post-rescate:**
- Si el estado de la planta es normal y el tensiómetro está entre 20–30 cb: el experimento puede reiniciar el ciclo de déficit según el régimen asignado
- Si persiste síntoma visual en Nivel 2 o superior: **no reiniciar el déficit** hasta consulta con Monteoliva

**Criterio de no-reinicio del ciclo de estrés:**  
Fila 1 (0% ETc) o fila 2 (15% ETc) no vuelve a su régimen de déficit hasta que todas las condiciones siguientes sean simultáneas:
1. Tensiómetro < 30 cb
2. Extensómetro D_max > 90% del histórico del nodo
3. Inspección visual: sin síntomas de Nivel 2 o superior
4. Mínimo 5 días desde el cierre del riego de rescate

---

## 7. RESTRICCIÓN ABSOLUTA — FILA 1 (0% ETc) EN FLORACIÓN

**Período de restricción:** Desde la detección de floración (GDD ≥ 280) hasta el cuaje (GDD ≥ 420), aproximadamente Octubre–Noviembre.

**Durante ese período:**
- La Fila 1 NO aplica 0% ETc
- La Fila 1 recibe el mismo riego que la Fila 2 (15% ETc)
- El Rain Bird debe reprogramarse manualmente antes del inicio de floración

**Responsable de verificar el estadio fenológico:** César Schiavoni desde el dashboard (alerta automática del motor GDD). Cuando el sistema detecta GDD ≥ 270, envía notificación push al productor: "Brotación avanzada — floración próxima — revisar configuración Fila 1 (0% ETc)".

**Javier debe confirmar visualmente** la presencia de racimos florales emergentes antes de ejecutar la reprogramación del Rain Bird. Foto de confirmación a César y Monteoliva.

---

## 8. ROTACIÓN DE ZONAS DE ESTRÉS ENTRE TEMPORADAS

Para proteger la integridad productiva del viñedo a largo plazo, las filas de estrés severo (15% ETc y 0% ETc) no se aplican en la misma fila en dos temporadas consecutivas:

| Temporada | Fila con 15% ETc | Fila con 0% ETc (secano) |
|---|---|---|
| 2026–2027 | Fila 2 | Fila 1 |
| 2027–2028 | Fila 4 | Fila 3 |
| 2028–2029 | Fila 2 | Fila 1 |

Las filas que estuvieron en 0% ETc la temporada anterior reciben 100% ETc durante el ciclo siguiente de recuperación.

---

## 9. REGISTRO DE EVENTOS DE RESCATE

Planilla de registro acumulada (Google Sheets, pestaña "Rescates"):

| Fecha | Fila | Criterio | Ψ_stem | Síntomas | Hora inicio riego | Duración (h) | Tensiómetro final | Recuperación 48h | Aprobó Monteoliva |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |

**Objetivo:** cero eventos de Nivel 3 (síntomas pre-embolia) durante el protocolo. Máximo tolerable: 2 eventos de Nivel 2 por temporada, ambos notificados y resueltos en < 24 h.

---

*Dra. Mariela Inés Monteoliva — IFRGV-UDEA, INTA-CONICET, CCT Córdoba — Abril 2026*
