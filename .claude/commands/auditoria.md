Eres un equipo de especialistas auditando el proyecto HydroVision AG en `c:\Temp\Agro`. Cada especialista revisa su dominio, encuentra inconsistencias y las corrige directamente en los archivos. No reportes sin corregir — si encontrás un error y podés corregirlo, corregilo.

## Rol de cada especialista

**Especialista 1 — Agrónomo / Fisiólogo vegetal**
Verifica que todos los parámetros científicos sean internamente consistentes:
- CWSI = (T_canopy − T_LL) / (T_UL − T_LL) — fórmula idéntica en todos los archivos
- HSI = 0.35×CWSI + 0.65×MDS — pesos consistentes en todos lados
- Métricas TRL 4 (Gate Review): R²≥0.75 CWSI vs Ψstem · R²≥0.65 MDS vs Ψstem · R²≥0.80 HSI vs Ψstem · MAE≤0.08 CWSI (R²~0.90-0.95 es el valor esperado por literatura, pero 0.80 es el piso formal del Gate)
- Número de sesiones Scholander: 4 sesiones OED (no 10, no otro número)
- Número de plantas por sesión: 5 zonas × N plantas
- Dataset: ~800 frames etiquetados con Ψstem (no 680, no otro número)
- Cultivar experimental: Malbec, Colonia Caroya, 1/3 ha, 5 regímenes hídricos
- Dra. Monteoliva: Investigadora Adjunta INTA-CONICET, IFRGV-UDEA, CCT Córdoba

**Especialista 2 — Ingeniero electrónico / Hardware**
Verifica consistencia técnica del hardware:
- MCU: ESP32-S3 DevKit off-the-shelf + MicroPython (no ESP32, no ESP32-S2, no Raspberry Pi)
- Cámara: MLX90640 breakout integrado (Adafruit 4407, sensor BAB), 32×24 px, FOV 110°×75°, NETD ~100 mK
- ADC extensómetro: ADS1231 24-bit, resolución 1 µm
- LoRa: 915 MHz (banda ISM Argentina) — nunca 433 MHz
- Corrección térmica tronco: DS18B20, α = 2.5 µm/°C
- Autonomía solar: ~120 horas sin sol, panel 6W, batería LiFePO4 6Ah
- Ciclo: 96 capturas/día (cada 15 min)
- Error CWSI sistema completo: ±0.008 con 28 px foliares promediados
- Gateway: RAK7268, ChirpStack, LoRaWAN

**Especialista 3 — Economista / Controller financiero**
Verifica que todos los números financieros sean internamente consistentes:
- ANR total: USD 120.000 (80% del total de USD 150.000)
- Contrapartida privada: USD 30.000 (20%)
- Honorarios por persona — verificar que coincidan en TODOS los documentos:
  - César Schiavoni: USD 18.000 (USD 1.500/mes × 12)
  - Lucas Bergon: USD 15.000
  - Inv. Art. 32: USD 6.000 (USD 500/mes × 12, ~177 hs, ~USD 34/hr)
  - Dra. Monteoliva: USD 10.800
  - Matías Tregnaghi: USD 6.000
  - Javier Schiavoni: USD 9.000 (USD 1.000/mes × 9 meses)
- Suma de honorarios + otros ítems debe cerrar en USD 120.000 ANR
- Límite bienes de capital: ≤ 30% ANR = ≤ USD 36.000
- Tasa Inv. Art. 32: USD 6.000 / 177 hs = ~USD 34/hr (no USD 33, no USD 35)

**Especialista 4 — Abogado regulatorio / Compliance ANPCyT**
Verifica cumplimiento de las Bases y Condiciones (archivo autoritativo: `anpcyt/instrucciones/Startup 2025 TRL 3-4.md` y `anpcyt/instrucciones/Bases y condiciones.md`):
- Deadline presentación: 21 de mayo de 2026 (no otra fecha)
- Deadline incorporación investigador Art. 32: 16 de mayo de 2026
- Ambos investigadores Art. 32 deben tener afiliación institucional activa
- Bienes de capital: origen de países miembros del BID (China ❌)
- Convocatoria: STARTUP 2025 TRL 3-4 — ANPCyT/FONARSEC (Préstamo BID N° 5293/OC-AR)
- TRL de entrada mínimo: 3. TRL objetivo: 4.
- Todo lo que se afirme sobre reglas ANPCyT debe ser verificado contra los archivos de instrucciones — si hay contradicción, prevalece el archivo de instrucciones.

**Especialista 5 — Director de Proyecto / Auditor de coherencia entre documentos**
Verifica que todos los documentos sean mutuamente consistentes:
- Buscar cualquier referencia a "Alexis González", "Alexis", "CTO" como nombre propio de este proyecto — reemplazar por "el investigador Art. 32" o "Inv. Art. 32"
- Buscar referencias a "Raspberry Pi", "RPi4", "FLIR Lepton" — el hardware correcto es ESP32-S3 + MLX90640
- Verificar que la descripción del rol del investigador Art. 32 sea consistente: validación estadística de señales, NO desarrollo de PINN ni fusión satelital
- Verificar que el equipo listado en todos los documentos sea el mismo (mismas personas, mismos roles, mismas cifras)
- Verificar que las fechas de inicio (Octubre 2026) y duración (12 meses) sean consistentes
- Verificar que los hitos TRL 4 sean idénticos en Plan de Trabajo, Gantt, y documentos de gestión
- Verificar que el número de nodos sea consistente: 10 nodos en viñedo experimental (5 calibración filas 1–5 + 5 producción filas 6–10)
- Horas Inv. Art. 32: ~177 horas totales (no 155, no otro número)
- Horas Javier Schiavoni: ~227 horas totales
- Horas Monteoliva: ~180 horas totales (~15 hs/mes × 12 meses)

## Proceso de auditoría

Usar `mcp__sequential-thinking__sequentialthinking` para razonar paso a paso durante las fases de detección y corrección. Registrar cada discrepancia como un pensamiento, evaluar cuál es el valor correcto según la jerarquía de autoridad, y decidir la acción antes de editar. Esto evita correcciones apresuradas y deja un registro del razonamiento.

1. **Relevamiento**: Leer los archivos clave del proyecto usando Grep para encontrar todos los valores de cada parámetro auditado.

2. **Detección**: Identificar discrepancias entre archivos. Usar sequential thinking para razonar sobre cada discrepancia encontrada antes de corregir. Para cada discrepancia, determinar cuál es el valor correcto usando esta jerarquía de autoridad:
   - Fuente primaria / más específica > fuente general
   - `anpcyt/instrucciones/` > cualquier otro documento
   - `ciencia/01-protocolo-scholander-formal.md` > otros para parámetros agronómicos
   - `gestion/doc-05-presupuesto.md` > otros para cifras financieras
   - `lucas/hardware/BOM-nodo-v1.md` > otros para especificaciones de hardware

3. **Corrección**: Corregir directamente con Edit tool. Si no podés determinar cuál valor es correcto, reportarlo al final como "REQUIERE DECISIÓN HUMANA" con el contexto.

4. **Reporte final**: Al terminar, producir un informe estructurado:
   - ✅ Verificado sin cambios (con qué se verificó)
   - 🔧 Corregido (archivo, línea, valor anterior → valor nuevo)
   - ⚠️ Requiere decisión humana (descripción del conflicto y opciones)

## Archivos a auditar (en este orden de prioridad)

**Documentos ANPCyT — máxima prioridad:**
- `anpcyt/doc-presentar/Plan-de-Trabajo-HydroVision-AG.md`
- `anpcyt/instrucciones/tramite-online.md`

**Documentos de gestión:**
- `gestion/doc-03-equipo.md`
- `gestion/doc-04-plan-trabajo.md`
- `gestion/doc-05-presupuesto.md`
- `gestion/doc-09-protocolo-campo.md`
- `gestion/Tareas-Equipo-HydroVision-AG.md`
- `gestion/Gantt-HydroVision-AG.md`

**Documentos científicos:**
- `ciencia/01-protocolo-scholander-formal.md`
- `ciencia/06-outline-paper-cientifico.md`
- `ciencia/07-cronograma-preciso-sesiones.md`

**Hardware:**
- `lucas/hardware/BOM-nodo-v1.md`
- `lucas/documentacion/hardware-formulario-ANPCyT.md`

**Documentos de búsqueda de investigador:**
- `investigador/convocatoria-investigador-art32.md`
- `investigador/mail-gintea.md`

Comenzá la auditoría ahora. Trabajá sistemáticamente por dominio, un especialista a la vez.
