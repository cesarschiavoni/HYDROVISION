## PROMPT PARA GENERACIÓN DE IMAGEN — Diagrama Conceptual CWSI + Fusión HSI

---

### ESTILO VISUAL

Diagrama científico de dos paneles (Panel A arriba, Panel B abajo), estilo figura de paper en revista de riego o fisiología vegetal (Agricultural Water Management, Plant Physiology). Fondo blanco. Tipografía serif para ecuaciones, sans-serif para etiquetas. Colores saturados pero profesionales: escala térmica (azul-frío a rojo-caliente), verde para MDS, púrpura para HSI. Bordes finos negros en gráficos. Calidad vectorial, legible a tamaño A4. Sin efectos 3D ni sombras.

---

### PANEL A — Concepto del CWSI (mitad superior de la imagen)

**Título:** "A) Crop Water Stress Index — CWSI (Jackson et al., 1981)"

**Sub-panel A1 (izquierda) — Termograma falso color del canopeo:**

Una imagen falso color de 32×24 píxeles (grilla visible, pixelada intencionalmente) mostrando un canopeo de vid visto desde la cámara MLX90640. Escala de color tipo "inferno" o "jet":

- **Píxeles azul-celeste** (~26-28°C): zona del panel Wet Ref (esquina inferior izquierda, ~4 píxeles)
- **Píxeles verde-amarillo** (~30-33°C): hojas del canopeo (zona central, ~28 píxeles agrupados). Etiqueta: "T_canopy"
- **Píxeles rojo-naranja** (~36-40°C): suelo expuesto y panel Dry Ref (bordes y esquina inferior derecha)
- **Píxeles negro/gris** (descartados): cielo, alambres, zonas sin vegetación

**Barra de color vertical** al lado derecho del termograma: escala de 24°C (azul) a 42°C (rojo), con tres marcadores horizontales:
- **T_LL** (línea punteada azul): ~27°C — "Límite inferior (hoja bien hidratada / Wet Ref)"
- **T_canopy** (línea sólida verde): ~31°C — "Temperatura foliar medida"
- **T_UL** (línea punteada roja): ~38°C — "Límite superior (hoja sin transpiración / Dry Ref)"

**Fórmula grande debajo del termograma:**

```
CWSI = (T_canopy − T_LL) / (T_UL − T_LL)
```

Con valores numéricos substituidos:
```
CWSI = (31 − 27) / (38 − 27) = 4/11 = 0,36
```

**Sub-panel A2 (derecha) — Escala de estrés:**

Una barra vertical con gradiente azul-a-rojo mostrando la escala del CWSI de 0 a 1, con 5 bandas anotadas:

| CWSI | Color | Clasificación | Acción |
|------|-------|---------------|--------|
| 0,0-0,10 | Azul | Sin estrés | No regar |
| 0,10-0,30 | Verde | Estrés leve | Monitorear |
| 0,30-0,50 | Amarillo | **Estrés moderado** | **Considerar riego** |
| 0,50-0,70 | Naranja | Estrés severo | Regar urgente |
| 0,70-1,0 | Rojo | Estrés crítico | Riego de emergencia |

Un **puntero/flecha** marcando CWSI = 0,36 en la zona amarilla, con etiqueta: "Ejemplo: CWSI = 0,36 → estrés moderado".

**Sub-panel A3 (abajo del termograma) — Diagrama físico conceptual:**

Ilustración esquemática simplificada de tres hojas de vid vistas de perfil:

1. **Hoja izquierda** (azul, con gotas de agua): "Bien hidratada — estomas abiertos, transpiración máxima → T_hoja < T_aire → **CWSI ≈ 0**". Flechas azules saliendo de la hoja (transpiración). Termómetro marcando ~27°C.

2. **Hoja central** (amarillo): "Estrés moderado — estomas parcialmente cerrados → T_hoja ≈ T_aire → **CWSI ≈ 0,3-0,5**". Flechas más pequeñas. Termómetro ~31°C.

3. **Hoja derecha** (rojo, marchita): "Estrés severo — estomas cerrados, sin transpiración → T_hoja >> T_aire → **CWSI → 1**". Sin flechas. Termómetro ~38°C.

---

### PANEL B — Fusión HSI con rampa de viento (mitad inferior de la imagen)

**Título:** "B) Hydric Stress Index — HSI = w_cwsi × CWSI + w_mds × MDS"

**Sub-panel B1 (izquierda) — Gráfico temporal de 24 horas:**

Gráfico de líneas con eje X = hora del día (0:00 a 24:00) y dos ejes Y:

**Eje Y izquierdo** (rojo): CWSI (0 a 1)
- Línea roja que sube desde ~0,05 a las 6:00 (amanecer), pico ~0,55 a las 14:00 (máximo estrés solar), baja a ~0,20 al atardecer (18:00), luego "sin dato" (línea interrumpida) durante la noche
- **Zona sombreada gris** marcando noche (0:00-6:00 y 19:00-24:00) con etiqueta: "CWSI no disponible (sin radiación solar)"

**Eje Y derecho** (azul): MDS normalizado (0 a 1)
- Línea azul que muestra el patrón dendrómetrico típico: contracción matutina (diámetro baja → MDS sube) desde 8:00, mínimo de diámetro (= máximo MDS) a las 15:00, re-expansión vespertina/nocturna (MDS baja)
- La línea azul **continúa durante la noche** (señal activa 24/7)
- Etiqueta: "MDS opera 24/7 — inmune a nubes, viento, noche"

**Línea púrpura gruesa**: HSI = 0,35 × CWSI + 0,65 × MDS
- Sigue un patrón intermedio entre CWSI y MDS durante el día
- Durante la noche, se convierte en 100% MDS (ya que CWSI no está disponible)

**Línea horizontal punteada naranja** a HSI = 0,30: "Umbral de riego"

**Sub-panel B2 (derecha) — Diagrama de la rampa de viento:**

Gráfico con eje X = velocidad del viento (0 a 14 m/s) y eje Y = peso en HSI (0% a 100%).

Dos líneas que se cruzan:

- **Línea roja descendente** (w_cwsi): empieza en 35% para 0-4 m/s, baja linealmente hasta 0% a 12 m/s. Etiqueta: "Peso CWSI"
- **Línea azul ascendente** (w_mds): empieza en 65% para 0-4 m/s, sube linealmente hasta 100% a 12 m/s. Etiqueta: "Peso MDS"

**Tres zonas sombreadas:**
- 0-4 m/s: verde claro — "Normal (error CWSI ±0,02)"
- 4-18 m/s: amarillo — "Transición gradual"
- >18 m/s: rojo claro — "Backup total — solo MDS"

**Fórmula debajo:**
```
w_cwsi = max(0, 0.35 × (1 − (v − 4) / 14))    para v > 4 m/s
w_mds  = 1 − w_cwsi
HSI    = w_cwsi × CWSI + w_mds × MDS
```

**Anotación:** "No es un switch on/off — es una transición suave. El MDS ya domina al 65% en calma total. A ≥18 m/s (65 km/h, Zonda severo): HSI = 100% MDS."

**Sub-panel B3 (abajo, tira horizontal) — Comparación de señales complementarias:**

Tabla visual de 3 columnas mostrando cuándo cada señal es útil:

| Condición | CWSI (térmica) | MDS (dendrómetro) | HSI (fusión) |
|-----------|:-:|:-:|:-:|
| Día soleado, sin viento | ✓✓ Óptimo | ✓ Activo | ✓✓ Ambas señales |
| Día nublado | ✗ Sin gradiente | ✓ Activo | ✓ Solo MDS |
| Noche | ✗ Sin radiación | ✓ Activo | ✓ Solo MDS |
| Viento >12 m/s | ✗ Error alto | ✓ Inmune | ✓ Solo MDS |
| Fumigación (PM2.5 alto) | ✗ Lente contaminado | ✓ Activo | ✓ Solo MDS |
| Post-lluvia (hojas mojadas) | ✗ Artefacto IR | ✓ MDS ≈ 0 | ✓ Calibración auto |

**Conclusión visual:** "HSI tiene señal válida el **100% del tiempo** — ninguna condición lo invalida."

---

### ANOTACIONES GENERALES

**Esquina superior izquierda:**
```
HydroVision AG — Índices de Estrés Hídrico
CWSI: Jackson et al. (1981) · HSI: fusión propietaria
Sensor: MLX90640 32×24 px · Dendrómetro: ADS1231 24-bit
```

**Esquina inferior derecha:**
"Error CWSI sistema completo: ±0,008 (28 px foliares promediados, NETD 100 mK). R² esperado HSI vs. ψ_stem: ≥0,80 (TRL 4 gate)."

---

### LO QUE NO DEBE INCLUIR

* No incluir fotos reales — solo diagramas esquemáticos y gráficos
* No usar escala de grises — usar colores diferenciados para cada señal
* No simplificar la rampa de viento a un switch binario
* No omitir la noche del gráfico temporal — es clave que MDS opera 24/7
* No incluir código fuente ni pseudocódigo
* No usar terminología en inglés excepto CWSI, MDS, HSI (que son siglas estándar)
