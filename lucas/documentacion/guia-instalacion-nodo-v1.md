# GUIA DE INSTALACION -- Nodo HydroVision AG v1
## Prototipo TRL 4 -- Vinedo Experimental Colonia Caroya

> **Audiencia:** Javier Schiavoni (tecnico de campo) + Lucas Bergon (soporte HW)
> **Tiempo estimado:** ~45 min por nodo (primera vez) / ~20 min con experiencia
> **Herramientas necesarias:** llave Allen 4mm, destornillador Phillips, multimetro, bridas UV

---

## PARA JAVIER — CONFIGURACION DE RIEGO Y EDICIONES

**Responsabilidad de Javier:** configurar el riego de cada fila segun el % asignado y hacer
ajustes durante la temporada segun el nodo y el Scholander.

**Responsabilidad de Lucas:** instalacion fisica de los 5 nodos (estaca, carcasa, sensores,
conexiones, firmware). Lucas verifica que cada nodo envie datos al backend.

### Tu tarea: Configurar el riego por fila

Tienes 10 filas. Cada una recibe un % de agua diferente:

| Fila | % de riego | ¿Tiene nodo? | Tu acción |
|------|-----------|-------------|-----------|
| 1 | 100% | No | Riego normal |
| 2 | 100% | **Sí (Nodo 1)** | Riego normal — es la referencia |
| 3 | 100% | No | Riego normal |
| 4 | 75% | **Sí (Nodo 2)** | Riego al 75% de lo normal |
| 5 | 100% | No | Riego normal |
| 6 | 50% | **Sí (Nodo 3)** | Riego al 50% de lo normal |
| 7 | 100% | No | Riego normal |
| 8 | 25% | **Sí (Nodo 4)** | Riego al 25% de lo normal |
| 9 | 100% | No | Riego normal |
| 10 | 0% | **Sí (Nodo 5)** | **Sin riego** (secano total) |

### Como se configura el % de riego

**Equipo:** Controlador Rain Bird de 10 zonas + 1 solenoide por fila.

**Proceso:**

1. **Calcula el tiempo base (100%):**
   - Mide o anota cuánto tiempo necesita la fila 1 o 2 para recibir 3.5 L/planta/día
   - Ejemplo: si ETc = 3.5 L/planta y la cinta gotea 1.5 L/h → 3.5 / 1.5 = 2.3 horas
   - Convierte a minutos: 2.3 h × 60 = **140 minutos = tiempo base**

2. **Programa cada fila en el controlador Rain Bird:**
   - Fila 1: 140 min (100%)
   - Fila 2: 140 min (100%) — **Control, mira el nodo para verificar**
   - Fila 3: 140 min (100%)
   - Fila 4: 105 min (75% de 140)
   - Fila 5: 140 min (100%)
   - Fila 6: 70 min (50% de 140)
   - Fila 7: 140 min (100%)
   - Fila 8: 35 min (25% de 140)
   - Fila 9: 140 min (100%)
   - Fila 10: 0 min (0% — solenoide siempre cerrado)

3. **Ajusta semanalmente:**
   - El nodo calcula la ETc cada día con sus sensores
   - Cada semana (lunes o viernes), Lucas te dice: "esta semana ETc = X"
   - Recalcula el tiempo base con el X nuevo
   - Reprograma el controlador

### Proceso de edicion — ajustes durante la temporada

Cada 2 semanas, durante la sesión Scholander (si hay):

1. **Mide ψ_stem** con la bomba en 3-5 plantas de cada fila
2. **Observa el CWSI del nodo** en el dashboard (en tiempo real)
3. **Compara:** si Scholander dice "muy seco" pero el nodo no lo detecta → ajusta

**Ejemplos de ajuste:**
- Si Fila 4 (75%) está muy seca → baja al 60%
- Si Fila 8 (25%) está menos seca de lo esperado → prueba al 15%
- Si Fila 10 (0%) muestra que las plantas aguantan bien → prueba 5% agua de rescate

Anota todos los cambios en una planilla (fecha, fila, % anterior, % nuevo, razón).

---

---

## INSTALACION DE NODOS — A CARGO DE LUCAS

Las secciones siguientes (0-9) describen la instalacion fisica de los nodos.
**Responsable:** Lucas Bergon (hardware, firmware, verificacion de conectividad).
**Colaboradores:** Javier y Franco ayudan en logistica y verificacion de campo.

---

## 0. ANTES DE SALIR AL CAMPO

### Checklist pre-instalacion

- [ ] Nodo cargado (bat_v > 3.4V -- verificar con multimetro en bornes)
- [ ] Panel solar limpio y sin rayaduras
- [ ] Firmware actualizado (verificar version en Serial Monitor: `HV-FW vX.X`)
- [ ] Gateway RAK7268 encendido y conectado al Starlink
- [ ] Estaca de acero inox + bracket angular disponibles
- [ ] Abrazadera de extensometro + strain gauge montado (Lucas prepara en taller)
- [ ] Reservorio Wet Ref lleno con agua destilada (10L)
- [ ] Cable de extensometro (3m blindado, conector M12)
- [ ] 6 bridas UV (para sujecion de cables al poste)
- [ ] Llave Allen 4mm + destornillador Phillips

### Condiciones de instalacion

- **NO instalar con lluvia** -- la humedad puede danar conectores abiertos
- **Horario recomendado:** manana (antes de las 11hs) -- evitar sol directo sobre la carcasa abierta
- **Temperatura:** entre 5C y 35C (fuera de este rango, la bateria puede comportarse anormalmente)

---

## 1. POSICION DEL NODO EN EL VINEDO

### Estructura del vinedo experimental

El vinedo tiene **10 filas de 136m** (136 plantas por fila, espaciado 1m entre plantas, 3m entre filas).
Cada fila recibe un **unico regimen hidrico** (la fila completa se riega igual). Las filas de
tratamiento (75%, 50%, 25%, 0%) se intercalan con filas de control (100% ETc) que actuan como
**buffer hidrico** — evitan que el movimiento lateral de agua en el suelo entre filas contiguas
contamine los tratamientos.

### Mapa de filas — regimen hidrico y nodos

| Fila | Tratamiento | Tipo | Nodo | Posicion nodo |
|------|-------------|------|------|---------------|
| 1 | 100% ETc | Buffer | — | — |
| 2 | 100% ETc | **Control** | **Nodo 1** | Planta 68 (centro) |
| 3 | 100% ETc | Buffer | — | — |
| 4 | 75% ETc | **Tratamiento** | **Nodo 2** | Planta 68 (centro) |
| 5 | 100% ETc | Buffer | — | — |
| 6 | 50% ETc | **Tratamiento** | **Nodo 3** | Planta 68 (centro) |
| 7 | 100% ETc | Buffer | — | — |
| 8 | 25% ETc | **Tratamiento** | **Nodo 4** | Planta 68 (centro) |
| 9 | 100% ETc | Buffer | — | — |
| 10 | 0% (secano) | **Tratamiento** | **Nodo 5** | Planta 68 (centro) |

**Total: 5 nodos instalados.** Filas buffer (1, 3, 5, 7, 9) = sin nodo. Riego independiente por fila con solenoides Rain Bird.

### Regla de ubicacion del nodo dentro de la fila

Cada nodo se instala en la **planta central de la fila** (~planta 68 de 136), lado norte de la hilera.

**CRITICO:** Evitar las 5 plantas de cada extremo de la fila. En esos extremos:
- Hay efecto borde por exposicion diferencial al viento y la radiacion
- El pixel Sentinel-2 (10m) puede mezclar con la cabecera o el pasillo

### Por que 1 nodo por fila de tratamiento y no 1 nodo por planta

El objetivo del nodo NO es medir cada planta individualmente — es **caracterizar la respuesta
hidrica de cada regimen de riego**. Un nodo por nivel de tratamiento es suficiente porque:

1. **Representatividad espacial del sensor.** La camara termica MLX90640 (32x24 px) a 2m del
   canopeo cubre un area de ~3m x 2m con 28+ pixeles foliares. Eso promedia la temperatura
   de ~15-20 hojas de ~3-4 plantas vecinas. El CWSI resultante ya es un promedio espacial
   representativo de la zona, no de una sola hoja.

2. **Homogeneidad dentro de la fila.** Todas las plantas de una fila reciben exactamente el
   mismo riego (misma cinta de goteo, mismo solenoide, mismo tiempo). La variabilidad de
   estres hidrico **dentro** de una fila es baja (CV < 10-15% segun Santesteban et al. 2017).
   La variabilidad **entre** filas con distinto riego es alta (CV 30-50%). Un nodo captura
   la diferencia entre tratamientos, que es lo que importa para calibrar el sistema.

3. **Costo vs. informacion.** 1 nodo = USD 149 COGS. 136 nodos por fila x 10 filas = 1.360
   nodos = USD 202.640 solo en hardware. La informacion adicional de 1.359 nodos extra vs.
   5 nodos bien ubicados es marginal — el estres se comporta de forma uniforme dentro de
   cada regimen de riego.

4. **Validacion cruzada.** El protocolo Scholander (bomba de presion) mide 10 plantas/fila
   en cada sesion, distribuidas a lo largo de la fila. Eso permite verificar que el nodo
   central es representativo de toda la fila. Si el CV intra-fila supera 20% en alguna
   sesion, se investiga la causa (obstruccion de gotero, raiz enferma, etc.).

5. **Escalabilidad comercial.** En produccion (Tier 1), la densidad es 1 nodo/10 ha.
   El viñedo experimental ya esta sobre-densificado (5 nodos en 0.37 ha = 1 nodo/0.07 ha)
   para tener resolucion por tratamiento. Mas nodos no mejoran la calibracion del modelo.

### Configuracion del porcentaje de riego por fila

El porcentaje de riego se refiere al **% de la ETc** (evapotranspiracion del cultivo):
- ETc = ET₀ × Kc, donde ET₀ se calcula con datos meteorologicos del nodo (T_air, HR, viento,
  radiacion) y Kc es el coeficiente de cultivo por estadio fenologico (Malbec Kc = 0.3 a 0.7).
- 100% ETc = se repone toda el agua que la planta pierde por transpiracion.

**Como se implementa fisicamente:**

Cada fila tiene su propia **valvula solenoide Rain Bird 24VAC** controlada por un
**controlador Rain Bird de 10 zonas**. El porcentaje se configura ajustando el **tiempo de riego**:

| Fila | Tratamiento | Tiempo de riego | Ejemplo (si 100% = 60 min/dia) |
|------|-------------|-----------------|-------------------------------|
| 1, 2, 4, 5, 7, 9 | 100% ETc | T_100 = ETc / caudal_gotero | 60 min/dia |
| 3 | 75% ETc | T_100 × 0.75 | 45 min/dia |
| 6 | 50% ETc | T_100 × 0.50 | 30 min/dia |
| 8 | 25% ETc | T_100 × 0.25 | 15 min/dia |
| 10 | 0% (secano) | Solenoide cerrado permanente | 0 min/dia |

**Calculo del tiempo base T_100:**

La cinta de goteo tiene emisores cada 1m con caudal de 1.5 L/h. Cada planta recibe 1 emisor.
- Ejemplo: si ETc del dia = 3.5 L/planta, entonces T_100 = 3.5 / 1.5 = 2.3 horas = 140 min.
- Se programa en el controlador Rain Bird como 2 riegos de 70 min (manana y tarde).
- Para fila 3 (75%): 140 × 0.75 = 105 min (2 × 52 min).
- Para fila 6 (50%): 140 × 0.50 = 70 min (1 × 70 min).

**Con nodo Tier 3 (automatico):** el nodo calcula ETc en tiempo real a partir de sus propios
sensores meteorologicos y ajusta el tiempo de riego automaticamente via GPIO → rele SSR →
solenoide Rain Bird. El productor solo configura el % de ETc deseado en el dashboard y el
sistema calcula y aplica el tiempo de apertura del solenoide en cada ciclo de riego.

**Frecuencia de actualizacion:** el controlador Rain Bird se reprograma semanalmente segun
la ETc acumulada de la semana (dato del nodo control, fila 1). En los meses de maxima
demanda (diciembre-febrero), ETc puede variar de 4 a 7 L/planta/dia — el tiempo de riego
se ajusta proporcionalmente.

> **Nota:** la ETc es un calculo agronomico estandar. La estacion Davis Vantage Pro2
> (instrumento de referencia) valida el calculo de ET₀ del nodo durante el primer mes.
> Una vez validado, el nodo opera autonomamente.

---

## 2. INSTALACION DE LA ESTACA Y BRACKET

### Referencia rapida — Distribucion de componentes (de arriba a abajo)

| Altura | Componente | Orientacion / Cara | Notas |
|--------|-----------|-------------------|-------|
| 2.4 m (punta) | Anemometro RS485 | Marca "N" al norte magnetico | Libre de obstrucciones — mide viento real |
| 2.0-2.2 m | Carcasa IP65 + camara MLX90640 + tubo colimador | Panel solar → norte. Camara → **este** (sotavento) | Tubo concentrico con lente, interior negro mate |
| 1.8-2.0 m | Shelter SHT31 (6 placas blancas) | Lado **norte** del poste | No tapar con ramas — necesita flujo de aire natural |
| 1.8-2.0 m | Pluviometro | Horizontal, nivelado | Sin obstrucciones arriba |
| 1.5-1.8 m | Paneles Dry Ref / Wet Ref | Apuntando al **cielo** | Sin sombra del canopeo. Manguera al reservorio 10L |
| ~1.5 m (canopeo) | Termopar foliar | Mismo lado que camara (**este**) | Clip en enves de hoja sana, no periferia |
| 0.3 m (tronco) | Extensometro MDS | Cara **norte** del tronco | Abrazadera firme sin comprimir corteza |
| Suelo | Reservorio Wet Ref (10L) | Base del mastil | Agua destilada. Recarga mensual |

> Consultar diagrama lateral completo en `mitigacion-viento.md` seccion "Distribucion y montaje".

### Paso 2.1 -- Clavar la estaca

1. Posicionar la estaca de acero inox (3m) junto a la planta seleccionada, del lado **norte** de la hilera
2. Clavar 60cm en el suelo (quedan 2.4m sobre nivel del suelo)
3. Verificar verticalidad con nivel de burbuja (o a ojo -- que no incline mas de 5 grados)
4. La estaca debe estar a **30cm del tronco** (no tocar la planta)

### Paso 2.2 -- Montar el bracket angular

1. Fijar el bracket angular al extremo superior de la estaca con los 2 tornillos Allen M6
2. El bracket debe apuntar al **interior de la hilera** (hacia el canopeo, no hacia el pasillo)
3. Inclinacion: **15 grados hacia abajo** -- para que la camara apunte al canopeo, no al cielo
4. Apretar firmemente -- el nodo pesa ~600g y el viento puede moverlo

---

## 3. MONTAJE DEL NODO EN EL BRACKET

1. Colocar la carcasa IP65 en el bracket con los 4 tornillos de fijacion
2. Verificar que la **ventana del MLX90640 apunte hacia abajo** (al canopeo)
3. **CRITICO — Orientacion a sotavento:** la camara MLX90640 debe apuntar al lado
   **ESTE** de la hilera (sotavento del Zonda). El viento dominante en Cuyo viene
   del oeste (Zonda); al medir el lado opuesto, las propias plantas actuan como
   barrera natural, reduciendo ~60-70% el efecto de enfriamiento convectivo sobre
   las hojas medidas. En zonas donde el viento dominante NO es del oeste (consultar
   estacion meteo local), orientar la camara al lado opuesto a la direccion
   predominante del viento.
4. **Montar el tubo colimador IR** sobre la ventana del MLX90640:
   - Alinear el tubo PVC negro (110mm × 250mm) concentrico con el lente
   - Fijar al bracket con las 2 abrazaderas plasticas incluidas
   - Verificar que el interior esta limpio y sin obstrucciones
   - El tubo debe apuntar en la misma direccion que la camara (hacia abajo/canopeo)
5. Verificar que el **panel solar apunte hacia el norte** (en hemisferio sur = maxima radiacion)
6. Conectar el cable de alimentacion del panel solar al conector M12 marcado "SOLAR"
7. **NO encender todavia** -- primero instalar sensores externos

---

## 4. INSTALACION DEL EXTENSOMETRO DE TRONCO

> **Esta es la parte mas delicada.** La abrazadera viene pre-montada por Lucas en el taller.

### Paso 4.1 -- Seleccionar el punto del tronco

- Altura: **30cm del suelo**
- Cara: **norte** del tronco (recibe sol directo -- importante para el DS18B20)
- Diametro minimo del tronco: 3cm (Malbec adulto tipico: 5-8cm)

### Paso 4.2 -- Montar la abrazadera

1. Abrir la abrazadera de aluminio anodizado
2. Colocarla alrededor del tronco a 30cm del suelo, cara norte
3. Ajustar el tornillo de presion hasta que quede **firme pero sin comprimir la corteza**
   - Si se aprieta demasiado: el strain gauge mide la presion de la abrazadera, no la contraccion del tronco
   - Si queda flojo: se desliza con el viento y genera ruido en la senal
4. Verificar que el cable blindado del strain gauge sale limpio sin doblarse

### Paso 4.3 -- Conectar al nodo

1. Pasar el cable de 3m por la estaca (sujetar con 2 bridas UV cada metro)
2. Conectar el conector M12 al pasacables marcado "MDS" en la carcasa
3. **Verificar continuidad** con multimetro: medir resistencia entre pines 1-2 del conector -- debe dar ~120 ohm (resistencia del strain gauge). Si da infinito: cable cortado o conector suelto.

---

## 5. INSTALACION DE SENSORES EXTERNOS

### 5.1 Anemometro RS485

1. Montar en el **extremo superior de la estaca** (por encima de la carcasa del nodo)
2. Orientar la marca "N" del anemometro hacia el **norte magnetico**
3. Conectar cable RS485 (2 hilos + GND) al conector M12 marcado "WIND"
4. Sujetar cable con bridas UV

### 5.1b Shelter anti-viento SHT31

> El shelter protege el sensor de T_air y HR del viento directo y radiacion solar.
> Sin shelter, el error en T_air puede ser de +-0.5C, lo que propaga +-0.05 a +-0.10
> de error al CWSI via el calculo de VPD.

1. Verificar que el shelter tiene 6 placas blancas con separacion uniforme de 15mm
2. El SHT31 debe estar montado en el **plato central** (plato 3 contando desde arriba)
3. Montar el shelter en el poste a la **misma altura que la carcasa** del nodo
4. Posicionar del **lado norte** del poste (maximo flujo de aire natural)
5. Sujetar con 2 bridas UV a la estaca
6. Conectar el cable I2C del SHT31 al conector M12 marcado "ENV" en la carcasa
7. **Verificar** que las placas no estan obstruidas por hojas o ramas de la vid

### 5.2 Termopar foliar

> El termopar mide la temperatura de una hoja por contacto directo, inmune al viento.
> Se usa para corregir en tiempo real la lectura infrarroja de la camara MLX90640.

1. Seleccionar una **hoja representativa** del canopeo a la altura de la camara:
   - Hoja sana, madura, sin manchas ni dano mecanico
   - Orientada al **mismo lado que la camara** (este / sotavento)
   - No elegir hojas de la periferia del canopeo (mas expuestas al viento)
2. Fijar el **clip mini-pinza** al **enves** de la hoja (cara inferior):
   - El enves tiene menor exposicion solar directa → menor artefacto por radiacion
   - El clip debe sujetar sin comprimir excesivamente (no cortar la circulacion de la hoja)
   - El hilo del termopar (0.1mm) debe quedar en contacto con el tejido foliar
3. Pasar el cable trenzado del termopar (2m) por la estaca hacia la carcasa
4. Conectar al conector M12 marcado "TC" en la carcasa
5. Sujetar cable con 2 bridas UV (dejar holgura para movimiento del canopeo)
6. **Mantenimiento mensual:** verificar que la hoja sigue viva y sana. Si se marchito o
   se desprendio, reemplazar por otra hoja representativa y recolocar el clip.

### 5.2b Calibracion del factor de correccion TC_BLEND_K

> El factor `TC_BLEND_K` (default 0.6) determina cuanto corrige el termopar a la lectura IR.
> Formula: `T_corr = T_IR + k × (T_termopar - T_IR)`. El default funciona bien para Malbec
> en Cuyo. Solo es necesario recalibrar si se cambia de varietal o se poda drasticamente.

**Materiales:** Bomba Scholander + camara de presion, nodo operativo con termopar instalado.

**Cuando hacerlo:** durante una sesion Scholander programada, en un dia con **viento moderado**
(5-10 m/s / 18-36 km/h). En calma total no sirve porque IR y termopar dan lo mismo.

**Procedimiento:**

1. Medir **potencial hidrico (psi_stem)** con Scholander en la planta del nodo
   - Minimo 5 mediciones, 1 cada 30 min, durante el mediodia solar (11-15 hs)
2. Para cada medicion, registrar del payload del nodo (backend o Serial Monitor):
   - `T_leaf_IR` = temperatura media IR sin correccion (campo `tc_mean` pre-correccion)
   - `T_termopar` = lectura del termopar (campo `tc_temp`)
   - `wind_ms` = velocidad del viento
3. En planilla, calcular CWSI con distintos valores de k (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
   - `T_blend(k) = T_IR + k × (T_termopar - T_IR)`
   - `CWSI_blend(k) = (T_blend - Tc_wet) / (Tc_dry - Tc_wet)`
4. Hacer regresion lineal de cada `CWSI_blend(k)` vs `psi_stem` (Scholander)
5. El **k que maximiza R²** es el k optimo para ese varietal/region

**Valores tipicos por varietal:**

| Varietal | Region | k esperado | Notas |
|----------|--------|------------|-------|
| Malbec | Cuyo / Cordoba | 0.5-0.7 | Default 0.6 — canopeo denso, buena barrera sotavento |
| Cabernet Sauvignon | Mendoza | 0.5-0.6 | Canopeo menos denso que Malbec |
| Olivo (Arauco) | San Juan | 0.6-0.8 | Canopeo abierto — mas dependiente del termopar |
| Cerezo | Mendoza / Patagonia | 0.4-0.6 | Hojas grandes — IR cubre bien |
| Arandano | NOA | 0.7-0.9 | Canopeo compacto — termopar mas representativo |

**Para cambiar el valor:** Lucas actualiza `TC_BLEND_K` en `config.h` y sube firmware OTA.
No requiere visita de campo.

**Cuando recalibrar:** solo si se cambia de varietal, se poda drasticamente (cambia la densidad
del canopeo y la barrera sotavento), o se reubica el nodo. No es necesario cada temporada.

### 5.3 Pluviometro

1. Montar en soporte horizontal a la **misma altura que la carcasa** (sin obstrucciones arriba)
2. Verificar que la bascula esta nivelada (ajustar con las patas de nivelacion)
3. Conectar cable de pulso al conector M12 marcado "RAIN"

### 5.4 Panel Dry Ref y Wet Ref

1. **Dry Ref** (aluminio negro): montar en el bracket inferior, apuntando al **cielo** (sin sombra del canopeo)
2. **Wet Ref** (fieltro): montar junto al Dry Ref, conectar la manguera del reservorio de 10L
3. Llenar el reservorio con agua destilada o clorada
4. Verificar que la micro-bomba peristaltica funciona: al encender el nodo debe escucharse un click de 3 segundos

---

## 6. ENCENDIDO Y VERIFICACION

### Paso 6.1 -- Primer encendido

1. Abrir la carcasa (4 tornillos perimetrales)
2. Conectar el cable de bateria al board (conector JST 2 pines)
3. El LED de status parpadea:
   - **3 parpadeos rapidos**: boot OK
   - **1 parpadeo lento cada 5s**: buscando GPS fix
   - **LED fijo 2s**: GPS fix obtenido, primer ciclo iniciado
4. Cerrar la carcasa y apretar los 4 tornillos

### Paso 6.2 -- Verificacion en el backend (celular)

Esperar 2-3 minutos. Verificar en el MVC del backend que:

- [ ] El nodo aparece con su node_id (derivado de MAC address)
- [ ] El payload contiene: t_air, hr, cwsi, mds_um, bat_v, gps_lat, gps_lon
- [ ] bat_v > 3.3V
- [ ] iso_nodo > 0.80 (si es < 0.80: la ventana del MLX esta sucia -- limpiar con pano)
- [ ] El timestamp es correcto (hora UTC-3 Argentina)

### Paso 6.3 -- Verificacion del extensometro

- En el backend, verificar que `mds_um` no es 0 ni -1 (error de lectura)
- Valor esperado en planta sin estres: 50-150 um de variacion diaria
- Si `mds_um` = 0 constante: verificar conexion M12 "MDS" y continuidad del cable

---

## 7. MANTENIMIENTO PERIODICO

| Tarea | Frecuencia | Quien | Como saber que hay que hacerlo |
|-------|-----------|-------|-------------------------------|
| Recarga reservorio Wet Ref | Mensual | Javier | Nivel del reservorio < 2L (visual) |
| Limpieza lente MLX90640 | Solo cuando ISO_nodo < 80% | Javier | El backend muestra alerta "iso_limpieza" |
| Limpieza tubo colimador IR | Cada temporada | Javier | Inspeccion visual -- polvo acumulado en interior |
| Reemplazo hoja termopar | Mensual | Javier | Hoja marchita, desprendida, o lectura termopar fuera de rango en backend |
| Verificacion abrazadera extensometro | En cada sesion Scholander | Javier | Inspeccion visual -- no debe haberse aflojado |
| Verificacion panel solar | Mensual | Javier | bat_v bajando dia a dia = panel sucio u obstruido |
| Firmware OTA | Cuando Lucas lo indique | Lucas (remoto) | Lucas actualiza desde Cordoba capital |

---

## 8. PROBLEMAS COMUNES

| Sintoma | Causa probable | Solucion |
|---------|---------------|----------|
| Nodo no aparece en backend | Sin conectividad LoRa | Verificar que gateway esta encendido. Verificar antena del nodo (conector SMA apretado). |
| bat_v < 3.0V | Panel solar obstruido o cable desconectado | Limpiar panel. Verificar conector "SOLAR". Si persiste: reemplazar bateria. |
| iso_nodo < 50% | Lente muy sucio | Limpiar con pano de microfibra seco. NO usar agua ni alcohol sobre el lente. |
| mds_um = 0 constante | Cable extensometro cortado o conector suelto | Verificar continuidad (120 ohm). Reconectar M12. |
| cwsi = -1 o NaN | Temperatura del aire fuera de rango o sensor SHT31 desconectado | Verificar conector SHT31 dentro de la carcasa. |
| GPS no fija | Antena obstruida por la carcasa | Solo ocurre en primer boot. Reiniciar el nodo con la carcasa abierta por 30s. |
| Bomba Wet Ref no arranca | Manguera obstruida o reservorio vacio | Purgar manguera. Rellenar reservorio. |

---

## 9. DESINSTALACION (fin de temporada)

1. Desconectar bateria (abrir carcasa, desenchufar JST)
2. Desmontar carcasa del bracket (4 tornillos)
3. Retirar extensometro: aflojar tornillo de la abrazadera, retirar con cuidado sin danar la corteza
4. Retirar sensores externos (anemometro, pluviometro)
5. Vaciar reservorio Wet Ref
6. Guardar todo en caja con identificacion del nodo (etiqueta con node_id)
7. **NO retirar la estaca ni el bracket** -- se reusan la temporada siguiente

---

> **Contacto soporte:** Lucas Bergon (WhatsApp) para problemas de hardware.
> Cesar Schiavoni para problemas de backend/datos.
> En caso de emergencia (nodo sin datos >24h): Lucas puede diagnosticar remotamente si el gateway tiene conexion.
