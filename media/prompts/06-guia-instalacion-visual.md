## PROMPT PARA GENERACIÓN DE IMAGEN — Guía Visual de Instalación del Nodo paso a paso

---

### ESTILO VISUAL

Secuencia de 8 viñetas (paneles) numeradas, dispuestas en 2 filas × 4 columnas, estilo manual de instalación de producto industrial o instrucciones IKEA mejoradas con contexto agronómico. Cada viñeta es una ilustración técnica simplificada con perspectiva 3/4, líneas limpias, colores planos, y una anotación breve. Fondo blanco por viñeta con borde fino gris. Flechas de acción en naranja. Íconos de herramientas en azul. Checkmarks verdes para verificaciones. Cruces rojas para errores comunes. Sin personas completas — solo manos con guantes de trabajo cuando sea necesario para mostrar la acción.

---

### VIÑETA 1 — Seleccionar posición en la hilera

**Ilustración:** Vista aérea simplificada de un tramo de hilera de vid (3-4 troncos visibles con canopeo). Una marca circular roja entre dos troncos indica la posición del nodo.

**Anotaciones:**
- Flecha: "~50 cm del tronco a cada lado"
- Flecha al pasillo: "Pasillo libre 2,5-3 m → maquinaria"
- ✓ "EN la línea de la hilera, entre 2 plantas"
- ✗ "NO en el pasillo entre filas"

**Texto:** "Paso 1 — Elegir la planta central de la fila (planta ~68 de 136). Cada fila lleva un nodo: 5 en zona de calibración (F1-F5) + 5 en zona de producción (F6-F10). Evitar las 5 plantas de cada extremo de la fila (efecto borde)."

---

### VIÑETA 2 — Clavar la estaca

**Ilustración:** Estaca de acero inoxidable siendo clavada en el suelo con un mazo. Se ve el corte del terreno con 60 cm enterrados y la punta cónica. Un nivel de burbuja está apoyado contra la estaca.

**Anotaciones:**
- "Estaca acero inox. 316L, 3 m total"
- "60 cm enterrados → 2,4 m visibles"
- "Verificar verticalidad con nivel"
- ✓ "Vertical ±5°"
- ✗ "NO inclinar"

**Texto:** "Paso 2 — Clavar 60 cm en el suelo franco-limoso. Usar mazo con protector de goma en la cabeza para no dañar el acero. Verificar verticalidad."

---

### VIÑETA 3 — Montar carcasa y panel solar

**Ilustración:** Manos con guantes montando la carcasa gris (Hammond IP67) sobre la estaca con abrazaderas de acero. El panel solar ya está fijado arriba con bracket inclinado.

**Anotaciones:**
- "Carcasa a 2,0-2,2 m"
- "Panel solar a ~2,3 m"
- "Panel → NORTE (inclinación ~30°)"
- "Anemómetro en punta (2,4 m)"
- Flecha curvada indicando norte: "N ↑"

**Texto:** "Paso 3 — Fijar carcasa con 2 abrazaderas (pad de goma EPDM). Panel solar orientado al norte, inclinado 30°. Anemómetro en la punta, marca 'N' al norte magnético."

---

### VIÑETA 4 — Orientar cámara al ESTE (sotavento)

**Ilustración:** Vista superior (planta) de la estaca con la carcasa. Una flecha grande roja sale de la ventana HDPE de la carcasa apuntando hacia el ESTE. Las hileras de vid están dibujadas como líneas verdes E-O. Una flecha de viento azul viene del OESTE.

**Anotaciones:**
- "Cámara MLX90640 → ESTE"
- "Viento dominante → OESTE"
- "Las plantas = barrera natural"
- "Tubo colimador concéntrico con lente"
- Flecha: "Reduce enfriamiento convectivo ~60-70%"

**Texto:** "Paso 4 — CRÍTICO: la ventana HDPE y el tubo colimador apuntan al ESTE (sotavento del Zonda). Las plantas actúan como barrera natural del viento."

---

### VIÑETA 5 — Instalar shelter SHT31 y pluviómetro

**Ilustración:** Shelter tipo Gill (6 placas blancas apiladas) montado en brazo horizontal al lado NORTE de la estaca. Pluviómetro (embudo verde) en otro brazo.

**Anotaciones:**
- "Shelter → lado NORTE"
- "SHT31 en plato central (#3)"
- "Pluviómetro nivelado"
- "Sin obstrucciones arriba del embudo"
- ✓ "Blanco reflectante"
- ✗ "NO oscuro"

**Texto:** "Paso 5 — Shelter al norte (máximo flujo de aire). SHT31 en el plato central. Pluviómetro nivelado, embudo libre de obstrucciones. Verificar nivel de burbuja."

---

### VIÑETA 6 — Instalar extensómetro en tronco

**Ilustración:** Close-up del tronco de vid con la abrazadera de aluminio a 30 cm del suelo, cara NORTE. Se ve el strain gauge pegado, el DS18B20 al lado, y el cable blindado subiendo por el tronco.

**Anotaciones:**
- "30 cm sobre suelo"
- "Cara NORTE del tronco"
- "Abrazadera firme pero sin comprimir corteza"
- "DS18B20 para corrección térmica"
- "Cable blindado 3 m → conector M12 'MDS'"
- ✗ "NO apretar demasiado — mide presión, no tronco"

**Texto:** "Paso 6 — Abrazadera a 30 cm del suelo, cara norte. Ajustar firme sin comprimir la corteza. El DS18B20 debe tener contacto térmico con la abrazadera (epoxi)."

---

### VIÑETA 7 — Colocar termopar en hoja

**Ilustración:** Close-up de una hoja de Malbec (lobulada, verde oscuro). El envés (cara inferior) visible, con el clip mini-pinza sujetando el hilo del termopar de 0,1 mm. El hilo es casi invisible.

**Anotaciones:**
- "Envés de la hoja (cara inferior)"
- "Hilo termopar Ø0,1 mm (<0,01 g)"
- "Hoja madura, sana, lado ESTE"
- "No en periferia del canopeo"
- "Dejar 30 cm de holgura en el cable"
- Flecha: "Cable trenzado → conector M12 'TC'"

**Texto:** "Paso 7 — Elegir hoja madura, sana, orientada al este, a la altura de la cámara (~1,5 m). Clip en el envés. El hilo pesa <0,01 g — no altera la temperatura natural de la hoja."

---

### VIÑETA 8 — Verificar con dashboard / primer boot

**Ilustración:** Pantalla de smartphone o laptop mostrando el dashboard web con un mapa (punto verde del nodo activo) y los primeros datos llegando (CWSI, MDS, HSI, batería, GPS). Un ícono de check verde grande.

**Anotaciones:**
- "Primer boot: GPS fix (timeout 2s)"
- "Verificar en dashboard:"
- "✓ GPS: lat/lon correctas"
- "✓ T_air: coherente con ambiente"
- "✓ Batería: >80%"
- "✓ ISO_nodo: >90%"
- "✓ LoRa: payload recibido en gateway"

**Texto:** "Paso 8 — Esperar primer ciclo (15 min). Verificar en el dashboard que todos los sensores reportan datos coherentes. Si ISO_nodo < 80%, revisar alineación del tubo colimador con la ventana HDPE."

---

### BARRA INFERIOR — Herramientas necesarias

Una tira horizontal debajo de las 8 viñetas, mostrando íconos de herramientas con etiquetas:

| Herramienta | Para qué |
|-------------|----------|
| Mazo con protector de goma | Clavar estaca |
| Nivel de burbuja | Verticalidad estaca + nivel pluviómetro |
| Llave Allen M4 | Ajustar abrazadera extensómetro |
| Destornillador Phillips | Tornillos carcasa IP67 |
| Brújula (o app celular) | Orientar panel solar al N, cámara al E |
| Bridas UV negras (×20) | Sujetar cables a estaca |
| Smartphone con dashboard | Verificar primer boot |

---

### ANOTACIONES GENERALES

**Esquina superior izquierda:**
```
HydroVision AG — Guía de Instalación Nodo v1
Tiempo estimado: 30-45 minutos por nodo
Requiere: 1 persona + herramientas listadas
```

**Esquina inferior derecha:**
"Mantenimiento mensual: verificar hoja del termopar (reemplazar si marchita), nivel de agua del reservorio (recargar si < 2L), ISO_nodo en dashboard (limpiar lente si < 80%)."

---

### LO QUE NO DEBE INCLUIR

* No incluir personas completas — solo manos con guantes cuando sea necesario
* No incluir texto extenso — cada viñeta tiene máximo 3 líneas + anotaciones
* No usar perspectivas inconsistentes entre viñetas — mantener 3/4 frontal
* No omitir los checkmarks y cruces — son la guía rápida de "bien vs. mal"
* No incluir precios ni referencias de compra
