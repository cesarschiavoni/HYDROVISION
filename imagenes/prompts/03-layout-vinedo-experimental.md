## PROMPT PARA GENERACIÓN DE IMAGEN — Layout Aéreo del Viñedo Experimental HydroVision AG

---

### ESTILO VISUAL

Vista aérea cenital (planta) del viñedo experimental, estilo diagrama técnico de publicación agronómica o mapa de ensayo de campo. Perspectiva perfectamente vertical (drone a 100m). Paleta de colores funcional: verde para vegetación, marrón para suelo, azul-a-rojo para gradiente hídrico, gris para filas buffer. Líneas de anotación finas y legibles. Fondo de suelo marrón claro con textura sutil de terreno semiárido. Sombras cortas consistentes con mediodía (sol cenital). Calidad de publicación científica. Sin personas ni vehículos.

---

### ESTRUCTURA DEL VIÑEDO

**Ubicación:** Colonia Caroya, Córdoba, Argentina, ~700 m s.n.m.
**Superficie:** 1/3 ha (~3.333 m²)
**Cultivo:** Vitis vinifera cv. Malbec, espaldera VSP

**Dimensiones:**
- **10 filas** paralelas corriendo **este-oeste**
- Cada fila: **136 metros** de largo
- **136 plantas por fila** (espaciado 1 m entre plantas)
- **3 metros entre filas** (pasillo para maquinaria)
- **Ancho total del bloque:** 10 filas × 3 m = ~30 m
- **Plantas totales:** 1.360 vides

Mostrar las 10 filas como bandas horizontales verdes (vegetación del canopeo) separadas por bandas marrón claro (pasillos de suelo desnudo). Las filas se numeran de norte a sur: Fila 1 (norte) a Fila 10 (sur).

---

### DISEÑO EXPERIMENTAL — 5 filas experimentales + 5 filas buffer intercalados

Cada fila experimental recibe un **único régimen hídrico** (la fila completa se riega igual). Las filas experimentales se intercalan con filas buffer a 100% ETc que evitan que el movimiento lateral de agua en el suelo contamine los tratamientos.

| Fila | Régimen | Tipo | Color | Nodo |
|------|---------|------|-------|------|
| **1** | 100% ETc | **Buffer** | Gris claro | — |
| **2** | 100% ETc | **Control** | **Azul intenso** | **Nodo 1** |
| **3** | 100% ETc | **Buffer** | Gris claro | — |
| **4** | 65% ETc | **Tratamiento** | **Celeste/verde** | **Nodo 2** |
| **5** | 100% ETc | **Buffer** | Gris claro | — |
| **6** | 40% ETc | **Tratamiento** | **Amarillo** | **Nodo 3** |
| **7** | 100% ETc | **Buffer** | Gris claro | — |
| **8** | 15% ETc | **Tratamiento** | **Naranja** | **Nodo 4** |
| **9** | 100% ETc | **Buffer** | Gris claro | — |
| **10** | 0% ETc (secano) | **Tratamiento** | **Rojo intenso** | **Nodo 5** |

- **Total plantas experimentales:** 5 filas × 136 = **680 vides**
- **Total plantas buffer:** 5 filas × 136 = **680 vides**
- Cada fila experimental se colorea uniformemente con su color de tratamiento (sin divisiones internas)
- Las filas buffer son gris claro uniforme, sin divisiones
- Etiqueta en filas buffer: "Buffer 100% ETc" en texto pequeño gris

---

### POSICIÓN DE LOS 5 NODOS

5 nodos marcados con **íconos circulares rojos** (Ø ~3 m en escala), uno por fila experimental. Cada nodo está posicionado:

- **En la línea de la hilera** (no en el pasillo), entre dos plantas consecutivas
- **En la planta central de la fila** (planta 68 de 136, ~68 m desde el extremo oeste)
- **Evitando las 5 plantas de cada extremo de la fila** (efecto borde por exposición diferencial)

Posiciones de los nodos (marcados como puntos rojos con etiqueta):

| Nodo | Fila | Régimen | Posición | Etiqueta |
|------|------|---------|----------|----------|
| N1 | 2 | 100% ETc (Control) | Planta 68 (centro) | "N1 — 100% ETc" |
| N2 | 4 | 65% ETc | Planta 68 (centro) | "N2 — 65% ETc" |
| N3 | 6 | 40% ETc | Planta 68 (centro) | "N3 — 40% ETc" |
| N4 | 8 | 15% ETc | Planta 68 (centro) | "N4 — 15% ETc" |
| N5 | 10 | 0% ETc (secano) | Planta 68 (centro) | "N5 — 0% ETc" |

Alrededor de cada nodo, mostrar un **círculo punteado** (~3 m de radio) representando el FOV del MLX90640 (cobertura de ~15-20 hojas por captura).

---

### SISTEMA DE RIEGO

**Líneas de riego por goteo:** una línea negra fina a lo largo de cada fila (debajo del canopeo). Visible en los pasillos como una línea delgada.

**Cabecera de riego (extremo oeste):**
- Un rectángulo gris oscuro representando el **cabezal de riego** con válvulas
- 5 líneas de color saliendo del cabezal, una por fila experimental, con el porcentaje de ETc anotado
- Etiqueta: "Controlador Rain Bird — 5 solenoides (1 por fila experimental)"

**Flujo del agua:** flechas desde el cabezal hacia cada fila experimental, con el caudal relativo indicado por el grosor de la flecha (100% ETc = flecha gruesa, 0% ETc = sin flecha / línea tachada con "×"). Las filas buffer reciben riego uniforme desde la misma cabecera.

---

### GATEWAY LoRaWAN

En una esquina del viñedo (preferiblemente **esquina noreste**, fuera del bloque de filas):

- Ícono de **torre/poste con antena** representando el gateway RAK7268
- Líneas punteadas azules radiando desde el gateway hacia cada uno de los 5 nodos
- Etiqueta: "Gateway RAK7268 — LoRaWAN 915 MHz"
- Anotación: "Alcance: 1-3 km campo abierto"

---

### ANOTACIONES Y LEYENDA

**Esquina superior izquierda — título:**
```
Diseño Experimental — Viñedo Malbec
Colonia Caroya, Córdoba, Argentina
1/3 ha · 10 filas × 136 plantas · 5 filas exp. + 5 buffer · 5 regímenes hídricos
HydroVision AG — TRL 4
```

**Esquina superior derecha — rosa de los vientos:**
- N arriba, S abajo, E derecha, O izquierda
- Anotación: "Filas E-O. Viento dominante: O→E"

**Esquina inferior izquierda — leyenda de colores:**
- Azul: 100% ETc (sin estrés)
- Celeste: 65% ETc (estrés leve)
- Amarillo: 40% ETc (estrés moderado)
- Naranja: 15% ETc (estrés severo)
- Rojo: 0% ETc (sin riego)
- Gris: Buffer 100% ETc
- Punto rojo: Nodo HydroVision

**Esquina inferior derecha — escala:**
- Barra de escala: "0 — 25 — 50 m"
- "Pasillo entre filas: 3 m (libre para maquinaria)"

**Cotas dimensionales:**
- Flecha horizontal sobre el bloque: "136 m"
- Flecha vertical: "~30 m (10 filas × 3 m)"
- Flecha entre dos filas: "3 m"
- Flecha entre dos plantas dentro de una fila: "1 m"

---

### CONTEXTO DEL PAISAJE

Alrededor del bloque de viñedo:
- **Norte:** camino de acceso de tierra (franja marrón, ~4 m de ancho)
- **Sur y Este:** más viñedo o campo abierto (marrón claro con textura)
- **Oeste:** cabecera de riego + acceso vehicular
- **Fondo lejano:** textura difusa de sierras chicas de Córdoba (ondulaciones suaves en marrón/verde tenue)

---

### LO QUE NO DEBE INCLUIR

* No incluir personas, vehículos ni animales
* No incluir edificaciones ni galpones (el viñedo experimental está aislado)
* No usar perspectiva 3D — la vista es estrictamente cenital (planta)
* No simplificar a menos de 10 filas ni alterar las proporciones
* No mostrar césped verde uniforme — es suelo semiárido, marrón claro
* No incluir logos ni marcas comerciales
* Las filas buffer NO tienen divisiones ni gradiente — son uniformes gris claro
* Las filas experimentales tampoco tienen divisiones internas — cada fila es un solo color uniforme correspondiente a su régimen hídrico
