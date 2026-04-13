# Sección Hardware — Formulario ANPCyT
## STARTUP 2025 TRL 3-4 — HydroVision AG
### Redactado por: Lucas Bergon (co-fundador, Hardware/PCB/Embebidos — MBG Controls)

---

## 1. Descripción del Nodo de Campo HydroVision AG

El nodo HydroVision AG es un sistema embebido autónomo diseñado para operar en campo de forma continua sin intervención humana. Integra adquisición multisensorial de señales fisiológicas directas de la planta, cómputo local de los índices agronómicos (CWSI, MDS, HSI, GDD), comunicación inalámbrica LoRaWAN y actuación en campo (alertas físicas + control de riego) en una unidad compacta con autonomía solar.

**Decisión de diseño unificado:** el mismo hardware sirve como prototipo TRL 4 y como unidad de producción comercial. No existe una versión de "laboratorio" que luego se rediseña para campo. Esta elección elimina el riesgo de divergencia entre prototipo y producto, reduce el tiempo al mercado y permite que las unidades construidas para TRL 4 sean las primeras unidades vendidas a clientes. El diseño del PCB y la carcasa es responsabilidad del co-fundador Lucas Bergon (MBG Controls, Colonia Caroya).

---

## 2. Especificación de Componentes

| # | Componente | Modelo / Especificación | Costo est. USD | Función |
|---|---|---|---|---|
| 1 | MCU | **ESP32-S3 DevKit** off-the-shelf (dual-core Xtensa LX7 240 MHz, módulo WROOM-1-N4 integrado, USB-C, regulador, pines header). Firmware **MicroPython**. | 8–12 | Procesamiento local: CWSI, HSI, GDD, drivers de sensores, LoRa, alertas. DevKit elimina PCB custom para TRL4. |
| 2 | Cámara LWIR | **MLX90640 breakout integrado** (Adafruit 4407 / SparkFun SEN-14844, sensor BAB 110°×75° FOV, NETD ~100 mK, conector I2C Stemma QT) | 45–55 | Temperatura foliar radiométrica → cálculo CWSI. Error CWSI por NETD: **±0.038** (dentro del umbral ±0.07 de Araújo-Paredes 2022). Módulo plug & play I2C. |
| 3 | Módulo LoRa | SX1276 / SX1262, 915 MHz | 4–6 | Transmisión nodo → gateway LoRaWAN. Sin cobertura celular requerida |
| 4 | Extensómetro tronco | Strain gauge + **ADS1231 24-bit ADC** (resolución 1 µm) + **DS18B20** (corrección térmica ±0.5°C) + abrazadera aluminio anodizado | 40–80 | MDS = D_max − D_min. R²=0.80–0.92 vs. ψ_stem (Fernández & Cuevas 2010). Inmune a viento. Opera 24/7 |
| 5 | Anemómetro | RS485 Modbus RTU, 0.1 m/s resolución, 0–60 m/s, carcasa ABS UV | 25–50 | Rampa gradual 4-12 m/s (14-43 km/h): peso CWSI se reduce linealmente de 35% a 0%. ≥12 m/s (43 km/h) → 100% MDS (Jones 2004). MAX485 en PCB |
| 6 | Pluviómetro | Báscula de balancín, pulso digital GPIO | 12–20 | Interrupción GPIO. Trigger auto-calibración Tc_wet cuando lluvia ≥ 5 mm y MDS ≈ 0 |
| 7 | Sensor T/HR | **SHT31** (±0.3°C, ±2% RH, I2C) + **shelter anti-viento** (6 placas, Gill-type) | 3.5–8 | Temperatura y HR para VPD, coeficientes CWSI, motor GDD. Shelter reduce error T_air por viento de ±0.5°C a ±0.1°C |
| 7b | Piranómetro | Sensor radiación solar (BPW34 + ADC o equivalente) | 15–20 | Radiación solar para cálculo físico de Tc_dry (balance energético). Fuente primaria: Dry Ref panel. Piranómetro: backup y validación científica en TRL 4 |
| 8 | GPS | u-blox NEO-6M o similar (UART) | 8–12 | Georreferenciación del nodo y sesiones. Hemisferio → reinicio acumulador GDD |
| 9 | RTC | DS3231 con batería CR2032 (I2C) | 2–4 | Timestamp sesiones. Persiste ante cortes de energía |
| 10 | IMU + Gimbal pan-tilt | ICM-42688-P + 2× servo MG90S (PWM via LEDC del ESP32-S3) | 20–35 | Escaneo activo: **5 posiciones fijas + 1 extra condicional** (viento > 20 km/h) a ±20°H / ±15°V. IMU compensa vibración. Fusión multi-frame local en ESP32-S3 |
| 11 | Panel solar + batería | Panel 6W policristalino 6V + LiPo / LiFePO4 6.000 mAh | 23–40 | Autonomía energética. Promedio de consumo ~0.18W. Autonomía sin sol: **~120 horas** (5+ días) |
| 12 | Carcasa IP67 (sin PCB custom) | **Hammond IP67 200×150×100mm** + pasacables M16. Arquitectura modular TRL4: DevKit + breakouts I2C/SPI — sin PCB custom. | 15–25 | Protección IP67 + integración modular. 0–45°C, 10–95% RH, polvo, viento 80 km/h. PCB custom reservada para TRL5+ producción. |
| 13 | Paneles Dry Ref / Wet Ref | Panel aluminio negro mate (ε≈0.98) + fieltro hidrofílico + micro-bomba peristáltica 6V GPIO + reservorio 10L | 20 | Calibración física dual 96×/día. Auto-diagnóstico óptico (ISO_nodo). Reservorio: 90–120 días de autonomía sin recarga |
| 13f | Tubo colimador IR | PVC negro 110mm × 250mm + 2 abrazaderas plásticas | 2–4 | Bloquea flujo lateral de aire sobre el FOV del MLX90640. Reduce enfriamiento convectivo de hojas en el campo de visión |
| 13g | Termopar foliar | Type T 0.1mm + MAX31855 SPI + clip mini-pinza + cable trenzado 2m | 4–8 | Ground truth T_leaf por contacto directo, inmune a viento. Corrección IR en tiempo real: T_corr = T_IR + 0.6×(T_tc − T_IR) |
| ~~14~~ | ~~Alertas físicas~~ | ~~LED + sirena~~ | ~~15–20~~ | **REMOVIDO** — mercado objetivo = plantaciones con riego automatizado. El nodo actúa autónomamente (Tier 2) o reporta vía app (Tier 1). Alertas visuales/sonoras no aportan valor. |
| 14b | Sensor partículas PM | **PMS5003** (Plantower) UART 9600 baud — PM1.0 / PM2.5 / PM10 µg/m³ | 12–18 | Detección automática de fumigación (PM2.5 > 200 µg/m³) y lluvia con aerosol. El firmware invalida automáticamente las capturas MLX90640 y extensómetro durante el evento y por el período de clearance post-evento (4h fumigación, 3h lluvia). Elimina necesidad de intervención manual de Javier. |
| 15 | Sistema de montaje | Estaca acero inox. 316 punta cónica 1.5m + bracket aluminio con nivel + conectores M12 IP67 + cableado UV | 30–45 | Instalación estable entre plantas. Resistente a tractor |
| 16 | MAX485 | Transceiver RS485 ↔ UART (en PCB) | 0.5 | Para anemómetro RS485 |
| 17 | Control riego — Tier 2-3 | Relé SSR 24VAC 2A + solenoide Rain Bird 24VAC 1" integrado en nodo. GPIO 41 → SSR → solenoide. Decisión autónoma por HSI (histéresis 0.30/0.20). | 16–25 | Automatización riego autónoma en nodo |
| **TOTAL Tier 1** (monitoreo) | | | **~USD 258–436** | Sin relé ni solenoide. Ahorro ~USD 15-20 vs anterior (sin LED/sirena). |
| **TOTAL Tier 2-3** (automatización) | | | **~USD 274–461** | Sensor + relé SSR + solenoide integrado. |
| **Precio de venta objetivo Tier 1 (Monitoreo)** | | | **USD 950** | Margen bruto hardware ~84% (COGS ~USD 149) |

---

## 3. Balance Energético — Autonomía Solar

| Parámetro | Valor |
|---|---|
| Consumo activo (ESP32-S3 + MLX90640 + sensores) | ~1.8 W |
| Consumo deep sleep | < 15 µA (ESP32-S3 + periféricos apagados) |
| Ciclo cada 15 min: 90s activo + 810s sleep | |
| Consumo promedio ponderado | **~0.18 W** |
| Batería LiPo 6.000 mAh a 3.7V | 22.2 Wh |
| Autonomía sin sol | **~120 horas (5+ días)** |
| Panel 6W con 6h sol efectivo/día | 30 Wh/día generados |
| Consumo diario promedio | ~4.3 Wh/día |
| Balance energético | **+25.7 Wh/día (margen 6×)** |

El ESP32-S3 consume ~85% menos energía que el Raspberry Pi 4 en el mismo ciclo de trabajo, lo que permite operar de forma continua incluso en semanas con escasa radiación solar (período invernal, días nublados consecutivos). En dormancia invernal (1 frame cada 6h), el consumo cae a ~1 µA y la autonomía sin sol supera los 6 meses.

---

## 4. Arquitectura de Procesamiento — ESP32 + Backend

Con ESP32-S3 como plataforma de cómputo, el procesamiento se distribuye entre el nodo y el backend:

### En el nodo (ESP32-S3 — tiempo real, funciona sin internet):
- Cálculo de **CWSI** (Jackson 1981): fórmula matemática directa con datos del MLX90640, SHT31 y paneles Dry/Wet Ref.
- Cálculo de **MDS** con corrección térmica (DS18B20) y estimación de ψ_stem.
- Cálculo de **HSI** con pesos adaptativos y lógica de confianza dinámica por viento.
- **Motor GDD** con detección de estadio fenológico y umbrales CWSI por estadio.
- **Auto-calibración Tc_wet** por eventos de lluvia y sesiones Scholander.
- **Auto-diagnóstico óptico** (ISO_nodo) con detección de obstrucción de lente.
- **Control de riego autónomo** integrado en nodo Tier 2-3: decisión local por HSI → GPIO → SSR → solenoide, sin depender del servidor.

### En el backend (FastAPI + PostgreSQL/PostGIS):
- Modelo **PINN** (Physics-Informed Neural Network, MobileNetV3-Tiny INT8): inferencia profunda sobre los frames térmicos transmitidos. Refina el CWSI calculado en el nodo con correcciones físicas de balance energético foliar. Latencia aceptable en backend (<1s) — el PINN mejora la precisión pero no bloquea las alertas críticas, que ya se generaron en el nodo.
- **Fusión con Sentinel-2**: calibración nodo-satélite para mapas de estrés de lote completo (50+ ha por nodo).
- **Dashboard web**: visualización GeoJSON, notificaciones push configurables (app móvil en TRL 5).
- **Historial y modelos de predicción**: fenología, forecast de cosecha, alertas fitosanitarias.

**Ventaja de esta arquitectura:** el nodo es autónomo en la detección y actuación de emergencia (alertas, riego). El backend agrega precisión y contexto espacial. Un nodo sin conectividad momentánea sigue protegiendo el cultivo.

---

## 5. Sistema de Captura Multi-Angular — Gimbal Pan-Tilt

La cámara MLX90640 se monta sobre un gimbal pan-tilt motorizado de 2 ejes (2× servo MG90S, controlados por PWM via LEDC del ESP32-S3). En cada ciclo de 15 minutos se ejecutan **5 capturas fijas + 1 condicional** en ~8–10 segundos:

| Posición | Ángulo H | Ángulo V | Condición | Propósito |
|---|---|---|---|---|
| Centro | 0° | 0° | Siempre | Referencia base — vista frontal del canopeo |
| Izquierda | −20° | 0° | Siempre | Zona de sombra entre filas |
| Derecha | +20° | 0° | Siempre | Zona de exposición máxima |
| Arriba | 0° | +15° | Siempre | Máxima cobertura foliar, mínima reflexión de suelo |
| Abajo | 0° | −10° | Siempre | Dosel inferior |
| Extra | aleatorio | aleatorio | Viento > 20 km/h | Frame adicional para validación estadística en condiciones de alta vibración |

**Algoritmo de fusión (en el ESP32-S3):**
1. Calcular fracción foliar de cada frame: píxeles en rango P20–P75 del histograma térmico.
2. Retener los 3 frames con mayor fracción foliar.
3. CWSI final = promedio ponderado por fracción foliar de los 3 CWSI individuales.
4. Si desviación estándar entre los 3 CWSI > 0.12 → flag `high_angular_variance` en el payload.

**Resultado:** error CWSI < ±0.07 (comparable a termografía UAV de baja altitud) con captura continua 24/7, sin piloto ANAC ni planificación de vuelo.

**Nota sobre resolución del MLX90640 (32×24 px):** a 6m de altura sobre el canopeo con FOV 110°×75°, cada píxel cubre ~0.53m × 0.38m. En la posición cenital (Arriba, +15°), los 768 píxeles totales mapean un área de ~17m × 9m; de éstos, típicamente 25–40 corresponden a masa foliar. El CWSI calculado sobre ese subconjunto promedia el estado hídrico de ~60 plantas por sesión — suficiente para el seguimiento agronómico continuo en parcelas de 1–10 ha.

---

## 6. Calibración Dual-Referencia (Dry Ref / Wet Ref)

Cada nodo incorpora dos paneles de referencia física montados ~20–50 cm debajo de la cámara en un bracket inferior, con superficies orientadas al cielo. Gracias al amplio FOV del MLX90640 (110°×75°), los paneles caen en la periferia inferior del frame térmico (filas ~20 de 24) en coordenadas de píxel fijas, dejando el centro libre para los ~28 píxeles foliares del canopeo:

- **Dry Ref:** panel de aluminio negro mate (ε≈0.98). Sin mantenimiento. T_dry medida directamente — no modelada.
- **Wet Ref:** panel de fieltro técnico hidrofílico mantenido en saturación por micro-bomba peristáltica 6V (controlada por GPIO del ESP32-S3), desde un reservorio de 10L. Autonomía 90–120 días sin recarga.

El índice Jones (Ig) se calcula 96 veces/día con referencias físicas medidas — sin depender de coeficientes NWSB estimados:

```
Ig = (T_canopeo − T_wet_ref) / (T_dry_ref − T_canopeo)
```

**Auto-diagnóstico óptico (ISO_nodo):** el firmware lee coordenadas de píxeles fijas pre-calibradas de los dos paneles en cada frame. Si T_dry_ref se desvía >1.5°C de la curva teórica (función de T_aire y radiación) → alerta "Lente Sucio/Empañado". El técnico de campo interviene solo cuando ISO_nodo < 80%.

---

## 7. Extensómetro de Tronco (MDS) — Segunda Señal Fisiológica

| Especificación | Valor |
|---|---|
| Sensor | Strain gauge de precisión |
| ADC | ADS1231 24-bit — resolución **1 µm** |
| Corrección térmica | DS18B20 ±0.5°C (α = 2.5 µm/°C, Pérez-López et al. 2008) |
| Correlación vs. ψ_stem | R²=0.80–0.92 (Fernández & Cuevas 2010) |
| Montaje | Tronco principal a 30 cm del suelo, cara norte. Abrazadera aluminio anodizado, diámetros 10–25 cm |
| Disponibilidad | 24/7 — inmune a condiciones meteorológicas |

El extensómetro tiene un segundo rol: cuando llueve ≥5mm y MDS≈0 (tronco al diámetro máximo = planta al máximo de hidratación), la temperatura foliar del MLX90640 en ese instante es el Tc_wet real del nodo. El firmware actualiza el baseline automáticamente (EMA, learning_rate=0.25) sin visita humana.

---

## 8. Precisión Térmica — MLX90640 vs. Umbral Agronómico

| Parámetro | MLX90640 | Umbral agronómico |
|---|---|---|
| NETD (ruido radiométrico) | ~100 mK | — |
| Error CWSI por NETD (1 píxel) | ±0.04 | < ±0.07 (Araújo-Paredes et al. 2022) |
| Error CWSI con 28 píxeles foliares promediados | **±0.008** | < ±0.07 ✓ |
| Error CWSI con paneles Dry/Wet Ref físicos (sin estimar Tc_wet) | ±0.03–0.05 | < ±0.07 ✓ |
| Resolución espacial a 6m, FOV 110° | ~0.53m/px | Suficiente para promedio foliar de parcela |

El promediado sobre múltiples píxeles foliares y la calibración física por paneles de referencia compensan el NETD mayor del MLX90640 respecto al FLIR Lepton 3.5 (50 mK). El error efectivo de CWSI del sistema completo se mantiene dentro del umbral publicado de ±0.07 unidades.

---

## 9. Condiciones de Operación en Campo

| Parámetro | Especificación |
|---|---|
| Temperatura ambiente | 0–45°C (picos 55°C en carcasa al sol directo en Cuyo) |
| Humedad relativa | 10–95% RH |
| Protección | IP65 (polvo + agua) |
| Viento | Hasta 80 km/h (estaca acero inox. 316) |
| UV | Tratamiento UV en carcasa ABS/PC y cableado exterior |
| Conectores externos | M12 IP67 (estándar industrial) |
| Temperatura interna | < 65°C a 45°C ambiente (ESP32-S3 genera mucho menos calor que RPi4) |
| Instalación | Primer nodo: técnico de campo, 2 horas. Nodos adicionales: productor solo con código QR |

---

## 10. Estado TRL 3 — Componentes Validados

### Validados en banco / laboratorio:
- [x] **MLX90640 110°×75° en ESP32-S3:** lectura de frames I2C estable. CWSI calculado sobre planta en maceta con resultado coherente con Jackson (1981).
- [x] **Extensómetro ADS1231 24-bit:** resolución 1 µm verificada en banco. SPI estable en ESP32.
- [x] **Corrección térmica DS18B20** sobre extensómetro: coeficiente α=2.5 µm/°C aplicado.
- [x] **Anemómetro RS485 Modbus RTU** con MAX485: lectura de velocidad de viento estable.
- [x] **Deep sleep ESP32-S3 con DS3231:** wakeup por timer verificado. Consumo sleep: 8 µA medido.
- [x] **Ciclo solar 6W + LiFePO4 6.000 mAh:** balance energético positivo verificado en laboratorio.
- [x] **Gimbal MG90S controlado por PWM LEDC del ESP32-S3:** secuencia angular 5 posiciones ejecutada correctamente.
- [x] **Pipeline Python CWSI/HSI/GDD:** 10 módulos, 135 tests, 0 fallos. Validación computacional completa.

### Pendientes para TRL 4 (Mes 1–12 del proyecto financiado):
- [ ] **PCB prototipo v1 integrada** (Mes 1–2) — MBG Controls / Lucas Bergon.
- [ ] **Integración LoRa nodo ↔ gateway + payload JSON** (Mes 2–3).
- [ ] **Fusión multi-frame en ESP32-S3:** algoritmo de selección por fracción foliar (Mes 2–3).
- [ ] **Extensómetro en tronco adulto de vid en campo** — validación Colonia Caroya (Mes 4).
- [ ] **Prototipo integrado completo con autonomía solar ≥ 72h** en campo (Mes 5).
- [ ] **800 frames térmicos etiquetados con Scholander** bajo protocolo Dra. Monteoliva (Mes 4–9).
- [ ] **Calibración coeficientes Bellvert (2016) para Malbec en Colonia Caroya/Cuyo** (Mes 4–9).
- [ ] **Modelo PINN INT8 en backend** (Mes 6–9 — César Schiavoni + Inv. Art. 32). Latencia < 1s.
- [ ] **Error CWSI predicho vs. Scholander < ±0.10** en viñedo experimental (Mes 9).

---

## 11. Plan de Validación TRL 4 — Viñedo Experimental Colonia Caroya

| Parámetro | Valor |
|---|---|
| Variedad | Malbec |
| Superficie | 1/3 ha (~3.333 m²) |
| Plantas totales | ~1.300 vides (1m entre plantas × 2.5m entre hileras) |
| Altitud | ~700 m s.n.m. |
| Nodos instalados | **5 nodos** (1 por zona hídrica) — las primeras 5 unidades del producto |
| Densidad comercial equivalente | 1 nodo cubre 1/3 ha (sobre-densificado vs. Tier 1: 1/10 ha) — fortaleza experimental |
| Técnicos de campo | Javier y Franco Schiavoni (residentes, hermanos de César) |
| Supervisión científica | Dra. Mariela Monteoliva (INTA-CONICET) — protocolo Scholander |
| Riego | Canal → goteo con 5 zonas independientes (Mes 3–4, contrapartida equipo) |

**Diseño experimental:**
- 4 filas de 136m con 5 zonas hídricas (100% ETc → sin riego).
- 32 brackets fijos en espaldera + gimbal multi-angular.
- Protocolo Scholander: 10 plantas/zona × 50 plantas/sesión, 2×/semana en período crítico (Mes 4–9).
- 800 frames térmicos etiquetados con ψ_stem verificado por Scholander.

**Posicionamiento de nodos dentro de cada zona hídrica:**
Cada nodo se instala en la **planta central de su zona** (~planta 14 desde el inicio de la zona de 27m, con espaciado 1m entre plantas). Se evitan las 3 plantas más cercanas a cada frontera de zona por dos razones: (1) en los extremos existe gradiente hídrico por movimiento lateral de agua entre tratamientos — la planta no representa el régimen de riego puro de la zona; (2) el píxel Sentinel-2 de calibración (10m × 10m) que contiene al nodo debe caer íntegramente dentro de la zona, garantizando que el valor espectral utilizado para calibrar la extrapolación satelital corresponde al tratamiento de esa zona y no a una mezcla de dos tratamientos adyacentes. El extensómetro de tronco se instala en la misma planta central que el nodo.

**Criterios de éxito TRL 4:**

| Hito | Meta |
|---|---|
| Autonomía solar continua | ≥ 72 horas sin sol |
| Transmisión LoRaWAN a 500m | Latencia < 5 s, payload < 50 bytes |
| Error CWSI vs. Scholander | < ±0.10 unidades |
| R² HSI vs. ψ_stem | ≥ 0.80 |
| Modelo PINN — accuracy en 120 frames independientes | > 85% |
| Dashboard web GeoJSON | Funcional (app móvil TRL 5) |

---

## 12. Rol de Lucas Bergon

Lucas Bergon (MBG Controls, 45% del capital de HydroVision AG) es responsable de todo el hardware del proyecto:

- Diseño del **PCB integrado** (Mes 1–2) y selección final de componentes.
- Desarrollo del **firmware ESP32-S3**: drivers de todos los sensores, CWSI/HSI/GDD en nodo, control gimbal, LoRa, alertas, deep sleep.
- **Instalación y mantenimiento** de los 5 nodos en viñedo experimental (Mes 4–5).
- Coordinación técnica con César Schiavoni (backend) para el pipeline de transmisión de frames al backend PINN.

MBG Controls tiene experiencia demostrada en diseño de PCBs industriales y sistemas embebidos con protocolos RS485/Modbus en ambientes agresivos — experiencia directamente aplicable a las condiciones del viñedo en Cuyo y NOA.
