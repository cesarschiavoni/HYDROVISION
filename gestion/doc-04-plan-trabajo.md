

El equipo adopta una metodología de desarrollo acelerado con IA generativa como herramienta principal de trabajo en los tres perfiles técnicos:

Desarrollador
Herramienta IA principal
Impacto en el proyecto
Reducción tiempo
César SchiavoniProject Leader / Dev IA + Backend
Claude Code (herramienta principal de construcción)
Dirección del proyecto, backend FastAPI, fusión Sentinel-2, pipeline CI/CD, dashboard web. Implementación completa usando Claude Code.
~50% menos tiempo — máximo beneficio en backend, APIs y frontend
Lucas BergonCOO / Líder Hardware, Firmware & Embedded
Claude Code
Arquitectura modular TRL4: integración ESP32-S3 DevKit + breakouts I2C/SPI, firmware MicroPython para sensores (MLX90640, SHT31, GPS, IMU, anemómetro), integración ChirpStack/LoRaWAN, testing de hardware (deep sleep, watchdog, autonomía solar), carcasa Hammond IP67, anotación inicial del dataset térmico.
~40% menos tiempo en desarrollo de drivers, firmware y testing
Investigador Art. 32 (a incorporar) — Validación de Señales y Datos Agronómicos
Claude Code + GitHub Copilot
Validación estadística de correlaciones de campo (CWSI↔MDS↔Ψstem), calibración de sensores dendrómetro, diseño experimental óptimo (OED), co-autoría de publicación científica. Análisis estadístico con datos Scholander reales.
~35% menos tiempo en implementación IA/embedded
César SchiavoniDirector de Desarrollo IA / Project Leader ANPCyT
Claude Code (uso intensivo — herramienta principal de construcción)
Módulos Python HSI, pipeline térmico, fusión satelital multi-fuente, tests automatizados, integración con firmware Lucas, documentación técnica ANPCyT. César diseña y ejecuta con Claude Code.
~60% menos tiempo de implementación — Claude Code genera el código, César revisa y valida
Resultado operativo: La adopción de IA generativa reduce las horas de implementación en 40–60% por perfil. El equipo técnico está especializado por capa — embedded (Lucas Bergon), backend/cloud/frontend (César Schiavoni con Claude Code). César diseña y ejecuta con IA; los especialistas validan cada capa.



Fase
Período
Actividades principales
Hito de cierre
Fase 0Setup
Mes 1–3
Constitución SAS. Adquisición de hardware. Setup entorno de desarrollo. Validación de drivers MicroPython para MLX90640 breakout + sensores meteorológicos (generados con Claude Code — Lucas confirma en banco). Adquisición del MLX90640 breakout integrado (Adafruit 4407) + ESP32-S3 DevKit en Semana 1. Setup entorno de desarrollo con Claude Code para los tres desarrolladores. Implementación del modo deep sleep con RTC DS3231. Primeras capturas térmicas en viñedo propio de Malbec en Colonia Caroya. Segmentación foliar por percentiles. Pipeline CWSI funcional. Instalación sistema drip diferencial en 10 filas × 136m — Zona de Calibración (filas 1–5: F1=0% ETc, F2=15%, F3=40%, F4=65%, F5=100% ETc) + Zona de Producción (filas 6–10: todas 100% ETc, nodos en modo comercial autónomo): tendido de cinta drip en 10 filas, conexión de 10 solenoides (1 por fila, todas las filas) al controlador Rain Bird, calibración de caudales por fila. Instalación de 64 brackets de captura fijos en postes de espaldera (cada ~10m). 5 regímenes hídricos independientes activos: 100% ETc → sin riego. Implementación del motor GDD: cálculo de grados-día acumulados desde SHT31, detección automática de brotación por convergencia térmica+GDD, integración del pluviómetro de balancín. César Schiavoni: backend base mínimo + ingesta MQTT → PostgreSQL (schema simple: nodo_id, timestamp, payload JSON). Conectividad de campo — modelo dual: gateway LoRaWAN conectado por Ethernet a router 4G industrial (Teltonika RUT241, opción principal — Colonia Caroya tiene cobertura 4G) + Starlink Mini X para prueba de integración del dispositivo en TRL 4. En TRL 5+, Starlink cubre zonas remotas sin 4G (Valle de Uco, San Juan, NOA).
Pipeline CWSI funcional en laboratorio. Nodo capturando imágenes térmicas verificadas.
Fase 1Dataset
Mes 4–6
Recopilación y procesamiento de datasets públicos: INIA Chile (vid Pinot Noir bajo riego deficitario), IRTA Cataluña (olivo), PlantVillage Thermal, FLIR ADAS — total 50.000+ imágenes. Construcción del simulador físico de imágenes térmicas sintéticas calibrado para Malbec en condiciones de Cuyo (balance energético foliar): genera 1.000.000 de imágenes sintéticas en la RTX 3070 (~40 horas de GPU). César Schiavoni: integración API Sentinel-2 Copernicus (GEE Connector) para descarga automática de NDVI/NDWI/NDRE. Modelo de correlación CWSI↔NDWI inicial. Protocolo de captura real diseñado con Dra. Monteoliva: 800 frames de Malbec bajo 5 regímenes hídricos y al menos 2 estadios fenológicos, con potencial hídrico verificado por bomba de Scholander — datos de calibración final del modelo.
800 frames reales etiquetados con potencial hídrico foliar verificado por Scholander (680 fine-tuning + 120 validación independiente). Simulador físico generando ≥100.000 imágenes sintéticas.
Fase 2Modelo IA
Mes 7–9
Pre-entrenamiento del backbone en 50.000 imágenes públicas (transfer learning). Fine-tuning con 1.000.000 imágenes sintéticas del simulador físico (~40h GPU en RTX 3070). Calibración final con 800 frames reales etiquetados con Scholander. Cuantización INT8. César Schiavoni ejecuta el pre-entrenamiento PINN y el fine-tuning en la RTX 3070 local. Arquitectura PINN en PyTorch con función de pérdida custom: L_total = MSE(CWSI_pred, CWSI_real) + λ · ||CWSI_pred − f(ΔT_pred, VPD)||², donde f() es la ecuación de Jackson et al. (1981). El investigador Art. 32 valida estadísticamente las correlaciones CWSI↔Ψstem del dataset de campo. Mariela Monteoliva valida el simulador físico contra los datos reales de Scholander antes del entrenamiento. César Schiavoni: FastAPI mínima (3 endpoints) + pipeline CI/CD básico (GitHub Actions + Docker) para deployment del modelo. Validación con set independiente de 120 frames reales no vistos durante entrenamiento. Validación del motor GDD contra observaciones fenológicas reales en Colonia Caroya (brotación, floración, envero observados vs. predichos por GDD).
Accuracy > 85% en set de validación independiente (120 frames reales no vistos). Latencia < 200ms en ESP32-S3. Modelo INT8 deployado.
Fase 3Integración
Mes 10–12
Integración completa del nodo. Pruebas LoRaWAN. Validación del control de riego autónomo integrado en nodo Tier 2: el nodo decide localmente cuándo regar según HSI (histéresis 0.30/0.20), activa solenoide Rain Bird vía GPIO → SSR en viñedo Colonia Caroya (fila 1, 0% ETc — activación automática de control de riego). El servidor recibe estado vía payload `/ingest`. Override manual disponible vía API REST. Conectividad dual validada en campo (viñedo Colonia Caroya): router 4G Teltonika RUT241 como opción principal + Starlink Mini X como prueba de integración del dispositivo (TRL 4). Prueba de autonomía 72h. Ximena Crespo: presentación solicitud de patente INPI. Documentación TRL 4 completa.
Sistema integrado 72h. Control riego autónomo demostrado (nodo Tier 2). Dashboard web con mapa de estrés georreferenciado. Conectividad dual (4G + Starlink) validada. Patente presentada. Nota: app móvil y onboarding QR son entregables de TRL 5.


### 6A. Gate Reviews — Métricas de Avance por Fase


Cada fase culmina en un Gate Review con métricas objetivas que determinan el avance al siguiente bloque. César Schiavoni (Project Leader) preside cada revisión. Participan según su área: Lucas Bergon (hardware), Inv. Art. 32 (validación datos/señales), Matías Tregnaghi (finanzas), Dra. Monteoliva (validación agronómica), Ximena Crespo (PI en Gate 3).

Gate
Fecha aprox.
Métricas mínimas de aprobación
Gate 0 — Setup completado
Fin Mes 3
Pipeline CWSI funcional en laboratorio. Nodo capturando imágenes térmicas. Firmware con deep sleep operativo. Backend base + ChirpStack levantados.
Gate 1 — Dataset validado
Fin Mes 6
800 frames reales capturados bajo protocolo Scholander (680 fine-tuning + 120 validación independiente), etiquetados con Ψstem medido. Capturados en 5 filas de calibración × 136m (1 régimen hídrico por fila, 10 nodos permanentes (5 calibración + 5 producción) con gimbal 7 ángulos × 96 ciclos/día → 800 frames alcanzables en 2 sesiones). Simulador físico generando imágenes sintéticas (≥ 100.000 al Mes 6). Operación autónoma del nodo > 72h continuas en campo. Campaña Scholander #1 completada (≥ 30 pares ΔT/VPD para calibración de ΔT_LL y ΔT_UL). Correlación CWSI↔NDWI inicial documentada. Auto-calibración baseline activa: ≥ 1 evento de lluvia con MDS≈0 capturado y tc_wet_offset actualizado por cada nodo, con persistencia JSON verificada ante reinicio.
Gate 2 — Modelo IA validado
Fin Mes 9
Accuracy > 85% en set de validación independiente (120 frames reales no vistos). Latencia < 200ms en ESP32-S3. Modelo INT8 deployado. Motor GDD con error ±5 días en predicción fenológica. Dashboard web funcional con alertas activas.
Gate 3 — TRL 4 demostrado
Fin Mes 12
Sistema integrado operativo 72h continuas. Control riego autónomo (nodo Tier 2: HSI → GPIO → SSR → solenoide Rain Bird) demostrado en viñedo experimental Colonia Caroya. Dashboard web con mapa de estrés georreferenciado. Solicitud INPI presentada. Informe TRL 4 completo para ANPCyT. Métricas de validación estadística (Inv. Art. 32): R²≥0.75 CWSI vs Ψstem · R²≥0.65 MDS vs Ψstem · R²≥0.80 HSI vs Ψstem · MAE≤0.08 CWSI en set independiente 120 frames. Nota: app móvil y onboarding QR son entregables de TRL 5.




## 7. Presupuesto del Proyecto
