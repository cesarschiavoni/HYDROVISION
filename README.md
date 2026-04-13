# HydroVision AG — Proyecto ANPCyT STARTUP 2025 TRL 3-4

Plataforma autónoma de inteligencia agronómica para cultivos de alto valor mediante termografía LWIR, dendrometría de tronco, motor fenológico automático y fusión satelital con IA Edge.

**Convocatoria:** Proyectos Innovadores Startup 2025 (TRL 3-4) — Agencia I+D+i / FONARSEC
**Préstamo:** BID N° 5293/OC-AR "Programa de Innovación Federal (PIF)"
**Deadline:** 21 de mayo de 2026
**Monto:** USD 150.000 (80% ANR USD 120.000 + 20% contrapartida USD 30.000)

---

## Estructura del repositorio

```
Agro/
├── anpcyt/                           # Documentación ANPCyT
│   ├── anexos/                       # Anexos oficiales de la convocatoria (PDFs)
│   ├── doc-presentar/                # Documentos a presentar
│   │   ├── Plan-de-Trabajo-HydroVision-AG.md   # Documento principal ANPCyT
│   │   ├── carta-acompanamiento-monteoliva.md
│   │   └── carta-compromiso-cesar.md
│   └── instrucciones/                # Bases, condiciones, trámite online
│       ├── Startup 2025 TRL 3-4.md   # Reglas de la convocatoria
│       └── tramite-online.md         # Cronograma + equipo para formulario web
│
├── hydrovision-app/                  # App web completa (FastAPI + Alpine.js + Leaflet)
│   ├── SPEC.md                       # Especificación técnica de la app
│   ├── app/                          # Código fuente
│   │   ├── main.py                   # FastAPI app + lifespan
│   │   ├── core.py                   # Lógica de negocio (CWSI, GDD, alertas)
│   │   ├── models.py                 # SQLAlchemy models
│   │   ├── schemas.py                # Pydantic schemas
│   │   ├── deps.py                   # Auth (HMAC token)
│   │   ├── config.py / mqtt.py
│   │   ├── routers/                  # admin, api, auth, backoffice, emails,
│   │   │                             # inference, pages, report, simulate
│   │   ├── services/                 # email_service, phenology
│   │   └── templates/                # dashboard, admin, backoffice, informe, etc.
│   ├── infra/                        # docker-compose.yml + schema_postgresql.sql
│   ├── services/                     # mqtt_ingester.py
│   └── tests/
│
├── equipo/                           # CVs del equipo (PDFs)
│   └── descartados/                  # Perfiles evaluados y descartados
│
├── legal/                            # Documentación legal y societaria
│   ├── pacto-de-socios.md
│   └── constitucion-sas/             # Datos SAS + generador PDF
│
├── ciencia/                          # Documentación científica (Monteoliva/INTA-CONICET)
│   ├── 01-protocolo-scholander-formal.md
│   ├── 02-aval-cientifico-monteoliva.md
│   ├── 03-contenido-agronomico-formulario.md
│   ├── 04-operativo-rescate-hidrico.md
│   ├── 05-adaptacion-variedades.md
│   ├── 06-outline-paper-cientifico.md
│   ├── 07-cronograma-preciso-sesiones.md   # Sesiones Scholander (autoritativo)
│   └── 08-balance-hidrico-sostenibilidad.md
│
├── gestion/                          # Gestión interna del proyecto
│   ├── Tareas-Equipo-HydroVision-AG.md    # Master task list
│   ├── Gantt-HydroVision-AG.md
│   ├── doc-01-presentacion.md        # Resumen ejecutivo
│   ├── doc-02-tecnico.md             # Documento técnico principal
│   ├── doc-03-equipo.md              # Equipo completo con roles
│   ├── doc-04-plan-trabajo.md        # Fases, gates, hitos (autoritativo)
│   ├── doc-05-presupuesto.md         # Presupuesto ANPCyT (autoritativo USD)
│   ├── doc-06-resultados-negocio.md  # Modelo de negocio, tiers, precios
│   ├── doc-07-ip-referencias.md      # Propiedad intelectual y anterioridad
│   ├── doc-08-vision.md              # Visión a largo plazo
│   ├── doc-09-protocolo-campo.md     # Protocolo operativo de campo
│   ├── doc-10-analisis-venture.md    # Análisis venture/inversión
│   ├── doc-11-identidad-visual.md    # Branding
│   ├── doc-12-patente-inpi.md        # Patente INPI
│   └── figuras-patente/              # 6 SVGs para patente INPI
│
├── cesar/                            # Módulos Python — Backend & IA
│   ├── *.py                          # CWSI, fusión, GDD, pipeline, alertas, etc.
│   ├── briefing-para-cesar.md
│   ├── draft_publicacion_cientifica.md
│   ├── descripcion_tecnica_patente_INPI.md
│   ├── tests/                        # 9 test files, 135+ tests
│   └── outputs/                      # Gráficos de validación TRL4
│
├── investigador/                           # IA — Simulador, PINN, fusión
│   ├── 01_simulador/                 # simulator.py, weather.py, generate_large_dataset.py
│   ├── 02_modelo/                    # pinn_model/loss, train, quantize, unet, preprocessing
│   ├── 03_fusion/                    # fusion_engine, validate_pinn, baseline
│   ├── config/                       # cultivares.json
│   ├── convocatoria-investigador-art32.md
│   ├── diagrama-arquitectura-datos.md
│   ├── pasos-modelos.md              # Guía paso a paso para el investigador Art. 32
│   └── outputs/                      # Resultados validación simulador
│
├── lucas/                            # Firmware & Hardware
│   ├── firmware/                     # nodo_main.ino (ESP32-S3)
│   ├── hardware/                     # BOM-nodo-v1.md (autoritativo), diagramas
│   ├── documentacion/                # Payload JSON, guía instalación, formulario HW
│   ├── briefing-para-lucas.md
│   └── README.md
│
├── matias/                           # Contador — Modelo financiero
│   ├── briefing-para-matias.md
│   ├── modelo_financiero_saas.py     # Proyecciones SaaS/HaaS
│   └── outputs/                      # Gráficos financieros
│
├── mvc/                              # Backend MVC legacy (prototipo TRL 3)
│   ├── app.py                        # FastAPI original
│   ├── models.py                     # SQLAlchemy models
│   ├── mqtt_ingester.py
│   ├── schema_postgresql.sql
│   ├── docker-compose.yml
│   ├── diagrama-interaccion.md
│   ├── templates/                    # dashboard, admin, informe
│   └── tests/
│
└── referencias/                      # Papers y bibliografía científica
```

## Equipo

| Rol | Persona | Carpeta |
|-----|---------|---------|
| Project Leader / Director IA & Backend | César Schiavoni | `cesar/` |
| Hardware & Firmware Engineer | Lucas Bergon | `lucas/` |
| Investigador en Validación de Señales y Datos Agronómicos (perfil Art. 32, a incorporar) | TBD — búsqueda activa CIII/G.In.T.E.A UTN FRC | `investigador/` |
| Contador / Modelo Financiero | Matías Tregnaghi | `matias/` |
| Asesora Científica INTA-CONICET | Dra. Mariela Monteoliva | `ciencia/` |
| Técnico de Campo Principal | Javier Schiavoni | — |
| Enólogo asesor — sitio validación campo | Gabriel Campana | — |
| Agente Propiedad Industrial | Ximena Crespo (Arteaga & Asociados) | — |
| Abogado — pacto de socios | Pablo Contreras | `legal/` |

## Stack técnico

- **Nodo:** ESP32-S3 + MLX90640 (térmica) + SHT31 + extensómetro + LoRa SX1276
- **Backend:** FastAPI + PostgreSQL + Mosquitto MQTT + ChirpStack LoRaWAN
- **IA:** PINN (Physics-Informed Neural Network) para CWSI, U-Net segmentación foliar
- **Fusión:** HSI = 0.35×CWSI + 0.65×MDS (con override por viento)
- **Satélite:** Sentinel-2 vía STAC/GEE
