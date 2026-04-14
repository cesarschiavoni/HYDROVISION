# HYDROVISION AG - Indice de Documentacion

Proyecto ANPCyT STARTUP 2025 TRL 3-4 | Plataforma Autonoma de Inteligencia Agronomica

---

## Estructura del documento

> Este archivo es el indice. Editar cada seccion en su archivo correspondiente.
> Para generar el PDF final: concatenar en el orden de la tabla.

| # | Archivo | Contenido | Lineas |
|---|---------|-----------|--------|
| 01 | [doc-01-presentacion.md](doc-01-presentacion.md) | Presentacion - Resumen, Problema y TRL | 200 |
| 02 | [doc-02-tecnico.md](doc-02-tecnico.md) | Descripcion Tecnica Detallada del Sistema | 949 |
| 03 | [doc-03-equipo.md](doc-03-equipo.md) | Equipo de Trabajo y Matriz RACI | 71 |
| 04 | [doc-04-plan-trabajo.md](doc-04-plan-trabajo.md) | Plan de Trabajo - 12 Meses y Gate Reviews | 75 |
| 05 | [doc-05-presupuesto.md](doc-05-presupuesto.md) | Presupuesto del Proyecto | 148 |
| 06 | [doc-06-resultados-negocio.md](doc-06-resultados-negocio.md) | Resultados, Modelo de Negocio y Analisis Competitivo | 925 |
| 07 | [doc-07-ip-referencias.md](doc-07-ip-referencias.md) | Propiedad Intelectual y Referencias Cientificas | 87 |
| 08 | [doc-08-vision.md](doc-08-vision.md) | Vision, Conclusion y Aval Monteoliva | 44 |
| 09 | [doc-09-protocolo-campo.md](doc-09-protocolo-campo.md) | Anexo Operativo - Protocolo de Campo Simplificado | 518 |

---

## Numeros clave - fuente unica de verdad

> Estas cifras aparecen en multiples secciones. Buscar con grep antes de cambiar.

| Concepto | Valor | Aparece en |
|----------|-------|------------|
| Monto ANR | USD 120.000 | 01, 05, 08 |
| Contrapartida equipo | USD 30.000 | 01, 05, 08 |
| Total proyecto | USD 150.000 | 01, 05 |
| Zonas hidricas | 5 | 02, 04, 09 |
| Filas experimentales | 5 (+ 5 buffer) | 02, 09 |
| Vides experimento | 680 | 02, 05 |
| Error CWSI objetivo | < +/-0.10 | 02, 06 |
| Nodo precio Tier 1 | USD 950-1.000 | 01, 06 |
| Break-even | 800 ha | 01, 06 |
| TRL actual / objetivo | TRL 3 -> TRL 4 | 01, 02, 08 |

---

## Documentos de gestion interna

> Estos archivos NO forman parte del formulario ANPCyT. Son de uso interno del equipo.

| Archivo | Proposito |
|---------|-----------|
| [Tareas-Equipo-HydroVision-AG.md](Tareas-Equipo-HydroVision-AG.md) | Tareas por persona, estado de avance, honorarios |
| [Gantt-HydroVision-AG.md](Gantt-HydroVision-AG.md) | Cronograma visual de 12 meses |
| [doc-10-analisis-venture.md](doc-10-analisis-venture.md) | Analisis Venture Architect — TAM/SAM/SOM precision, 5 oportunidades desatendidas, 10 problemas con urgencia/WTP (Modulos 3-7 pendientes) |

---

## Codigo generado por Claude Code (abr-2026)

> Scripts funcionales con datos sinteticos. Se re-ejecutan con datos reales de campo.

| Archivo | Proposito | Tarea origen |
|---------|-----------|--------------|
| `cesar/gdd_engine.py` | Motor GDD multi-varietal — 11 cultivos, 3 estrategias de reinicio | Inv. Art. 32 #6 |
| `mvc/app.py` (endpoints nuevos) | POST /api/inference (PINN), GET /api/nodos/{id}/latest, GET /api/validacion/reporte | Inv. Art. 32 #5 + Cesar #3 |
| `investigador/nb_validacion_simulador_scholander.py` | R² scatter, Bland-Altman, calibracion por regimen (5 niveles ETc) | Inv. Art. 32 #8 |
| `cesar/nb_validacion_trl4.py` | 4 graficos TRL 4: HSI vs psi_stem, mapa estres, extensometro, satelite vs nodo | Cesar #6 |
| `matias/modelo_financiero_saas.py` | Modelo financiero 3 escenarios x 5 anios, ARR/EBITDA/LTV-CAC por tier | Matias #5 |
| `cesar/motor_propuesta_automatizada.py` | Propuesta PDF automatizada: Sentinel-2 + ROI personalizado | R15 |

---

## Como ensamblar el PDF final

Para generar el documento completo concatenar en este orden:

    cat doc-01-presentacion.md doc-02-tecnico.md doc-03-equipo.md doc-04-plan-trabajo.md doc-05-presupuesto.md doc-06-resultados-negocio.md doc-07-ip-referencias.md doc-08-vision.md doc-09-protocolo-campo.md > hydrovision-ag-completo.md
