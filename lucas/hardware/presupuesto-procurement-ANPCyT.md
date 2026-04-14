# Presupuesto Hardware — ANPCyT TRL 4
## HydroVision AG — 10 Nodos (5 calibración + 5 producción) + 1 Gateway — Proveedores BID-Válidos

---

## Restricción ANPCyT obligatoria

> **Art. e) Bases y Condiciones:** Los bienes de capital deben ser **nuevos y de origen de países miembros del BID**.
> Límite: ≤ 30% del ANR = ≤ **USD 36.000** sobre USD 120.000 ANR.

**China NO es miembro del BID.** AliExpress, LCSC y JLCPCB son proveedores chinos — sus facturas **no son válidas** para rendir ante ANPCyT.

**Proveedores válidos:** Mouser (USA), DigiKey (USA), SparkFun (USA), distribuidores argentinos formales, proveedores de la UE.

---

## BOM Completo — 10 Nodos de Campo (5 calibración + 5 producción)

| # | Componente | Modelo / Part# | Qty | Proveedor BID-válido | USD unit | USD total |
|---|---|---|---|---|---|---|
| 1 | MCU ESP32-S3 DevKit | ESP32-S3 DevKit off-the-shelf (MicroPython) | 6 (+1 spare) | **DigiKey** ESP32-S3-DevKitC-1-N8 · **Mouser** 356-ESP32S3DEVKTC1N8 · **MercadoLibre AR** "ESP32-S3 DevKit" | 12 | 72 |
| 2 | Módulo LoRa 915 MHz | SX1276 915 MHz (EBYTE E32 vía dist. o bare SX1276) | 6 (+1 spare) | **Mouser** EBYTE vía dist. USA · o **DigiKey** Dorji DRF1278F | 10 | 60 |
| 3 | Cámara LWIR breakout | **MLX90640 breakout integrado** (Adafruit 4407 / SparkFun SEN-14844, sensor BAB 110° FOV) | 6 (+1 spare) | **Adafruit** adafruit.com/product/4407 · **DigiKey** 1528-4407-ND · **SparkFun** SEN-14844 (USA ✓ BID) | 55 | 330 |
| 3-alt | Cámara LWIR alternativa A | MLX90641BAB (16×12 px — si no hay stock del 90640) | — | **Mouser** 951-MLX90641BAB | 20 | — |
| 4a | ADC 24-bit extensómetro | ADS1231IPWR | 6 (+2 spare) | **Mouser** 595-ADS1231IPWR · **DigiKey** ADS1231IPWR-ND | 5 | 30 |
| 4b | Sensor temperatura tronco | DS18B20 waterproof cable | 6 (+2 spare) | **Mouser** 700-DS18B20 · **DigiKey** DS18B20-ND | 3 | 18 |
| 4c | Strain gauge full-bridge 120Ω | Strain gauge 120Ω full-bridge | 10 (+5 spare) | **Omega Engineering** (USA) dist. AR: omega.com/en-us · o **HBM** (Alemania) contacto: hbm.com | 20 | 200 |
| 4d | Abrazadera aluminio anodizado | Custom tornería — 30 cm tronco | 6 | **Tornería local AR** (Colonia Caroya / Córdoba) | 15 | 90 |
| 5 | Anemómetro RS485 IP65 | 0–60 m/s Modbus RTU | 12 (10 nodos + 2 spare) | **Davis Instruments** 6410 (USA) dist. AR · o **Lufft** (Alemania) dist. AR: lufft.com | 55 | 660 |
| 6 | Pluviómetro báscula | 0,2 mm/pulso IP65 | 6 (+1 spare) | **MercadoLibre AR** — buscar proveedor con factura A (origen nacional o europeo, verificar ficha técnica) · Alt: **Davis Instruments** 7852M | 20 | 120 |
| 7 | Sensor T/HR | SHT31-DIS-B (±0,3°C ±2% RH) | 6 (+2 spare) | **Mouser** 841-SHT31-DIS-B · **DigiKey** 1649-SHT31-DIS-B2.5KCT-ND | 4 | 24 |
| 7b | Piranómetro | VEML7700 I2C (preferido sobre BPW34) | 6 (+1 spare) | **Mouser** 841-VEML7700CB-ND · **DigiKey** | 3 | 18 |
| 8 | GPS | u-blox NEO-6M módulo | 6 (+1 spare) | **SparkFun** GPS-13722 (USA) · **Mouser** u-blox dist. oficial | 15 | 90 |
| 9 | RTC | DS3231SN + CR2032 | 6 (+2 spare) | **Mouser** 700-DS3231SN · **DigiKey** DS3231SN-ND | 5 | 30 |
| 10 | Panel solar | 6V / 6W policristalino | 6 (+1 spare) | **MercadoLibre AR** — verificar origen nacional o europeo en ficha técnica del vendedor | 18 | 108 |
| 11 | MPPT / cargador | DFR0559 (recomendado TRL 4) | 6 (+1 spare) | **DigiKey** FIT0628 (DFRobot vía DigiKey) | 15 | 90 |
| 12 | Batería | LiFePO4 32650 3,2V 6Ah | 6 (+1 spare) | **BatterySpace** (USA) — batteryspace.com · Alt: **MercadoLibre AR** verificar origen en ficha | 16 | 96 |
| 13 | MAX485 transceiver RS485 | MAX485ESA+ SOIC-8 | 20 (lote — pesan nada) | **Mouser** 700-MAX485ESA+T · **DigiKey** MAX485ESA+-ND | 1,50 | 30 |
| 13b | IMU | ICM-42688-P breakout | 6 (+1 spare) | **SparkFun** DEV-19764 (USA) | 13 | 78 |
| 13b | Servo gimbal pan | MG90S metal gear (pan) | 7 (+2 spare) | **Hitec HS-65MG** dist. AR (USA/Korea) · o **Futaba S3114** (Mouser) | 14 | 98 |
| 13b | Servo gimbal tilt | MG90S metal gear (tilt) | 7 (+2 spare) | **Hitec HS-65MG** · o **Futaba S3114** (Mouser) | 14 | 98 |
| 13c | Dry Ref — aluminio negro mate | Chapa Al + pintura Rust-Oleum negro mate alta temp | 6 | **Ferretería local AR** (aluminio anodizado + pintura) | 8 | 48 |
| 13c | Wet Ref — fieltro hidrofílico | Fieltro técnico + bomba peristáltica 6V | 6 | Fieltro: tlapalería AR · Bomba: **Mouser** peristáltica 6V (12V con regulador) | 18 | 108 |
| 13c | Reservorio 10L + tubing | Reservorio plástico + manguera silicona | 6 | **Ferretería / Hidráulica local AR** | 10 | 60 |
| 13d | Sensor partículas | PMS5003 Plantower con cable JST 8 pines | 6 (+1 spare) | **Mouser** 992-PMS5003 · **DigiKey** | 16 | 96 |
| 13e | Actuador piezoeléctrico | Murata MZB1001T02 | 10 (lote) | **Mouser** 81-MZB1001T02 ← único proveedor real | 7 | 70 |
| 13e | Boost converter | MT3608L (para driver piezo) | 10 (lote) | **Mouser** · **DigiKey** MT3608L | 1 | 10 |
| 14 | Relé SSR 24VAC | Crydom D2425 o equiv. 24VAC 2A | 10 (1 por nodo, todas las filas) | **Mouser** 280-D2425-ND · **DigiKey** · **Electrocomponentes AR** (dist. Crydom) | 7 | 35 |
| 15 | Solenoide Rain Bird 24VAC | Rain Bird 24VAC 1" | 10 (1 por fila, todas las filas) | **Distribuidores Rain Bird AR** — Red Rego, Tecniriego, etc. (producto USA) | 22 | 110 |
| 16 | ~~PCB custom~~ | **ELIMINADA para TRL4** — arquitectura modular DevKit + breakouts I2C/SPI | — | — | 0 | 0 |
| 17 | Carcasa IP67 Hammond | 200×150×100 mm + pasacables M16 IP67 | 6 (+1 spare) | **Hammond Manufacturing** dist. AR (Canadá ✓ BID) · o **MercadoLibre AR** (verificar origen, pedir factura A) | 22 | 132 |
| 18 | Sistema de montaje | Estaca inox 316 1,5m + bracket Al + conectores M12 IP67 | 10 | **Ferretería industrial AR** (acero inox local) + **Mouser/DigiKey** M12 IP67 | 40 | 400 |
| | **SUBTOTAL 10 NODOS** | | | | | **~USD 5.000** |

---

## Gateway LoRaWAN + Conectividad (1 sitio)

| # | Componente | Modelo | Qty | Proveedor BID-válido | USD unit | USD total |
|---|---|---|---|---|---|---|
| G1 | Gateway LoRaWAN | RAK7268 + antena 8 dBi | 1 | **RAKwireless store USA** (store.rakwireless.com — envío desde USA, verificar certificado de origen) · Alt: **Dragino LPS8N** dist. USA | 260 | 260 |
| G2a | Router 4G industrial | Teltonika RUT241 | 1 | **Dist. AR Teltonika** (Lituania — UE ✓) — teltonika-networks.com/distributors | 175 | 175 |
| G2a | SIM M2M | Claro IoT / Movistar M2M | 1 | **Operadores AR** — plan IoT/M2M (~USD 4/mes) | 48/año | 48 |
| | **SUBTOTAL GATEWAY (opción 4G)** | | | | | **~USD 483** |

---

## Resumen General

| Ítem | USD |
|---|---|
| 10 nodos completos (todos con relé SSR + solenoide, 1 por fila) | ~5.000 |
| Gateway + conectividad (año 1) | ~483 |
| **TOTAL hardware TRL 4** | **~USD 5.483** |
| Límite bienes de capital ANPCyT (30% ANR) | USD 36.000 |
| **Margen disponible** | **USD 30.517** |

El hardware TRL 4 (~USD 5.483 para 10 nodos) está muy por debajo del límite de USD 36.000. **Nota:** la eliminación de la PCB custom (−USD 120/nodo) compensa el mayor costo de los módulos breakout. Arquitectura modular TRL4 sin necesidad de diseño KiCad ni fabricación de PCB. Todos los nodos (filas 1–10) llevan SSR + solenoide Rain Bird (control automático de riego por fila).

---

## ~~Nota PCB~~ — ELIMINADA para TRL4

**La PCB custom 4-layer se elimina en la arquitectura TRL4.** Todos los componentes se conectan al ESP32-S3 DevKit mediante módulos breakout estándar con cables I2C (Stemma QT/Qwiic) y SPI. Esto elimina 8-12 semanas de diseño KiCad + fabricación + ensamblado, y evita el problema de compliance BID con JLCPCB.

**Para TRL5+ producción (vol. 500+):** evaluar PCB custom 4-layer. Proveedores BID-compliant: Eurocircuits (Bélgica, UE), PCB Argentina (Bs As).

---

## Checklist de compra (por cada ítem)

- [ ] ¿El proveedor está en un país miembro del BID? (USA, Argentina, UE, Brasil, Chile, etc.)
- [ ] ¿El componente es nuevo (no usado)?
- [ ] ¿La factura tiene razón social y país del proveedor explícito?
- [ ] ¿Se guardó la factura en la carpeta de rendición ANPCyT del trimestre correspondiente?
- [ ] ¿El total acumulado de bienes de capital con fondos ANR sigue por debajo de USD 36.000?

---

*Generado: Abril 2026 — HydroVision AG / Lucas Bergon (Hardware Lead)*
