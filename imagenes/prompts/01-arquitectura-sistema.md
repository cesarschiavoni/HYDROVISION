## PROMPT PARA GENERACIÓN DE IMAGEN — Arquitectura End-to-End del Sistema HydroVision AG

---

### ESTILO VISUAL

Diagrama técnico profesional de arquitectura de sistema, estilo infografía de publicación científica o white paper de ingeniería. Fondo blanco limpio. Bloques rectangulares redondeados con bordes de colores diferenciados por capa (hardware verde, comunicación azul, backend púrpura, frontend naranja). Flechas direccionales gruesas indicando flujo de datos. Texto negro sans-serif legible. Iconografía técnica minimalista dentro de cada bloque. Sin efectos 3D, sin sombras exageradas, sin degradados innecesarios. Paleta profesional: verde oscuro, azul INTA, púrpura backend, naranja dashboard, gris neutro para textos secundarios.

---

### ESTRUCTURA DEL DIAGRAMA — Flujo de izquierda a derecha (o de abajo hacia arriba)

El diagrama muestra el recorrido completo de un dato desde el sensor físico en el viñedo hasta la decisión de riego en la pantalla del productor. Cinco capas claramente diferenciadas:

---

### CAPA 1 — NODO DE CAMPO (verde, lado izquierdo)

Un bloque grande verde con ícono de nodo IoT. Título: **"Nodo IoT LWIR v1"**. Subtítulo: "ESP32-S3 + MicroPython".

Dentro del bloque, 4 sub-bloques verticales representando los grupos de sensores:

**Sub-bloque 1 — Imagen térmica:**
- Ícono de cámara. "MLX90640 32×24 px"
- "Gimbal 6+1 posiciones (7 ángulos)"
- "→ CWSI = (Tc − T_LL) / (T_UL − T_LL)"

**Sub-bloque 2 — Dendrómetro:**
- Ícono de tronco con abrazadera. "Strain gauge 120Ω + ADS1231 24-bit"
- "→ MDS = D_max − D_min (µm)"

**Sub-bloque 3 — Meteo:**
- Íconos de viento, lluvia, sol. "Anemómetro RS485 · Pluviómetro · SHT31 · VEML7700"

**Sub-bloque 4 — Edge computing:**
- Ícono de CPU. "HSI = 0,35 × CWSI + 0,65 × MDS"
- "Rampa viento 4-18 m/s"
- "96 capturas/día (cada 15 min)"
- "Payload JSON v1"

**Debajo del bloque:** "×10 nodos (5 calibración + 5 producción)" con 10 íconos de nodo en fila: 5 verdes (calibración) + 5 azules (producción).

**Anotación lateral:** "Energía: Panel 6W + LiFePO4 6Ah → 120h sin sol"

---

### CAPA 2 — COMUNICACIÓN LoRaWAN (azul, centro-izquierda)

Una flecha ancha azul con ondas de radio sale del nodo hacia un bloque azul.

**Flecha:** "LoRaWAN 915 MHz — SF7, BW 125 kHz — 1-3 km campo abierto"

**Bloque Gateway:**
- Ícono de antena/torre. "Gateway RAK7268"
- "ChirpStack LoRaWAN Server"
- "Ethernet / 4G → Internet"

**Anotación:** "Sin SIM por nodo. Sin Wi-Fi. Sin internet en campo."

---

### CAPA 3 — BACKEND (púrpura, centro)

Un bloque grande púrpura. Título: **"Backend FastAPI"**. Subtítulo: "Docker Compose — PostgreSQL + Mosquitto MQTT + Redis".

Dentro, 4 sub-bloques:

**Sub-bloque 1 — Ingesta:**
- "MQTT Subscriber" ← flecha desde gateway
- "Topic: hydrovision/{node_id}/telemetry"
- "Validación + persistencia en PostgreSQL"

**Sub-bloque 2 — Modelo IA:**
- Ícono de red neuronal. "PINN MobileNetV3-Tiny INT8"
- "Entrenado con 800 frames etiquetados (ψ_stem Scholander)"
- "Inferencia en servidor (no en nodo)"

**Sub-bloque 3 — Fusión satelital:**
- Ícono de satélite. "Google Earth Engine"
- "Sentinel-2 (10m/px, 5 días) + SAOCOM SAR"
- "Downscaling: nodo calibra satélite → mapa de lote completo"

**Sub-bloque 4 — Motor de decisión:**
- "HSI ≥ 0,30 → Alerta: regar"
- "HSI < 0,20 → OK: no regar"
- "Lógica por zona, por cultivo, por fenología"

---

### CAPA 4 — FRONTEND / DASHBOARD (naranja, centro-derecha)

Un bloque naranja con ícono de pantalla/laptop. Título: **"Dashboard Web"**. Subtítulo: "Jinja2 + Alpine.js + Leaflet + Chart.js".

Dentro:

**Sub-bloque 1 — Mapa:**
- Miniatura de mapa Leaflet con puntos de nodos sobre polígono de viñedo.
- "Mapa CWSI/HSI interpolado sobre imagen satelital"

**Sub-bloque 2 — Gráficos:**
- Miniatura de gráfico temporal con dos líneas (CWSI rojo, MDS azul).
- "Histórico 30/90/365 días — umbral de riego visible"

**Sub-bloque 3 — Alertas:**
- Ícono de campana. "Notificaciones push: estrés, fumigación, sensor offline"

---

### CAPA 5 — ACTUACIÓN (verde oscuro, lado derecho)

Un bloque verde oscuro con ícono de grifo/solenoide. Título: **"Control de Riego"**.

**Tres sub-bloques verticales representando los Tiers:**

| Tier | Modo | Acción |
|------|------|--------|
| **Tier 1** | Monitoreo | Productor decide manualmente con datos del dashboard |
| **Tier 2** | Recomendación | Sistema sugiere "regar zona C — HSI 0,42" → productor confirma |
| **Tier 3** | Autónomo | Nodo abre solenoide Rain Bird directamente (GPIO → SSR → 24VAC) |

**Flecha de retorno** (línea punteada) desde Tier 3 de vuelta al nodo: "Feedback loop — el riego reduce HSI → el nodo detecta la mejora en el siguiente ciclo".

---

### ANOTACIONES GENERALES

**Esquina superior izquierda — recuadro de identificación:**
```
HydroVision AG — Arquitectura del Sistema v1
ANPCyT STARTUP 2025 TRL 3→4
Nodo → LoRaWAN → Backend → Dashboard → Riego
```

**Esquina inferior derecha — leyenda de colores:**
- Verde: Hardware / Campo
- Azul: Comunicación inalámbrica
- Púrpura: Backend / Procesamiento
- Naranja: Frontend / Usuario
- Verde oscuro: Actuación / Riego

**Pie del diagrama:**
"Latencia end-to-end: <30 segundos (captura → visualización). Sin dependencia de internet en campo (LoRaWAN privado). Sin intervención humana en ciclo normal."

---

### LO QUE NO DEBE INCLUIR

* No incluir nombres de personas ni roles del equipo
* No incluir precios ni costos
* No incluir código fuente
* No usar colores neón, efectos de brillo ni fondos oscuros
* No simplificar el flujo — mostrar las 5 capas completas
* No incluir logos de empresas comerciales (Adafruit, SparkFun, etc.)
