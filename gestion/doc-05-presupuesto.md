
## 7. Presupuesto del Proyecto

**Monto total: USD 150.000 · ANPCyT ANR (80%): USD 120.000 · Contrapartida equipo (20%): USD 30.000**

---

### 7.1 Aportes ANPCyT — USD 120.000 (80%)

#### Hardware y equipamiento de campo

| Item | Descripcion breve | USD |
|------|-------------------|----:|
| 10 nodos prototipo (5 calibración + 5 producción) | ESP32-S3 DevKit (MicroPython) x10 + MLX90640 breakout integrado (Adafruit 4407) x10 + SHT31 breakout + piranometro BPW34 x10 + GPS u-blox x10 + IMU ICM-42688-P x10 + LoRa SX1276 x10 + panel solar 6W + LiFePO4 6000mAh x10 + carcasa Hammond IP67 200x150x100mm x10 (sin PCB custom — arquitectura modular breakouts I2C/SPI) + anemometro RS485 x10 + extensometro ADS1231 x10 + pluviometro x10 + PMS5003 x10 + bomba Wet Ref x10 + SSR x10 (1 rele SSR por nodo, todas las filas — solenoides incluidos en [B]) + repuestos criticos x3 juegos + prototipo testing destructivo + herramientas banco + proteccion ESD | 7.500 |
| Gateway LoRaWAN + conectividad dual | RAK7268 antena 8dBi (USD 250) + Router 4G Teltonika RUT241 (USD 190) + chip M2M 6 meses campaña activa (USD 30) + Starlink Mini X kit para validación en zonas sin 4G (USD 215) + plan Starlink 6 meses campaña (USD 162). Modelo dual: 4G como opción principal (Colonia Caroya tiene cobertura), Starlink para validación de campo remoto (Mendoza/San Juan). | 847 |
| Instrumentos validacion ground truth | Tensiometros calibrados x5 (1/zona hidrica) + sensores capacitivos x6 + HOBO MX2301 x1 + bomba Scholander + Davis Vantage Pro2 + termometro contacto + multimetro precision + N2 comprimido x8 recargas + luxometro + balanza precision + maletin IP67 x1. Nota: calibrador cuerpo negro e instrumental portatil adicional provistos por laboratorio MEBA-IFRGV-UDEA (INTA-CONICET, Dra. Monteoliva) sin costo para el proyecto. | 5.642 |
| [A]+[B] Infraestructura y equipamiento riego experimental | [A] Riego diferencial 10 filas: tanque australiano 20.000L + bomba centrifuga 0,5HP + caneria PE 63/50/32mm completa + cinta drip 1.450m + accesorios (USD 2.858). [B] Control experimental 5 filas de calibración + 5 filas de producción con nodos comerciales: solenoides Rain Bird 24VAC x10 (USD 350, 1 por fila — todas las filas) + controlador 10 zonas + filtro + brackets x64 + paneles referencia x64 + tuneles exclusion lluvia parcial filas 1 y 2 (0% y 15% ETc) + estacas x1.360 + cableado + drip reposicion + kit reparacion + senalizacion + malla antigranizo + canaleta UV (USD 3.300). Sistema imprescindible para los 5 regimenes hidricos independientes del protocolo experimental. | 6.158 |
| **Subtotal hardware** | | **20.147** |

#### Honorarios equipo

| Persona | Rol | Dedicacion | Periodo | USD |
|---------|-----|-----------|---------|----:|
| Cesar Schiavoni | Director IA y Backend / Project Leader ANPCyT | 40 hs/semana (20 ANR + 20 especie) | 12 meses | 18.000 |
| Inv. Art. 32 (a incorporar) | Investigador Validación Señales y Datos Agronómicos — Perfil Art. 32 | ~5 hs/semana (~177 hs totales) | 12 meses | 6.000 |
| Lucas Bergon | Embedded & Hardware / COO | 50% Mes 1-6 · 25% Mes 7-12 | 12 meses | 15.000 |
| Dra. Mariela Monteoliva | Investigadora INTA-CONICET — Perfil Art. 32 | ~15 hs/mes promedio (~180 hs totales) | 12 meses | 10.800 |
| Matias Tregnaghi | CFO / Contador Publico Senior | 20% dedicacion | 12 meses | 6.000 |
| Javier Schiavoni | Tecnico de campo / Base+riego + Protocolo Scholander | ~227 hs totales (base tanque + riego + campo + Scholander 4 sesiones OED + 10 nodos) | Mes 1-9 | 9.000 |
| **Subtotal honorarios** | | | | **64.800** |

> Ximena Crespo (Agente PI, Arteaga y Asociados) incluida en el item Propiedad Intelectual.
> Gabriel Campana (Asesor Vitivinicola) participa como advisor en equity, sin costo para el presupuesto ANPCyT.

#### Infraestructura cloud y licencias

| Item | Detalle | USD |
|------|---------|----:|
| Infraestructura cloud y herramientas | Google Colab Pro x1 (César — entrenamiento PINN + fine-tuning datos Scholander, respaldo RTX 3070): USD 10/mes x 12 = USD 120 · Cloudflare R2 storage dataset imagenes termicas: USD 5/mes x 12 = USD 60 · Dominio .com.ar: USD 10 · SSL: Let's Encrypt (gratuito) · Contingencias cloud: USD 310. VPS MVC (FastAPI+PostgreSQL+Mosquitto+ChirpStack+Redis, Docker Compose): Oracle Cloud Always Free Tier (4 OCPUs ARM + 24GB RAM — permanentemente gratuito). GitHub Free, W&B Free (hasta 3 usuarios), Mapbox Free (hasta 50.000 cargas/mes), Figma Free — todos suficientes para escala TRL 3-4. | 500 |
| Licencias Claude Code (Art. 21g) | Claude Code Max x 2 desarrolladores (Cesar + Lucas) x 12 meses. USD 100/mes neto por usuario. IVA e Impuesto PAIS no elegibles (Art. 22j/22k). | 2.400 |
| **Subtotal cloud y licencias** | | **2.900** |

#### Gastos operativos y servicios

| Item | Detalle | USD |
|------|---------|----:|
| Constitucion SAS + legal | Abogado estatuto + pacto socios con vesting (USD 400) + IGJ + sellados (USD 200) + AFIP + asesoramiento tributario (USD 200) | 800 |
| Contaduria y rendicion ANPCyT | Contador externo informes trimestrales + rendicion final. USD 200/mes x 12 | 2.400 |
| Seguros del proyecto | (1) Poliza RC Civil para actividades de investigacion en campo agricola — cobertura USD 50.000 — asegurador: Sancor / Federacion Patronal / Zurich (USD 500/ano). (2) Poliza todo riesgo equipos electronicos portatiles — valor asegurado USD 9.500 (10 nodos ESP32-S3 + gateway RAK7268 + bomba Scholander + Davis Vantage Pro2) — uso en campo exterior — asegurador: Sancor / Federacion Patronal / Zurich (USD 500/ano). Colaboradores monotributistas gestionan su propio ART. | 1.000 |
| Viajes y movilidad | Movilidad local Cordoba ciudad <-> Colonia Caroya para sesiones Scholander, instalacion y mantenimiento (~20 viajes x USD 15 combustible = USD 300) + 1-2 viajes Buenos Aires para Gate Reviews presenciales ANPCyT si son requeridos (aereo + alojamiento 1 noche = USD 500). Validacion TRL 3-4 concentrada en sitio experimental Colonia Caroya. | 800 |
| Propiedad intelectual — patente INPI | Agente PI redaccion (USD 1.500) + tasas INPI (USD 400) + busqueda anterioridad certificada (USD 1.100) + gestion examinador (USD 500) | 3.500 |
| Difusion cientifica y vinculacion | (1) RAFV — Reunión Argentina de Fisiología Vegetal (Sociedad Argentina de Fisiología Vegetal, SAFV). Mendoza ciudad, segunda mitad 2027 (agosto-noviembre, fecha a confirmar — edicion XXXVI o XXXVII segun frecuencia; la XXXV fue agosto 2025 en Mar del Plata). 1 persona (Dra. Monteoliva): inscripcion USD 150 + pasaje aereo Cordoba-Mendoza ida/vuelta USD 200 + alojamiento 2 noches Mendoza USD 160 + viaticos USD 90 = USD 600. Presentacion resultados campana Scholander + validacion CWSI. Si INTA-CONICET financia parcialmente (variable segun disponibilidad), saldo redirigido a imprevistos. (2) Publicacion cientifica open access: APC en revista indexada Q1-Q2 (Agricultural Water Management / Biosystems Engineering / Computers and Electronics in Agriculture) USD 1.200. Co-autoria Inv. Art. 32 + Dra. Monteoliva + Cesar. Entregable cientifico clave TRL 3-4. (3) Informe tecnico de resultados preliminares para productores vitivinicolas: diseno e impresion USD 400. Base para vinculacion comercial TRL 5. (4) Congreso o workshop AgTech (1 persona): inscripcion USD 100 + transporte/alojamiento USD 300 + viaticos USD 100 = USD 500. Vinculacion con ecosistema AgTech argentino, networking con potenciales clientes y partners. | 2.700 |
| Capacitacion equipo (Art. 21f) | (1) TinyML y edge inference — Lucas Bergon (USD 500): programa Harvard/Google en Coursera (Introduction to Embedded Machine Learning + Computer Vision with Embedded ML) + certificacion Edge Impulse Studio. Contenido: cuantizacion INT8, optimizacion de modelos para microcontroladores con memoria limitada, deployment en ESP32-S3, inferencia edge sin conectividad. Aplicacion directa: ejecutar el modelo PINN cuantizado en el nodo para estimacion CWSI offline. (2) Workshop de termografia aplicada a viticultura — equipo (USD 600): principios de camara termica LWIR, calibracion y emisividad, calculo CWSI desde imagenes termicas, interpretacion de mapas de estres hidrico, protocolos de captura en campo (ventana horaria, condiciones de referencia, correccion atmosferica). Participantes: Cesar + Inv. Art. 32 + Javier. Proveedor: INTA o especialista en termografia agricola. Duracion estimada: 2 dias. (3) Gestion administrativa y rendicion de cuentas ANPCyT — Matias Tregnaghi (USD 400): requisitos documentales de informes trimestrales de avance, rendicion final, criterios de elegibilidad de gastos, sistema SIGEF ANPCyT, justificacion de honorarios y comprobantes. Matias es el responsable directo de las rendiciones. Curso ofrecido por ANPCyT o consultora especializada en gestion de proyectos con financiamiento publico. (4) Material bibliografico tecnico (USD 200): libros especializados en termografia infrarroja aplicada a estres hidrico en vid, papers de acceso pago sobre CWSI y redes neuronales informadas por fisica (PINN), documentacion tecnica ESP32-S3/MLX90640 y manuales de calibracion de instrumentos. | 1.900 |
| Bienes de consumo y materiales (Art. 21d) | Cinta drip reposicion (USD 200) + cables/conectores/consumibles electronicos (USD 300) + materiales laboratorio calibracion (USD 200) + EPP campo (USD 150) + papeleria (USD 150) + consumibles SMD (USD 400) + empaque transporte nodos (USD 200) + agua destilada Wet Ref (USD 100) + N2 Scholander incluido en Instrumentos | 2.500 |
| Imprevistos y contingencias (~13,8%) | Reposicion componentes campo (10 nodos expuestos 12 meses) + variaciones importacion/tipo cambio + sesiones Scholander adicionales + reposicion drip/solenoides + contingencias operativas. Buffer justificado: hardware importado expuesto 12 meses en campo (lluvia, fumigaciones, granizo), protocolo Scholander sujeto a reprogramacion por condiciones climaticas, tipo de cambio volatil en Argentina. | 16.553 |
| **Subtotal operativos** | | **32.153** |

---

### Verificacion de totales y limites Art. 21

| Subtotal | USD | % ANR |
|----------|----:|------:|
| Hardware y equipamiento | 20.147 | 16,8% |
| Honorarios equipo | 64.800 | 54,0% |
| Cloud y licencias | 2.900 | 2,4% |
| Operativos y servicios | 32.153 | 26,8% |
| **TOTAL ANR ANPCyT (80%)** | **120.000** | **100%** |

| Categoria Art. 21 | Items incluidos | USD | % ANR | Limite |
|--------------------|----------------|----:|------:|--------|
| a) Honorarios | Equipo completo | 64.800 | 54,0% | Sin limite |
| b) Infraestructura | [A]+[B] Riego experimental completo | 6.158 | 5,1% | <= 15% OK |
| c) Servicios terceros | Legal + contaduria + PI + publicacion OA + informe tecnico + inscripciones congresos | 8.550 | 7,1% | <= 20% OK |
| d) Bienes consumo | Consumibles y materiales campo | 2.500 | 2,1% | Sin limite |
| e) Bienes capital | Hardware + gateway + conectividad + instrumentos | 13.989 | 11,7% | <= 30% OK |
| f) Capacitacion | TinyML + termografia + gestion ANPCyT + material bibliografico | 1.900 | 1,6% | Sin limite |
| g) Licencias/software | Claude Code Max x2 | 2.400 | 2,0% | Sin limite |
| h) Insumos/materiales | Fusionado con d) | — | — | Sin limite |
| i) Pasajes y viaticos | Movilidad local + Gate Reviews BA + pasajes congresos (RAFV + AgTech) | 1.650 | 1,4% | Sin limite |
| j) Conexiones/servidores | Colab Pro + Cloudflare R2 + dominio | 500 | 0,4% | Sin limite |
| k) Gestion operativa | Seguros | 1.000 | 0,8% | <= 5% OK |
| — | Imprevistos | 16.553 | 13,8% | — |
| | **TOTAL** | **120.000** | | |

---

### 7.2 Contrapartida equipo fundador — USD 30.000 (20%)

| Aporte | Titular | Descripcion | USD |
|--------|---------|-------------|----:|
| Estacion de trabajo IA | Cesar Schiavoni | Intel Core i7-12700K + RTX 3070 8GB VRAM + 32GB RAM DDR4 + SSD 480GB + HDD 2TB. Uso exclusivo para entrenamiento del simulador fisico y modelo PINN. Valorizacion a precio de mercado secundario Cordoba abr-2026. | 2.500 |
| Vinedo experimental Colonia Caroya | Cesar Schiavoni | Acceso exclusivo 12 meses a parcela Malbec (3.672 m² cultivados, 10 filas × 136m, 1.360 vides). Riego por canal, galpon, electricidad, instalacion permanente de equipos. | 5.000 |
| Horas en especie co-fundadores | Cesar (70%) / Lucas (30%) | Cesar 434hs × USD 25/hs = USD 10.850 (coordinacion tecnica, gestion ANPCyT, backend no facturado). Lucas 116hs × USD 40/hs = USD 4.650 (diseño sistema modular, integración DevKit + breakouts, firmware MicroPython, testing banco). | 15.500 |
| Material vegetal (1.360 vides) | Familia Schiavoni | Malbec injertado sobre pie americano — vinedo experimental. Valuacion: ARS 4.800/planta × 1.360. Nota de cesion familiar. | 5.440 |
| Herramientas de campo | Lucas Bergon / familia Schiavoni | Kit completo campo IP54 para instalacion y mantenimiento del sistema experimental. | 400 |
| Celular monitoreo de campo | Cesar Schiavoni | Xiaomi Redmi Note 13 Pro+ 5G + plan datos 6 meses. Uso exclusivo para monitoreo remoto del vinedo experimental. | 450 |
| Equipamiento tecnico | Lucas Bergon / MBG Controls | Osciloscopio, analizador logico, soldadores, fuentes reguladas, multimetro, herramientas SMD. Equipamiento MBG Controls a disposicion del proyecto. | 710 |
| **TOTAL CONTRAPARTIDA** | **Cesar ~24.240 / Lucas ~5.760** | **Cumple 20% requerido (Art. 44)** | **30.000** |

---

| | USD |
|---|----:|
| ANR ANPCyT (80%) | 120.000 |
| Contrapartida equipo (20%) | 30.000 |
| **TOTAL GENERAL DEL PROYECTO** | **150.000** |

---

### Notas de detalle por item

**10 nodos prototipo (5 calibración + 5 producción) (USD 7.500)**
Componentes x10 unidades: ESP32-S3 DevKit off-the-shelf x10 (USD 120) · MLX90640 breakout integrado Adafruit 4407 x10 (USD 550) · SHT31 breakout + piranometro BPW34 x10 (USD 400) · GPS u-blox NEO-6M x10 (USD 200) · ICM-42688-P IMU SPI x10 (USD 100) · SX1276 LoRa x10 (USD 150) · Panel solar 6W + regulador + LiFePO4 6000mAh x10 (USD 750) · Carcasa Hammond IP67 200x150x100mm + pasacables M16 x10 (USD 250) · Watchdog TPL5010 x10 (USD 40) · Cables I2C Stemma QT/Qwiic + dupont + misc (USD 350) · Sistema montaje estaca+bracket+M12 x10 (USD 450) · Proteccion ventana optica x10 (USD 180) · Anemometro RS485 copa x10 (USD 250) · Extensometro tronco: strain gauge + ADS1231 + DS18B20 + abrazadera x10 (USD 300) · Bomba peristaltica Wet Ref x10 (USD 160) · SSR relay x10 (USD 175, 1 relé por nodo — solenoides de riego incluidos en [B]) · Pluviometro balancin x10 (USD 150) · PMS5003 particulas x10 (USD 200) · Repuestos criticos x3 juegos (USD 825) · Prototipo testing destructivo y validacion termica (USD 450) · Herramientas banco: soldador estacion, flux, cables prueba (USD 300) · Proteccion ESD (USD 150). Total BOM x10: USD 7.500. Nota: eliminacion de PCB custom 4-layer (−USD 600) compensa mayor costo de breakouts MLX90640 y DevKit. Arquitectura modular TRL4.

**Gateway LoRaWAN + conectividad dual (USD 847)**
RAK7268 con antena omnidireccional 8dBi, fuente regulada, mastil y cableado coaxial de campo (USD 250). Router 4G industrial Teltonika RUT241 (USD 190) + chip SIM M2M 6 meses campana activa (USD 30) — opcion principal para Colonia Caroya (cobertura celular disponible). Starlink Mini X kit (USD 215) + plan Mini 6 meses (USD 162) — para validacion de conectividad en campo remoto (Mendoza/San Juan sin cobertura 4G). Modelo dual documentado en doc-06 sec 8.2.4A.

**Instrumentos validacion ground truth (USD 5.642)**
Tensiometros calibrados x5 (USD 500 — 1 por zona hidrica) · Sensores capacitivos humedad suelo x6 (USD 360) · Datalogger HOBO MX2301 x1 (USD 200) · Bomba Scholander Soilmoisture PMS-1505D (USD 2.000) · Estacion Davis Vantage Pro2 calibracion VPD (USD 1.000) · Termometro contacto referencia MLX90640 (USD 200) · Multimetro precision calibracion ADC (USD 300) · N2 comprimido Scholander x8 recargas (USD 200) · Luxometro calibracion piranometro BPW34 (USD 250) · Balanza precision calibracion extensometro (USD 400) · Maletin transporte IP67 x1 campanas (USD 232). Nota: calibrador de cuerpo negro para verificacion termica e instrumental portatil adicional de campanas provistos por el laboratorio MEBA-IFRGV-UDEA (INTA-CONICET, Dra. Monteoliva) como parte de la colaboracion institucional — sin costo para el proyecto.

**[A]+[B] Infraestructura y equipamiento riego experimental (USD 6.158 — ANR, Art. 21b)**
[A] Riego diferencial 10 filas (USD 2.858 — financiado con ANR): Tanque australiano 20.000L (USD 800) · Bomba centrifuga autocebante 0,5HP (USD 150) · Caneria PE 63mm suministro 15m (USD 68) · Caneria PE 63mm header principal 136m (USD 612) · Caneria PE 50mm derivaciones a filas 10 x 4m (USD 473) · Caneria PE 32mm conexiones 80m (USD 160) · Cinta goteo 16mm emisor 1m 1,5L/h x 1.450m (USD 435) · Accesorios (USD 160). Justificacion: infraestructura experimental imprescindible para crear los 5 regimenes hidricos independientes (1 tratamiento uniforme por fila) — eje central del protocolo TRL 3-4.
[B] Control experimental 10 filas — 5 calibración + 5 producción (USD 3.300 — ANR): Solenoides Rain Bird 24VAC x10 (USD 350, 1 por fila — todas las filas) · Controlador Rain Bird 10 zonas + trafo 24V (USD 200) · Filtro malla 2" + regulador presion (USD 120) · Brackets acero inox x64 (USD 640) · Paneles referencia emisividad e=0.98 x64 (USD 256) · Tuneles exclusion lluvia parcial filas 1 y 2 (0% y 15% ETc) (USD 220) · Estacas numeradas x1.360 (USD 272) · Kit cableado campo (USD 164) · Cinta drip reposicion + accesorios (USD 245) · Kit reparacion solenoides (USD 250) · Senalizacion filas de calibracion (USD 80) · Malla antigranizo nodos (USD 370) · Canaleta portacables UV (USD 132).

**Cesar Schiavoni — Director IA y Backend / Project Leader (USD 18.000)**
USD 1.500/mes x 12. Dedicacion 40 hs/semana: 20 hs/sem facturadas al proyecto (ANR) + 20 hs/sem aporte en especie (contrapartida). Direccion integral del proyecto, coordinacion equipo, desarrollo backend (FastAPI + MQTT + PostgreSQL), fusion Sentinel-2 (CWSI-NDWI), pipeline CI/CD, validacion sistema completo. Implementacion acelerada con Claude Code. Coordinacion INTA-CONICET (Dra. Monteoliva), Gate Reviews, interlocucion ANPCyT y rendiciones.

**Investigador en Validación de Señales y Datos Agronómicos — Perfil Art. 32, a incorporar (USD 6.000)**
USD 500/mes x 12 (~5 hs/semana promedio, ~177 hs totales). Análisis estadístico de correlaciones CWSI↔MDS↔Ψstem con datos Scholander reales, calibración de sensores dendrómetro por regresión, diseño experimental óptimo (OED), validación métricas TRL 4 (R²≥0.75, MAE≤0.08 CWSI). Co-autoría publicación científica. Perfil: procesamiento de señales/estadística/instrumentación (CIII / G.In.T.E.A UTN FRC u equivalente).

**Lucas Bergon — Embedded & Hardware / COO (USD 15.000)**
USD 1.500/mes x 6 (Mes 1-6, 50%) + USD 1.000/mes x 6 (Mes 7-12, 25%). Fundador MBG Controls. Arquitectura modular TRL4: integración ESP32-S3 DevKit + breakouts I2C/SPI, firmware MicroPython (MLX90640, SHT31, GPS, IMU), integración ChirpStack/LoRaWAN, testing hardware, carcasa Hammond IP67 y montaje campo. Aporte en especie diseño sistema modular (USD 3.000) en contrapartida.

**Dra. Mariela Monteoliva — INTA/CONICET, Perfil Art. 32 (USD 10.800)**
USD 900/mes x 12. Honorarios profesionales independientes. ~180 hs efectivas: diseno protocolo experimental (Mes 1-3, ~5h/mes) · capturas Scholander (Mes 4-6, ~25h/mes) · validacion (Mes 7-9, ~12h/mes) · publicacion (Mes 10-12, ~18h/mes). Calibracion CWSI locales, supervision Javier, co-autoria publicacion. Incluye acceso lab MEBA-IFRGV-UDEA INTA-CONICET.

**Matias Tregnaghi — CFO / Contador Senior (USD 6.000)**
USD 500/mes x 12, dedicacion 20%. CPA + Diplomatura Finanzas Pymes. Presupuesto ejecutivo, tracking gastos, rendiciones ANPCyT trimestrales + final, liquidacion honorarios, cumplimiento AFIP, coordinacion contador externo y PI.

**Javier Schiavoni — Tecnico de Campo (USD 9.000)**
USD 1.000/mes x 9. Residente Colonia Caroya. ~227 hs efectivas: (0) preparacion base tanque Mes 1 (nivelado tractor, encofrado, hormigonado losa 3m×3m, curado 48h — ~10h); (1) instalacion completa infraestructura riego Mes 1-2 (colocacion tanque 20.000L, excavacion zanjas 136m + cross-headers, tendido 1.450m cinta drip, instalacion electrica 70m, operacion tractor, pruebas hidraulicas — ~80h) + mantenimiento vinedo (72h) + operacion Scholander 4 sesiones OED (20h) + extensometros + mantenimiento nodos (Wet Ref, limpieza lente ISO_nodo). Entrenado por Dra. Monteoliva en protocolo Scholander. Compensacion acorde a carga fisica (zanjas, tractor, instalacion riego) y responsabilidad tecnica (instrumentacion cientifica de precision).

**Infraestructura cloud (USD 500)**
Google Colab Pro x1 usuario (César — entrenamiento PINN + fine-tuning con datos Scholander reales, respaldo RTX 3070): USD 10/mes x 12 = USD 120. Cloudflare R2 storage dataset imagenes termicas (egress gratuito, almacenamiento USD 0,015/GB): ~USD 5/mes x 12 = USD 60. Dominio .com.ar: USD 10. SSL: Let's Encrypt (gratuito). Contingencias cloud: USD 310. VPS MVC (FastAPI + PostgreSQL + Mosquitto + ChirpStack + Redis, Docker Compose): Oracle Cloud Always Free Tier (4 OCPUs ARM Ampere + 24GB RAM, permanentemente gratuito — suficiente para MVC TRL 3-4). Licencias: GitHub Free (repos privados + Actions 2.000 min/mes), W&B Free (tracking ML hasta 3 usuarios), Mapbox Free (50.000 cargas/mes), Figma Free (hasta 3 proyectos) — todos adecuados para escala TRL 3-4 sin usuarios externos.

**Claude Code (USD 2.400)**
Claude Code Max x 2 desarrolladores (Cesar + Lucas) x 12 meses. USD 100/mes neto por usuario. IVA e Impuesto PAIS no elegibles (Art. 22j/22k). Herramienta IA generativa como acelerador de desarrollo backend, firmware, documentacion y analisis.

**Propiedad intelectual (USD 3.500)**
Agente PI redaccion reivindicaciones (USD 1.500) + tasas INPI solicitud patente (USD 400) + busqueda anterioridad certificada nacional e internacional (USD 1.100) + gestion primera respuesta examinador (USD 500).
