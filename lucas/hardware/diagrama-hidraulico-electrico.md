# Diagrama Hidráulico y Eléctrico — HydroVision AG TRL 4
## Sistema de riego diferencial — Viñedo Malbec Colonia Caroya

---

## 1. P&ID — Sistema hidráulico completo

```
                          MEDIDOR EPEC
                              |
                    [Q1: BIPOLAR 10A]          <- protección circuito 70m
                              |
                    ~~~~ 70m / 2×4mm² ~~~~     <- caída tensión: 2.0% @ 7.1A
                              |
                    [Q2: TERMOMAG 10A]         <- protección motor
                              |
          .-------------------+-------------------.
          |              TABLERO BOMBA             |
          |   [PS: PRESOSTATO 1.5-3.0 bar]        |
          |   [PI: MANÓMETRO GLICERINA]            |
          |   [EX: VASO EXPANSIÓN 2L]             |
          '-------------------+-------------------'
                              |
    CANAL ACEQUIA             |
         |                    |
    [ST: FILTRO MALLA 3/4"]  |
         |                    |
         +---[XV-F: Vf]---[P1: BOMBA 1HP]---[XV-R: Vr]---+
         |    COMP 1"          Pedrollo CP600              |
         |    LLENADO          60 L/min / 38m              |
         |    (modo fill)      220V monof.                 |
         |                                                 |
         |              [CV: CHECK 1"]                     |
         |                    |                            |
         |              TANQUE 20.000 L                    |
         |              polietileno                        |
         |              [LV: BOYA auto]                    |
         |              autonomía ~9hs riego               |
         |                    |                            |
         '--------------------'                            |
                                                           |
              HEADER PRINCIPAL PE 63mm PN6 / 136m <-------'
                              |
              P2 [REG PRESIÓN cabezal 2"] + [FI: FILTRO MALLA 2"]
                              |
          .----.----.----.----.----.----.----.----.----.----+
          |    |    |    |    |    |    |    |    |    |
         F1   F2   F3   F4   F5   F6   F7   F8   F9  F10
         0%  15%  40%  65% 100% 100% 100% 100% 100% 100%
        [SV1][SV2][SV3][SV4][SV5][SV6][SV7][SV8][SV9][SV10]
         |    |    |    |    |    |    |    |    |    |
        136m drip por fila — cinta 16mm 1.5L/h@1bar — 136 emisores/fila

     Zona CALIBRACIÓN (F1–F5): 5 regímenes hídricos (0%, 15%, 40%, 65%, 100% ETc)
     Zona PRODUCCIÓN (F6–F10): todas 100% ETc, nodos en modo comercial autónomo
     canal Rain Bird: 1=F1(0%,cerrado) 2=F2(15%) 3=F3(40%) 4=F4(65%) 5=F5(100%)
                      6=F6(100%) 7=F7(100%) 8=F8(100%) 9=F9(100%) 10=F10(100%)
```

---

## 2. Diagrama eléctrico

```
MEDIDOR EPEC (220V / 50Hz)
       |
       +----[Q1 BIPOLAR 10A]----+                 TABLERO RAIN BIRD
                                |                       |
                    ============= 70m 2×4mm² Cu ======  |  ===== 15m 2×1.5mm² =====
                                |                       |
                    [Q2 TERMOMAG 10A]         [TRAFO 24VAC 40VA]
                                |                       |
                    [PS PRESOSTATO]           [CTRL RAIN BIRD 10 ZONAS]
                     set: 1.5 bar ON                    |
                          3.0 bar OFF          canal 1  --+-- SV-F1  (0%, cerrado permanente)
                                |              canal 2  --+-- SV-F2  (15% ETc)
                    [MOTOR BOMBA 1HP]          canal 3  --+-- SV-F3  (40% ETc)
                     220V / 4.5A FLA          canal 4  --+-- SV-F4  (65% ETc)
                     cos φ ≈ 0.85             canal 5  --+-- SV-F5  (100% ETc, control calib.)
                     I arranque ≈ 25A (1s)    canal 6  --+-- SV-F6  (100% ETc, producción)
                     IP54 — exterior          canal 7  --+-- SV-F7  (100% ETc, producción)
                                              canal 8  --+-- SV-F8  (100% ETc, producción)
                                              canal 9  --+-- SV-F9  (100% ETc, producción)
                                              canal 10 --+-- SV-F10 (100% ETc, producción)
```

---

## 3. Especificaciones de diseño

### Hidráulica

| Parámetro | Valor | Fuente |
|-----------|-------|--------|
| Caudal por fila (136 emisores) | 3.4 L/min | 136 × 1.5 L/h ÷ 60 |
| Caudal producción permanente (5 filas F6–F10) | 17.0 L/min | 5 filas zona producción a 100% ETc |
| Caudal máximo simultáneo (9 filas) | 30.6 L/min | 9 filas activas (F1 = 0%, cerrada) |
| Presión de trabajo en header | 1.5–2.0 bar | presostato set point |
| Presión mínima extremo de fila | ≥ 0.8 bar | verificar con manómetro portátil |
| Pérdida de carga cinta drip 16mm / 136m | ~0.15 bar | cálculo Hazen-Williams |
| Tiempo llenado tanque 20.000 L | ~5.5 hs | 60 L/min bomba caudal libre |
| Autonomía tanque (solo producción 5 filas) | ~19.6 hs | 20.000 L ÷ 17.0 L/min |
| Autonomía tanque (máx 9 filas) | ~10.9 hs | 20.000 L ÷ 30.6 L/min |

### Eléctrica

| Parámetro | Valor | Notas |
|-----------|-------|-------|
| Tensión suministro | 220V / 50Hz | monofásico desde medidor EPEC |
| Longitud circuito | 70m | desde medidor hasta tablero bomba |
| Sección cable | 2×4mm² Cu IRAM | mínimo para caída ≤ 3% a 70m |
| Caída de tensión | 4.4V = 2.0% | @ 7.1A (FLA × 1.25) |
| Protección origen (medidor) | Bipolar 10A | Q1 |
| Protección destino (bomba) | Termomagnético 10A | Q2 |
| Corriente arranque motor | ~25A por ~1 segundo | Q1 y Q2 deben ser curva C o D |
| Tensión solenoides Rain Bird | 24VAC | transformador en tablero Rain Bird |
| Corriente por solenoide | ~250 mA | 1 solenoide por canal Rain Bird |

---

## 4. Secuencia de modos — lógica de operación

```
                    INICIO
                       |
               ¿turno de canal?
              /                \
            SI                  NO
             |                   |
        Abrir Vf             Abrir Vr
        Cerrar Vr            Cerrar Vf
        Encender bomba       Abrir Mi deseadas
             |               Rain Bird ejecuta
        Boya cierra sola         |
        al llegar a 20.000L  ¿tanque vacío?
             |              /            \
        Apagar bomba      NO             SI
        Cerrar Vf          |              |
                       continúa       esperar
                                    próximo turno
```

---

## 5. Lista de válvulas y etiquetado en campo

| Tag | Tipo | DN | Función | Ubicación |
|-----|------|----|---------|-----------|
| Vf | Compuerta bronce | 1" | Modo llenado canal→tanque | Tablero hidráulico |
| Vr | Compuerta bronce | 1" | Modo riego tanque→header | Tablero hidráulico |
| CV | Check antirretorno | 1" | Evita vaciado tanque al canal | Salida tanque |
| LV | Boya flotante | — | Control nivel tanque | Tanque interior |
| M1 | Esfera bronce | 1" | Habilita Fila 1 | Ramal F1 |
| M2 | Esfera bronce | 1" | Habilita Fila 2 | Ramal F2 |
| M3 | Esfera bronce | 1" | Habilita Fila 3 | Ramal F3 |
| M4 | Esfera bronce | 1" | Habilita Fila 4 | Ramal F4 |
| R1–R4 | Regulador caudal | 16mm | Caudal por fila | Aguas abajo Mi |
| SV-A..E | Solenoide Rain Bird 24VAC | 1" | Tratamiento hídrico zona | Inicio cada zona |
| P2 | Regulador presión | 2" | Limita presión header | Cabezal central |
| ST | Filtro malla inox | 3/4" | Protección bomba | Succión bomba |

---

## 6. Arquitectura de control — riego autonomo en nodo (Tier 3)

**Cambio arquitectonico:** El nodo decide localmente cuando regar. No espera ordenes
del servidor. El backend solo se entera del estado via el payload `/ingest`.

```
NODO ESP32-S3 (sensor + actuador Tier 3)
  Cada 15 min:
    1. Medir sensores → calcular HSI
    2. HSI >= 0.30 → GPIO PIN_SOLENOIDE → SSR rele ON
       HSI <  0.20 → GPIO PIN_SOLENOIDE → SSR rele OFF (histeresis)
    3. Protecciones: max 120 min, inhibir en lluvia, ventana horaria
    4. Reportar estado en payload:
       "solenoid": {canal, active, reason, ciclos_activo}
                        |
                   LoRa SX1276 915 MHz
                        |
                   GATEWAY RAK7268
                        |
                   BROKER MQTT (4G / Starlink Mini X)
                        |
SERVIDOR (FastAPI — app.py)
  POST /ingest
    ├── Telemetry INSERT (datos + estado solenoide)
    ├── IrrigationLog INSERT (si cambio de estado)
    └── _NODE_IRRIGATION[node_id] = sol.active
  POST /api/irrigate/{node_id}  ← override manual (emergencia/demo)
    └── [TRL 5+] MQTT → nodo → ejecuta y reporta en siguiente /ingest
```

**Eliminado:** El Controlador de Riego independiente (ESP32 + LoRa RX + 5 reles SSR)
ya no es necesario. El rele SSR se integra directamente en el nodo sensor (Tier 3).
Nodos Tier 1-2 (solo sensor) no tienen rele: `SOLENOIDE_CANAL = 0` en config.h.

### Responsabilidades por dispositivo

| Dispositivo | Responsabilidad | NO hace |
|-------------|----------------|---------|
| Nodo ESP32-S3 (Tier 3) | Mide sensores + decide y ejecuta riego autonomamente. Reporta estado via LoRa TX. | No espera ordenes del servidor para regar. |
| Nodo ESP32-S3 (Tier 1-2) | Solo mide sensores. Sin solenoide. | No controla riego. |
| Servidor FastAPI | Recibe telemetria, registra eventos de riego, muestra dashboard. Override manual de emergencia. | No decide cuando regar (en produccion). |
| Gateway RAK7268 | Bidireccional: sube telemetria y baja overrides manuales. | — |
| Solenoides Rain Bird | Abren/cierran el paso de agua al sector. | — |

### Mapeo nodo → canal Rain Bird → solenoide (campo Colonia Caroya)

| NodeConfig.node_id | NodeConfig.solenoid | Canal Rain Bird | Solenoide | Zona asignada |
|--------------------|--------------------|-----------------|-----------|---------------|
| HV-A4CF12B3 | 1 | canal 1 | SV-A | Bloque Norte |
| HV-B8A21F9C | 2 | canal 2 | SV-B | Centro-Norte |
| HV-C2D35E1A | 3 | canal 3 | SV-C | Centro-Sur |
| *(sin nodo)* | — | canal 4 | SV-D | Bloque Sur |
| *(sin nodo)* | — | canal 5 | SV-E | Bloque Este |

---

## 7. Notas de instalación críticas

1. **Cable eléctrico (riego)**: enterrar a mínimo 40cm en caño corrugado. No tender en superficie — riesgo de daño por maquinaria agrícola.
2. **Arranque motor**: los disyuntores Q1 y Q2 deben ser **curva C** (no curva B) para tolerar la corriente de arranque del motor (~25A por ~1s) sin disparar.
3. **Modo llenado y riego son mutuamente excluyentes**: nunca abrir Vf y Vr simultáneamente. Instalar cartel en tablero.
4. **Cinta drip envejecida**: la bomba está sobredimensionada (1HP en lugar de 3/4HP) para mantener presión adecuada con cintas de 2+ temporadas que tienen mayor pérdida de carga por incrustaciones.
5. **Purga mensual**: abrir tapón extremo de cada fila 30 segundos para eliminar sedimentos de la cinta.
6. **Solenoides**: cada fila tiene su propio solenoide en un canal Rain Bird independiente (10 canales total). Corriente por canal: ~250 mA — dentro del límite del transformador 40VA.
