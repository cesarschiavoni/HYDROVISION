# HydroVision AG — ANPCyT STARTUP 2025 TRL 3-4

Nodo IoT LWIR para monitoreo continuo de estrés hídrico en vid (Vitis vinifera cv. Malbec).
Convocatoria FONARSEC — Préstamo BID N° 5293/OC-AR. ANR USD 120.000 + contrapartida USD 30.000.

**🔴 Deadline presentación ANPCyT: 21/05/2026** (prórroga del cierre original 03/03/2026).
Inicio proyecto estimado: Octubre 2026 (~30 días hábiles desde firma del Convenio). Duración: 12 meses (dentro del límite de 18 meses del Art. 23 Bases). TRL 3 → 4.

SAS firmada 16/04/2026 (IPJ Córdoba, sede Colonia Caroya). Inscripción registral + CUIT AFIP en trámite.

**🔴 Requisitos críticos FAQ oficial (17/04/2026):**
- SAS debe estar **totalmente inscripta con CUIT activo** al postular (FAQ #12 — no se admite documentación provisoria).
- Todos los honorarios deben ser **facturados como monotributo/autónomo**, NO salarios (FAQ #9 — salarios no son elegibles ni contrapartida).
- **Garantía de cumplimiento = 10% del ANR = USD 12.000** (FAQ #13 — pagaré a la vista, aval bancario o seguro de caución).
- Contacto oficial consultas: **convocatoria.startup@agencia.gob.ar**

---

## Archivos autoritativos (jerarquía de verdad)

Cuando hay conflicto entre documentos, prevalece la fuente más específica:

| Dominio | Fuente autoritativa |
|---|---|
| Instrucciones ANPCyT | `anpcyt/instrucciones/Startup 2025 TRL 3-4.md` y `Bases y condiciones.md` |
| Presupuesto | `gestion/doc-05-presupuesto.md` |
| Hardware / BOM | `lucas/hardware/BOM-nodo-v1.md` |
| Protocolo agronómico | `ciencia/01-protocolo-scholander-formal.md` |
| Equipo y roles | `gestion/doc-03-equipo.md` |
| Sesiones Scholander | `ciencia/07-cronograma-preciso-sesiones.md` |
| Webapp (arquitectura, rutas, modelos) | `hydrovision-app/SPEC.md` |

### Documento principal ANPCyT

`anpcyt/doc-presentar/Plan-de-Trabajo-HydroVision-AG.md` (~1800 líneas, ~53K tokens)
→ Leer por secciones con offset/limit, NUNCA completo de una vez.

---

## Parámetros canónicos

- **Sesiones Scholander**: 4 sesiones OED (D-optimal), no 10
- **Hardware**: ESP32-S3 DevKit off-the-shelf + MicroPython + MLX90640 breakout 32×24 (Adafruit 4407)
- **Dataset**: 800 frames etiquetados con Ψstem (680 fine-tuning + 120 validación)
- **HSI**: 0.35×CWSI + 0.65×MDS
- **CWSI**: (T_canopy − T_LL) / (T_UL − T_LL)
- **LoRa**: 915 MHz ISM Argentina
- **Autonomía solar**: ~120 horas sin sol (sistema completo)
- **Viñedo experimental**: 10 filas — filas 1–5 calibración (5 regímenes hídricos) + filas 6–10 producción (100% ETc, nodos modo comercial)
- **Nodos**: 10 permanentes (5 calibración + 5 producción)

---

## Stack tecnológico

### Webapp (`hydrovision-app/`)
- **Backend**: FastAPI + SQLAlchemy + Pydantic v2
- **Frontend**: Jinja2 templates + Alpine.js 3.x + Tailwind CSS + Leaflet 1.9.4 + Chart.js 3.9.1 (pinned)
- **DB**: SQLite (desarrollo) / PostgreSQL 15 (producción)
- **Mensajería**: Mosquitto MQTT (paho-mqtt) → ChirpStack LoRaWAN
- **Infra**: Docker Compose (PostgreSQL + Mosquitto + ChirpStack + Redis + FastAPI)
- **Puerto dev**: 8096 (uvicorn)

### Módulo ML (`investigador/`)
- PyTorch + CUDA 12.1 (RTX 3070), timm, segmentation-models-pytorch
- Export edge: TFLite Micro INT8 / ONNX
- Tracking: Weights & Biases (wandb)

### Módulo satelital (`cesar/`)
- Google Earth Engine (earthengine-api), scikit-learn, scipy

---

## Cómo ejecutar

```bash
# Webapp (desarrollo con SQLite)
cd hydrovision-app
uvicorn app.main:app --port 8096 --reload

# Webapp (producción con Docker)
cd hydrovision-app
docker compose -f infra/docker-compose.yml up -d

# Tests webapp
cd hydrovision-app && pytest

# Tests módulo satelital
cd cesar && pytest

# ML — instalar GPU primero
cd investigador && install_gpu.bat   # luego: pip install -r requirements.txt
python verify_gpu.py                 # verificar CUDA
```

---

## Equipo

| Persona | Rol | Dedicación | USD |
|---|---|---|---|
| César Schiavoni | Project Leader / Dev IA + Backend | 12 meses | 18.000 |
| Lucas Bergon | COO / Hardware + Firmware | 12 meses | 15.000 |
| Dra. Monteoliva | Investigadora INTA-CONICET Art. 32 | ~180 h | 10.800 |
| Javier Schiavoni | Técnico de Campo | ~227 h, 9 meses | 9.000 |
| Inv. Art. 32 (a incorporar) | Validación estadística señales | ~177 h | 6.000 |
| Matías Tregnaghi | CFO / Contador | 12 meses | 6.000 |

---

## Estructura de carpetas

| Carpeta | Contenido | Responsable |
|---|---|---|
| `cesar/` | Código Python: pipelines satelitales, fusión CWSI, módulos backend | César |
| `lucas/` | Hardware: BOM, firmware MicroPython, documentación nodo | Lucas |
| `investigador/` | Modelo IA: simulador Scholander, entrenamiento PINN/U-Net, fusión edge | (a incorporar) |
| `hydrovision-app/` | Webapp completa: FastAPI backend + frontend Alpine.js/Leaflet | César |
| `ciencia/` | Documentos científicos: protocolo Scholander, outline paper, cronograma sesiones | Monteoliva |
| `anpcyt/` | Documentos para presentar a la agencia: Plan de Trabajo, cartas, anexos | César |
| `gestion/` | Documentos internos: presupuesto, equipo, Gantt, visión, patente INPI | César / Matías |
| `equipo/` | CVs y documentos del equipo (ignorado por .claudeignore) | — |
| `legal/` | Constitución SAS, pacto de socios | César / Matías |
| `matias/` | Borradores financieros, modelo SaaS (ignorado por .claudeignore) | Matías |
| `referencias/` | Papers y PDFs de referencia (ignorado por .claudeignore) | — |
| `mvc/` | **LEGACY — no usar.** Versión anterior monolítica de la webapp, reemplazada por `hydrovision-app/` | — |

---

## Reglas de trabajo

1. **Compliance ANPCyT**: todo cambio en el Plan de Trabajo debe verificarse contra `anpcyt/instrucciones/Startup 2025 TRL 3-4.md` y `Bases y condiciones.md`.
2. **No inventar datos**: los parámetros canónicos (arriba) son los únicos válidos. No cambiar cantidades de sesiones, resolución de sensores, fórmulas, etc., sin verificar la fuente autoritativa.
3. **Chart.js 3.9.1 pinned**: no actualizar. Se usa `responsive: false` + canvas dinámico por un bug conocido con Alpine `x-if`.
4. **Idioma**: toda la documentación y comentarios de código están en español.
5. **Archivos grandes**: leer con offset/limit. Aplica al Plan de Trabajo y a cualquier archivo >500 líneas.
6. **`mvc/` es legacy**: nunca editar ni referenciar. La webapp activa es `hydrovision-app/`.
7. **SPEC.md es autoritativo** para la webapp: rutas, modelos, config, y esquemas se documentan ahí.
