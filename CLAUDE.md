# HydroVision AG — ANPCyT STARTUP 2025 TRL 3-4

Nodo IoT LWIR para monitoreo continuo de estrés hídrico en vid (Vitis vinifera cv. Malbec).
Convocatoria FONARSEC — Préstamo BID N° 5293/OC-AR. ANR USD 120.000 + contrapartida USD 30.000.
Inicio estimado: Octubre 2026. Duración: 12 meses. TRL 3 → 4.

## Archivos autoritativos (jerarquía de verdad)

Cuando hay conflicto entre documentos, prevalece la fuente más específica:
- **Instrucciones ANPCyT**: `anpcyt/instrucciones/Startup 2025 TRL 3-4.md` y `Bases y condiciones.md`
- **Presupuesto**: `gestion/doc-05-presupuesto.md`
- **Hardware**: `lucas/hardware/BOM-nodo-v1.md`
- **Protocolo agronómico**: `ciencia/01-protocolo-scholander-formal.md`
- **Equipo y roles**: `gestion/doc-03-equipo.md`
- **Sesiones Scholander**: `ciencia/07-cronograma-preciso-sesiones.md`

## Documento principal ANPCyT

`anpcyt/doc-presentar/Plan-de-Trabajo-HydroVision-AG.md` (~1800 líneas, ~53K tokens)
→ Leer por secciones con offset/limit, NUNCA completo.

## Parámetros canónicos

- **Sesiones Scholander**: 4 sesiones OED (D-optimal), no 10
- **Hardware**: ESP32-S3 DevKit off-the-shelf + MicroPython + MLX90640 breakout 32×24 (Adafruit 4407)
- **Dataset**: 800 frames etiquetados con Ψstem (680 fine-tuning + 120 validación)
- **HSI**: 0.35×CWSI + 0.65×MDS
- **CWSI**: (T_canopy − T_LL) / (T_UL − T_LL)
- **LoRa**: 915 MHz ISM Argentina
- **Autonomía solar**: ~120 horas sin sol (sistema completo)

## Equipo

| Persona | Rol | Horas | USD |
|---|---|---|---|
| César Schiavoni | Project Leader / Dev IA + Backend | 12 meses | 18.000 |
| Lucas Bergon | COO / Hardware + Firmware | 12 meses | 15.000 |
| Dra. Monteoliva | Investigadora INTA-CONICET Art. 32 | ~180h | 10.800 |
| Javier Schiavoni | Técnico de Campo | ~208h, 9 meses | 9.000 |
| Inv. Art. 32 (a incorporar) | Validación estadística señales | ~177h | 6.000 |
| Matías Tregnaghi | CFO / Contador | 12 meses | 6.000 |

## Convenciones

- Los archivos en `cesar/` son código Python (backend, modelos, pipelines)
- Los archivos en `lucas/` son hardware (BOM, firmware, documentación)
- Los archivos en `investigador/` son modelo IA (simulador, entrenamiento, fusión)
- Los archivos en `gestion/` son documentos internos del proyecto
- Los archivos en `anpcyt/` son documentos para presentar a la agencia
