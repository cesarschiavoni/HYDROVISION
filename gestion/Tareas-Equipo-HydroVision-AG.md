# Tareas por Miembro del Equipo — HydroVision AG
**Proyecto ANPCyT Startup 2025 TRL 3-4 · Colonia Caroya, Córdoba**
Última actualización: abril 2026

---

## César Schiavoni — Director de Desarrollo IA / Project Leader ANPCyT
**Dedicación:** 40 hs/semana (20 hs/sem facturadas al proyecto · 20 hs/sem aporte en especie)
**Período:** Mes 1–12
**Honorarios:** USD 1.500/mes × 12 = **USD 18.000** (20 hs/sem ANR; las otras 20 hs/sem son contrapartida en especie)

### Tareas técnicas (con Claude Code)

> **Scope TRL 3-4:** MVC funcional con nodo + LoRa — backend FastAPI recibe payloads MQTT, persiste en PostgreSQL, visualización básica de datos. No dashboard comercial, no app móvil, no SaaS, no onboarding QR. El output del proyecto es el MVC funcional + modelo PINN validado + notebooks con R² vs Scholander + motor de alertas agronómicas. Apps y API comercial son TRL 5.

| # | Tarea | Período | Entregable |
|---|-------|---------|------------|
| 1 | Generación y validación de los **13 módulos Python del stack HSI**: cwsi_formula, thermal_pipeline, gdd_engine, synthetic_data_gen, sentinel2_fusion, dendrometry, combined_stress_index, baseline, fusion_engine, field_config, optical_health, pipeline_satelital, gee_connector | Mes 1–6 | Módulos con tests unitarios básicos |
| 2 | ~~**Pipeline de ingesta mínima**~~ → **✓ Claude Code** — schema PostgreSQL en `mvc/schema_postgresql.sql` (7 tablas), `mvc/docker-compose.yml` (FastAPI + PostgreSQL + Mosquitto + ChirpStack + Redis), **`mvc/mqtt_ingester.py`** (suscriptor MQTT → PostgreSQL INSERT con 3 topics: telemetry/alert/status) + **14 tests** en `mvc/tests/test_mqtt_ingester.py` (payload parsing, calidad descarte, topic routing, irrigation state). César valida con nodo real | Mes 4–6 | Ingesta funcional, datos accesibles para análisis |
| 3 | ~~**FastAPI mínimo** (3 endpoints)~~ → **✓ Claude Code** — POST /ingest (ya existía), GET /api/nodos/{id}/latest, GET /api/validacion/reporte (CSV HSI vs ψ_stem) implementados en `mvc/app.py` | Mes 5–7 | API operativa para el experimento de campo |
| 4 | Integración firmware Lucas con stack Python: validar protocolo MQTT nodo↔backend, parser payload JSON v1 (schema documentado en `lucas/documentacion/payload-json-v1-schema.md` — **✓ Claude Code**), test end-to-end en banco | Mes 3–5 | Integración validada con nodo real |
| 5 | **Ejecución entrenamiento GPU en RTX 3070 propio** (contrapartida en especie): simulador físico ~40h · 1M imágenes + fine-tuning PINN + cuantización INT8. Pipeline implementado; César ejecuta y monitorea con W&B | Mes 4–8 | Modelos entrenados y validados |
| 6 | ~~**Notebooks de validación TRL 4**~~ → **✓ Claude Code** — (a) `cesar/nb_validacion_trl4.py`: 4 gráficos HSI vs ψ_stem (R²=0.84), mapa estrés, calibración extensómetro (R²=0.92), satélite vs nodo; (b) **`cesar/nb_validacion_fusion_satelite.py`**: R13 completo — scatter R² calibración S2 (R²=0.957), mapa CWSI campo, correlación NDWI↔CWSI, anomalías NDVI. Datos sintéticos; se re-ejecuta con datos reales | Mes 7–10 | Evidencia técnica para Gate Reviews G2/G3 y publicación |
| 7 | Documentación técnica ANPCyT: informes trimestrales (template **✓ Claude Code** en `cesar/template_informe_trimestral_anpcyt.md`), memoria descriptiva, presentaciones Gate Review | Mes 3, 6, 9, 12 | Reportes aprobados |
| 8 | ~~**Motor de propuesta automatizada**~~ → **✓ Claude Code** — `cesar/motor_propuesta_automatizada.py`: análisis Sentinel-2 sintético → densidad óptima nodos → ROI personalizado → PDF. Demo: 4 propuestas generadas. **Herramienta interna de prospección TRL 4; en TRL 5 conecta a GEE API para producción** | Mes 8–10 | Herramienta interna para estimación comercial |

### Tareas de gestión
| # | Tarea | Período |
|---|-------|---------|
| 9 | Coordinación con Dra. Monteoliva: protocolo Scholander, parámetros PINN, validación agronómica | Mes 1–12 |
| 10 | ~~R12: Motor de alertas agronómicas~~ → **✓ Claude Code** — `cesar/alertas_agronomicas.py` (12 reglas codificadas y testeadas, umbrales configurables). Módulo Python funcional entregado como R12 en TRL 4. **La interfaz de configuración por productor (app, push/SMS) es TRL 5** | Mes 6–8 |
| 11 | Coordinación logística de campañas de campo con Javier Schiavoni | Mes 3–9 |
| 12 | Interlocución ANPCyT: rendiciones, hitos, comunicación oficial con el organismo | Mes 1–12 |
| 13 | Coordinación con Matías Tregnaghi: presupuesto ejecutivo mensual, rendiciones | Mes 1–12 |
| 14 | ~~R10: Informe de validación comercial~~ → **Diferido TRL 5** — template pre-generado con Claude Code en `cesar/template_entrevistas_productores_R10.md` | TRL 5 |
| 15 | **Campaña externa** — César + Lucas Bergon: Bodega Las Cañitas ×1 (Gabriel Campana). Validación del sistema en viñedo externo, entrevistas R10 + vinculación productores TRL 5. Las campañas Mendoza/San Juan son TRL 5+ | Mes 11 |
| 16 | **Co-autoría publicación científica** con Dra. Monteoliva e Inv. Art. 32 — resultados HSI vs ψ_stem en Malbec. Draft generado con Claude Code; César aporta datos y análisis estadístico | Mes 10–12 |
| 17 | **Descripción técnica para patente INPI** — **✓ Claude Code** en `cesar/descripcion_tecnica_patente_INPI.md`. Entregado a Ximena Crespo para redacción de reivindicaciones legales | Mes 8–9 |
| 18 | **Documentación ANPCyT para presentación** — **✓ Claude Code**: carta compromiso (`anpcyt/doc-presentar/carta-compromiso-cesar.md`), carta acompañamiento Monteoliva (`anpcyt/doc-presentar/carta-acompanamiento-monteoliva.md`), draft publicación (`cesar/draft_publicacion_cientifica.md`). César coordina firmas | Mes 1–2 |

---

## Lucas Bergon — COO / Líder Hardware, Firmware & Embedded
**Empresa:** MBG Controls, Colonia Caroya
**Dedicación:** 50% Mes 1–6 (diseño HW + firmware) · 25% Mes 7–12 (integración campo + validación)
**Honorarios:** USD 1.500/mes × 6 + USD 1.000/mes × 6 = **USD 15.000**
**Nota:** aporte en especie de Lucas (horas USD 4.650 + herramientas USD 400 + equipamiento MBG USD 710 = USD 5.760) figura como contrapartida — no incluido en honorarios.

### Resuelto con Claude antes del inicio del proyecto (Lucas solo debe revisar y validar)

| Qué | Archivo |
|---|---|
| Ciclo principal, deep sleep, RTC memory, Node ID desde MAC | `lucas/firmware/nodo_main.ino` |
| Lógica completa CWSI / HSI / MDS / Tc_dry / auto-calibración Tc_wet | `lucas/firmware/nodo_main.ino` |
| Serialización JSON payload v1 + topics MQTT telemetry/status/alert | `lucas/firmware/nodo_main.ino` |
| Driver **MLX90640** I2C + filtro píxeles foliares P20–P75 | `lucas/firmware/driver_mlx90640.h` |
| Driver **ADS1231** bit-bang 24-bit + **DS18B20** corrección térmica α=2.5 µm/°C | `lucas/firmware/driver_mds.h` |
| Driver **SHT31** I2C → t_air / rh | `lucas/firmware/driver_sht31.h` |
| Driver **DS3231 RTC** I2C + sync GPS | `lucas/firmware/driver_rtc.h` |
| Driver **GPS u-blox NEO-6M** UART1 + TinyGPSPlus + caché RTC memory | `lucas/firmware/driver_gps.h` |
| Driver **anemómetro RS485** Modbus RTU + CRC16 via MAX485 | `lucas/firmware/driver_anemometro.h` |
| Driver **pluviómetro** ISR IRAM_ATTR + debounce → rain_mm | `lucas/firmware/driver_pluviometro.h` |
| Driver **piranómetro BPW34** ADC promedio 8 muestras → rad_wm2 | `lucas/firmware/driver_piranometro.h` |
| Driver **bomba peristáltica** Wet Ref GPIO pulso temporizado | `lucas/firmware/driver_bomba_wetref.h` |
| Driver **gimbal MG90S** LEDC PWM 16-bit + 6 posiciones fijas + 1 nadir condicional (viento > 20 km/h) = 7 ángulos totales + fusión multi-frame | `lucas/firmware/driver_gimbal.h` |
| Driver **LoRa SX1276** `publicar_lora(topic, json)` + sleep pre-deep-sleep | `lucas/firmware/driver_lora.h` |
| Driver **PMS5003** partículas UART1 — detección automática fumigación + lluvia | `lucas/firmware/driver_pms5003.h` |
| Driver **ICM-42688-P IMU** SPI — verifica estabilización gimbal antes de captura, detecta desplazamiento | `lucas/firmware/driver_imu.h` |
| ~~Driver **LED tricolor + sirena**~~ (REMOVIDO — alertas vía WhatsApp, email y dashboard) | ~~`lucas/firmware/driver_alertas.h`~~ |
| Driver **motor GDD + fenología autónoma** — 10 estadios Malbec, CWSI dinámico por estadio, sleep adaptativo | `lucas/firmware/driver_gdd.h` |
| **ISO_nodo** (diagnóstico lente) — `mlx_iso_nodo(t_air)` integrado en driver_mlx90640.h | `lucas/firmware/driver_mlx90640.h` |
| Lista de librerías MicroPython | `lucas/firmware/requirements.txt` |
| BOM v1 con todos los componentes y decisiones documentadas | `lucas/hardware/BOM-nodo-v1.md` |
| Sección hardware completa para formulario ANPCyT | `lucas/documentacion/hardware-formulario-ANPCyT.md` |

### Tareas Mes 1–6 (diseño hardware y validación — lo que realmente hace Lucas)
| # | Tarea | Período |
|---|-------|---------|
| 1 | **Validar firmware en banco**: cargar módulos MicroPython en ESP32-S3 DevKit, confirmar que los 15 drivers corren sin errores, verificar salida REPL de cada sensor | Mes 1 |
| 2 | **Calibrar 3 constantes** con hardware real: `ADS1231_COUNTS_PER_UM` (extensómetro referencia), `PYRANO_WPM2_PER_MV` (piranómetro referencia), `PLUV_MM_PER_PULSE` (datasheet sensor comprado) | Mes 2–3 |
| 3 | ~~**Confirmar PIN_BAT_ADC** (GPIO 11)~~ → **✓ Resuelto** — PIN_BAT_ADC movido a GPIO 40 (`config.h`). SPI explícito reasignado a GPIO 34/33/32 para evitar conflicto. Verificar en PCB que GPIO 40 (ADC1_CH9) está libre. | Mes 1 |
| 4 | **Integración modular TRL4**: cableado ESP32-S3 DevKit + breakouts I2C/SPI (MLX90640, SHT31, IMU, etc.) en carcasa Hammond IP67 200×150×100mm | Mes 1–3 |
| 5 | **Montaje 10 nodos prototipo (5 calibración + 5 producción)** — carcasa Hammond IP67 + pasacables M16 + sistema de montaje campo | Mes 2–4 |
| 6 | **Testing integrado en banco**: autonomía ≥ 72h, deep sleep 8µA, IP67 (0–45°C), vibración gimbal | Mes 4–6 |
| 7 | Anotación inicial del dataset térmico (~400 frames MLX90640) con el Inv. Art. 32 | Mes 4–6 |

### Tareas Mes 7–12 (integración campo y validación)
| # | Tarea | Período |
|---|-------|---------|
| 11 | Instalación física de los **10 nodos** en el viñedo experimental (1 por fila, filas 1–10: 5 en zona de calibración + 5 en zona de producción, junto a Javier Schiavoni). **Posición: planta central de la fila (~planta 68 de 136)**. Evitar las 5 plantas de cada extremo de la fila — efecto borde por exposición diferencial y mezcla de píxeles Sentinel-2. | Mes 3–4 |
| 12 | Firmware OTA: actualizaciones over-the-air, corrección de bugs detectados en campo | Mes 7–12 |
| 13 | Soporte técnico a Javier: diagnóstico remoto por dashboard ISO_nodo, reemplazo de componentes | Mes 7–9 |
| 14 | ~~Documentación técnica definitiva~~ → **✓ Claude Code** (estructura) — `lucas/documentacion/guia-instalacion-nodo-v1.md` (guía completa de instalación). **Lucas revisa, valida y agrega fotos reales del nodo instalado** | Mes 4–6 |
| 15 | **Campaña externa** con César — Bodega Las Cañitas ×1 (Gabriel Campana): instalación temporal de nodo en viñedo externo, soporte HW en campo, diagnóstico de conectividad LoRa. Las campañas Mendoza/San Juan son TRL 5+ | Mes 11 |
| 16 | ~~Documentación complementaria~~ → **✓ Claude Code**: diagrama hidráulico-eléctrico (`lucas/hardware/diagrama-hidraulico-electrico.md`), control fenológico de riego (`lucas/documentacion/control-fenologico-riego.md`), diagrama de interacción MVC (`mvc/diagrama-interaccion.md`) | — |

---

## Investigador en Validación de Señales y Datos Agronómicos — Perfil científico-tecnológico Art. 32 (a incorporar)
**Dedicación:** ~5 hs/semana promedio (~177 hs totales en 12 meses)
**Honorarios:** USD 500/mes × 12 = **USD 6.000**
**Perfil buscado:** investigador con formación en procesamiento de señales, estadística aplicada o instrumentación — CIII / G.In.T.E.A UTN FRC o equivalente. **Perfil científico-tecnológico** según Art. 32 Bases y Condiciones: contribución original al análisis de correlaciones CWSI↔MDS↔Ψstem, calibración de sensores dendrómetro por regresión y diseño experimental óptimo (OED). La infraestructura ML (PINN, simulador, U-Net, pipeline de entrenamiento) está implementada — el investigador valida los resultados de campo, no desarrolla infraestructura.

### Capa de modelo IA
| # | Tarea | Período | Entregable |
|---|-------|---------|------------|
| 1 | **Código del simulador físico** de imágenes térmicas: balance energético foliar calibrado para Malbec, output ajustado al MLX90640 (NETD ~100 mK). **César ejecuta los runs en su RTX 3070 (~40h, 1M imágenes)** — el Inv. Art. 32 revisa los resultados estadísticos | Mes 1–5 | Script validado + dataset sintético |
| 2 | ~~Función de pérdida PINN custom en PyTorch~~ → **✓ Claude Code** — implementado en `investigador/02_modelo/pinn_loss.py` + `pinn_model.py` | — | Resuelto |
| 3 | ~~**Pipeline de entrenamiento completo**~~ → **✓ Claude Code** — estructura `investigador/` con train/val splits, W&B config | — | Resuelto |
| 4 | ~~U-Net++ ResNet34 para segmentación semántica 32×24 px~~ → **✓ Claude Code** — implementado en `investigador/02_modelo/unet_segmentation.py` | — | Resuelto |
| 5 | ~~Cuantización INT8 + **deploy PINN en backend FastAPI**~~ → **✓ Claude Code** — endpoint POST /api/inference en `mvc/app.py` con carga lazy del modelo PINN (FP32 o INT8), latencia < 1s. `quantize.py` ya existía. | — | Resuelto |
| 6 | ~~Motor GDD multi-varietal~~ → **✓ Claude Code** — `cesar/gdd_engine.py` extendido a 11 cultivos: Malbec, Cabernet, Bonarda, Syrah, Olivo (T_base=12.5°C), Arándano (7°C), Cerezo (4.5°C), Pistacho, Nogal, Citrus Naranja/Limón. 3 estrategias reinicio + horas de frío. 14 tests pasan. | Mes 2–4 | Motor fenológico operativo |
| 7 | ~~Modelo de correlación CWSI↔NDWI para fusión Sentinel-2~~ → **✓ Claude Code** — `CWSINDWICorrelationModel` en `cesar/sentinel2_fusion.py` | — | Resuelto |
| 8 | ~~Validación del simulador~~ → **✓ Claude Code** (estructura) — `investigador/nb_validacion_simulador_scholander.py`: R² scatter, Bland-Altman, calibración por régimen, histograma error (R²=0.99 con datos sintéticos). **Inv. Art. 32 re-ejecuta con datos Scholander reales de Monteoliva y valida estadísticamente** | Mes 5–9 | R² simulador vs. real documentado |

### Capa de hardware y sensores
| # | Tarea | Período |
|---|-------|---------|
| 9 | ~~Integración sensores MLX90640 + SHT31 + piranómetro: parser payload JSON v1~~ → **✓ Claude Code** — `procesar_payload()` en `cesar/pipeline_satelital.py` | — |
| 10 | Coordinación con Lucas Bergon: layout PCB, validación protocolo I2C MLX90640, rango ADC piranómetro | Mes 2–5 |
| 11 | Anotación dataset térmico (~400 frames MLX90640) con Lucas Bergon | Mes 4–6 |
| 12 | ~~Diagrama de arquitectura de datos~~ → **✓ Claude Code** — `investigador/diagrama-arquitectura-datos.md`: flujo completo nodo→LoRa→gateway→MQTT→FastAPI→PostgreSQL→dashboard | — |

---

## Dra. Mariela Monteoliva — Investigadora INTA-CONICET
**Institución:** MEBA-IFRGV-UDEA, CCT Córdoba
**Dedicación:** ~180 hs efectivas en 12 meses · ~5h/mes diseño (Mes 1–3) · ~25h/mes capturas (Mes 4–6) · ~12h/mes validación (Mes 7–9) · ~18h/mes publicación (Mes 10–12)
**Honorarios:** USD 900/mes × 12 = **USD 10.800**

| # | Tarea | Período | Horas | Propósito |
|---|-------|---------|-------|-----------|
| 1 | ~~Diseño del protocolo experimental~~ → **✓ Claude Code** (estructura completa) — `ciencia/01-protocolo-scholander-formal.md` + `cesar/planilla_scholander_template.csv`. **Mariela revisa, ajusta y aprueba** el protocolo y la planilla | Mes 1–2 | 8h | Base científica del TRL 4 |
| 2 | Calibración de parámetros CWSI para Malbec Colonia Caroya: coeficientes ΔT_LL y ΔT_UL por estadio fenológico. Coeficientes teóricos en `ciencia/03-contenido-agronomico-formulario.md` — **calibración real con datos de campo es de Mariela** | Mes 1–3 | 15h | Parametrización local del modelo |
| 3 | Supervisión y entrenamiento de Javier Schiavoni en el protocolo Scholander (1–2 sesiones presenciales) | Mes 3 | 8h | Habilitación del técnico de campo |
| 4 | ~~Validación del simulador~~ → **✓ Claude Code** (script) — `investigador/nb_validacion_simulador_scholander.py`. **Mariela interpreta resultados y valida que la fisiología sea coherente** con datos reales de campo | Mes 5–9 | 15h | Garantiza que el simulador refleja la fisiología real |
| 5 | Revisión científica de los 4 informes de sesiones Scholander (OED): verificación de valores ψ_stem, detección de outliers, aprobación de frames para el dataset PINN | Mes 4–9 | 60h | Control de calidad del dataset de entrenamiento |
| 6 | ~~Co-autoría publicación~~ → **✓ Claude Code** (draft + outline) — `cesar/draft_publicacion_cientifica.md` + `ciencia/06-outline-paper-cientifico.md`. **Mariela revisa, aporta discusión fisiológica, y co-firma** | Mes 10–12 | 30h | Visibilidad científica del proyecto |
| 7 | Asesoramiento continuo al equipo: consultas sobre fisiología hídrica, interpretación de anomalías en datos CWSI/MDS, criterio para descarte de sesiones | Mes 1–12 | 44h | Soporte científico transversal |

**Desglose auditado:** 8 + 15 + 8 + 15 + 60 + 30 + 44 = **180 horas**

---

## Javier Schiavoni — Técnico de Campo Principal
**Residencia:** Colonia Caroya (a metros del viñedo experimental)
**Dedicación:** ~227 hs efectivas · Mes 1–9 (≈7 hs/semana promedio)
**Honorarios:** USD 1.000/mes × 9 = **USD 9.000**

### Para qué sirve cada tarea

| # | Tarea | Período | Propósito claro |
|---|-------|---------|-----------------|
| 0 | Preparación de la base para el tanque australiano 20.000L: nivelado del terreno con tractor, encofrado de losa de hormigón 3m×3m×0,15m, mezcla y vertido de hormigón, curado 48h antes de colocar el tanque. Sin base adecuada el tanque lleno (~20 ton) puede hundirse, inclinarse o agrietarse. | Mes 1 · ~10h | Prerequisito de toda la instalación de riego — el tanque no puede colocarse sin una base nivelada y firme |
| 1 | Instalación completa infraestructura de riego: colocación del tanque sobre la losa, excavación zanjas para cañería PE, tendido 1.450m cinta drip (10 filas), instalación eléctrica 70m, operación tractor, conexión 10 solenoides Rain Bird (1 por fila, todas las filas), pruebas hidráulicas | Mes 1–2 · 80h | Infraestructura base: sin riego diferencial por fila no hay protocolo de 5 regímenes hídricos |
| 2 | Mantenimiento del viñedo experimental: verificación de caudales, lectura de tensiómetros, registro de lluvia, detección de fallas en solenoides | Mes 1–9 · 8h/mes = 72h | Mantiene los 5 regímenes hídricos diferenciados activos durante toda la campaña |
| 3 | Instalación del extensómetro de tronco en 10 plantas de referencia (1 por fila): abrazadera aluminio anodizado, cara norte, 30 cm altura, verificación strain gauge. **La planta de referencia debe ser la misma planta central donde se instala el nodo** (planta 68 de la fila, ≥5 plantas alejada de cada extremo). | Mes 3 · 45 min/nodo × 10 = 8h | El extensómetro mide MDS 24/7 — es la señal de tronco que calibra la cámara y valida el modelo |
| 4 | Operación de la bomba Scholander en 4 sesiones OED (Mes 4–9): medición ψ_stem en ventana 10–14hs, registro en planilla `cesar/planilla_scholander_template.csv` (**✓ Claude Code**), etiquetado de frames | Mes 4–9 · 5h/sesión × 4 = 20h | **No es para calibrar el sistema** — eso lo hacen el Wet Ref y el extensómetro solos. Es para: (a) validar que la estimación MDS→ψ_stem es correcta para este viñedo, (b) etiquetar los frames que entrena el modelo PINN, (c) medir el R² del HSI contra gold standard |
| 5 | Verificación del extensómetro en cada sesión Scholander: inspección visual de abrazadera, cable y conexiones, confirmación de D_max/D_min del día en el celular (Xiaomi Redmi Note 13 Pro+ 5G) | Mes 4–9 · 15 min/sesión × 4 = 1h | Confirma que el sensor de tronco está operando correctamente antes de cada sesión |
| 6 | Coordinación logística y registro: verificar condiciones meteorológicas (>48h sin lluvia significativa antes de sesión), activar ventanas horarias 9hs/12hs/16hs | Mes 4–9 · ~30 min/semana × 14 semanas = 8h | Garantiza que las mediciones se toman en las condiciones correctas |
| 7a | Recarga mensual del reservorio de 10L del Wet Ref con agua destilada o clorada (10 nodos) | Mes 4–10 · 15 min/nodo × 10 × 7 meses = 18h | El Wet Ref físico provee T_wet en tiempo real — **es el mecanismo principal de calibración térmica**, sin este la cámara usa solo el modelo matemático de respaldo |
| 7b | Limpieza del lente de la cámara térmica **únicamente cuando el dashboard reporta ISO_nodo < 80%** — el sistema avisa por la tablet | Eventual · ~2 eventos × 10 nodos × 30 min = 10h | Mantenimiento reactivo basado en diagnóstico automático — no hay limpiezas fijas semanales |
| 7c | **Fumigación y lluvia: sin acción requerida.** El sensor PMS5003 detecta automáticamente el aerosol de fumigación (PM2.5 > 200 µg/m³) y la lluvia con aerosol. El firmware invalida las capturas MLX90640 y extensómetro durante el evento y por 4h post-fumigación / 3h post-lluvia. El payload incluye `calidad_captura` y el backend descarta los frames automáticamente. | — | Javier no necesita hacer nada durante ni después de una fumigación |

**Desglose auditado:** 10 (base tanque) + 80 (riego) + 72 (mant. viñedo) + 8 (extensómetros ×10 nodos) + 20 (Scholander 4 sesiones OED) + 1 (verif. extens.) + 8 (coord. logística) + 18 (Wet Ref ×10 nodos) + 10 (limpieza lente ×10 nodos) = **227 horas**

---

## Franco Schiavoni — Soporte de Campo
**Rol:** asistencia a Javier en instalación y sesiones Scholander
**Dedicación:** sin costo adicional (productor residente, aporte en especie familiar)

| # | Tarea | Período |
|---|-------|---------|
| 1 | Asistencia en instalación del riego diferencial y de los nodos | Mes 1–4 |
| 2 | Asistencia en sesiones Scholander: sostener plantas, registrar datos en planilla paralela, soporte logístico | Mes 4–9 |

---

## Matías Tregnaghi — CFO / Contador Público Senior
**Dedicación:** 20% part-time · Mes 1–12
**Honorarios:** USD 500/mes × 12 = **USD 6.000**

| # | Tarea | Período | Detalle |
|---|-------|---------|---------|
| 1 | Setup financiero y legal: constitución SAS, inscripción AFIP, estructura tributaria | Mes 1–2 | Base legal del proyecto |
| 2 | Presupuesto ejecutivo mensual: tracking de gastos vs. plan ANPCyT | Mes 1–12 | Control financiero continuo |
| 3 | Rendiciones ANPCyT: informes trimestrales de avance financiero + rendición final | Mes 3, 6, 9, 12 | Obligación contractual con el organismo |
| 4 | Liquidación de honorarios mensuales de cada miembro del equipo | Mes 1–12 | Cumplimiento laboral/fiscal |
| 5 | ~~Análisis de rentabilidad SaaS por tier~~ → **✓ Claude Code** — `matias/modelo_financiero_saas.py`: 3 escenarios × 5 años, ARR/EBITDA/LTV-CAC por tier, 4 gráficos + 2 CSVs. **Matías revisa supuestos y ajusta parámetros** | Mes 10–12 | Preparación ronda post-ANPCyT |
| 6 | Coordinación con Pablo Contreras (abogado) en pacto de socios y cláusulas de PI | Mes 1–3 | Matías hace la SAS; Pablo redacta el pacto de socios |

---

## Ximena Crespo — Agente de Propiedad Intelectual (Patente)
**Firma:** Arteaga y Asociados
**Rol:** contratada exclusivamente para patente — honorario incluido en ítem Propiedad Intelectual (USD 3.500)

| # | Tarea | Período | Detalle |
|---|-------|---------|---------|
| 1 | **Búsqueda formal de anterioridad** nacional e internacional con informe certificado (Google Patents, Espacenet, INPI) | Mes 6–8 | Informe certificado — input para reivindicaciones |
| 2 | **Redacción de reivindicaciones y descripción técnica** para solicitud de patente de invención INPI (sistema CWSI + gimbal + PINN + GDD multi-varietal + fusión HSI) | Mes 8–10 | César entrega descripción técnica base generada con Claude Code; Ximena redacta reivindicaciones legales |
| 3 | **Presentación solicitud de patente INPI** Argentina | Mes 10–11 | Tasas INPI + gestión administrativa |
| 4 | **Gestión primera respuesta del examinador INPI** | Mes 11–12 | Respuesta a observaciones formales y de fondo |
| 5 | Estrategia PCT para Chile, Brasil y USA (preparación Año 2 — no se ejecuta en TRL 4) | Mes 11–12 | Documento de estrategia, no presentación |

---

## Pablo Contreras — Abogado
**Rol:** pacto de socios, asesoramiento legal PI
**Dedicación:** puntual — Mes 1–3
**Honorarios:** incluido en ítem Legal + constitución SAS (USD 800)

| # | Tarea | Período | Detalle |
|---|-------|---------|---------|
| 1 | **Redacción del pacto de socios** con cláusulas de vesting (4 años, cliff 12 meses), PI y non-compete | Mes 1–3 | Coordinado con Matías Tregnaghi y César |
| 2 | Asesoramiento sobre titularidad de la propiedad intelectual del software y hardware — cesión de IP a HydroVision AG SAS | Mes 2–3 | Definir estructura legal de protección IP |

---

## Gabriel Campana — Asesor Vitivinícola / Validación Varietal
**Bodega:** Estancia Las Cañitas, Colonia Caroya
**Rol:** advisor en equity — sin costo para presupuesto ANPCyT
**Dedicación:** puntual — Mes 10–12 (validación de campo)

| # | Tarea | Período | Detalle |
|---|-------|---------|---------|
| 1 | **Validación de campo en Bodega Las Cañitas** con al menos 2 variedades distintas a Malbec | Mes 10–12 | Provee acceso al viñedo + variedades + datos de riego existentes |
| 2 | Feedback sobre usabilidad del sistema desde perspectiva de productor profesional | Mes 11–12 | Input para R10 (informe validación comercial) |
| 3 | Participación en Gate Review 3 (TRL 4 demostrado) | Mes 12 | Validación de campo varietal — firma acta |

---

## Resumen de dedicación y costo por miembro

| Miembro | Rol | Dedicación | Honorarios ANR | Fuente |
|---------|-----|-----------|----------------|--------|
| César Schiavoni | Project Leader / Dev IA | 40 hs/sem · 12 meses | USD 18.000 | ANR (20hs/sem × USD 1.500/mes) + especie (20hs/sem) |
| Lucas Bergon | COO / Hardware & Firmware | 50% M1-6 · 25% M7-12 | USD 15.000 | ANR + especie (horas USD 4.650 + herramientas USD 400 + equipamiento MBG USD 710 = USD 5.760) |
| Inv. Art. 32 (a incorporar) | Investigador en Validación de Señales y Datos Agronómicos (perfil Art. 32) | ~5 hs/sem promedio (~177 hs totales) | USD 6.000 | ANR (USD 500/mes) |
| Dra. Monteoliva | Investigadora INTA-CONICET | ~180h en 12 meses | USD 10.800 | ANR (USD 900/mes) |
| Javier Schiavoni | Técnico de Campo Principal | ~227h · 9 meses | USD 9.000 | ANR (USD 1.000/mes) |
| Franco Schiavoni | Soporte Campo | eventual | USD 0 | Especie familiar |
| Matías Tregnaghi | CFO / Contador | 20% · 12 meses | USD 6.000 | ANR (USD 500/mes) |
| Ximena Crespo | Agente PI (patente) | honorario único | incluido en ítem PI | ANR |
| Pablo Contreras | Abogado (SAS + pacto socios) | puntual · Mes 1–3 | incluido en ítem Legal | ANR |
| Gabriel Campana | Asesor Vitivinícola | puntual · Mes 10–12 | USD 0 | Advisor en equity |
| **TOTAL HONORARIOS** | | | **USD 64.800** | |

---

## Resumen de costos del proyecto (ANR USD 120.000)

| Rubro | Monto USD | Nota |
|---|---|---|
| Honorarios equipo (ver tabla arriba) | 64.800 | César USD 1.500/mes; Inv. Art. 32 USD 500/mes; Javier USD 1.000/mes (~227h, incluye base tanque + riego + Scholander + 10 nodos) |
| Hardware — 10 nodos ESP32-S3 + MLX90640 (5 calibración + 5 producción) | 7.500 | Incluye repuestos, prototipo testing, herramientas banco |
| Gateway RAK7268 + conectividad dual (4G + Starlink Mini X) | 847 | RAK7268 + Teltonika RUT241 + chip M2M + Starlink Mini X + plan |
| Instrumentos referencia (Scholander, Davis, HOBO, etc.) | 5.642 | Nota: calibrador cuerpo negro e instrumental portátil provistos por lab INTA-CONICET |
| Equipamiento campo experimental [B] (solenoides x10, brackets x64, paneles ref. x64, etc.) | 3.300 | Solenoides Rain Bird x10 (1/fila — todas las filas) + controlador 10 zonas + brackets + paneles ref. + túneles + estacas + cableado + malla antigranizo + canaleta UV |
| Infraestructura cloud + herramientas desarrollo | 500 | Colab Pro (César) + Cloudflare R2 + dominio. VPS: Oracle Free Tier. Licencias: free tiers suficientes para TRL 3-4 |
| Claude Code Max (2 devs × 12 meses, USD 100/mes neto) | 2.400 | Art. 21g — IVA e Impuesto PAIS no elegibles (Art. 22j/22k) |
| Legal + constitución SAS | 800 | |
| Contaduría externa + rendiciones ANPCyT | 2.400 | |
| Seguros (RC campo + equipos importados) | 1.000 | ART no aplica (monotributistas); sin traslados externos en TRL 3-4 |
| Viajes y movilidad (solo Colonia Caroya) | 800 | Movilidad local Cba↔Colonia Caroya + 1-2 viajes BA para Gate Reviews ANPCyT |
| Propiedad intelectual (patente INPI) | 3.500 | |
| Difusión científica + congresos + vinculación | 2.700 | Congreso SAFV (todo incluido) + publicación open access + informe técnico productores + congreso AgTech (todo incluido) |
| Capacitación del equipo (Art. 21f) | 1.900 | TinyML Lucas (Edge Impulse/Coursera) + workshop termografía equipo + gestión ANPCyT Matías + bibliografía técnica |
| Bienes de consumo y materiales campo (Art. 21d) | 2.500 | Consumibles electrónicos, lab, campo, EPP |
| Imprevistos y contingencias (~16,1%) | 19.353 | Reposición campo, tipo de cambio, sesiones Scholander adicionales, contingencias operativas |
| **TOTAL ANR** | **USD 120.000** | **Suma verificada — todos los límites Art. 21 cumplidos** |

> **Nota scope software:** TRL 3-4 no incluye dashboard comercial, app móvil, API comercial, SaaS, onboarding QR ni alertas push. El entregable de software es: (1) **MVC funcional** — backend FastAPI que recibe payloads del nodo vía LoRa/MQTT, los persiste en PostgreSQL y permite visualizar datos básicos (el MVC se deploya en el VPS del presupuesto cloud); (2) modelo PINN validado + notebooks de validación científica (R² vs Scholander); (3) motor de alertas agronómicas (reglas Python). Dashboard comercial, app React Native y onboarding QR son TRL 5.
>
> **Contrapartida (USD 30.000):** César: estación IA USD 2.500 + viñedo experimental USD 5.000 + horas especie USD 15.500 + vides USD 5.440 + herramientas USD 400 + celular USD 450 = USD 29.290. Lucas: equipamiento electrónico MBG Controls USD 710. Total: USD 30.000.
