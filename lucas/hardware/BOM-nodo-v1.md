# BOM — Nodo HydroVision AG v1
## Bill of Materials — Revisión inicial (completar con Lucas)

> **COGS de referencia (lote 50 unidades):** USD 149/nodo base (incluye shelter SHT31, tubo colimador IR y termopar foliar).
> **Con mejoras v2 viento:** USD 158-163/nodo (+$9-14 por segundo termopar + placas Muller). Ultrasónico opcional: +$12-35.
> **Arquitectura TRL4:** ESP32-S3 DevKit + módulos breakout I2C/SPI + MicroPython — sin PCB custom.
> Con volumen 500+ unidades: COGS baja a ~USD 121-130 (arquitectura revierte a bare chip + PCB custom de producción).
> El total "235-415" de la última fila es el rango máximo de mercado — no el COGS de producción.

| # | Componente | Modelo / Part# | Qty | COGS USD | Dónde comprar | Función en el sistema | Notas críticas |
|---|---|---|---|---|---|---|---|
| 1 | **MCU** | **ESP32-S3 DevKit** (off-the-shelf, con módulo WROOM-1-N4 integrado) | 1 | 8–12 | AliExpress "ESP32-S3 DevKit N4" · MercadoLibre "ESP32-S3 DevKit" | Cerebro del nodo. Ejecuta el firmware completo en **MicroPython**: pipeline CWSI, cálculo HSI, control de todos los sensores (I2C/SPI/Modbus RTU), serialización JSON, deep sleep entre ciclos. Dual-core 240 MHz, 8MB RAM, Wi-Fi/BLE (no usado en campo — solo para debug). Placa de desarrollo off-the-shelf — **elimina la necesidad de PCB custom para TRL4**. | DevKit incluye regulador, USB-C, antena integrada y pines header listos para conectar breakouts I2C/SPI. Deep sleep: 8 µA. Ciclos: 96/día a 15 min. Firmware en MicroPython (no C/Arduino) — desarrollo más rápido con misma funcionalidad. |
| 2 | **Módulo LoRa** | EBYTE E32-900T20D (SX1276 interno) | 1 | 5–7 | AliExpress "E32-900T20D" | Comunicación inalámbrica nodo → gateway de campo. Transmite el payload JSON cada 15 min por LoRaWAN privado a 915 MHz. Rango en campo abierto: 1–3 km. Sin internet ni SIM card. | **Comprar 915 MHz únicamente** (banda ISM Argentina, Res. 296/2021 ENACOM). El Ra-02 sin sufijo H es 433 MHz — no sirve. Config.h: `LORA_FREQ_HZ 915E6`, SF7, BW125kHz, 17dBm. Driver: `driver_lora.h`. |
| 3 | **Cámara LWIR** | **MLX90640 breakout integrado** (Adafruit 4407 o SparkFun SEN-14844, sensor MLX90640ESF-BAB-000-SP con lente 110° FOV incluido) | 1 | 45–55 | Adafruit adafruit.com/product/4407 · SparkFun sparkfun.com · MercadoLibre "MLX90640 breakout" · AliExpress "MLX90640 module I2C" | Mide temperatura del canopeo (hoja) en una grilla de 32×24 píxeles. Módulo breakout integrado con lente 110°×75° FOV ya montado y enfocado, level shifter I2C, y agujeros de montaje M2.5. Se conecta al ESP32-S3 DevKit con un cable I2C Stemma QT/Qwiic — **plug & play, sin diseño óptico ni PCB custom**. | **Verificar FOV 110°** (suffix BAB). Sensor: MLX90640ESF-BAB-000-SP (mismo chip, en módulo integrado). NETD 100 mK → error CWSI ±0.008 con 28 px foliares. Conector I2C estándar (0x33). Librerías MicroPython disponibles. Comprar 7 unidades (5 + 2 spare). Para vol. 500+: evaluar bare chip a USD 18-22 con PCB custom de producción. |
| 3b | **Cámara LWIR alt-A** | MLX90641BAB (16×12 px) | 1 | 18–22 | Mouser / LCSC / Melexis | Misma función que fila 3, menor resolución. Usar si MLX90640 no tiene stock. Mismo package TO39, mismo protocolo I2C, misma dirección 0x33. Resolución reducida → menos px foliares (~7-10 px vs. 28) → error CWSI mayor (~±0.025). | HW-03 alternativa A. Solo cambiar `SENSOR_TERMICO SENSOR_TERMICO_MLX90641` en config.h — nada más en firmware. Aceptable para detección de estrés severo (CWSI > 0.6), degradado para precisión fina. |
| 3c | **Cámara LWIR alt-B** | Heimann HMS-C11L (16×16 px) | 1 | 22–28 | Heimann Sensor GmbH (Alemania) — contacto directo para muestras | Misma función que fila 3. Fabricante independiente de Melexis → diversifica supply chain completamente. 16×16 px, TO39-compatible, I2C dirección 0x40. | HW-03 alternativa B. Cambiar `SENSOR_TERMICO SENSOR_TERMICO_HMS_C11L` en config.h. **Pendiente:** validar timing I2C del HMS-C11L contra driver — API ligeramente distinta al MLX. No usar en producción sin validación previa. |
| 4 | **Extensómetro** | Strain gauge 120Ω full-bridge + ADS1231IPWR + DS18B20 waterproof + abrazadera Al anodizado | 1 conjunto | 18–35 | ADS1231: LCSC C92560 · Strain gauge: AliExpress "strain gauge 120ohm full bridge" · DS18B20: LCSC C105950 · Abrazadera: tornería local | Mide la micro-contracción diaria del tronco (MDS = D_max − D_min en µm). Es la señal secundaria del HSI — indica el estado hídrico acumulado del sistema suelo-planta. Opera 24/7 incluyendo noches y días nublados cuando el CWSI no funciona. El DS18B20 corrige la dilatación térmica del tronco (α = 2,5 µm/°C). | ADS1231: resolución 1 µm, interfaz bit-bang SPI (SCLK=14, DOUT=15, PDWN=16). Montar abrazadera a 30 cm del suelo, cara norte del tronco. **Calibrar ADS1231_COUNTS_PER_UM** con medición de referencia antes de usar (ver pendientes README). MDS_MAX_MM = 0,5 mm en config.h — ajustar con datos del viñedo en mes 4-6. Driver: `driver_mds.h`. |
| 5 | **Anemómetro** | RS485 Modbus RTU, 0–60 m/s, IP65 | 1 | 20–35 | AliExpress "wind speed sensor RS485 modbus rtu IP65" (elegir ≥ 200 ventas, ≥ 4.5★) | Mide velocidad del viento para corregir el CWSI. El viento produce enfriamiento convectivo artificial de la hoja. El firmware aplica rampa gradual 4-18 m/s (14-65 km/h): el peso del CWSI se reduce linealmente de 35% a 0% (extendida por mitigaciones v2: Kalman IR↔termopar, Muller gbh, Hampel filter). A ≥18 m/s (65 km/h): `wind_override=true` → HSI = 100% MDS. Las 9 capas de mitigación física (sotavento, shelter, tubo colimador, termopar) + mejoras algorítmicas v2 extienden el rango útil del CWSI de 4 a 18 m/s. Sin este sensor, el sistema daría falsas alarmas en días de Zonda en San Juan (~15-30 días/temporada). | Config.h: `WIND_RAMP_LO 4.0f`, `WIND_RAMP_HI 18.0f`, `RS485_REG_WIND 0x0000`. **Verificar con el datasheet del sensor comprado** que el registro 0x0000 es velocidad — algunos modelos usan 0x0001. MAX485 (fila 13) es el transceiver. Driver: `driver_anemometro.h`. Comprar 2 (spare). |
| 6 | **Pluviómetro** | Báscula de balancín 0,2 mm/pulso, IP65 | 1 | 12–18 | AliExpress "rain gauge tipping bucket 0.2mm pulse" · MercadoLibre AR "pluviómetro báscula" | Detecta lluvia en tiempo real. Dos usos críticos: (1) trigger de auto-calibración del baseline Tc_wet — cuando llueve ≥ 5 mm y MDS ≈ 0, la temperatura foliar medida en ese momento ES el Tc_wet real del nodo (ver sección 4.2.3 de doc-02). (2) Activar clearance de 3h post-lluvia para evitar capturas térmicas con gotas en el canopeo. | Pin: GPIO 2 (interrupción ISR + debounce 200ms). `PLUV_MM_PER_PULSE 0.2f` en config.h — **confirmar con el datasheet del modelo comprado**. `LLUVIA_MIN_MM 5.0f` = umbral para activar auto-calibración Tc_wet. Driver: `driver_pluviometro.h`. |
| 7 | **Sensor T/HR** | SHT31-DIS-B (±0,3°C, ±2% RH, I2C) | 1 | 1,80 | LCSC C97083 (chip) · AliExpress "SHT31 breakout" para proto | Mide temperatura del aire (T_air) y humedad relativa (RH) del entorno. T_air es usada en el cálculo de CWSI para derivar ΔT_LL y ΔT_UL (límites del índice). RH entra en el cálculo del VPD, que determina la demanda evapotranspirativa. Error en T_air de ±1°C produce error de CWSI de ±0.08 — justifica el SHT31 sobre el BME280 (±1°C). | I2C dirección 0x44. **Instalar dentro del shelter anti-viento (fila 7c).** **No exponer al sol directo** — T_air se sobreestimaría 3-8°C con irradiación directa. Driver: `driver_sht31.h`. Nota: el firmware busca `Adafruit_SHT31` — si se cambia a SHT40, actualizar librería y driver. |
| 7c | **Shelter anti-viento SHT31** | Shelter tipo Gill de 6 placas (impresion 3D PETG o platos plasticos apilados) | 1 | 0,50–2 | Impresion 3D local (PETG blanco) o ferreteria (6 platos plasticos blancos 12cm + varilla roscada M4 inox + separadores 15mm) | Protege el SHT31 del viento directo y la radiacion solar sin impedir la ventilacion pasiva. Sin shelter, el viento directo sobre el SHT31 puede introducir error de ±0,5°C en T_air por enfriamiento convectivo, que propaga ±0,05-0,10 de error al CWSI via el calculo de VPD. Las 6 placas horizontales apiladas con separacion de 15mm crean un ambiente de conveccion natural donde el aire se renueva pero sin flujo forzado. Diseño basado en el shelter Gill estandar de estaciones meteorologicas (WMO Guide No. 8, 2018). | Dimensiones: 6 placas circulares de 12cm diametro, separadas 15mm, montadas en varilla M4 central. Total: ~12cm diametro × 10cm alto. Color: **blanco** (refleja radiacion solar — no usar colores oscuros). Material: PETG (resiste UV y temperatura hasta 70°C) o platos plasticos blancos de ferreteria. Montar a la misma altura que la carcasa del nodo, del lado norte del poste (maximo flujo de aire). El SHT31 se ubica en el plato central (plato 3 de 6, contando desde arriba). Sujetar al poste con 2 bridas UV. |
| 7b | **Piranómetro** | BPW34 + ADC (o VEML7700 I2C) | 1 | 0,15–3 | BPW34: LCSC C259698 · VEML7700: LCSC C387631 | Mide radiación solar incidente (W/m²). Se usa para dos propósitos: (1) calcular Tc_dry con el balance energético foliar (Itier & Katerji 1991) en lugar de la aproximación empírica actual; (2) activar modo ahorro HW-02 cuando rad < 150 W/m² indica día nublado (CWSI poco informativo). | **Opción preferida: VEML7700** (I2C 16-bit, USD 1,20) — evita la etapa analógica y la calibración de `PYRANO_WPM2_PER_MV`. Si se usa VEML7700, actualizar `driver_piranometro.h` de ADC a I2C. BPW34 requiere calibración con sensor de referencia (Davis Vantage Pro2). Si no hay referencia disponible en TRL 4, usar fallback: Tc_dry estimada desde T_air + RH + viento (aproximación ya implementada en `calcular_tc_dry()`). |
| 8 | **GPS** | u-blox NEO-6M con antena cerámica | 1 | 5–8 | AliExpress "NEO-6M GPS module Arduino" | Obtiene la posición geográfica del nodo (lat/lon) en el primer boot. La posición se persiste en RTC memory y no se vuelve a leer en ciclos subsiguientes — el GPS está apagado el 99,9% del tiempo. La posición es usada por el backend para mapear el nodo en el lote, asociarlo con la capa Sentinel-2 correcta, y verificar que no se movió (vs. IMU). | UART1 (RX=5). Solo se activa en boot 1 con timeout de 2000 ms (`GPS_TIMEOUT_MS`). Si no hay fix en 2s, el nodo funciona sin GPS hasta el próximo reset. `rtc_gps_ok` persiste en RTC memory. Driver: `driver_gps.h`. |
| 9 | **RTC** | DS3231SN + CR2032 | 1 | 1,50 | LCSC C9868 (chip) · AliExpress "DS3231 RTC module" para proto | Mantiene la hora exacta entre ciclos de deep sleep. Sin RTC, el ESP32 pierde la hora al entrar en deep sleep y el timestamp del payload sería incorrecto. El DS3231 tiene ±2 ppm de drift (< 1 min/año). La hora local se usa en HW-02 para `ventana_solar_activa()`. | I2C 0x68. Batería CR2032 mantiene la hora ante cortes de energía (días de tormenta, mantenimiento). `rtc_leer_hora_local()` implementado en `driver_rtc.h` — convierte UTC a UTC-3 Argentina. Sincronizar con GPS en primer boot (`rtc_sync_gps()`). |
| 10 | **Panel solar** | Policristalino 6V / 6W | 1 | 12–18 | MercadoLibre AR "panel solar 6V 6W" · AliExpress "6V 6W solar panel" | Recarga la batería durante el día. Con HW-02 (activación adaptativa), el consumo promedio del nodo es ~14 µA equivalente en deep sleep + picos de 180 mA durante captura activa. Un panel de 6W a 6h de sol efectivo/día en Cuyo genera 36 Wh/día vs. consumo promedio ~0,18W × 24h = 4,3 Wh/día. Balance energético: +31 Wh/día de excedente en verano. | **6V nominal** (no 12V). El MPPT-CN3791 está diseñado para 6V de entrada. En invierno (4h sol/día): genera 24 Wh vs. 4,3 Wh consumo — sigue positivo. El nodo puede operar indefinidamente con el panel. Sin panel: autonomía de batería 13-17 meses (LiFePO4 6Ah). |
| 11 | **MPPT / cargador** | DFR0559 (recomendado) o CN3791 + inductor + caps | 1 | 3–6 (CN3791) / 10–15 (DFR0559) | CN3791: LCSC C5443 · DFR0559: AliExpress "DFR0559 solar power manager" | Gestiona la carga de la batería desde el panel solar con seguimiento del punto de máxima potencia (MPPT). Sin MPPT, el panel opera a voltaje fijo y pierde hasta 30% de eficiencia de carga. | **Recomendado para TRL 4: DFR0559** — módulo completo MPPT + cargador + salidas reguladas 5V y 3.3V. Evita diseñar el circuito de potencia desde cero. CN3791 es la opción chip para producción (menor costo, requiere diseño de circuito con inductor 22µH y capacitores). |
| 12 | **Batería** | LiFePO4 32650 3,2V 6Ah | 1 | 8–15 | AliExpress "LiFePO4 32650 6Ah" | Almacena energía para operar durante la noche y días nublados. Con el consumo del nodo (~0,18W promedio), 6Ah × 3,2V = 19,2 Wh → autonomía ~4,4 días sin sol. | **LiFePO4 sobre LiPo**: ciclos de vida 2000+ vs. 500 (LiPo), estable a temperaturas altas (interior de carcasa puede llegar a 50°C en verano de Cuyo). Tensión nominal 3.2V — ajustar `BAT_FULL_MV 3600` en config.h si se usa LiFePO4 (no 4200 que es LiPo). Tensión mínima operativa: `BAT_EMPTY_MV 2800` para LiFePO4. |
| 13 | **MAX485** | MAX485ESA+ (SOIC-8) | 1 | 0,25 | LCSC C7705 | Transceiver que convierte el bus RS485 diferencial del anemómetro al UART del ESP32. El anemómetro Modbus RTU usa RS485 porque el par diferencial es inmune a interferencias a distancias de hasta 100m en campo (el anemómetro puede estar lejos del nodo). | Pedir en lote de 10 — pesan nada. Pin DE (driver enable): GPIO 3, HIGH para transmitir, LOW para recibir. Protocolo Modbus RTU 9600 baud. No requiere librería externa — implementado en `driver_anemometro.h` con CRC16. |
| 13b | **IMU + Gimbal** | ICM-42688-P breakout + 2× servo MG90S (metal gear) | 1 conjunto | 8–18 | ICM-42688-P: AliExpress "ICM-42688-P breakout" o SparkFun DEV-19764 · MG90S: AliExpress "MG90S servo metal gear" ×2 | El gimbal mueve la cámara MLX90640 a 5-6 posiciones angulares antes de cada captura (pan ±20°, tilt ±15°). Esto aumenta la cobertura efectiva del canopeo y reduce el error CWSI de ±0.10 a ±0.07 (equivalente a un drone térmico de baja altitud). La IMU verifica que el gimbal se estabilizó antes de capturar (sin vibración > 0,5 m/s²) y detecta si el nodo fue golpeado o movido. | SPI: CS=22, INT1=23 (bus compartido con LoRa en MOSI=34/MISO=33/SCLK=32). Servos: LEDC PWM GPIO 20 (PAN) y 21 (TILT). **Comprar MG90S metálico** — los SG90 plásticos se deforman con temperatura. `GIMBAL_SETTLE_MS 300` en config.h. Librería: SparkFun ICM-42688-P. Driver: `driver_imu.h` + `driver_gimbal.h`. |
| 13c | **Paneles Dry/Wet Ref** | Al anodizado negro (Dry) + fieltro hidrofílico + bomba peristáltica 6V + reservorio 10L (Wet) | 1 conjunto | 15–22 | Aluminio negro: ferretería industrial + pintura Rust-Oleum negro mate alta temp · Fieltro: tlapalería · Bomba: AliExpress "peristaltic pump 6V" · Reservorio: ferretería local | Los paneles de referencia son el mecanismo de auto-calibración física del CWSI. El panel Dry (aluminio negro, ε ≈ 0,98) tiene temperatura conocida = T_aire + offset solar → sirve como Tc_dry de referencia física. El panel Wet (fieltro empapado) tiene temperatura próxima a Tc_wet → âncora el límite inferior del CWSI. La bomba recarga el fieltro húmedo automáticamente (pulso de 3 seg cada ciclo). El ISO_nodo compara la temperatura medida del Dry Ref contra la esperada para detectar lente sucio. | Posición en el frame MLX: filas/columnas calibradas en campo con `mlx_calibrar_iso_nodo()` (ver pendientes README). Autonomía del reservorio de agua: 90-120 días. `BOMBA_PULSO_MS 3000` en config.h. Driver ISO_nodo integrado en `driver_mlx90640.h`. |
| 13d | **Sensor partículas** | PMS5003 (Plantower) — PM1.0/PM2.5/PM10 | 1 | 10–14 | LCSC C2660761 · AliExpress "PMS5003 particulate sensor" (pedir con cable JST 8 pines) | Detecta automáticamente eventos de fumigación (PM2.5 > 200 µg/m³) y lluvia con aerosol. Cuando detecta fumigación, el firmware invalida las capturas térmicas de las siguientes 4h (el aerosol contamina el lente MLX90640). Sin este sensor, el sistema requeriría que el productor informe manualmente cada fumigación — inviable en operación autónoma. Además detecta lluvia por PM elevado antes de que el pluviómetro registre acumulación. | UART1 compartido con GPS (RX=12, TX=13 desde boot 1 en adelante — GPS usa GPIO 5 solo en boot 0). Protocolo propietario Plantower de 32 bytes — implementado en `driver_pms5003.h` sin librería externa. `PMS_WARMUP_MS 3000` (3s calentamiento láser). Umbrales: fumigación PM2.5 > 200, lluvia > 80 en config.h. |
| 13e | **Limpieza piezoeléctrica** | Murata MZB1001T02 + driver boost MT3608L | 1 | 4–6 | Murata MZB1001T02: Mouser Part# 81-MZB1001T02 · MT3608L boost: LCSC C84818 | El actuador piezoeléctrico vibra el lente del MLX90640 durante 500ms antes de cada captura para desprender polvo, rocío y residuos de fumigación. Sin limpieza activa, la acumulación gradual de polvo reduce la transmitancia del lente y degrada el ISO_nodo progresivamente hasta invalidar las mediciones. Elimina la necesidad de mantenimiento manual del lente (cada 2-4 semanas en campo). Reivindicación técnica #1 de la patente en trámite. | GPIO 24 (`PIN_PIEZO_CLEANER`). El MT3608L eleva 3,7V (batería) a 20Vpp para excitar el piezo (rango de operación del MZB1001T02: 15-30Vpp). Pulso: 500ms cada ciclo de captura. `PIEZO_PULSO_MS 500` en config.h. **Solo Mouser/DigiKey** — no está en AliExpress. Pedir en lote de 10. |
| 13f | **Tubo colimador IR** | Tubo PVC 110mm diámetro × 250mm largo, pintado negro mate interior (Rust-Oleum alta temp.) + soporte bracket de fijación | 1 | 2–4 | Ferretería local (tubo PVC 110mm sanitario) + pintura negro mate alta temp. | Bloquea el flujo lateral de viento sobre el campo visual (FOV) de la cámara MLX90640 sin alterar las condiciones naturales de las hojas. Funciona como un parasol cilíndrico: la cámara ve a través del tubo, pero el viento transversal no entra al FOV. Reduce el ruido por movimiento de hoja dentro del campo visual y atenúa la convección forzada en la zona de medición inmediata. Principio similar a los radiómetros de campo profesionales (Apogee SI-111/SI-131). Reduce error CWSI por movimiento de hoja de ±0.04 a ±0.01. | Montar solidario al bracket de la cámara, concéntrico con el lente MLX90640. La longitud de 250mm no recorta el FOV de 110°×75° a la distancia de trabajo de 6m (el canopeo cubierto pasa de ~60 a ~45 plantas — suficiente). Interior pintado negro mate para evitar reflexiones IR internas. **No usar tubo metálico** — el metal se calienta al sol y emite IR que contamina la lectura. PVC es transparente a LWIR en pared, pero opaco en el diámetro → funciona como colimador. Limpiar interior cada temporada (polvo acumulado). |
| 13g | **Termopar foliar** | Termopar tipo T (cobre-constantán) Ø0.1mm + amplificador MAX31855KASA+ (SPI) + clip de fijación a hoja | 1 conjunto | 4–8 | MAX31855: LCSC C12563 · Termopar tipo T 0.1mm: AliExpress "thermocouple type T 0.1mm wire" (pedir AWG 40, par trenzado, 2m largo) · Clip: impresión 3D mini-pinza con resorte | Mide la temperatura de una hoja representativa por **contacto directo**, inmune al viento. Se usa como referencia cruzada (ground truth) para corregir la lectura IR del MLX90640 en tiempo real. La corrección empírica `T_leaf_corr = T_leaf_IR + k × (T_termopar - T_leaf_IR)` compensa el enfriamiento convectivo que afecta a la lectura IR pero no al termopar. Reduce el error CWSI por convección de viento de ±0.08 a ±0.02. Combinado con el tubo colimador, el error total por viento baja a ±0.03 (cerca del piso NETD ±0.008 del sensor). | SPI: CS en GPIO 25 (`PIN_TC_CS`), bus compartido con LoRa + IMU (MOSI=34/MISO=33/SCLK=32). El MAX31855 tiene resolución de 0.25°C y precisión de ±1.0°C en el rango 0-70°C — suficiente para corrección diferencial (lo que importa es la **diferencia** T_termopar - T_IR, no el valor absoluto). El termopar tipo T (cobre-constantán) es el estándar para medición foliar en fisiología vegetal. Hilo de 0.1mm (AWG 40) para minimizar la masa térmica sobre la hoja (la punta pesa <0.01g — no altera la temperatura de la hoja). Clip de fijación: mini-pinza 3D con resorte que sujeta el hilo del termopar al envés de una hoja representativa a la altura del canopeo. **Reemplazar la hoja cada visita de mantenimiento** (mensual) si se nota marchitamiento o daño por el clip. Driver: `driver_termopar.h`. Factor de corrección `k` calibrado en campo con Scholander (valor inicial sugerido: k=0.6 — ajustar por varietal). |
| 13h | **Segundo termopar foliar** [A3] | Termopar tipo T Ø0.1mm + MAX31855KASA+ (SPI) + clip — idéntico a 13g | 1 conjunto | 4–8 | Mismo que 13g | Segundo termopar en hoja diferente de la misma planta. El firmware promedia ambas lecturas si las dos son válidas (diferencia < 2°C). Si una falla o diverge, usa la otra (degradación elegante). Redundancia: si una hoja se mueve o pierde contacto por viento, la otra sigue midiendo. Reduce el error por fallo de contacto en eventos de viento fuerte. | SPI: CS en GPIO 26 (`PIN_TC2_CS`). `TC2_ENABLED true` en config.h. Mismo bus SPI compartido. Instalar en hoja del mismo cuadrante pero en un sarmiento diferente (diversidad espacial). |
| 13i | **Placas Muller aluminio** [C4] | 2 placas aluminio 5×5cm (una pintada negro mate α=0.95, una blanca α=0.15) + bracket de montaje en FOV del MLX90640 | 1 conjunto | 1–2 | Ferretería industrial (planchuela aluminio 1mm) + Rust-Oleum negro mate + blanco brillante | Referencia dual Muller (2021, New Phytologist) para medir la conductancia de la capa límite (gbh) in situ. La diferencia de temperatura entre la placa negra y blanca, combinada con la radiación solar medida, permite calcular gbh directamente: `gbh = (Δα × Rn) / (ρ·Cp × ΔT)`. El gbh es el parámetro físico que el viento modifica — medirlo directamente es más preciso que estimarlo desde la velocidad del viento. Se integra con el quality score del firmware y alimenta al modelo ML de corrección. | Posicionar ambas placas dentro del FOV del MLX90640, en las filas/columnas configuradas en config.h (`MULLER_BLACK_ROW_INI`, etc.). **Las placas NO deben hacer sombra al canopeo.** Montar en bracket inferior, apuntando al cielo (misma orientación que paneles Dry/Wet Ref). Espesor: 2mm (`MULLER_THICKNESS_M 0.002`). Separación mínima entre placas: 3cm para evitar conducción lateral. |
| 5b | **Anemómetro ultrasónico 2D** [A1] (upgrade opcional) | FT742 / Gill WindSonic / genérico China — RS485 Modbus RTU, velocidad + dirección, sin partes móviles | 1 | 15–40 | AliExpress "ultrasonic wind sensor RS485 2D" · Gill Instruments (WindSonic) | Upgrade opcional del anemómetro mecánico (fila 5). Mide velocidad Y dirección del viento sin partes móviles. Permite al firmware saber si el viento viene por sotavento (menor efecto en hoja) o barlovento (mayor efecto). Sin inercia de cazoletas: responde en <1s a cambios de ráfaga. Vida útil > 10 años sin mantenimiento (sin piezas de desgaste). | Misma interfaz RS485 Modbus RTU → drop-in replacement. `ANEMO_TYPE ANEMO_TYPE_ULTRASONIC` en config.h. Agrega campo `wind_dir` [grados] al payload JSON. **No obligatorio para TRL4** — el mecánico (fila 5) sigue siendo la opción por defecto. El ultrasónico se recomienda para nodos en zonas de Zonda frecuente donde la información de dirección mejora la corrección. |
| 14 | **Rele SSR 24VAC** (Tier 3) | Rele estado solido 24VAC 2A + diodo volante | 1 | 1–3 | AliExpress "SSR relay 24VAC" | Tier 3: el nodo controla directamente un solenoide Rain Bird. GPIO 41 → SSR → solenoide 24VAC. El nodo decide autonomamente cuando regar (HSI >= 0.30). Tier 1-2: no se instala este componente. | `PIN_SOLENOIDE 41` en config.h. `SOLENOIDE_CANAL 0` = sin solenoide (Tier 1-2). El GPIO mantiene estado durante deep sleep via `gpio_hold_en()`. Driver: `driver_solenoide.h`. |
| 15 | **Solenoide Rain Bird** (Tier 3) | Rain Bird 24VAC 1" | 1 por nodo | 15–25 | Rain Bird distribuidores AR | Control automatico de riego. Activado directamente por el nodo cuando HSI cruza el umbral. Sin Controlador de Riego intermedio. | Wiring: nodo GPIO → SSR → solenoide. Transformador 24VAC existente en tablero Rain Bird. Cada nodo Tier 3 controla UN solenoide (1 canal). |
| 16 | ~~**PCB custom**~~ | **ELIMINADA para TRL4** — todos los componentes usan módulos breakout I2C/SPI conectados al ESP32-S3 DevKit | 0 | 0 | — | **Arquitectura modular TRL4:** el ESP32-S3 DevKit reemplaza la PCB custom. Todos los sensores se conectan via cables I2C (Stemma QT/Qwiic) o SPI. Los módulos se montan dentro de la carcasa con tornillos o velcro industrial. Si un módulo falla, se reemplaza en 5 minutos sin herramientas de soldadura. | **Para TRL5+ producción (vol. 500+):** evaluar PCB custom 4-layer para reducir COGS ~USD 25-30/nodo. El diseño modular de TRL4 sirve como validación funcional antes de invertir en PCB de producción. Separación de planos analógico/digital sigue siendo crítica para ADS1231. |
| 17 | **Carcasa IP67** | **Hammond 1554W o Gewiss GW44210** — ABS/PC **200×150×100mm** + pasacables M16 IP67 | 1 | 15–25 | MercadoLibre AR "caja estanca IP67 200x150" · Hammond distribuidores · AliExpress "IP67 enclosure 200x150x100" · Pasacables: AliExpress "cable gland M16 IP67" | Protege la electrónica del campo: polvo, rocío, fumigaciones, lluvia, temperaturas extremas (−5°C a +60°C). **Dimensiones aumentadas a 200×150×100mm** para alojar holgadamente los módulos breakout, DevKit, batería y cableado I2C/SPI. Más robusta que la versión anterior (150×100×70mm). IP67 = sellado contra polvo + inmersión temporal. | Comprar con membrana de ventilación (GORE-Tex o similar) para evitar condensación interior. 6-7 pasacables M16 por carcasa. Espacio interior suficiente para gestión térmica pasiva sin aleta externa (el ESP32-S3 DevKit genera poco calor). |
| **TOTAL COGS Tier 1-2 (base)** | | | | **USD ~149** (lote 50) / **~USD 121** (lote 500+) | | Incluye tubo colimador + termopar foliar + shelter SHT31. Sin relé ni solenoide. Arquitectura TRL4: DevKit + breakouts + sin PCB custom. | **Arquitectura modular TRL4:** DevKit (+$6.50) + breakout MLX (+$16) + Hammond IP67 (+$6) − PCB custom (−$27.50) = delta neto ~+$1/nodo. A vol. 500+: se revierte a bare chip + PCB custom → COGS similar. |
| **TOTAL COGS Tier 1-2 (con v2 wind)** | | | | **USD ~158-163** (lote 50) | | Todo lo base + segundo termopar (13h, +$4-8) + placas Muller (13i, +$1-2) + reservorio capilar Wet Ref (ya en 13c). Sin ultrasónico (fila 5b es upgrade opcional, +$12-35 adicional). | **Mejoras v2 viento:** COGS incremental +$5-10/nodo (sin ultrasónico) o +$17-45/nodo (con ultrasónico). Las mejoras de software (B1-B6, C1-C6) no tienen costo de hardware. |
| **TOTAL COGS Tier 3** | | | | **USD ~165** (lote 50) / **~USD 137** (lote 500+) | | Todo lo anterior + relé SSR + solenoide Rain Bird integrado. | El costo incremental de Tier 3 vs Tier 1-2 es ~USD 16-25 (relé + cableado). El solenoide Rain Bird ya existe en campo. |

---

## ~~BOM — Controlador de Riego (dispositivo independiente)~~ — DEPRECADO

> **Arquitectura reemplazada (abril 2026):** El controlador de riego independiente
> (ESP32 WROOM-32 + LoRa RX + 5 relés SSR) ya no existe. El control de solenoide
> se integra directamente en el nodo sensor Tier 3 mediante un relé SSR único
> controlado por GPIO del ESP32-S3. El nodo decide autónomamente cuándo regar
> basándose en el HSI local (histéresis 0.30/0.20). El servidor solo se entera
> del estado vía el payload `/ingest`.
>
> **Ver:** ítems 14-15 del BOM principal (Tier 3) y `driver_solenoide.h` en firmware.
>
> **Ahorro:** se elimina un dispositivo completo (USD ~80-120) y se reemplaza por
> 1 relé SSR + 1 solenoide integrados en el nodo Tier 3 (USD ~16 adicionales vs Tier 1-2).

---

## BOM — Gateway LoRaWAN + Conectividad (por sitio de campo)

> **Ratio:** 1 gateway cada 10 nodos (o 1 por lote físico, lo que sea mayor).
> El gateway se conecta por Ethernet a la opción de conectividad disponible.
> Todo el equipo de gateway + conectividad es propiedad de HydroVision AG (comodato).

| # | Componente | Modelo / Part# | Qty | COGS USD | Dónde comprar | Función | Notas |
|---|---|---|---|---|---|---|---|
| G1 | **Gateway LoRaWAN** | RAK7268 + antena omnidireccional 8 dBi | 1 | 250 | RAKwireless store / distribuidores | Recibe payloads LoRa de hasta 10 nodos y los reenvía al backend vía ChirpStack + Ethernet. Alcance práctico en viñedo: 2–5 km. | Antena externa 8 dBi en mástil a 3m mínimo. Fuente regulada 12V incluida. IP30 — requiere carcasa IP65 externa si se monta a la intemperie. |
| G2a | **Router 4G industrial** (opción A — donde hay cobertura celular) | Teltonika RUT241 | 1 | 155–190 | Teltonika distribuidores AR / MercadoLibre | Conecta el gateway a internet vía red celular 4G LTE. Volumen de datos ínfimo (~30–50 MB/mes para 10 nodos). | Industrial IP30, rango −40/+75°C. Failover automático. Gestión remota Teltonika RMS (gratuito hasta 25 dispositivos). Acepta cualquier operador argentino (Claro, Personal, Movistar). |
| G2a-SIM | **Chip SIM M2M** | SIM prepaga datos M2M (Claro IoT / Movistar M2M) | 1 | 3–5/mes | Operadores AR — plan IoT/M2M | Conectividad celular para el RUT241. 50 MB/mes es más que suficiente. | Plan M2M industrial es más barato y estable que prepago consumidor. USD ~36–60/año por gateway. |
| G2b | **Starlink Mini X** (opción B — donde NO hay cobertura 4G) | Starlink Mini X kit (antena + router WiFi) | 1 | ~215 | Starlink.com (al blue) | Conecta el gateway a internet vía satélite LEO. Para campos remotos sin cobertura celular (zonas de Mendoza, San Juan, Patagonia). | **Solo se ofrece en Tier 2-3** — el revenue de Tier 1 (USD 80/ha) no justifica el costo. El gateway se conecta al Starlink por Ethernet (puerto adaptador USB-C a Ethernet). Plan Mini: USD 27/mes (USD 324/año). |
| **TOTAL por sitio (4G)** | | | | **USD ~440–470** (gateway + router + SIM año 1) | | Opción default — mayoría de campos. | Año 2+: solo chip M2M ~USD 50/año. |
| **TOTAL por sitio (Starlink)** | | | | **USD ~465 + USD 324/año** (gateway + Starlink + plan año 1) | | Opción para campos sin 4G. | Año 2+: plan Starlink USD 324/año. |

---

## Notas de diseño

- **Extensómetro: strain gauge + ADS1231 SPI** — decidido. Ver fila 4.
- **MLX90640: usar versión 110°×75° FOV** (no la de 55°×35°).
  Cálculo a H=6m sobre canopia: cobertura = 17m × 9.2m → ~60 plantas Malbec
  (espaciado 1m entre plantas × 3.0m entre hileras en viñedo Colonia Caroya). Cumple "50+ plantas/sesión".
  Montar en poste de 7m total (3m mástil + 4m extensión), orientado al norte, inclinado 15°
  hacia el interior de la hilera para minimizar reflexión de suelo.
- Consumo en deep sleep < 100 µA objetivo → considerar corte de alimentación a periféricos
- La cámara LWIR consume ~700 mW activa → calcular duty cycle vs. batería/panel

## Decisiones tomadas

### Formato y frecuencia del payload MQTT

**Frecuencia:** cada 15 minutos (SLEEP_INTERVAL_SEC = 900).
- Justificación: la dinámica del CWSI en vid tiene constante de tiempo > 30 min.
  15 min captura el gradiente térmico del mediodía solar (pico de estrés) sin agotar batería.
- Durante lluvia (pluviómetro activo): wakeup por interrupción GPIO adicional para actualizar
  Tc_wet inmediatamente.

**Topic MQTT:**
```
hydrovision/{node_id}/telemetry      → datos de campo (cada 15 min)
hydrovision/{node_id}/status         → heartbeat + batería (cada 1 h)
hydrovision/{node_id}/alert          → alertas urgentes (HSI > umbral configurable)
```

**Payload JSON — topic telemetry:**
```json
{
  "v": 1,
  "node_id": "HV-A4CF12B3E7",
  "ts": 1743980400,
  "cycle": 1024,
  "env": {
    "t_air": 28.3,
    "rh": 42.1,
    "wind_ms": 2.7,
    "rain_mm": 0.0
  },
  "thermal": {
    "tc_mean": 31.2,
    "tc_max": 34.8,
    "tc_wet": 26.1,
    "tc_dry": 38.5,
    "cwsi": 0.47,
    "valid_pixels": 28
  },
  "dendro": {
    "mds_mm": 0.112,
    "mds_norm": 0.224
  },
  "hsi": {
    "value": 0.313,
    "w_cwsi": 0.35,
    "w_mds": 0.65,
    "wind_override": false
  },
  "gps": { "lat": -31.2018, "lon": -64.0927 },
  "bat_pct": 82,
  "pm2_5": 14,
  "calidad_captura": "ok"
}
```
- `v`: versión del esquema (versionado para backward-compat en backend)
- `valid_pixels`: píxeles LWIR dentro de rango foliar válido (filtrar suelo/cielo)
- `wind_override`: `true` cuando viento ≥ 18 m/s (65 km/h) → w_cwsi=0, w_mds=1. Entre 4-18 m/s rampa gradual
- `pm2_5`: µg/m³ medido por PMS5003 en el ciclo
- `calidad_captura`: `"ok"` | `"lluvia"` | `"post_lluvia"` | `"fumigacion"` | `"post_fumigacion"`. El backend descarta automáticamente cualquier frame distinto de `"ok"` para el cálculo de HSI y para pares de calibración Sentinel-2.

### Altura de montaje del nodo

**Definido: 6 m sobre el canopeo** (poste total ~7 m).
- MLX90640 versión 110°×75° FOV a 6m cubre 17m×9.2m = ~60 plantas Malbec.
- Orientación: norte geográfico, inclinación 15° hacia interior de hilera.
- Montar la cámara apuntando al canopeo entre las 11:00 y 14:00 hs solar
  (ventana de mayor diferencial térmico CWSI).
- **BOM fila 3**: módulo breakout MLX90640 con sensor BAB (110° FOV) integrado — Adafruit 4407 o SparkFun SEN-14844.

### Nodos para el viñedo experimental (1/3 ha Malbec, Colonia Caroya)

**Dos contextos distintos — no hay contradicción:**

**Producto comercial (densidad Tier 1):** 1 nodo para todo el viñedo de 1/3 ha.
- Cobertura térmica: ~60 plantas/sesión (4.6% de muestra) es suficiente para calibrar Sentinel-2.
- Consistente con el argumento comercial "1 nodo/10 ha".

**Experimento TRL 4: 5 nodos** (1 por zona hídrica).
- El diseño experimental requiere medir CWSI y MDS en cada uno de los 5 tratamientos
  hídricos independientes (100% ETc → sin riego) para validar que el sistema detecta
  el gradiente de estrés inducido.
- Sin 1 nodo por zona, no se puede comparar HSI predicho vs. ψ_stem Scholander
  con tratamiento controlado como variable independiente.
- Los 5 nodos TRL 4 son las primeras 5 unidades del producto.

### Identificación única del nodo (Node ID)

**Definido: MAC Wi-Fi del ESP32, sin EEPROM adicional.**
- El ESP32 tiene MAC burned en eFuse por Espressif en fábrica. Es única globalmente.
- Formato: `HV-` + últimos 5 bytes de la MAC en hex mayúscula → `HV-A4CF12B3E7`
- Se deriva en boot con `esp_read_mac()`, se almacena en RTC_DATA_ATTR para no
  recalcular en cada ciclo.
- Sin colisión posible entre nodos. Sin proceso de programación adicional.
- El backend usa `node_id` como clave primaria en la tabla de nodos.

---

## Cumplimiento ANPCyT — Origen BID (Bienes de Capital)

**Regla aplicable — Bases y Condiciones Art. e):**
> Los bienes de capital deben ser **nuevos y de origen de países miembros del BID**.
> Límite: ≤ 30% del ANR (≤ USD 36.000 sobre USD 120.000 ANR).

**China NO es miembro del BID.** AliExpress y LCSC son proveedores chinos — facturas de esas fuentes no son válidas para rendir ante ANPCyT. Mouser, DigiKey y SparkFun (USA) sí son válidos. MercadoLibre Argentina también (origen nacional).

### Regla práctica para Lucas

> **Toda compra con fondos ANPCyT debe hacerse a través de Mouser, DigiKey, SparkFun, proveedores argentinos formales, o distribuidores europeos (UE).** Guardar factura con país de origen del proveedor explícito. No comprar en AliExpress/LCSC con fondos del proyecto.

### Tabla de cumplimiento por componente

| # | Componente | Proveedor en BOM original | BID? | Proveedor ANPCyT válido | Costo est. USD (Mouser/DigiKey) | Delta vs. BOM |
|---|---|---|---|---|---|---|
| 1 | ESP32-S3 DevKit (off-the-shelf) | AliExpress / MeLi | ❌ China (AliExpress) / ✓ AR (MeLi) | **MercadoLibre AR** "ESP32-S3 DevKit" · **DigiKey** ESP32-S3-DevKitC-1-N8 · **Mouser** 356-ESP32S3DEVKTC1N8 | USD 10–15 | +2–5 vs AliExpress |
| 2 | Módulo LoRa SX1276 | AliExpress E32-900T20D | ❌ China | **Mouser** módulo Ebyte vía dist. AR · o bare **SX1276** Mouser 579-SX1276IMLTRT + PCB propia | USD 8–14 | +3–7 |
| 3 | MLX90640 breakout integrado (Adafruit 4407) | Adafruit / SparkFun (USA) | ✓ USA | **Adafruit** adafruit.com/product/4407 · **SparkFun** SEN-14844 · **DigiKey** 1528-4407-ND. Incluye sensor MLX90640ESF-BAB + lente + PCB I2C. | USD 45–60 | +10–15 vs bare chip |
| 4 | ADS1231IPWR (ADC 24-bit) | LCSC C92560 | ❌ China | **Mouser** 595-ADS1231IPWR · **DigiKey** ADS1231IPWR-ND | USD 4–6 | +1–2 |
| 4 | DS18B20 waterproof | LCSC C105950 | ❌ China | **Mouser** 700-DS18B20 · **DigiKey** DS18B20-ND | USD 2–4 | +0,5–1 |
| 4 | Strain gauge 120Ω | AliExpress | ❌ China | **Omega Engineering** (USA) — dist. AR Dytran/Omega · o **HBM** (Alemania) dist. local | USD 15–30 | +5–15 |
| 4 | Abrazadera Al anodizado | Tornería local | ✓ AR | Tornería local AR — sin cambio | — | 0 |
| 5 | Anemómetro RS485 IP65 | AliExpress | ❌ China | **Davis Instruments** (USA) Anemometer 6410 · o **Lufft** (Alemania) dist. AR · o **MercadoLibre AR** buscar origen nacional | USD 40–80 | +20–45 |
| 6 | Pluviómetro báscula 0,2mm | AliExpress + MeLi | MeLi ✓ | **MercadoLibre AR** origen nacional — válido. Evitar AliExpress. | USD 15–25 | 0 (si MeLi) |
| 7 | SHT31-DIS-B | LCSC C97083 | ❌ China | **Mouser** 841-SHT31-DIS-B · **DigiKey** 1649-SHT31-DIS-B2.5KCT-ND | USD 3–5 | +1–2 |
| 7b | VEML7700 (piranómetro) | LCSC C387631 | ❌ China | **Mouser** 841-VEML7700CB-ND · **DigiKey** | USD 2–4 | +0,5–1 |
| 8 | GPS u-blox NEO-6M | AliExpress | ❌ China | **Mouser** módulo u-blox NEO-6M (dist. oficial) · **SparkFun** GPS-13722 | USD 12–20 | +4–8 |
| 9 | DS3231SN RTC | LCSC C9868 | ❌ China | **Mouser** 700-DS3231SN · **DigiKey** DS3231SN-ND | USD 3–6 | +1–2 |
| 10 | Panel solar 6V/6W | MeLi + AliExpress | MeLi ✓ | **MercadoLibre AR** — válido si proveedor argentino. Evitar AliExpress. | USD 14–22 | 0 (si MeLi) |
| 11 | DFR0559 MPPT / CN3791 | AliExpress | ❌ China | **DFR0559**: DFRobot tiene dist. USA (DigiKey FIT0628) · CN3791 bare: **Mouser** | USD 12–18 | +2–5 |
| 12 | LiFePO4 32650 6Ah | AliExpress | ❌ China | **BatterySpace** (USA) · **MercadoLibre AR** (verificar origen en ficha técnica) | USD 12–20 | +4–8 |
| 13 | MAX485ESA+ | LCSC C7705 | ❌ China | **Mouser** 700-MAX485ESA+T · **DigiKey** MAX485ESA+-ND | USD 1–2 | +0,5 |
| 13b | ICM-42688-P breakout | AliExpress | ❌ China | **SparkFun** DEV-19764 (USA) | USD 12–15 | +2–5 |
| 13b | Servo MG90S metal gear ×2 | AliExpress | ❌ China | **Hitec HS-65MG** (USA/Korea) dist. AR · o **Mouser** servos Futaba | USD 10–18 c/u | +5–10 c/u |
| 13c | Paneles Dry/Wet Ref | Ferretería + AliExpress (bomba) | Ferretería ✓ | Ferretería AR (aluminio, pintura) ✓ · Bomba: **Mouser** peristáltica 12V o similar | USD 18–28 | +3–8 |
| 13d | PMS5003 Plantower | LCSC + AliExpress | ❌ China | **Mouser** 992-PMS5003 · **DigiKey** | USD 15–22 | +3–8 |
| 13e | Murata MZB1001T02 | **Mouser** | ✓ USA | Ya correcto — Mouser único proveedor real. | USD 5–8 | 0 |
| 14 | Relé SSR 24VAC | AliExpress | ❌ China | **Mouser** Crydom SSR 24VAC · **Electrocomponentes AR** | USD 4–8 | +2–4 |
| 15 | Rain Bird solenoide 24VAC | Distribuidores AR | ✓ USA/AR | Sin cambio — distribuidores AR oficiales Rain Bird | USD 15–25 | 0 |
| 16 | ~~PCB custom~~ | **ELIMINADA para TRL4** — arquitectura modular con DevKit + breakouts | — | — | USD 0 | −20–35 (ahorro) |
| 17 | Carcasa IP67 Hammond 200×150×100mm + pasacables M16 | MeLi + Hammond dist. AR | ✓ AR / Canadá | **MercadoLibre AR** "caja estanca IP67 200x150" · **Hammond Mfg** dist. AR (Canadá ✓ BID) · AliExpress "IP67 enclosure 200x150x100" | USD 15–28 | 0–10 |
| G1 | Gateway RAK7268 | RAKwireless (HK) | ❌ | **RAK tiene distribuidores USA** (RAKwireless.com → order en USD, envío USA) — verificar certificado de origen | USD 260–300 | +10–50 |
| G2a | Router Teltonika RUT241 | Dist. AR | ✓ Lituania (UE) | Sin cambio | — | 0 |

### Estimación de delta de costo total (5 nodos + 1 gateway)

| Escenario | COGS/nodo | Total 5 nodos | Gateway | Total hardware |
|---|---|---|---|---|
| BOM TRL4 modular (DevKit + breakouts) | ~USD 149 | ~USD 745 | ~USD 440 | ~USD 1.185 |
| BOM BID-compliant (Mouser/DigiKey/Adafruit) | ~USD 180–215 | ~USD 900–1.075 | ~USD 480–510 | ~USD 1.380–1.585 |
| **Delta vs. fuentes económicas** | +USD 31–66 | **+USD 155–330** | +USD 40–70 | **+USD 195–400** |

El delta (~USD 195–400 sobre el total de hardware TRL 4) es absorbible dentro del presupuesto ANPCyT sin modificar hitos. El ítem "Bienes de Capital" en el presupuesto cubre este rango. **Nota:** la eliminación de la PCB custom (−$20-35/nodo) compensa parcialmente el mayor costo de los módulos breakout.

### ~~Componente crítico: PCB~~ — ELIMINADA para TRL4

**La PCB custom 4-layer se elimina en la arquitectura TRL4.** Todos los componentes se conectan al ESP32-S3 DevKit mediante módulos breakout estándar con cables I2C (Stemma QT/Qwiic) y SPI. Esto elimina 8-12 semanas de diseño KiCad + fabricación + ensamblado.

**Para TRL5+ producción (vol. 500+):** evaluar PCB custom 4-layer para reducir COGS ~$25-30/nodo. Proveedores BID-compliant: Eurocircuits (Bélgica, UE), PCB Argentina (Bs As), o JLCPCB (consultar con Matías Tregnaghi si el servicio de manufactura cuenta como "bien de capital importado").

### Checklist para Lucas al comprar

- [ ] ¿El proveedor es de un país miembro del BID? (USA, UE, Argentina, Chile, Brasil, etc.)
- [ ] ¿La factura tiene razón social y país del proveedor explícito?
- [ ] ¿El componente es nuevo (no usado/reacondicionado)?
- [ ] ¿El total de bienes de capital comprados con ANR está por debajo de USD 36.000?
- [ ] ¿Guardé la factura en la carpeta de rendición ANPCyT correspondiente al trimestre?


---

## Guía de compras — dónde conseguir cada componente

### Contexto Argentina — leer antes de comprar

**El problema:** Argentina tiene aranceles de importación ~35% + IVA 21% + percepción
AFIP 8% sobre electrónica importada. Mouser/DigiKey envían a Argentina con DHL/FedEx —
casi siempre quedan en aduana y salen más caros de lo esperado.

**Las tres estrategias que funcionan en 2025-2026:**

| Estrategia | Cuándo usarla | Costo adicional |
|---|---|---|
| **LCSC** (lcsc.com) + envío directo | Chips y módulos estándar — el 80% de la BOM | Envío desde China USD 8-15 para paquete 200g. Sin aduana si < USD 200 declarado por EMS. |
| **AliExpress** directo | Módulos, sensores, carcasas — lo que no está en LCSC | Envío gratis o USD 2-5. Latencia 25-45 días por Correo Argentino. Usar "Envío por AliExpress" — más rápido que Standard. |
| **MercadoLibre Argentina** | Componentes comunes cuando urgís o no querés esperar aduana | 2-3× precio internacional — pero disponible al día siguiente y sin riesgo de aduana. |
| **Mouser/DigiKey + reenvío** | Solo para lo que no conseguís en LCSC ni AliExpress (MLX90640, Murata piezo) | Usar transenvios.com o reenvio.us (casilla en Miami). Costo fijo ~USD 15-20 de flete + declarar como "electronic component sample" para minimizar retención. |
| **MercadoLibre Chile** (para Mendoza) | Componentes que llegan mucho más rápido cruzando la cordillera | Coordinar con contactos en Mendoza que reciben en Chile. |

**Regla práctica para TRL4 (arquitectura modular):** la mayoría de los componentes son módulos breakout off-the-shelf — buscar primero en AliExpress (más barato) y MercadoLibre (más rápido). Para módulos BID-compliant: Adafruit, SparkFun, DigiKey. Mouser solo para componentes de nicho (Murata piezo). **No se necesitan chips SMD sueltos** (se eliminó la PCB custom).

---

### Por componente

---

#### MCU — ESP32-S3 DevKit

**Lo que necesitás:** placa de desarrollo ESP32-S3 DevKit off-the-shelf con módulo WROOM-1-N4 integrado, USB-C, regulador, y pines header para conectar breakouts I2C/SPI. **No se usa PCB custom para TRL4** — el DevKit ES la placa base del nodo.

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **ESP32-S3 DevKit** (recomendado TRL4) | AliExpress | buscar "ESP32-S3-DevKitC-1 N4" o "ESP32-S3 DevKit N4" | USD 8-12 | Placa de desarrollo completa: regulador, USB-C, antena integrada, pines header. Firmware MicroPython. Deep sleep 8 µA. |
| ESP32-S3 DevKit | MercadoLibre AR | buscar "ESP32-S3 DevKit" | ARS 15.000-20.000 | Disponible local si urgís. Misma placa. |
| ESP32-S3 DevKit | DigiKey / Mouser | ESP32-S3-DevKitC-1-N8 | USD 10-15 | BID-compliant (USA). Versión N8 (8MB Flash) — compatible. |

**Nota:** firmware en MicroPython (no C/Arduino). Usa `machine.unique_id()` para derivar node_id. La arquitectura modular con DevKit + breakouts elimina la PCB custom para TRL4.

---

#### LoRa — SX1276 915 MHz

**Lo que necesitás:** módulo con SX1276, frecuencia 915 MHz, conector SMA o U.FL, regulador 3.3V integrado. El Ra-02 original es SX1278 (433 MHz) — **no sirve**. Buscar específicamente 915 MHz.

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **EBYTE E32-900T20D** (recomendado) | AliExpress / LCSC | buscar "E32-900T20D" | USD 5-8 | SX1276 interno, 915 MHz, 20 dBm, conector SMA, regulado 3.3V. EBYTE es fabricante establecido, no genérico. |
| Ra-01H (Hope RF, 915 MHz) | AliExpress | buscar "Ra-01H LoRa 915" | USD 4-6 | Alternativa. Verificar que diga "915" — Ra-01 sin H es 433 MHz. |
| TTGO LoRa32 (todo en uno) | MercadoLibre AR | buscar "TTGO LoRa32 915" | ARS 30.000-40.000 | ESP32 + LoRa en una placa. Útil para prototipo del gateway, no para el nodo de campo. |

**Nota driver:** `driver_lora.h` y `config.h` asumen biblioteca sandeepmistry/LoRa. Compatible con Ra-01H y EBYTE E32-900T20D.

---

#### MLX90640 breakout integrado — sensor térmico LWIR

**Crítico:** comprar módulo breakout con sensor versión **BAB** (110°×75° FOV) ya integrado con lente y PCB I2C. **Para TRL4 se usa el módulo breakout completo** — plug & play via I2C Stemma QT/Qwiic, sin diseño óptico ni soldadura del sensor TO39.

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **Adafruit MLX90640 breakout** (recomendado TRL4) | **Adafruit** (USA, BID ✓) | Product# 4407 / DigiKey 1528-4407-ND | USD 45-55 | Módulo completo: sensor BAB + lente 110° + level shifter I2C + agujeros M2.5. Conector Stemma QT. Pedir 7 unidades (5 + 2 spare). |
| SparkFun MLX90640 breakout | **SparkFun** (USA, BID ✓) | SEN-14844 | USD 48-55 | Similar al Adafruit. Conector Qwiic. Verificar que sea versión 110° FOV. |
| MLX90640 breakout clone | AliExpress | buscar "MLX90640 breakout I2C module" | USD 35-50 | Clones chinos del breakout. **Verificar que sea BAB (110°)** — muchos venden versión 55° sin especificar. No BID-compliant. |
| MLX90640ESF-BAB-000-SP bare chip | Mouser | Part# 951-MLX90640ESF-BAB-000-SP | USD 32-38 | **Solo para TRL5+ producción** con PCB custom. No usar bare chip en TRL4 — requiere diseño óptico y soldadura TO39. |

**Evitar para TRL4:** bare chip TO39 sin breakout. **Para vol. 500+:** evaluar bare chip a USD 18-22 con PCB custom de producción.

---

#### Extensómetro — ADS1231 + Strain gauge + DS18B20

El conjunto más difícil de la BOM. No existe como módulo integrado — hay que armarlo.

**ADS1231 (ADC 24-bit):**

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **ADS1231IPWR** (TSSOP-16) | **LCSC** | C92560 | USD 2,50 | Chip solo — necesita PCB con pull-ups y capacitores de desacoplo (ver datasheet TI). |
| ADS1231IPWR | Mouser | Part# 595-ADS1231IPWR | USD 3,80 | Misma opción, Mouser si LCSC no tiene stock. |

**Strain gauge (célula de carga / galga extensiométrica para tronco):**

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **Galga extensiométrica 120Ω full-bridge** | AliExpress | buscar "strain gauge 120ohm full bridge precision" | USD 2-5 | Elegir full-bridge (4 hilos) para mejor cancelación de temperatura. Resolución 1-2 µm con ADS1231 24-bit. |
| Abrazadera de aluminio anodizado | Tornería local (Córdoba/Mendoza) | — | USD 5-10 | Pieza mecanizada a medida para el diámetro del tronco. Cotizar en cualquier taller de aluminio. Diámetro interno ajustable 40-80mm para Malbec. |

**DS18B20 (corrección térmica):**

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| DS18B20 TO-92 | LCSC | C105950 | USD 0,40 | El chip original Maxim/Dallas. Algunos AliExpress venden clones con peor precisión. |
| DS18B20 waterproof (con cable 1m) | AliExpress | buscar "DS18B20 waterproof probe" | USD 1-2 | Recomendado para montaje en tronco — ya viene sellado. |

---

#### Anemómetro RS485 Modbus

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **Anemómetro RS485 Modbus 0-60m/s** (recomendado) | AliExpress | buscar "wind speed sensor RS485 modbus rtu" | USD 20-35 | Elegir vendedor con ≥ 200 ventas y ≥ 4.5 estrellas. Confirmar que incluye manual de registros Modbus — el registro 0x0000 es el estándar para velocidad pero algunos usan otro. Config.h tiene `RS485_REG_WIND 0x0000` — verificar con el datasheet del que comprés. |
| Mismo, con datalogger | AliExpress | buscar "RS485 anemometer 0-60ms ModbusRTU IP65" | USD 28-45 | Versión IP65 recomendada para campo. |

**Nota:** comprar 2 unidades — uno para cada zona de validación. El segundo sirve de spare ante rotura en campo.

---

#### Pluviómetro

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **Pluviómetro báscula 0.2mm/pulso** | AliExpress | buscar "rain gauge tipping bucket 0.2mm pulse" | USD 12-20 | El de báscula es el estándar meteorológico. Verificar que sea 0.2 mm/pulso (constante `PLUV_MM_PER_PULSE` en config.h). |
| Pluviómetro Davis compatible | MercadoLibre AR | buscar "pluviómetro báscula Davis" | ARS 40.000-60.000 | Más caro, mejor calidad, calibración conocida. Válido si conseguís precio razonable. |

---

#### SHT31 — temperatura y humedad

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **SHT31 breakout I2C** (recomendado TRL4) | AliExpress | buscar "SHT31 breakout I2C" | USD 2-5 | Breakout con pull-ups integrados — se conecta directamente al bus I2C del DevKit. Sin soldadura. |
| Adafruit SHT31-D breakout | Adafruit / MercadoLibre | buscar "SHT31 Adafruit" | USD 10-15 local | BID-compliant. Conector Stemma QT. |
| SHT31-DIS-B (chip solo) | LCSC | C97083 | USD 1,80 | **Solo para TRL5+ producción** con PCB custom. Requiere decoupling 100nF. |

**Firmware:** librería MicroPython `sht31` (I2C). No usar SHT40 sin cambiar la librería.

---

#### Piranómetro — BPW34 + ADC

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **BPW34** fotodiodo | LCSC | C259698 | USD 0,15 | El fotodiodo. Respuesta espectral 400-1100nm — cubre la radiación PAR necesaria para estimar Tc_dry. Requiere resistencia de carga (100kΩ) y etapa de amplificación simple (op-amp rail-to-rail, ej. MCP601). |
| BPW34 en breakout | AliExpress | buscar "BPW34 photodiode module" | USD 1-3 | Ya con resistencia de carga. Conectar salida a PIN_PYRANO_ADC (GPIO 1). |
| **Alternativa recomendada: VEML7700** | LCSC | C387631 | USD 1,20 | Sensor de iluminancia I2C, 16-bit. Rango hasta 120.000 lux (~1200 W/m²). Más preciso que BPW34 + ADC y sin etapa analógica. Si usás VEML7700, actualizar `driver_piranometro.h` para I2C en lugar de ADC. |

**Nota práctica:** el piranómetro BPW34 + ADC requiere calibración con sensor de referencia (Davis Vantage Pro2 o similar). Si no tenés referencia disponible para TRL 4, usar la opción fallback del doc-02: Tc_dry calculado a partir del panel Dry Ref + temperatura aire sin piranómetro.

---

#### GPS — u-blox NEO-6M

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **NEO-6M módulo con antena cerámica** | AliExpress | buscar "NEO-6M GPS module Arduino" | USD 5-8 | El más común. Incluye antena cerámica integrada — suficiente para uso al aire libre. |
| NEO-6M con antena externa | AliExpress | buscar "NEO-6M GPS external antenna" | USD 7-10 | Preferible si la carcasa IP65 atenúa la señal GPS. Antena externa con conector U.FL. |
| u-blox NEO-M9N (más moderno) | Mouser / LCSC | — | USD 15-20 | Más rápido en el fix inicial. No necesario para TRL 4 — el NEO-6M es suficiente dado que GPS solo se lee en el primer boot. |

**Nota firmware:** el GPS solo se usa en el primer boot para obtener posición (luego se persiste en RTC memory). El costo de energía y tiempo de fix no son críticos.

---

#### DS3231 RTC

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **DS3231SN** (chip SOIC-16) | LCSC | C9868 | USD 1,50 | Chip solo con precisión ±2ppm. |
| DS3231 módulo con CR2032 | AliExpress | buscar "DS3231 RTC module" | USD 1-2 | Módulo completo con batería. Suficiente para TRL 4. |
| DS3231 módulo | MercadoLibre AR | buscar "modulo RTC DS3231" | ARS 3.000-5.000 | Disponible local si urgís. |

---

#### Panel solar 6W + MPPT + Batería

**Panel solar:**

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| Panel 6V 6W policristalino | MercadoLibre AR | buscar "panel solar 6V 6W" | ARS 15.000-25.000 | Disponible local, evita importación. Verificar que sea 6V nominal (no 12V). |
| Panel 6V 6W | AliExpress | buscar "6V 6W solar panel polycrystalline" | USD 8-12 + envío | Misma opción si querés ahorrar. |

**MPPT + cargador:**

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **CN3791** (chip MPPT para LiPo) | LCSC | C5443 | USD 0,50 | Chip para diseñar circuito MPPT mínimo. Requiere inductor + capacitores. |
| Módulo MPPT TP4056 + CN3791 | AliExpress | buscar "MPPT solar charger 6V LiPo" | USD 3-6 | Módulo ya armado. Más fácil para TRL 4. |
| **DFRobot DFR0559** (Solar Power Manager) | DigiKey / AliExpress | buscar "DFR0559" | USD 10-15 | Módulo completo: MPPT + cargador + salida regulada 5V/3.3V. Ideal para TRL 4 — un solo componente maneja todo el sistema energético. Recomendado si no querés diseñar el circuito de potencia desde cero. |

**Batería:**

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **LiFePO4 3.2V 6Ah** (recomendado) | AliExpress | buscar "LiFePO4 32650 6Ah" o "LiFePO4 26650 5Ah" | USD 8-15 | Más estable a temperatura (campo exterior). Voltaje nominal 3.2V — compatible con CN3791 si se configura correctamente. Ciclos de vida 2000+ vs 500 de LiPo. |
| LiPo 3.7V 4Ah (alternativa) | AliExpress | buscar "LiPo 3.7V 4000mAh" | USD 8-12 | Más energía por peso, pero degrada más rápido con calor (campo en verano de Cuyo puede llegar a 50°C interior de carcasa). |

---

#### MAX485 — transceiver RS485

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **MAX485ESA+** (SOIC-8) | LCSC | C7705 | USD 0,25 | Chip Maxim original. Comprar en lote de 10 — pesan nada y el flete se amortiza. |
| Módulo MAX485 | AliExpress | buscar "MAX485 module TTL RS485" | USD 0,50-1 | Breakout ya armado. Para proto. |

---

#### ICM-42688-P — IMU + servos MG90S

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **SparkFun IMU Breakout ICM-42688-P** (recomendado) | SparkFun (DEV-19764) / AliExpress clon | buscar "ICM-42688-P breakout" | USD 15-20 SparkFun / USD 6-10 AliExpress | Para TRL 4 usar el breakout SparkFun — ya tiene pull-ups y decoupling. La librería del firmware (SparkFun ICM-42688-P) es para este breakout. |
| MG90S servo (×2) | AliExpress / MercadoLibre | buscar "MG90S servo metal gear" | USD 2-4 cada uno | Comprar metálicos (MG90S) — los plásticos (SG90) se deforman con temperatura. 2 unidades por nodo + 2 de repuesto para TRL 4. |

---

#### Murata MZB1001T02 — limpieza piezoeléctrica

**El más difícil de conseguir en Argentina.** No está en AliExpress. Solo distribuidores autorizados Murata.

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **Murata MZB1001T02** | **Mouser** | Part# 81-MZB1001T02 | USD 3,50 | Pedir junto con otras cosas de Mouser para amortizar el flete. Comprar 10 unidades. |
| MZB1001T02 | DigiKey | Part# 490-MZB1001T02-ND | USD 3,80 | Alternativa a Mouser si hay mejor precio. |
| Driver boost 20Vpp | LCSC | buscar "MT3608 boost module" o chip "MT3608L" | USD 0,10-0,80 | El MT3608 es un boost converter que puede generar 20V desde 3.7V para excitar el piezo. Pedir módulo ya armado para TRL 4. |

---

#### Sensor de partículas — PMS5003

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **PMS5003** (Plantower) | AliExpress | buscar "PMS5003 particulate sensor" | USD 12-18 | Pedir con cable conector — el PMS5003 tiene conector JST de 8 pines. Verificar que venga con el adaptador de pines para la placa de pruebas. |
| PMS5003 | LCSC | C2660761 | USD 10-14 | Mismo sensor, más barato si pedís junto con otros componentes. |
| Adafruit PMSA003I | Adafruit | Product# 4632 | USD 45 | Versión con I2C — no compatible con el driver_pms5003.h actual que usa UART. Solo si querés cambiar el driver. |

---

#### ~~PCB custom~~ — ELIMINADA para TRL4

**No se necesita PCB custom para TRL4.** La arquitectura modular usa ESP32-S3 DevKit como placa base + módulos breakout I2C/SPI conectados con cables Stemma QT/Qwiic y dupont. Los módulos se montan dentro de la carcasa Hammond con tornillos M2.5 o velcro industrial.

**Para TRL5+ producción (vol. 500+):** diseñar PCB custom 4-layer en KiCad. Proveedores: JLCPCB (USD 20-35/5u), Eurocircuits (BID-compliant, EUR 80-150/10u), PCB Argentina.

---

#### Carcasa IP67 — Hammond 200×150×100mm

**Dimensiones aumentadas** para alojar holgadamente el DevKit + módulos breakout + batería + cableado I2C/SPI. La carcasa anterior (150×100×70mm) era demasiado ajustada para la arquitectura modular TRL4.

| Opción | Dónde | Part / búsqueda | Precio aprox. | Notas |
|---|---|---|---|---|
| **Hammond 1554W / Gewiss GW44210** (recomendado) | MercadoLibre AR / Hammond dist. AR | buscar "caja estanca IP67 200x150" o "Hammond 1554W" | USD 15-25 / ARS 15.000-25.000 | ABS/PC IP67, 200×150×100mm. Más robusta que IP65. Pedir con membrana de ventilación (Gore-Tex) para condensación. Hammond es canadiense (BID ✓). |
| Caja IP67 genérica 200×150×100mm | AliExpress | buscar "IP67 enclosure ABS 200x150x100" | USD 8-15 | Similar calidad. No BID-compliant. |
| Pasacables IP67 M16 | LCSC / AliExpress | buscar "cable gland M16 IP67" | USD 0,50-1 c/u | Comprar 6-7 por carcasa (power, anemómetro RS485, extensómetro, pluviómetro, antena LoRa, I2C externo). |

---

### Orden de compra recomendado — lote TRL 4 (5 nodos) — Arquitectura modular

> **Nota:** la arquitectura TRL4 usa DevKit + módulos breakout. No se necesita PCB custom ni componentes SMD sueltos para soldar.

**Pedido 1 — Adafruit / SparkFun** (módulos breakout BID-compliant, via transenvios.com):
- MLX90640 breakout Adafruit 4407 ×7 (5 nodos + 2 spare — **verificar FOV 110° BAB**)
- SparkFun ICM-42688-P breakout ×7
- Murata MZB1001T02 ×15 (agregar desde Mouser al mismo pedido)

**Pedido 2 — AliExpress** (módulos y sensores):
- ESP32-S3 DevKit N4 ×7
- EBYTE E32-900T20D ×7 (LoRa 915 MHz)
- SHT31 breakout I2C ×7
- NEO-6M GPS módulo ×7
- DS3231 RTC módulo ×7
- MAX485 módulo RS485 ×7
- PMS5003 ×7
- ADS1231 módulo o chip ×10
- Anemómetro RS485 Modbus IP65 ×7
- Pluviómetro báscula 0.2mm ×7
- MG90S servo metálico ×15
- LiFePO4 32650 6Ah ×7
- Panel solar 6V 6W ×7
- DFR0559 Solar Power Manager ×7
- MT3608L boost módulo ×10
- DS18B20 waterproof ×10
- Strain gauge 120Ω full-bridge ×15
- Cables Stemma QT/Qwiic 100mm ×20 + dupont hembra-hembra ×50

**Pedido 3 — Local / MercadoLibre**:
- Carcasa Hammond IP67 200×150×100mm ×7 + pasacables M16 IP67 ×50
- Panel solar 6V 6W (si urgís)
- Abrazaderas de aluminio (tornería local)
- Pintura negro mate alta temp. + tubo PVC 110mm (ferretería industrial)

**Tiempo estimado de llegada:**
- Adafruit/Mouser via transenvios: 10-15 días total
- AliExpress: 25-45 días (Correo Argentino) / 10-15 días (AliExpress Standard)
- Local/MeLi: 1-3 días

**Presupuesto total estimado lote 5 nodos + spare:**
- Adafruit/Mouser: USD 350-420 + USD 25 flete
- AliExpress: USD 250-350
- Local/MeLi: USD 80-120
- **Total aproximado: USD 700-915 para 5 nodos con repuestos**

---

## Notas de mejoras de hardware pendientes (doc-02 sec. 4.6.3)

### HW-01 — Reducción de COGS del componente óptico

| Acción | Estado | Impacto en COGS |
|---|---|---|
| Contactar Melexis directo (sales@melexis.com) con forecast 500 u/año | Pendiente antes de TRL 5 | MLX90640: USD 30 → USD 18-22 |
| Panel PTFE + anodizado negro — fabricar internamente | Pendiente antes de lote TRL 5 | Panel ref.: USD 6 → USD 2 |
| Integrar alojamiento óptico en molde de carcasa principal | Pendiente en diseño PCB+carcasa | Carcasa óptica: USD 5 → USD 0 (amortizado a partir de unidad 51) |
| **Impacto total con escala** | | **+USD 47 → +USD 22 vs. MDS-solo** |

### HW-02 — Activación adaptativa del MLX90640

Implementar en el firmware MicroPython: función `ventana_solar_activa()` en el módulo de RTC.
Constantes en configuración: `MLX_VENTANA_SOLAR_INI=7`, `MLX_VENTANA_SOLAR_FIN=19`, `MLX_RAD_MIN_WM2=150`.

**Pendiente de Lucas:** integrar el llamado a `ventana_solar_activa()` en el ciclo principal del firmware MicroPython antes del bloque de captura MLX90640.

Impacto: consumo equivalente ~22 µA → ~14 µA. Autonomía sin solar: 13 meses → 17 meses.

### HW-03 — Footprint PCB dual-sensor (MLX90640 / MLX90641 / Heimann HMS-C11L)

| Tarea | Quién | Cuándo |
|---|---|---|
| Diseñar footprint TO39 con pads compatibles con los 3 sensores (superposición ~80%) | Lucas | Durante diseño PCB KiCad — no requiere revisión posterior si se hace desde el inicio |
| Agregar jumpers J1/J2 (0Ω 0402) para selección de ruta I2C | Lucas | Junto con footprint |
| Validar protocolo I2C del Heimann HMS-C11L contra datasheet | Lucas | Antes de usar en producción — MLX90641 ya validado por familia |
| Actualizar `driver_mlx90640.h` para usar `SENSOR_TERM_W/H/ADDR` de config.h en lugar de hardcoded 32/24/0x33 | Lucas | Sprint siguiente al diseño PCB |

Costo adicional de ingeniería: ~4 horas de diseño PCB. Costo de no hacerlo: nueva revisión de PCB ante escasez de componente.
