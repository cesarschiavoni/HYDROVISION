## PROMPT PARA GENERACIÓN DE IMAGEN — Nodo de Campo HydroVision AG v1

---

### ESTILO VISUAL

Ilustración técnica fotorrealista de alta calidad, estilo diagrama de producto para datasheet de ingeniería o publicación científica. Vista en perspectiva 3/4 frontal-derecha, ligeramente elevada (~25-30° sobre el horizonte), que muestre el ensamblaje vertical completo desde debajo del nivel del suelo (corte de terreno) hasta la punta de la estaca con el anemómetro. Líneas de anotación finas blancas con etiquetas en texto negro sans-serif. Luz natural de mediodía argentino, cielo despejado azul profundo, sombras definidas proyectadas hacia el sur (sol al norte, hemisferio sur). Calidad de documentación técnica profesional, con nivel de detalle comparable a un manual de instalación industrial. Paleta de colores realista: grises metálicos, verdes de viñedo, marrón de suelo seco, azul cielo. Sin personas, sin animales, sin marcas de agua, sin logos comerciales, sin efectos de neón ni iluminación artificial.

---

### ESCENA — Viñedo experimental Malbec, Colonia Caroya, Córdoba, Argentina

Un viñedo de **vid Vitis vinifera cv. Malbec** conducido en sistema de **espaldera** (VSP — Vertical Shoot Positioning), ubicado en **Colonia Caroya, provincia de Córdoba, Argentina**, a ~700 m s.n.m. Clima semiárido continental con veranos calurosos (máximas de 38-42°C) e inviernos secos.

**Estructura de la espaldera visible:** postes verticales de madera tratada cada ~4-5 m, con 3 niveles de alambre galvanizado horizontal tensado entre ellos (alambre de formación a ~80 cm, alambre de contención a ~1,2 m, alambre superior a ~1,5-1,8 m). Los sarmientos verdes crecen verticalmente guiados por los alambres, formando una **cortina vegetal continua** (canopeo) de ~1,2 a 1,8 m de altura sobre el suelo. Las hojas son grandes, lobuladas, verde oscuro en el haz y más claras con pubescencia en el envés, típicas del Malbec.

**Los troncos** de las vides tienen ~5-8 cm de diámetro, corteza rugosa marrón oscuro con estrías longitudinales, separados **1 m entre sí** a lo largo de la hilera. Son visibles al menos 3-4 troncos consecutivos en la hilera donde está instalado el nodo.

**Las filas** corren aproximadamente este-oeste. El **pasillo entre filas** tiene ~2,5-3 m de ancho, claramente libre y despejado para el tránsito de maquinaria agrícola (se ven marcas de ruedas de tractor en el suelo). El suelo es **franco-limoso seco**, marrón claro, con una **cinta de riego por goteo negra** visible a lo largo de la base de cada hilera, justo debajo de los troncos.

De fondo se ven **hileras adicionales del viñedo** perdiéndose en la distancia. En la fila adyacente (visible a ~3 m a través del pasillo) NO hay nodo — es una fila "buffer" de riego al 100% ETc. El fondo lejano muestra el paisaje ondulado de las sierras chicas de Córdoba bajo el cielo despejado.

---

### SUJETO PRINCIPAL — Ensamblaje completo del nodo instalado EN LA LÍNEA DE LA HILERA, entre dos plantas consecutivas

**Posición de la estaca — DETALLE CRÍTICO:**

La estaca del nodo está clavada **en la misma línea de la hilera de vid**, exactamente entre dos plantas consecutivas, a **~50 cm del tronco de cada planta vecina**. La estaca NO está en el pasillo entre filas — está protegida dentro de la línea de plantación. A ambos lados de la estaca, a ~50 cm de distancia, se ve un tronco de vid con su canopeo. Los alambres de la espaldera pasan a ambos lados de la estaca sin tocarla. El pasillo entre filas (a la derecha en la imagen, ~2,5 m de ancho) está completamente libre para el paso de maquinaria.

**Mostrar cotas dimensionales horizontales:** "~50 cm" entre la estaca y cada tronco vecino, y "~2,5-3 m" indicando el ancho del pasillo entre filas, con una anotación: "Pasillo libre — maquinaria agrícola".

**La estaca:** tubo redondo de **acero inoxidable 316L**, diámetro ~25 mm, con brillo metálico mate (no cromado brillante ni pintado). **3 metros de largo total**, con **60 cm enterrados** bajo tierra. Mostrar un **corte del terreno** en la base que revele la porción enterrada terminando en **punta cónica** para facilitar el clavado. Sobre el nivel del suelo quedan **2,4 m visibles**. La estaca está perfectamente vertical (verificada con nivel de burbuja durante la instalación).

**Peso total del nodo montado: ~1,6 kg.** El nodo se compone de los siguientes elementos, montados de arriba hacia abajo sobre la estaca. Cada componente debe tener una **línea de anotación con flecha** señalando el componente exacto:

---

### COMPONENTE 1 — ANEMÓMETRO RS485 (punta del mástil, 2,4 m sobre suelo)

En el extremo superior absoluto de la estaca, montado sobre un brazo corto horizontal de acero inoxidable que sobresale ~15 cm. Un **anemómetro de 3 copelas hemisféricas giratorias**, carcasa plástica ABS gris claro/blanca, resistente a UV, clasificación IP65. Las copelas son semiesferas cóncavas de ~30 mm de diámetro cada una, montadas sobre brazos radiales a 120°, libres de girar sobre un eje vertical con rodamiento sellado. Diámetro del rotor de copelas: ~Ø60 mm. Altura total del instrumento: ~150 mm. Peso: ~200 g.

La marca "N" grabada en la base del anemómetro está orientada hacia el **norte magnético**. Está en el punto más alto del nodo, completamente libre de obstrucciones — mide el viento real del ambiente, no el atenuado por el canopeo de abajo.

Un cable RS485 (par trenzado de 2 hilos + malla GND, cubierta negra UV-resistente) baja por la estaca hacia la carcasa principal, sujeto con **bridas de nylon negras UV** cada ~50 cm.

**Etiquetar:** "Anemómetro RS485 copelas — IP65, 0-60 m/s, Modbus RTU 9600 baud. Marca N al norte. Libre de obstrucciones. Conector M12 'WIND'."

**Especificaciones técnicas (en texto pequeño junto a la etiqueta):**

* Protocolo: Modbus RTU vía MAX485 (SOIC-8) en la carcasa
* Registro de lectura: 0x0000 (velocidad instantánea)
* Función en el sistema: corrige CWSI por enfriamiento convectivo. Rampa 4-18 m/s: peso CWSI se reduce linealmente de 35% a 0%. A ≥18 m/s → HSI = 100% MDS.

---

### COMPONENTE 2 — PANEL SOLAR 6W (parte superior, ~2,3-2,4 m sobre suelo)

Inmediatamente debajo del anemómetro. Un **panel solar policristalino de 6W**, dimensiones **200 × 170 mm** (tamaño de un libro de bolsillo). Superficie de celdas fotovoltaicas azul oscuro/negro con reflejos iridiscentes característicos del silicio policristalino, organizadas en un patrón cuadriculado visible. Marco de aluminio anodizado fino (~3 mm de ancho) alrededor del panel. Vidrio templado de protección sobre las celdas. Peso: ~300 g.

Montado sobre un **bracket de inclinación ajustable** de aluminio (perfil en L con ranura de ajuste y mariposa M6) fijado con abrazadera de acero a la estaca. El panel está inclinado **~30° respecto a la horizontal**, con la cara activa orientada mirando hacia el **NORTE** (orientación óptima para captar máxima radiación solar en el hemisferio sur, latitud ~31°S).

Un cable bipolar (rojo/negro, sección 0,75 mm²) sale de la caja de conexiones trasera del panel y baja por la estaca hasta la carcasa principal, entrando a través de un **pasacable IP67 de plástico negro** (PG7) marcado con la etiqueta "SOLAR" en relieve.

**Etiquetar:** "Panel solar 6W policristalino — 200×170 mm, 6V nominal, orientado al norte, inclinación ~30°. Balance energético: genera 24-36 Wh/día en Córdoba vs. consumo 4,3 Wh/día → excedente +20-32 Wh/día."

---

### COMPONENTE 3 — CARCASA PRINCIPAL CON ELECTRÓNICA (2,0-2,2 m sobre suelo)

La pieza central y más grande del nodo. Una **carcasa estanca tipo Hammond 1554W** (o equivalente Gewiss GW44210), material **ABS/PC inyectado**, color **gris claro** (RAL 7035), dimensiones **200 × 150 × 100 mm**. Superficie lisa con bordes redondeados. Tapa con junta de neopreno y **4 tornillos de cierre perimetral** Phillips de acero inoxidable en las esquinas. Clasificación **IP67** (sellada contra polvo e inmersión temporal). Peso con electrónica adentro: ~800 g.

Fijada a la estaca con **dos abrazaderas de acero inoxidable tipo manguera** (cinta perforada con tornillo sin fin), una arriba y otra abajo de la carcasa. Entre la abrazadera y la carcasa hay un pad de goma EPDM antivibración.

**En la tapa superior de la carcasa:** una **membrana de ventilación GORE-Tex** (disco blanco de ~15 mm Ø, encastrado) que permite el intercambio de presión y evita condensación interior sin dejar pasar agua.

**En la cara SUR de la carcasa** (la cara que mira hacia el canopeo de la vid): una **ventana circular de HDPE** (polietileno de alta densidad, transparente al infrarrojo lejano LWIR 8-14 µm, opaca al visible), diámetro ~40 mm, montada al ras con junta de silicona. A través de esta ventana mira la cámara térmica MLX90640. La superficie del HDPE tiene un aspecto translúcido-lechoso, ligeramente opaco.

**En la cara superior, lateral o trasera:** una **antena LoRa 915 MHz** tipo stubby/whip de ~80 mm de largo, color negro, con conector SMA dorado en la base, roscada a un pasacable metálico. Es la antena de comunicación inalámbrica hacia el gateway de campo.

**En la cara inferior de la carcasa:** **6 a 7 pasacables IP67** de plástico negro (PG7 y PG9), alineados en fila. Cada uno tiene una etiqueta en relieve grabada en la carcasa:

* **"SOLAR"** — cable del panel solar
* **"WIND"** — cable RS485 del anemómetro
* **"ENV"** — cable I2C del shelter SHT31 externo
* **"TC"** — cable del termopar foliar
* **"MDS"** — cable blindado del extensómetro de tronco
* **"RAIN"** — cable de pulso del pluviómetro
* **"PM"** — cable UART del sensor de partículas PMS5003

Todos los cables salen por debajo (nunca por arriba) para que el agua de lluvia no pueda escurrir hacia los pasacables.

---

### COMPONENTE 3b — VISTA EN CORTE / TRANSPARENCIA DEL INTERIOR DE LA CARCASA

Mostrar la mitad frontal de la carcasa como **transparente o en corte tipo fantasma** (paredes semi-transparentes con un tono azulado sutil), revelando la disposición interna de los módulos electrónicos, montados con tornillos M2.5 sobre separadores (standoffs) de nylon o con velcro industrial sobre la base de la carcasa. Los módulos están interconectados con **cables I2C Stemma QT/Qwiic** (cables de 4 conductores con funda amarilla y conectores JST-SH de 4 pines en cada extremo) y cables SPI (cables finos multicolores).

**Módulos visibles adentro (de arriba a abajo, de izquierda a derecha):**

**3b.1 — ESP32-S3 DevKit** (cerebro del nodo):
Placa PCB verde, ~70×25 mm, con un **módulo WROOM-1-N4 plateado rectangular** (~18×20 mm, con cubierta metálica y antena impresa en el borde) soldado en el centro. Conector **USB-C** visible en un borde corto (usado para programación y debug, no en operación normal). **Pines header macho** (doble fila, 2×20 pines, color negro) a ambos lados de la placa. Un **LED rojo diminuto** (LED de status). Sobre la placa, texto serigrafiado "ESP32-S3 DevKit".

* Procesador: Dual-core Xtensa LX7, 240 MHz, 8 MB RAM
* Firmware: **MicroPython** (no C/Arduino)
* Deep sleep: 8 µA entre ciclos de 15 min
* Ejecuta: pipeline CWSI, cálculo HSI, control de 12+ sensores, serialización JSON, LoRa

**3b.2 — MLX90640 breakout** (cámara térmica LWIR):
Placa PCB pequeña **roja** (Adafruit 4407), ~25×25 mm, con el sensor térmico en un **encapsulado TO39 metálico plateado/dorado** (~Ø10 mm, cilíndrico con 4 pines) con **lente de silicio integrado** (reflejo oscuro circular en la cara frontal) que provee FOV de 110°×75°. Un conector I2C **Stemma QT** (JST-SH negro de 4 pines) en el borde. 4 agujeros de montaje M2.5 en las esquinas. La placa está montada **sobre la plataforma del gimbal** (ver 3b.3), alineada con la ventana HDPE de la cara sur.

* Resolución: **32×24 píxeles** (768 píxeles térmicos totales)
* NETD: ~100 mK (ruido radiométrico)
* Error CWSI con 28 píxeles foliares promediados: **±0,008**
* Dirección I2C: 0x33
* Sensor: MLX90640ESF-BAB-000-SP (suffix BAB = 110° FOV)

**3b.3 — Gimbal pan-tilt de 2 ejes** (escaneo multi-angular):
Un mecanismo compacto compuesto por **2 micro-servos MG90S de engranajes metálicos**, cada uno de color **azul** con etiqueta "MG90S" visible, dimensiones ~23×12×29 mm cada uno. Están montados en un **bracket ortogonal** de aluminio/plástico formando una L: un servo está horizontal (controla el paneo), el otro vertical (controla la inclinación). La placa MLX90640 está atornillada sobre la plataforma superior del gimbal, de modo que el servo de paneo gira toda la plataforma horizontalmente y el servo de inclinación la pivotea verticalmente.

Mostrar flechas curvas indicando los rangos de movimiento:

* **PAN (horizontal):** ±20° (de -20° izquierda a +20° derecha)
* **TILT (vertical):** +15° arriba / -10° abajo (rango asimétrico)

**Tabla de posiciones de escaneo** (mostrar como mini-tabla o anotación junto al gimbal):

| Pos | Pan   | Tilt  | Función                           |
| --- | ----- | ----- | ---------------------------------- |
| 0   | 0°   | 0°   | Centro — referencia base          |
| 1   | -20° | 0°   | Izquierda — sombra entre filas    |
| 2   | +20° | 0°   | Derecha — exposición máxima     |
| 3   | 0°   | +15° | Arriba — máx. cobertura foliar   |
| 4   | 0°   | -10° | Abajo — dosel inferior            |
| 5*  | 0°   | -30° | *Nadir — solo si viento > 20 km/h |

Secuencia completa: ~8-10 segundos. Tiempo de estabilización entre posiciones: 300 ms (verificado por IMU). PWM 50 Hz, pulso 500-2500 µs. GPIO 20 (PAN), GPIO 21 (TILT).

Algoritmo de fusión: el firmware retiene los 3 frames con mayor fracción foliar → CWSI final = promedio ponderado por fracción foliar. Si desviación estándar > 0,12 → flag `high_angular_variance` en el payload.

**3b.4 — ICM-42688-P IMU** (sensor inercial):
PCB breakout diminuta verde/negra, ~15×15 mm. Sensor inercial de 6 ejes (acelerómetro 3 ejes + giroscopio 3 ejes). Verifica que el gimbal se estabilizó antes de cada captura (vibración < 0,5 m/s²) y detecta si el nodo fue golpeado, movido o inclinado por viento/animal/tractor. SPI (CS=GPIO 22, INT1=GPIO 23).

**3b.5 — SHT31 breakout interno** (sensor ambiental backup):
PCB diminuta púrpura, ~15×15 mm. Sensor de temperatura (±0,3°C) y humedad relativa (±2% RH). I2C dirección 0x44. Backup del SHT31 principal que está en el shelter externo.

**3b.6 — ADS1231 ADC** (conversor para extensómetro):
PCB verde pequeña ~20×15 mm con chip SOIC. Conversor analógico-digital de **24 bits** de altísima resolución. Convierte la señal analógica del strain gauge del extensómetro de tronco en un valor digital con resolución de **1 µm** (1 micrómetro = 0,001 mm). Interfaz SPI bit-bang (SCLK=GPIO 14, DOUT=GPIO 15, PDWN=GPIO 16).

**3b.7 — MAX31855 amplificador de termopar:**
PCB breakout pequeña azul/verde ~20×12 mm. Amplifica y digitaliza la señal del termopar foliar externo tipo T (cobre-constantán). Resolución 0,25°C, precisión ±1,0°C en rango 0-70°C. SPI (CS=GPIO 25). Lo que importa para la corrección no es la precisión absoluta sino la **diferencia** T_termopar − T_IR.

**3b.8 — Módulo LoRa EBYTE E32-900T20D** (comunicación):
PCB rectangular verde ~30×20 mm con una pequeña antena en espiral impresa y un conector **SMA hembra dorado** en el borde. Chip transceiver Semtech SX1276 bajo cubierta metálica.

* Frecuencia: **915 MHz** (banda ISM Argentina, Resolución 296/2021 ENACOM)
* Modulación: LoRa, SF7, BW 125 kHz, CR 4/5
* Potencia: 17 dBm
* Alcance en campo abierto: 1-3 km
* Transmite payload JSON cada 15 min al gateway RAK7268

**3b.9 — MAX485** (transceiver RS485):
Chip SOIC-8 diminuto (~5×4 mm) soldado sobre una pequeña plaqueta adaptadora. Convierte el bus diferencial RS485 del anemómetro al UART del ESP32-S3. GPIO 3 (Driver Enable).

**3b.10 — Batería LiFePO4 32650:**
Celda cilíndrica (formato 32650) o prismática, color **azul** con etiqueta del fabricante, ~90×60×25 mm (prismática) o Ø32×65 mm (cilíndrica). Conectada al sistema por un **conector JST de 2 pines** (rojo/negro).

* Química: **LiFePO4** (litio-ferrofosfato) — no LiPo
* Tensión nominal: **3,2V**
* Capacidad: **6 Ah** (19,2 Wh)
* Autonomía sin sol: **~120 horas (~5 días)**
* Ciclos de vida: 2000+ (4× más que LiPo)
* Estable hasta 60°C (crítico para interior de carcasa en verano argentino)
* Tensión llena: 3,6V / Tensión mínima: 2,8V

**3b.11 — Cargador solar MPPT DFR0559:**
PCB módulo ~40×30 mm con componentes SMD, inductor toroidal visible, LEDs indicadores de carga. Gestiona la carga desde el panel solar 6W con seguimiento del punto de máxima potencia (MPPT). Sin MPPT se pierde hasta 30% de eficiencia. Salidas reguladas 5V y 3,3V.

**3b.12 — PMS5003 sensor de partículas** (Plantower):
Módulo rectangular cerrado ~50×38×21 mm, carcasa metálica plateada con aberturas de entrada y salida de aire (ventilador interno miniatura). Detecta PM1.0 / PM2.5 / PM10 en µg/m³.

* UART (RX=GPIO 12, TX=GPIO 13)
* Warmup: 3 segundos (láser interno)
* Detecta **fumigación** automáticamente (PM2.5 > 200 µg/m³) → invalida capturas térmicas por 4h (el aerosol contamina el lente)
* Detecta lluvia con aerosol (PM > 80) → clearance 3h
* Elimina la necesidad de que el productor informe manualmente cada fumigación

**3b.13 — Murata MZB1001T02 actuador piezoeléctrico** (limpieza del lente):
Disco cerámico piezoeléctrico diminuto (~Ø10 mm) pegado directamente sobre la cara interior de la ventana HDPE, con un driver boost MT3608L (~15×10 mm PCB) que eleva 3,7V de la batería a 20Vpp para excitarlo. Vibra durante 500 ms antes de cada captura para desprender polvo, rocío y residuos de fumigación de la ventana. GPIO 24.

* Elimina mantenimiento manual del lente (antes cada 2-4 semanas)
* Reivindicación técnica #1 de la patente INPI en trámite

**3b.14 — VEML7700 piranómetro** (sensor de radiación solar):
PCB breakout diminuta ~10×10 mm, sensor digital de luz ambiental I2C 16-bit (dirección 0x10). Mide radiación solar incidente (W/m²). Cuando rad < 150 W/m² (día nublado) activa modo ahorro — el CWSI es poco informativo sin gradiente solar.

**3b.15 — DS3231 RTC** (reloj de tiempo real):
Módulo pequeño ~15×15 mm con cristal oscilador y slot para batería CR2032 de respaldo (visible como disco plateado de 20 mm). Mantiene la hora exacta entre ciclos de deep sleep (drift < 1 min/año). I2C 0x68. La batería CR2032 mantiene la hora ante cortes de energía prolongados.

**3b.16 — GPS u-blox NEO-6M:**
Módulo ~25×25 mm con antena cerámica cuadrada visible (~15×15 mm, color marrón/dorado). Solo se activa en el primer boot (timeout 2000 ms) para obtener lat/lon del nodo. Después queda permanentemente apagado (el GPS consume demasiado para uso continuo). La posición se persiste en RTC memory.

**Etiquetar la carcasa completa:** "Carcasa Hammond IP67 — 200×150×100mm, ABS/PC gris. 16 módulos electrónicos internos. Arquitectura modular TRL4: DevKit + breakouts I2C/SPI — sin PCB custom. Cada módulo reemplazable en 5 min. Firmware MicroPython. Deep sleep 8 µA. Ciclo: 96 capturas/día (cada 15 min). COGS: USD 149/nodo (lote 50)."

---

### COMPONENTE 4 — TUBO COLIMADOR IR (solidario a la carcasa, cara SUR)

Un trozo de **tubo PVC sanitario** de color gris oscuro exterior, diámetro **Ø110 mm**, largo **250 mm**, con el **interior pintado negro mate** (pintura Rust-Oleum alta temperatura, para eliminar reflexiones IR internas). Montado **concéntrico con la ventana HDPE** de la cámara MLX90640, sobresaliendo horizontalmente desde la cara sur de la carcasa con una ligera inclinación hacia abajo (~15°) apuntando hacia el canopeo de la vid. Fijado al bracket de la carcasa con **2 abrazaderas plásticas negras** (tipo abrazadera de caño). Peso: ~200 g.

El extremo exterior del tubo (el que apunta al canopeo) está abierto, mostrando el interior negro mate limpio. El extremo interior está sellado contra la carcasa con silicona, con solo la ventana HDPE circular visible en el centro.

**Principio de funcionamiento:** el tubo bloquea el flujo lateral de viento sobre el campo visual de la cámara sin alterar las condiciones naturales de las hojas que está midiendo. Funciona como un parasol cilíndrico: la cámara ve a través del tubo, pero el viento transversal no penetra el FOV. Similar a los radiómetros de campo profesionales (Apogee SI-111/SI-131).

**Mostrar el eje óptico del tubo como una línea discontinua roja/naranja** que se extiende desde el lente del MLX90640 y se abre en un **cono translúcido amarillo-anaranjado claro** hacia el canopeo, representando el **FOV de 110°×75°**. El cono debe abarcar un área de ~3m × 2m del canopeo a la altura de ~1,5 m, iluminando las hojas que caen dentro del campo de visión. Anotar dentro del cono: "~28 píxeles foliares → error CWSI ±0,008".

**IMPORTANTE:** el tubo es de PVC, **NO de metal**. Anotar: "PVC (no metal) — el metal se calienta al sol y emite IR que contamina la lectura."

**Etiquetar:** "Tubo colimador IR — PVC Ø110×250mm, interior negro mate. Concéntrico con lente MLX90640. Apunta al canopeo (abajo/este, sotavento del Zonda). Reduce error CWSI por movimiento de hoja: de ±0,04 a ±0,01."

---

### COMPONENTE 5 — SHELTER ANTI-VIENTO SHT31 (1,8-2,0 m, lado NORTE de la estaca)

Una **mini-pantalla de radiación meteorológica tipo Gill** (diseño estándar WMO Guide No. 8, 2018). Consiste en **6 placas circulares horizontales de color blanco brillante** (PETG blanco resistente a UV, o platos plásticos blancos de ferretería), diámetro **Ø120 mm** cada una, ligeramente convexas. Las placas están apiladas verticalmente con una **separación de 15 mm** entre ellas, sostenidas por una **varilla roscada M4 de acero inoxidable** que atraviesa el centro de todas las placas. **Separadores de nylon de 15 mm** entre cada placa mantienen la distancia uniforme.

Dimensiones totales del shelter: Ø120 mm × ~100 mm de alto. Peso: ~150 g. Los costados están completamente abiertos, permitiendo que el aire fluya libremente entre las placas por convección natural, pero las placas bloquean la radiación solar directa y la lluvia.

Montado en un **brazo horizontal de aluminio** (~100 mm de largo, perfil en L) que sale de la estaca hacia el lado **NORTE** del poste (máximo flujo de aire natural en hemisferio sur). Sujeto a la estaca con **2 bridas de nylon UV negras**.

En el **plato central** (plato número 3 contando desde arriba) se aloja el **sensor SHT31** (chip Sensirion, visible como un pequeño componente blanco de ~2,5×2,5 mm en un breakout PCB púrpura de ~15×15 mm). Mide la **temperatura del aire** (T_air) con precisión ±0,3°C y la **humedad relativa** (RH) con ±2%.

Un cable I2C (4 conductores, funda amarilla Stemma QT) sale del shelter y baja por la estaca hasta el pasacable "ENV" de la carcasa.

**Etiquetar:** "Shelter tipo Gill — 6 placas blancas Ø120mm, separación 15mm. SHT31 (±0,3°C, ±2% RH, I2C 0x44) en plato central. Lado norte del poste. Conector M12 'ENV'. Reduce error T_air por viento/radiación de ±0,5°C a ±0,1°C. Sin shelter: error CWSI propagado de ±0,05-0,10 por VPD."

---

### COMPONENTE 6 — PLUVIÓMETRO (1,8-2,0 m, brazo horizontal)

Un **pluviómetro de báscula de balancín** (tipping bucket) montado sobre un brazo horizontal rígido de aluminio que sale de la estaca. Embudo receptor de **Ø80 mm** de color verde oscuro o gris, con borde afilado calibrado para la captación. Carcasa cilíndrica IP65 debajo del embudo que contiene el mecanismo de balancín. El instrumento está perfectamente **nivelado** (ajustado con las patas de nivelación de burbuja integradas). No hay obstrucciones arriba del embudo (el panel solar y la carcasa están por encima pero desplazados). Peso: ~200 g.

Cable de pulso digital (2 conductores finos) baja por la estaca hasta el pasacable M12 "RAIN". Conectado a GPIO 2 del ESP32-S3 (interrupción ISR con debounce de 200 ms).

Resolución: **0,2 mm por pulso de balancín** (cada basculación = 0,2 mm de precipitación acumulada).

**Función dual crítica:**

1. Trigger de **auto-calibración del baseline Tc_wet**: cuando llueve ≥5 mm y el MDS del tronco ≈ 0 (planta al máximo de hidratación), la temperatura foliar medida por el MLX90640 en ese instante ES el Tc_wet real del nodo. El firmware actualiza el baseline automáticamente (EMA, learning_rate=0,25) sin visita humana.
2. Activar **clearance de 3h post-lluvia** para evitar capturas térmicas con gotas de agua en las hojas (las gotas distorsionan la lectura IR).

**Etiquetar:** "Pluviómetro tipping bucket — Ø80mm, 0,2 mm/pulso, IP65. Nivelado. GPIO 2 (ISR). Trigger auto-calibración Tc_wet (lluvia ≥5mm + MDS≈0). Clearance 3h post-lluvia. Conector M12 'RAIN'."

---

### COMPONENTE 7 — PANELES DE REFERENCIA DRY REF / WET REF (1,5-1,8 m, bracket inferior)

Dos paneles planos de **~100×100 mm** cada uno, montados lado a lado en **brazos horizontales** que salen de un bracket inferior fijado a la estaca, con las superficies **apuntando hacia el cielo** (orientados skyward, ~20° de horizontal). No deben tener sombra del canopeo arriba. Peso conjunto: ~300 g.

**Relación geométrica con la cámara:** los paneles están montados ~20–50 cm debajo de la carcasa (que está a 2.0–2.2 m) y el eje óptico de la cámara apunta hacia abajo/este al canopeo (~15° de inclinación). Sin embargo, el FOV del MLX90640 es muy amplio (**110°×75°**), por lo que los paneles caen en la **periferia inferior del frame** (filas ~20 de 24, bordes izquierdo y derecho). El centro del frame queda libre para los ~28 píxeles foliares del canopeo. En cada frame de 768 píxeles, el firmware lee directamente las temperaturas de los paneles en **coordenadas de píxel fijas** pre-calibradas durante la instalación (función `mlx_calibrar_iso_nodo()`).

**Panel Dry Ref (el de la izquierda en la imagen):**
Placa de **aluminio anodizado negro mate** (emisividad ε ≈ 0,98 — prácticamente un cuerpo negro). Superficie completamente opaca, oscura, sin brillo, con textura micro-rugosa del anodizado. Sin mantenimiento. Su temperatura es medida directamente por el MLX90640 (no modelada ni estimada). Representa el **límite superior de temperatura (T_UL)** del CWSI: la temperatura más alta que una superficie seca alcanza en las condiciones actuales.

**Panel Wet Ref (el de la derecha):**
Misma placa de aluminio pero cubierta con una capa de **fieltro técnico hidrofílico blanco** (aspecto de tela de algodón grueso, color blanco-crema), mantenido **permanentemente húmedo** por una **micro-bomba peristáltica de 6V**. La bomba es un **motor cilíndrico pequeño** (~30×20 mm, color negro con eje plateado) montado con un bracket sobre la estaca a la misma altura. La bomba tiene un rollo de **manguera de silicona transparente** (Ø interno 2 mm, Ø externo 4 mm) que la atraviesa. La bomba succiona agua destilada del **reservorio** de abajo y la pulsa sobre el fieltro durante **3 segundos** en cada ciclo de 15 minutos (GPIO 35).

Representa el **límite inferior de temperatura (T_LL)** del CWSI: la temperatura más baja que una superficie alcanza por evaporación máxima.

**Manguera de silicona:** visible como un tubo transparente fino (Ø4 mm) que sube por la estaca desde el reservorio en el suelo hasta la bomba y luego al panel Wet Ref. Se ven pequeñas gotas de agua dentro de la manguera.

**Auto-diagnóstico óptico (ISO_nodo):** el firmware compara la T_dry_ref medida contra la curva teórica esperada (función de T_aire y radiación). Si se desvía >1,5°C → alerta "Lente Sucio/Empañado". El técnico solo interviene cuando ISO_nodo < 80%.

**Fórmula del índice Jones (visible como anotación):**

```
Ig = (T_canopeo − T_wet_ref) / (T_dry_ref − T_canopeo)
```

Calculado 96 veces/día con referencias físicas medidas — sin depender de coeficientes NWSB estimados.

**Etiquetar Dry Ref:** "Dry Ref — aluminio negro mate (ε≈0,98). T_UL para CWSI. Sin mantenimiento. Medición directa por MLX90640."
**Etiquetar Wet Ref:** "Wet Ref — fieltro hidrofílico + bomba peristáltica 6V (pulso 3s/ciclo, GPIO 35) + reservorio 10L. T_LL para CWSI. Autonomía: 90-120 días sin recarga."

---

### COMPONENTE 8 — RESERVORIO DE AGUA (base de la estaca, nivel del suelo)

En la base de la estaca, apoyado en el suelo, un **bidón de plástico translúcido** (HDPE o PP, color semi-transparente blanquecino) de **10 litros** de capacidad, con tapa rosca. Se ve el nivel de **agua destilada** en su interior (líquido transparente). La manguera de silicona transparente sale de la tapa del bidón (con un adaptador pasante) y sube por la estaca hasta la bomba peristáltica.

**Etiquetar:** "Reservorio 10L — agua destilada. Alimenta panel Wet Ref vía bomba peristáltica. Autonomía: 90-120 días. Recarga mensual por el técnico de campo."

---

### COMPONENTE 9 — TERMOPAR FOLIAR (a nivel del canopeo, ~1,5 m)

En el canopeo de la vid, en una **hoja representativa** de la planta más cercana a la estaca (~50 cm). La hoja seleccionada es:

* Madura, sana, verde oscuro, sin manchas, sin daño mecánico ni enfermedad
* Orientada al **mismo lado que la cámara (ESTE / sotavento del Zonda)**
* No en la periferia del canopeo (las hojas periféricas están más expuestas al viento)
* A la altura de la cámara (~1,5 m)

En el **envés** (cara inferior) de esa hoja, fijado con un **clip mini-pinza de resorte** (impreso en 3D, plástico blanco, ~15×10 mm, con un pequeño resorte de acero), hay un **hilo de termopar tipo T** (cobre-constantán) de **Ø0,1 mm** (AWG 40, extremadamente fino, casi invisible). La punta del hilo está en contacto directo con el tejido foliar. El hilo pesa **<0,01 g** — no altera la temperatura natural de la hoja.

Se elige el envés porque tiene menor exposición solar directa → menor artefacto por radiación absorbida.

El **cable trenzado del termopar** (2 metros de largo, par trenzado fino con aislamiento teflón, color marrón/blanco) sale del clip, baja suavemente por la hoja y los alambres de la espaldera (con holgura para que el canopeo se mueva con el viento), luego sube por la estaca hasta la carcasa, entrando por el pasacable "TC". Sujeto a la estaca con **2 bridas UV negras**, dejando ~30 cm de holgura en el extremo de la hoja.

**Función:** mide la temperatura de la hoja por **contacto directo**, completamente inmune al viento (el viento enfría la superficie de la hoja por convección pero no cambia la lectura de un sensor de contacto). Se usa como referencia cruzada para corregir la lectura IR del MLX90640 en tiempo real.

**Fórmula de corrección (visible como anotación):**

```
T_corr = T_IR + k × (T_termopar − T_IR)
```

donde **k = 0,6** (valor default para Malbec en Colonia Caroya, calibrado contra Scholander). El factor k se puede recalibrar por varietal/región (rango típico: 0,4-0,9).

Combinado con el tubo colimador, reduce el error total CWSI por viento de ±0,12-0,18 a **±0,03** (cerca del piso NETD de ±0,008 del sensor).

**Mantenimiento mensual:** verificar que la hoja sigue viva y sana. Si se marchitó o desprendió, reemplazar por otra hoja representativa y recolocar el clip.

**Etiquetar:** "Termopar tipo T (Cu-Constantán) — Ø0,1mm (AWG 40, <0,01g), clip en envés de hoja, lado este (sotavento Zonda). Ground truth T_foliar por contacto, inmune a viento. Corrección IR: T_corr = T_IR + 0,6×(T_tc − T_IR). Reduce error CWSI por viento de ±0,08 a ±0,02. Amplificador MAX31855 (SPI) en carcasa. Conector M12 'TC'."

---

### COMPONENTE 10 — EXTENSÓMETRO DE TRONCO / DENDRÓMETRO MDS (30 cm sobre suelo, EN EL TRONCO)

En el **tronco de la vid más cercana** a la estaca (~50 cm de la estaca), a **30 cm de altura sobre el nivel del suelo**, en la **cara NORTE del tronco** (recibe sol directo en hemisferio sur):

Una **abrazadera de aluminio anodizado** (~60×30 mm, superficie plateada mate del anodizado, ~3 mm de espesor) ciñe el tronco de la vid como un collar. Fijada con un **tornillo de presión** (Allen M4 inoxidable) que permite ajustar el diámetro de la abrazadera al tronco (acepta diámetros de 3 a 25 cm; Malbec adulto típico: 5-8 cm). La abrazadera debe estar **firme pero sin comprimir la corteza** — si se aprieta demasiado, el strain gauge mide la presión de la abrazadera y no la contracción natural del tronco (~50-200 µm/día). Si queda floja, se desliza con el viento y genera ruido.

Sobre la abrazadera, en la cara exterior (la que mira al norte), está pegado un **strain gauge de precisión** (sensor de deformación, visible como un elemento plano diminuto tipo estampilla, ~10×5 mm, con patrón de serpentina metálica visible, color cobre/dorado sobre soporte plástico translúcido). Está adherido con adhesivo cianoacrilato y cubierto con una capa de barniz protector. Resistencia: 120Ω (puente completo). El strain gauge detecta las **micro-variaciones diarias del diámetro del tronco** causadas por la contracción y dilatación del xilema al transportar agua.

**MDS = Máxima Diferencia de Shrinkage = D_max − D_min** (en micrómetros, µm). Valores típicos:

* Planta sin estrés: 50-150 µm/día
* Planta con estrés moderado: 150-300 µm/día
* Planta con estrés severo: >300 µm/día

Justo al lado del strain gauge, pegado con epoxi a la abrazadera, un diminuto **sensor de temperatura DS18B20** en encapsulado **TO-92** (pieza negra con 3 pines metálicos, ~5×4×4 mm, con la cara plana marcada "DS18B20"). Mide la temperatura del tronco/abrazadera para corregir la dilatación térmica del aluminio. Coeficiente de compensación: **α = 2,5 µm/°C** (Pérez-López et al. 2008). Sin esta corrección, un cambio de 10°C entre noche y día produce un artefacto de 25 µm — comparable a la señal real de MDS.

Un **cable blindado** (malla de cobre + funda negra, Ø3 mm, con conector M12 IP67 macho en el extremo) de **3 metros** sale de la abrazadera, sube verticalmente por el tronco, cruza ~50 cm horizontalmente hasta la estaca, y sube por la estaca hasta la carcasa, conectándose al pasacable "MDS". Sujeto con **bridas UV negras** cada metro.

**El extensómetro tiene un segundo rol:** cuando llueve ≥5 mm y MDS ≈ 0 (tronco al diámetro máximo = planta al máximo de hidratación), la T_foliar medida por el MLX90640 en ese instante es el Tc_wet real del nodo. El firmware actualiza el baseline automáticamente.

**Por qué a 30 cm del suelo:** el tronco a esa altura tiene diámetro estable, está por debajo de la zona de injerto, y no interfiere con labores de poda ni cosecha.
**Por qué cara norte:** el DS18B20 mide la temperatura real del tronco al sol. Si se montara en la cara sur (sombra), la corrección térmica sería menos precisa.

**Etiquetar:** "Extensómetro MDS — Strain gauge 120Ω + ADS1231 24-bit (resolución 1 µm) + DS18B20 (corrección térmica α=2,5 µm/°C). Cara norte del tronco, 30 cm sobre suelo. Abrazadera Al anodizado (3-25 cm Ø). Cable blindado 3m, conector M12 'MDS'. R²=0,80-0,92 vs ψ_stem (Fernández & Cuevas 2010). Inmune a viento. Opera 24/7 incluyendo noches y días nublados."

---

### ANOTACIONES DIMENSIONALES Y CONTEXTUALES

**1. Línea de cotas vertical** (en el lado izquierdo de la imagen, con líneas horizontales punteadas a cada nivel):

| Cota                 | Componente                                                               |
| -------------------- | ------------------------------------------------------------------------ |
| -0,6 m (bajo tierra) | Punta cónica de la estaca (visible en corte de terreno)                 |
| 0 m                  | **Nivel del suelo** (línea gruesa marrón) — reservorio 10L      |
| 0,3 m                | Extensómetro MDS en tronco                                              |
| 0,8 m                | Alambre de formación de la espaldera (1er nivel)                        |
| 1,2 m                | Alambre de contención de la espaldera (2do nivel) — inicio del canopeo |
| 1,5 m                | **Nivel del canopeo** (línea punteada verde) — termopar foliar   |
| 1,5-1,8 m            | Paneles Dry/Wet Ref + bomba peristáltica                                |
| 1,8 m                | Alambre superior de la espaldera (3er nivel) — tope del canopeo         |
| 1,8-2,0 m            | Shelter SHT31 / Pluviómetro                                             |
| 2,0-2,2 m            | Carcasa principal + tubo colimador                                       |
| ~2,3 m               | Panel solar 6W                                                           |
| 2,4 m                | Anemómetro (punta del mástil)                                          |

**2. Cotas horizontales:**

* "~50 cm" entre la estaca y el tronco izquierdo
* "~50 cm" entre la estaca y el tronco derecho
* "~2,5-3 m" indicando el ancho del pasillo entre filas, con anotación: "**Pasillo libre — tránsito de maquinaria agrícola** (tractores, pulverizadoras, desmalezadoras)"
* Flecha indicando la dirección de la fila de plantación (E-O)

**3. Rosa de los vientos** (esquina inferior derecha):

* **N** apuntando hacia el lado del panel solar/shelter
* **S** hacia el canopeo donde apunta la cámara
* **E** hacia la dirección del termopar foliar y la cámara (sotavento)
* **O** (de donde viene el viento Zonda dominante)
* Anotación junto a la rosa: "Cámara y termopar → ESTE (sotavento Zonda). Las plantas actúan como barrera natural, reduciendo ~60-70% el enfriamiento convectivo."

**4. Cono de visión del MLX90640:**
Proyectado como un cono translúcido amarillo-anaranjado claro desde el tubo colimador hacia el canopeo. Ángulo de apertura: 110° horizontal × 75° vertical. Dentro del cono, sobre las hojas del canopeo iluminadas, anotar:

* "FOV 110°×75°"
* "32×24 px (768 px totales)"
* "~28 px foliares → error CWSI ±0,008"
* "Cubre ~3m × 2m de canopeo → ~15-20 hojas de 3-4 plantas"

**5. Recuadro informativo** (esquina superior izquierda, fondo semi-transparente blanco):

```
HydroVision AG — Nodo IoT LWIR v1
Prototipo TRL 4 — ANPCyT STARTUP 2025
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MCU: ESP32-S3 DevKit + MicroPython
Cámara: MLX90640 32×24 (Adafruit 4407, BAB 110°)
Comunicación: LoRaWAN 915 MHz → gateway RAK7268
Energía: Panel 6W + LiFePO4 6Ah → autonomía ~120h sin sol
Ciclo: 96 capturas/día (cada 15 min) + gimbal 5+1 posiciones
Peso: ~1,6 kg | COGS: USD 149/nodo (lote 50)
Montaje: en línea de hilera, entre plantas — protegido de maquinaria
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Índices calculados en nodo (edge computing):
  CWSI = (T_canopeo − T_LL) / (T_UL − T_LL)
  HSI = 0,35 × CWSI + 0,65 × MDS
  Error CWSI sistema completo: ±0,008 (28 px promediados)
```

**6. Fórmulas visibles** como anotaciones técnicas flotantes con tipografía monoespaciada:

* `CWSI = (T_canopeo − T_LL) / (T_UL − T_LL)` — Jackson, 1981
* `HSI = 0,35 × CWSI + 0,65 × MDS` — HydroVision AG (fusión)
* `T_corr = T_IR + 0,6 × (T_tc − T_IR)` — corrección termopar
* `MDS = D_max − D_min (µm)` — contracción diaria del tronco

**7. Texto del viñedo** (superpuesto sutil en la parte inferior de la imagen):
"Viñedo experimental Malbec — Colonia Caroya, Córdoba, Argentina — 1/3 ha (~3.333 m²), 10 filas × 136 plantas (5 filas experimentales + 5 buffer intercalados), espaldera VSP, ~700 m s.n.m. — 5 nodos (1 por fila experimental) — Regímenes hídricos: 100% / 65% / 40% / 15% / 0% ETc — Riego por goteo con controlador Rain Bird"

**8. Pequeño diagrama inset** (esquina inferior izquierda, ~15% del área de la imagen):
Vista aérea esquemática del viñedo mostrando las 10 filas paralelas (este-oeste). 5 filas experimentales, cada una con un único régimen hídrico (fila completa uniforme): Fila 2 = 100% ETc (azul, control), Fila 4 = 65% ETc (celeste), Fila 6 = 40% ETc (amarillo), Fila 8 = 15% ETc (naranja), Fila 10 = 0% ETc (rojo, secano). 5 filas buffer intercaladas (1, 3, 5, 7, 9) en gris claro — todas a 100% ETc. 5 nodos marcados con ícono circular rojo, uno en el centro de cada fila experimental (planta 68). Título del inset: "Diseño experimental — 5 filas × 1 tratamiento por fila (680 vides exp. + 680 buffer)".

---

### LO QUE NO DEBE INCLUIR LA IMAGEN

* No incluir personas, manos, animales ni insectos
* No incluir marcas comerciales ni logos de fabricantes en los componentes
* No incluir marcas de agua ni textos del generador de imágenes
* No incluir iluminación irreal, neón, resplandores fantasy ni halos
* No simplificar los componentes como bloques genéricos — cada uno debe ser identificable individualmente
* La **estaca es de acero inoxidable 316L** — brillo metálico mate plateado, NO madera, NO pintada, NO cromada brillante
* Los **servos MG90S son AZULES** (no negros, no grises)
* La **carcasa es GRIS CLARO** (RAL 7035, tipo Hammond/Gewiss), no negra, no blanca
* La **placa Adafruit MLX90640 es ROJA**, no verde
* El **tubo colimador es PVC gris** exterior con interior negro mate, no metal
* La **batería LiFePO4 es AZUL** (estándar del fabricante)
* El **HDPE de la ventana** es translúcido-lechoso, NO transparente como vidrio
* Las **hojas del Malbec** son lobuladas con 5 lóbulos, verdes oscuras, con pubescencia clara en el envés — no hojas genéricas lisas
* La cinta de riego por goteo es **negra**, no verde ni marrón
* El suelo es seco y marrón claro, **no césped verde** (es viñedo de zona semiárida)
* La estaca va **ENTRE dos plantas en la línea de la hilera**, NO en el pasillo entre filas
