
# DIAGRAMA DE GANTT - HydroVision AG
## TRL 3 -> 4 | Inicio estimado: Octubre 2026 | Cierre: Septiembre 2027

**Referencias:** XX = periodo activo | S1-S4 = sesion Scholander campo | G0-G3 = Gate Review ANPCyT | V1-V4 = campaña externa | PI = patente INPI | CF = congreso

| Tarea / Hito                                            | Oct | Nov | Dic | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep |
|---------------------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
| **FENOLOGIA MALBEC - Colonia Caroya (~700m, Sierras Chicas)** |     |     |     |     |     |     |     |     |     |     |     |     |
|   Brotacion                                             | XX |    |    |    |    |    |    |    |    |    |    |    |
|   Floracion                                             |    | XX |    |    |    |    |    |    |    |    |    |    |
|   Desarrollo del fruto                                  |    |    | XX |    |    |    |    |    |    |    |    |    |
|   Envero / Pre-maduracion                               |    |    | XX | XX |    |    |    |    |    |    |    |    |
|   COSECHA (mediados febrero)                            |    |    |    | XX | XX |    |    |    |    |    |    |    |
|   Dormancia invernal                                    |    |    |    |    |    | XX | XX | XX | XX | XX | XX |    |
|   Nueva brotacion temporada 2027-28                     |    |    |    |    |    |    |    |    |    |    |    | XX |
|---------------------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
| **LEGAL / ADMINISTRATIVO                               ** |     |     |     |     |     |     |     |     |     |     |     |     |
|   Constitucion HydroVision AG SAS (IGJ) + AFIP          | XX | XX |    |    |    |    |    |    |    |    |    |    |
|   Pacto de socios + clausulas vesting 4 anos            | XX | XX |    |    |    |    |    |    |    |    |    |    |
|   Seguros (RC + equipos importados + ART campo)         | XX | XX | XX | XX | XX | XX | XX | XX | XX | XX | XX | XX |
|   Contaduria / rendiciones ANPCyT (trimestral)          | XX | XX | XX | XX | XX | XX | XX | XX | XX | XX | XX | XX |
|---------------------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
| **ADQUISICION & RECEPCION HARDWARE                     ** |     |     |     |     |     |     |     |     |     |     |     |     |
|   ESP32-S3 x10 + MLX90640 110° x10 (10 nodos permanentes) | XX |    |    |    |    |    |    |    |    |    |    |    |
|   Recepcion ESP32-S3 + MLX90640 (lead time ~2 sem)       | XX |    |    |    |    |    |    |    |    |    |    |    |
|   SHT31 x10 + GPS u-blox x10 + IMU ICM-42688 x10        | XX |    |    |    |    |    |    |    |    |    |    |    |
|   SX1276 x10 + ADS1231 x10 + servos MG90S x10          | XX |    |    |    |    |    |    |    |    |    |    |    |
|   Piranómetro BPW34 x10 + bomba peristáltica x10        | XX |    |    |    |    |    |    |    |    |    |    |    |
|   Gateway RAK7268 + Starlink Mini kit                   | XX |    |    |    |    |    |    |    |    |    |    |    |
|   Scholander + tensiómetros x8 + Davis Vantage          | XX | XX |    |    |    |    |    |    |    |    |    |    |
|   HOBO MX2301 x2 + calibrador cuerpo negro              | XX | XX |    |    |    |    |    |    |    |    |    |    |
|   Integracion modular DevKit+breakouts (Lucas)          | XX | XX |    |    |    |    |    |    |    |    |    |    |
|   Montaje 10 nodos en carcasa Hammond IP67 (Lucas)      |    | XX | XX |    |    |    |    |    |    |    |    |    |
|   Carcasa IP67 + sistema montaje estaca/bracket         |    | XX | XX |    |    |    |    |    |    |    |    |    |
|   Drip 1.450m + solenoides x10 + controlador Rain Bird  | XX | XX |    |    |    |    |    |    |    |    |    |    |
|   Brackets acero x64 + paneles emisividad x64           | XX | XX |    |    |    |    |    |    |    |    |    |    |
|---------------------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
| **INSTALACION VINEDO EXPERIMENTAL (Tecnico + Lucas)    ** |     |     |     |     |     |     |     |     |     |     |     |     |
|   Tendido cinta drip 10 filas x 136m                    | XX | XX |    |    |    |    |    |    |    |    |    |    |
|   Instalacion 10 solenoides (1/fila) + Rain Bird        | XX | XX |    |    |    |    |    |    |    |    |    |    |
|   Prueba caudales 5 regimenes hidricos (0-100% ETc)     |    | XX |    |    |    |    |    |    |    |    |    |    |
|   Instalacion 64 brackets en postes espaldera           |    | XX |    |    |    |    |    |    |    |    |    |    |
|   Tuneles exclusion lluvia filas 1 y 2 (0% y 15% ETc)   |    | XX |    |    |    |    |    |    |    |    |    |    |
|   Instalacion 8 tensiómetros + paneles + estacas        |    | XX |    |    |    |    |    |    |    |    |    |    |
|   Mantenimiento rutinario vinedo (tecnico campo)        | XX | XX | XX | XX | XX | XX | XX | XX | XX |    |    |    |
|---------------------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
| **HARDWARE & FIRMWARE (Lucas Bergon)                  ** |     |     |     |     |     |     |     |     |     |     |     |     |
|   Setup entorno desarrollo + Claude Code                | XX |    |    |    |    |    |    |    |    |    |    |    |
|   Driver MLX90640 I2C (32x24, FOV 110°, filtro P20-P75)  | XX | XX | XX |    |    |    |    |    |    |    |    |    |
|   Drivers SHT31, GPS u-blox, IMU, DS3231, pluviometro   | XX | XX | XX |    |    |    |    |    |    |    |    |    |
|   Driver ADS1231 SPI + DS18B20 (extensometro tronco)    | XX | XX | XX |    |    |    |    |    |    |    |    |    |
|   Driver piranometro ADC + bomba Wet Ref GPIO           |    | XX | XX |    |    |    |    |    |    |    |    |    |
|   Drivers MicroPython: servos MG90S gimbal pan-tilt     | XX | XX | XX |    |    |    |    |    |    |    |    |    |
|   Firmware MicroPython ESP32-S3: deep sleep 8uA, Node ID MAC, JSON v1  |    | XX | XX |    |    |    |    |    |    |    |    |    |
|   Integracion ChirpStack/LoRaWAN + protocolo MQTT       |    | XX | XX | XX |    |    |    |    |    |    |    |    |
|   Sistema solar: panel 6W + LiFePO4 + regulador MPPT       |    | XX | XX |    |    |    |    |    |    |    |    |    |
|   Gimbal pan-tilt 2 ejes: 7 angulos automaticos         |    | XX | XX | XX |    |    |    |    |    |    |    |    |
|   Prueba autonomia solar 72h continuas                  |    |    |    | XX |    |    |    |    |    |    |    |    |
|   Testing banco: deep sleep, watchdog, autonomia        |    |    |    | XX | XX | XX |    |    |    |    |    |    |
|   Integracion completa nodo (todas las capas HW)        |    |    |    |    |    |    |    |    |    | XX | XX |    |
|   ~~Alertas fisicas: LED tricolor + sirena 90dB~~ (REMOVIDO) |    |    |    |    |    |    |    |    |    |    |    |    |
|   Control riego autonomo nodo (GPIO → SSR → solenoide)  |    |    |    |    |    |    |    |    |    |    | XX | XX |
|   Prueba autonomia 72h sistema completo integrado       |    |    |    |    |    |    |    |    |    |    |    | XX |
|---------------------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
| **IA / MODELO PINN + VALIDACION (César + Inv. Art. 32) ** |     |     |     |     |     |     |     |     |     |     |     |     |
|   Motor GDD: acumulador + deteccion brotacion auto      | XX | XX | XX |    |    |    |    |    |    |    |    |    |
|   Pipeline CWSI funcional en laboratorio (Python)       | XX | XX |    |    |    |    |    |    |    |    |    |    |
|   Segmentacion foliar U-Net++ ResNet34                  |    | XX | XX | XX |    |    |    |    |    |    |    |    |
|   Recopilacion datasets publicos 50.000+ imgs           |    |    |    | XX | XX | XX |    |    |    |    |    |    |
|   Simulador fisico: generador 1M imgs sinteticas        |    |    |    | XX | XX | XX |    |    |    |    |    |    |
|   Correlacion inicial CWSI-NDWI (Sentinel-2)            |    |    |    |    | XX | XX |    |    |    |    |    |    |
|   Pre-entrenamiento backbone (50K imgs publicas)        |    |    |    |    |    |    | XX |    |    |    |    |    |
|   Fine-tuning PINN (~40h GPU RTX 3070 Cesar)            |    |    |    |    |    |    | XX | XX |    |    |    |    |
|   Calibracion real PINN (800 frames Scholander)         |    |    |    |    |    |    |    | XX | XX |    |    |    |
|   Cuantizacion INT8 + deploy PINN en backend FastAPI    |    |    |    |    |    |    |    | XX | XX |    |    |    |
|   Validacion set independiente 120 frames (>85%)        |    |    |    |    |    |    |    |    | XX |    |    |    |
|   Validacion motor GDD vs. fenologia observada          |    |    |    |    |    |    |    |    | XX |    |    |    |
|   Soporte tecnico integracion Fase 3 (25%)              |    |    |    |    |    |    |    |    |    | XX | XX | XX |
|---------------------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
| **BACKEND & CLOUD (César + Claude Code)                ** |     |     |     |     |     |     |     |     |     |     |     |     |
|   Setup ChirpStack + Mosquitto (MQTT)                   | XX | XX |    |    |    |    |    |    |    |    |    |    |
|   ChirpStack Network Server + PostgreSQL/PostGIS        | XX | XX | XX |    |    |    |    |    |    |    |    |    |
|   Base de datos InfluxDB time-series CWSI + GDD         |    | XX | XX | XX |    |    |    |    |    |    |    |    |
|   API Sentinel-2 Copernicus (NDVI/NDWI/NDRE auto)       |    |    |    | XX | XX | XX |    |    |    |    |    |    |
|   API REST FastAPI + esquema OpenAPI                    |    |    |    |    | XX | XX | XX | XX |    |    |    |    |
|   Fusion CWSI-NDWI vía Google Earth Engine              |    |    |    |    |    | XX | XX | XX | XX |    |    |    |
|   Pipeline CI/CD GitHub Actions + Docker                |    |    |    |    |    | XX | XX | XX |    |    |    |    |
|   Hardening seguridad (OAuth2, rate limiting)           |    |    |    |    | XX | XX |    |    |    |    |    |    |
|   Motor reglas riego configurable (backend)             |    |    |    |    |    |    |    |    | XX | XX | XX |    |
|---------------------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
| **FRONTEND & APP MOVIL — diferido TRL 5              ** |     |     |     |     |     |     |     |     |     |     |     |     |
|---------------------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
| **SESIONES SCHOLANDER (Monteoliva + Tecnico campo)     ** |     |     |     |     |     |     |     |     |     |     |     |     |
|   Diseno protocolo experimental (Monteoliva)            | XX | XX | XX |    |    |    |    |    |    |    |    |    |
|   SESION 1 - Post-brotación / Calibración línea base    |  S1  |     |     |     |     |     |     |     |     |     |     |     |
|   SESION 2 - Pre-envero / Máxima demanda hídrica        |     |     |     |  S2  |     |     |     |     |     |     |     |     |
|   SESION 3 - Post-envero / Estrategia RDI enológica     |     |     |     |     |  S3  |     |     |     |     |     |     |     |
|   SESION 4 - Pre-cosecha / Cierre del dataset           |     |     |     |     |     |  S4  |     |     |     |     |     |     |
|   Validacion simulador vs. datos Scholander reales      |    |    |    |    |    |    | XX | XX | XX |    |    |    |
|   Co-autoria publicacion cientifica                     |    |    |    |    |    |    |    |    |    | XX | XX | XX |
|---------------------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
| **CAMPANAS EXTERNAS — TRL 5+                           ** |     |     |     |     |     |     |     |     |     |     |     |     |
|   Campaña Bodega Las Canitas (TRL 5)                    |     |     |     |     |     |     |     |     |     |     |     |     |
|---------------------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
| **PROPIEDAD INTELECTUAL (Ximena Crespo)                ** |     |     |     |     |     |     |     |     |     |     |     |     |
|   Busqueda formal anterioridad INPI+EPO+USPTO           | XX | XX | XX |    |    |    |    |    |    |    |    |    |
|   Redaccion reivindicaciones + descripcion tecnica      |    |    |    |    |    |    |    |    | XX | XX | XX |    |
|   Presentacion solicitud patente INPI Argentina         |     |     |     |     |     |     |     |     |     |     |     |  PI  |
|---------------------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
| **GATE REVIEWS & HITOS ANPCYT                          ** |     |     |     |     |     |     |     |     |     |     |     |     |
|   G0 - Pipeline CWSI + nodo capturando (fin M3)         |     |     |  G0  |     |     |     |     |     |     |     |     |     |
|   G1 - Dataset validado + simulador OK (fin M6)         |     |     |     |     |     |  G1  |     |     |     |     |     |     |
|   G2 - Modelo >85% accuracy + INT8 OK (fin M9)          |     |     |     |     |     |     |     |     |  G2  |     |     |     |
|   G3 - TRL 4 demostrado + informe final (fin M12)       |     |     |     |     |     |     |     |     |     |     |     |  G3  |
|---------------------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
| **DIFUSION & VINCULACION                               ** |     |     |     |     |     |     |     |     |     |     |     |     |
|   Material tecnico: manual + videos tutoriales          |    |    |    |    |    |    |    |    | XX | XX | XX | XX |
|   Diseno identidad corporativa + web MVP                |    |    |    |    |    |    |    | XX | XX | XX |    |    |
|   Congreso Soc. Argentina Fisiologia Vegetal            |     |     |     |     |     |     |     |     |     |  CF  |     |     |
|   Publicacion cientifica open access                    |    |    |    |    |    |    |    |    |    | XX | XX | XX |