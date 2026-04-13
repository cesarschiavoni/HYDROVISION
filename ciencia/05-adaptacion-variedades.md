
# ADAPTACIÓN DEL PROTOCOLO A OTRAS VARIEDADES Y REGIONES
## HydroVision AG — Sección §11D del Plan de Trabajo
## Elaborado por: Dra. Mariela Inés Monteoliva (INTA-CONICET)

---

## 1. FUNDAMENTO: POR QUÉ CADA VARIEDAD NECESITA SU PROPIA CALIBRACIÓN

La fórmula CWSI de Jackson (1981) es universal en su estructura pero sus parámetros son específicos de especie, variedad, sistema de conducción y macroclima. Dos variables críticas determinan la magnitud del error si se aplican coeficientes incorrectos:

**1. Estrategia estomática (isohydric vs. anisohydric):**

Las variedades de vid presentan dos estrategias opuestas para enfrentar el déficit hídrico:

| Estrategia | Comportamiento | Ejemplo de variedad | Efecto sobre CWSI |
|---|---|---|---|
| **Isohydric** | Cierra estomas temprano, mantiene Ψ_stem constante a expensas de fotosíntesis | Grenache, Tempranillo, Malbec | CWSI sube bruscamente ante déficit leve → umbrales más bajos |
| **Anisohydric** | Mantiene estomas abiertos, permite caída de Ψ_stem para sostener fotosíntesis | Syrah, Chardonnay, Cabernet Sauvignon | CWSI sube gradualmente → umbrales más altos |

Usar el umbral de alerta de una variedad isohydric en una anisohydric subestima el estrés real. Usar el umbral anisohydric en una isohydric genera alarmas falsas y riego innecesario.

**2. Temperatura base (T_base) para GDD:**

| Cultivo | T_base (°C) | Fuente | T_base incorrecta en ±2°C → error GDD al final de temporada |
|---|---|---|---|
| Vid (Malbec, Cab, Syrah, Bonarda) | 10.0 | Catania & Avagnina, INTA 2007 | ±80–120 GDD → desfase fenológico 5–9 días |
| Olivo | 12.5 | García-Tejero et al. 2018 | ±60–90 GDD → cambio de coeficientes en momento incorrecto |
| Cerezo | 7.0 | CIREN Chile 2010 | ±100–150 GDD → desfase hasta 14 días en brotación |
| Arándano | 7.0 | USDA, Hancock & Finn 2012 | Similar a cerezo |
| Pistacho | 12.0 | Kanber et al. 1993 | ±60 GDD — cultivo de ciclo muy largo |
| Nogal | 10.0 | Sparks 1992 | ±70 GDD |
| Citrus (naranja, limón) | 12.5 | FAO-56 (Allen et al. 1998) | Ciclo casi perenne — GDD de menor relevancia |

---

## 2. TABLA COMPARATIVA DE PARÁMETROS CWSI POR VARIEDAD

### 2.1 Vid (*Vitis vinifera* L.) — Variedades prioritarias HydroVision AG

| Variedad | Estrategia | T_base (°C) | ΔT_LL típico a VPD 2.0 kPa | ΔT_UL típico | Umbral alerta CWSI | Umbral rescate Ψ_stem | Fuente |
|---|---|---|---|---|---|---|---|
| **Malbec** | Isohydric moderado | 10 | −1.8 a −2.2°C | +3.0°C | 0.30 | −1.5 MPa | Calibración Colonia Caroya (en curso) |
| **Cabernet Sauvignon** | Anisohydric | 10 | −2.0 a −2.5°C | +3.0°C | 0.35 | −1.8 MPa | Bellvert et al. 2016; Schultz 2003 |
| **Syrah** | Anisohydric fuerte | 10 | −2.2 a −2.8°C | +3.0°C | 0.40 | −1.8 MPa | Schultz 2003; Medrano et al. 2003 |
| **Bonarda** | Isohydric | 10 | −1.6 a −2.0°C | +3.0°C | 0.28 | −1.4 MPa | Estimado por analogía con Malbec |
| **Torrontés Riojano** | Isohydric | 10 | −1.7 a −2.1°C | +3.0°C | 0.30 | −1.5 MPa | Estimado — pendiente calibración |
| **Chardonnay** | Anisohydric | 10 | −2.1 a −2.6°C | +3.0°C | 0.35 | −1.7 MPa | Bellvert et al. 2016 |
| **Sauvignon Blanc** | Anisohydric moderado | 10 | −2.0 a −2.4°C | +3.0°C | 0.33 | −1.6 MPa | Estimado por analogía Chardonnay |

*Nota: ΔT_LL = T_foliar − T_aire en planta sin estrés. Valores negativos indican que la planta bien hidratada está más fría que el aire (transpiración activa). Los valores de la tabla son para VPD 2.0 kPa; la línea base completa es ΔT_LL = a + b·VPD.*

### 2.2 Otros cultivos prioritarios HydroVision AG

| Cultivo | Especie | T_base (°C) | Umbral alerta CWSI | Umbral rescate Ψ_stem | Estrategia | Fuente |
|---|---|---|---|---|---|---|
| **Olivo** | *Olea europaea* | 12.5 | 0.40 | −3.0 MPa | Anisohydric muy fuerte | García-Tejero et al. 2018; Capraro et al. 2025 |
| **Cerezo** | *Prunus avium* | 7.0 | 0.30 | −1.2 MPa | Isohydric moderado | Blanco & Kalcsits 2021 |
| **Pistacho** | *Pistacia vera* | 12.0 | 0.45 | −3.5 MPa | Anisohydric extremo | Kanber et al. 1993 |
| **Nogal** | *Juglans regia* | 10.0 | 0.35 | −1.5 MPa | Isohydric moderado | Espadafor et al. 2015 |
| **Arándano** | *Vaccinium corymbosum* | 7.0 | 0.25 | −0.8 MPa | Isohydric sensible | Williamson et al. 2015 |
| **Naranja** | *Citrus sinensis* | 12.5 | 0.30 | −1.5 MPa | Isohydric | García-Tejero et al. 2011 |
| **Limón** | *Citrus limon* | 12.5 | 0.32 | −1.6 MPa | Isohydric | FAO-56 Allen et al. 1998 |

*Nota: El olivo tolera déficits severos sin daño productivo — umbral de rescate sustancialmente más negativo que en vid. Arándano es la especie más sensible del portfolio.*

---

## 3. CHECKLIST OPERATIVO — CALIBRACIÓN EN NUEVA VARIEDAD

Antes de activar HydroVision AG en un lote con una variedad no calibrada, el equipo debe completar este checklist. La responsabilidad es de la Dra. Monteoliva (validación científica) y César Schiavoni (configuración del sistema).

### Paso C1 — Verificación previa (antes de instalar el nodo)

- [ ] Confirmar especie y variedad con el productor. Verificar que coincide con la lista de la tabla §2
- [ ] Confirmar sistema de conducción (espaldera, parral, vaso libre) — afecta el ángulo de captura del gimbal
- [ ] Consultar historial de riego previo y obtener las últimas 2–3 temporadas de datos de ETo local (INTA, SMN, INIA Chile)
- [ ] Identificar la fuente bibliográfica de coeficientes provisionales (tabla §2 de este documento)
- [ ] Si la variedad NO está en la tabla §2: escalar a Dra. Monteoliva para definir coeficientes provisionales

### Paso C2 — Configuración inicial del nodo

- [ ] Cargar en el firmware: `varietal` = nombre de variedad, `t_base` = valor de la tabla §2.2
- [ ] Cargar coeficientes provisionales CWSI: `delta_t_ll_a`, `delta_t_ll_b`, `delta_t_ul`
- [ ] Configurar `cwsi_umbral_alerta` y `cwsi_umbral_rescate` según tabla §2
- [ ] Verificar `gdd_brotacion_umbral` para la variedad (vid: 80–120; cerezo: 50–80; olivo: GDD menos relevante por ciclo perenne)

### Paso C3 — Primera sesión de calibración (imprescindible en campo)

Ejecutar en las primeras 2 semanas de operación del nodo:

- [ ] Medir Ψ_stem en ≥ 5 plantas representativas del lote bajo **condiciones de plena hidratación** (Ψ_stem > −0.5 MPa), idealmente 12–24 h después de un riego completo o lluvia > 10 mm
- [ ] Registrar simultáneamente: T_foliar (app del nodo), T_aire (SHT31), HR (SHT31), hora → calcular VPD
- [ ] El sistema calcula automáticamente el offset del baseline vía EMA (Nivel 2 del stack de calibración)
- [ ] Si la diferencia entre el CWSI calculado con coeficientes provisionales y el CWSI esperado (≈ 0.05–0.15 para planta sin estrés) supera 0.15 unidades: reportar a Monteoliva para revisión de coeficientes

### Paso C4 — Validación a los 30 días

- [ ] Medir Ψ_stem en ≥ 10 plantas en 2 fechas distintas: una con CWSI < 0.20 (sin estrés) y una con CWSI > 0.40 (estrés moderado)
- [ ] Calcular R² del ajuste lineal Ψ_stem ~ CWSI con los datos acumulados
- [ ] Si R² < 0.50: escalar a Monteoliva. El sistema puede seguir operando pero las alertas se marcan con "calibración provisional"
- [ ] Si R² ≥ 0.50: calibración aceptable para uso comercial. Continuar acumulando datos para mejorar

### Paso C5 — Actualización del modelo PINN (el investigador Art. 32)

- [ ] Una vez que el nodo acumula ≥ 100 pares (Ψ_stem medido, frame LWIR + metadata), exportar el dataset al pipeline de el investigador Art. 32
- [ ] El dataset se integra al proceso de fine-tuning del modelo PINN para la nueva variedad
- [ ] Tiempo estimado de fine-tuning: 2–4 días de cómputo en la GPU local (RTX 3090)

---

## 4. REGIONES PRIORITARIAS — PARÁMETROS ESPECÍFICOS

### 4.1 Mendoza — Valle de Uco (foco Año 1 comercial)

| Parámetro | Valor | Notas |
|---|---|---|
| Altitud | 800–1.200 m s.n.m. | Amplitud térmica diaria mayor → VPD más extremo al mediodía |
| VPD típico Jan–Feb (12 hs) | 3.0–5.5 kPa | Rango más amplio que Córdoba → mayor importancia de línea base calibrada |
| ETo media anual | 1.100–1.400 mm | Alta demanda evaporativa — RDI más difícil de mantener |
| Precipitación media anual | 180–350 mm | Lluvia insuficiente para el cultivo — 100% dependencia del riego |
| Suelo dominante | Arenoso-franco a franco-arcilloso | Menor capacidad de retención que Colonia Caroya → más frecuencia de riego |
| Variedades principales | Malbec (68%), Cabernet Sauvignon (14%), Chardonnay (8%) | |
| Ajuste específico del protocolo | Ventana de medición 9:30–12:30 hs (VPD sube más rápido) | Evitar medición después de las 12:30 hs en enero/febrero |

### 4.2 San Juan — Valle del Tulum (foco olivo y vid Año 1)

| Parámetro | Valor | Notas |
|---|---|---|
| VPD típico Dic–Feb (12 hs) | 4.0–6.5 kPa | El más alto del portfolio — condiciones extremas |
| ETo media anual | 1.400–1.700 mm | La mayor del portfolio |
| Temperatura máxima promedio enero | 36–40°C | Temperatura foliar puede superar 45°C — verificar rango operativo del MLX90640 |
| Olivo: Ψ_stem pre-cosecha tolerado | −3.0 a −4.0 MPa | El olivo es muy resistente — los umbrales de vid NO aplican |
| Ajuste clave | T° carcasa nodo puede superar 55°C — verificar disipación térmica del PCB | |

### 4.3 Chile — Región de Coquimbo y Maule (foco Año 2 PCT)

| Parámetro | Valor | Notas |
|---|---|---|
| Megasequía activa | −40% precipitaciones vs. media histórica 2010–2024 | Demanda creciente de tecnología de riego de precisión |
| Marco legal | Ley 18.450 de fomento al riego (subsidios gubernamentales) — activo | Riego tecnificado subsidiado → bajo barrera de adopción |
| Cultivos prioritarios | Chardonnay, Cab. Sauvignon (Maule); Nogal, Olivo (Coquimbo) | |
| Ajuste legal | Certificación de calibración por organismo chileno (INIA Chile) requerida para uso en licitaciones públicas | |

---

## 5. IMPACTO DEL SISTEMA DE CONDUCCIÓN SOBRE EL ÁNGULO DEL GIMBAL

La posición óptima del gimbal varía según el sistema de conducción. El técnico de instalación debe verificar estos ángulos con el inclinómetro de la app antes de apretar los tornillos del bracket:

| Sistema de conducción | Ángulo vertical óptimo | Ángulo horizontal | Distancia nodo-planta | Cultivos típicos |
|---|---|---|---|---|
| Espaldera simple o doble | 35–45° | ±20° (5 posiciones) | 0.6–1.0 m del tronco | Vid (todas), cerezo en alta densidad |
| Parral | 75–85° (casi cenital) | ±15° | 1.0–1.5 m lateral | Vid parral (San Juan), nogal |
| Vaso libre | 25–35° | ±25° | 0.8–1.2 m del tronco | Olivo intensivo, cerezo, pistacho |
| Alta densidad lineal | 40–50° | ±15° | 0.5–0.8 m | Arándano, cerezo enano |

---

## 6. CHECKLIST DE VALIDACIÓN DE COEFICIENTES — USO INTERNO

Para que los coeficientes CWSI de una variedad sean considerados "validados" por Dra. Monteoliva y puedan incorporarse a la base de datos de HydroVision AG como referencia permanente:

- [ ] ≥ 30 pares (Ψ_stem, CWSI medido) con VPD en rango 1.0–4.5 kPa
- [ ] Cobertura del rango completo de Ψ_stem de la variedad (desde sin estrés hasta umbral de rescate)
- [ ] R² del ajuste lineal Ψ_stem ~ CWSI ≥ 0.60 (meta ≥ 0.75 post-TRL 4)
- [ ] Al menos 2 sesiones de campo separadas por ≥ 30 días
- [ ] Revisión y aprobación firmada por Dra. Monteoliva
- [ ] Incorporación al documento de coeficientes (secreto comercial, repositorio privado)

---

*Dra. Mariela Inés Monteoliva — INTA EEA Córdoba / CONICET — Abril 2026*
