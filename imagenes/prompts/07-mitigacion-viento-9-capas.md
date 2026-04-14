## PROMPT PARA GENERACIÓN DE IMAGEN — 9 Capas de Mitigación de Viento

---

### ESTILO VISUAL

Diagrama en cascada vertical (waterfall), estilo defensa en profundidad de ciberseguridad o diagrama de capas de protección industrial. Fondo blanco. Cada capa es una barra horizontal ancha con color propio, organizadas de arriba (capa más externa / física) a abajo (capa más interna / firmware). El error CWSI se muestra reduciéndose progresivamente de izquierda (alto) a derecha (bajo) a medida que se apilan las capas. Texto negro sans-serif, números en negrita. Paleta: verdes para capas físicas (hardware/instalación), azules para capas firmware, púrpura para la fusión HSI. Sin efectos 3D ni sombras.

---

### ESTRUCTURA PRINCIPAL — Cascada de 9 capas

**Título del diagrama:** "Mitigación de viento — 9 capas de defensa en profundidad"

**Subtítulo:** "Sin mitigación: CWSI confiable solo hasta 4 m/s (14 km/h). Con 9 capas + mitigaciones v2: confiable hasta 18 m/s (65 km/h). El CWSI pasa de ser útil el 20-40% a útil el 95-98% de los días de temporada."

---

### LADO IZQUIERDO — Barras de capas (cascada vertical)

9 barras horizontales apiladas verticalmente, cada una con:
- Número de capa (0-8)
- Nombre
- Tipo (etiqueta: "Física" en verde o "Firmware" en azul)
- Breve descripción
- Costo incremental
- Miniatura/ícono ilustrativo

**CAPAS FÍSICAS (verde):**

**Capa 0 — Orientación a sotavento** (verde claro)
- Ícono: vista aérea de hilera con flecha de viento y cámara en lado opuesto
- "Cámara al ESTE — las plantas son barrera natural"
- "Reduce velocidad del viento en zona medida ~60-70%"
- "Costo: USD 0 (instrucción de instalación)"
- **Error: ±0,08 → ±0,03**

**Capa 1 — Tubo colimador IR** (verde medio)
- Ícono: tubo PVC gris con interior negro y cámara detrás
- "PVC Ø110 × 250 mm, interior negro mate"
- "Bloquea flujo lateral de viento en el FOV"
- "Costo: USD 2-4"
- **Error por movimiento de hoja: ±0,04 → ±0,01**

**Capa 2 — Shelter anti-viento SHT31** (verde medio)
- Ícono: shelter Gill de 6 placas blancas con sensor en el centro
- "Shelter tipo Gill — convección natural sin flujo forzado"
- "Elimina error en T_air/RH/VPD por viento directo"
- "Costo: USD 0,50-2"
- **Error propagado al CWSI: ±0,05-0,10 → ±0,01**

**Capa 3 — Termopar foliar de contacto** (verde oscuro)
- Ícono: hoja con hilo fino pegado al envés
- "Tipo T, Ø0,1 mm — mide T_hoja por contacto, inmune al viento"
- "T_corr = T_IR + 0,6 × (T_tc − T_IR)"
- "Costo: USD 4-8"
- **Error por convección: ±0,08 → ±0,02**

**CAPAS FIRMWARE (azul):**

**Capa 4 — Compensación Tc_dry** (celeste)
- Ícono: gráfico con línea de Tc_dry ajustada
- "Corrige baseline superior inflado por viento"
- "delta *= (1 − wind/20)"
- "Costo: USD 0 (firmware)"
- **Efecto: elimina sesgo en denominador del CWSI**

**Capa 5 — Buffer térmico + filtro de calma** (azul claro)
- Ícono: 5 barras con la mediana resaltada
- "5 lecturas/ciclo → mediana de lecturas con viento < 2 m/s"
- "Descarta outliers por ráfagas"
- "Costo: USD 0 (firmware)"
- **Efecto: elimina ruido instantáneo**

**Capa 6 — Fusión HSI (65% MDS base)** (azul medio)
- Ícono: balanza con CWSI (35%) y MDS (65%)
- "MDS ya domina por diseño — error CWSI atenuado 65%"
- "Un error de +0,15 en CWSI impacta solo +0,053 en HSI"
- "Costo: USD 0 (firmware)"
- **Efecto: atenuación inherente del error CWSI**

**Capa 7 — Rampa gradual 4-18 m/s** (azul oscuro)
- Ícono: gráfico con dos líneas cruzándose (w_cwsi baja, w_mds sube)
- "Transición suave — nunca un salto abrupto"
- "4 m/s: 35% CWSI → 18 m/s: 0% CWSI"
- "Costo: USD 0 (firmware)"
- **Efecto: degradación controlada, no pérdida súbita**

**Capa 8 — Fallback CWSI inválido** (púrpura)
- Ícono: escudo con checkmark
- "CWSI = −1 (no calibrado, rango insuficiente) → HSI = 100% MDS"
- "Red de seguridad final"
- "Costo: USD 0 (firmware)"
- **Efecto: el sistema NUNCA produce un HSI sin sentido**

---

### LADO DERECHO — Gráfico de reducción de error

Un gráfico de barras horizontales alineado con las capas del lado izquierdo.

**Eje X:** Error CWSI (de 0,20 a 0,00)
**Eje Y:** Cada capa (alineada con la barra del lado izquierdo)

Las barras muestran el error RESIDUAL después de cada capa acumulada:
- Sin mitigación: █████████████████ **±0,18** (barra roja larga)
- +Capa 0: ████████████ **±0,12** (barra naranja)
- +Capa 1: ██████████ **±0,10**
- +Capa 2: ████████ **±0,08**
- +Capa 3: █████ **±0,05**
- +Capa 4: ████ **±0,04**
- +Capa 5: ███ **±0,035**
- +Capa 6: ██ **±0,025** (atenuado 65%)
- +Capa 7: █ **±0,015** (con rampa)
- +Capa 8: ▪ **<±0,01** (near NETD floor)

Una **línea vertical punteada verde** a ±0,07 marcando: "Umbral aceptable (Araújo-Paredes et al. 2022)"

Una **línea vertical punteada azul** a ±0,008 marcando: "Piso NETD del sensor (28 px promediados)"

---

### BARRA INFERIOR — Comparación antes/después

Una tira horizontal ancha dividida en dos mitades:

**Mitad izquierda (fondo rojo claro):** "SIN MITIGACIÓN"
- "CWSI confiable: 0-4 m/s (0-14 km/h)"
- "Días útiles en temporada: 20-40%"
- "Error a 8 m/s: ±0,15-0,18"
- Ícono: termómetro roto

**Mitad derecha (fondo verde claro):** "CON 9 CAPAS"
- "CWSI confiable: 0-18 m/s (0-65 km/h)"
- "Días útiles en temporada: 95-98%"
- "Error a 8 m/s: ±0,03-0,04"
- "Solo Zonda extremo (>18 m/s / 65 km/h, 2-5 días/temporada) fuerza backup total MDS"
- Ícono: termómetro con escudo

**Centro (entre ambas mitades):** Flecha grande "→" con "Costo incremental: USD 9/nodo (6,5% del COGS)"

---

### BARRA LATERAL — Tabla de velocidades de viento

En el margen derecho o inferior, una mini-tabla de referencia:

| m/s | km/h | Descripción | Estado CWSI |
|-----|------|-------------|-------------|
| 0-4 | 0-14 | Brisa suave | Normal — error ±0,02 |
| 8 | 29 | Viento moderado | Transición — w_cwsi 0,25 |
| 12 | 43 | Viento fuerte | Transición — w_cwsi 0,15 |
| 15 | 54 | Zonda moderado | MDS domina 92% — w_cwsi 0,08 |
| 18 | 65 | Zonda fuerte | Backup total MDS |
| >18 | >65 | Zonda extremo | Solo MDS |

---

### ANOTACIONES GENERALES

**Esquina superior izquierda:**
```
HydroVision AG — Mitigación de Viento
9 capas de defensa en profundidad
4 físicas (hardware/instalación) + 5 firmware
COGS incremental: USD 9/nodo
```

**Esquina inferior derecha:**
"Referencia: Araújo-Paredes et al. (2022) — error CWSI ±0,07 aceptable para riego de precisión. Las 9 capas logran ±0,03-0,04 a 8 m/s, dentro del umbral con margen. Fuente: doc-02-tecnico.md § 4.2.4."

---

### LO QUE NO DEBE INCLUIR

* No incluir las 14 mejoras v2 adicionales — solo las 9 capas base
* No representar las capas como un diagrama circular (onion diagram) — usar cascada vertical
* No omitir los costos — son parte del argumento (USD 9 total para todo)
* No simplificar la rampa a un switch binario
* No usar colores similares para capas físicas y firmware — diferenciar claramente
* No incluir fotos reales — solo íconos esquemáticos
