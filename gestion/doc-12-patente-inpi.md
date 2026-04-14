
# SOLICITUD DE PATENTE DE INVENCIÓN — INPI ARGENTINA
## HydroVision AG — Sistema autónomo de monitoreo de estrés hídrico en cultivos

**Tipo de protección:** Patente de Invención  
**Solicitante:** HydroVision AG S.A.S.  
**Inventores:** César Schiavoni, Lucas Bergon  
**Agente de la Propiedad Industrial:** Ximena Crespo (AGPI Matrícula [N°])  
**Fecha de prioridad Argentina (INPI):** [a completar al presentar]  
**Estrategia PCT:** Presentación PCT dentro de 12 meses — jurisdicciones: Chile, Brasil, Estados Unidos

---

## I. TÍTULO DE LA INVENCIÓN

**NODO SENSOR AUTÓNOMO DE CAMPO CON TERMOGRAFÍA LWIR, EXTENSOMETRÍA DE TRONCO Y FUSIÓN DE ÍNDICE HÍDRICO ADAPTATIVO PARA CONTROL DE RIEGO EN CULTIVOS PERENNES, Y SISTEMA DE CALIBRACIÓN NODO-SATÉLITE ASOCIADO**

---

## II. CAMPO DE LA INVENCIÓN

La presente invención pertenece al campo de la agricultura de precisión e instrumentación agronómica. Específicamente, se refiere a un sistema embebido autónomo de campo para la medición continua del estrés hídrico en cultivos, que integra: (a) una cámara de imagen térmica infrarroja de onda larga (LWIR) sobre soporte pan-tilt motorizado con compensación inercial; (b) un extensómetro de tronco de alta resolución con corrección térmica; (c) un motor fenológico autónomo basado en grados-día acumulados (GDD); (d) un índice de estrés hídrico compuesto (HSI) con confianza dinámica ponderada por velocidad de viento; (e) una arquitectura de inferencia local mediante red neuronal informada por física (PINN) embebida en microcontrolador de bajo consumo; y (f) un método de calibración nodo-satélite que extiende la cobertura de un único nodo a aproximadamente 50 hectáreas mediante fusión con imágenes multiespectrales Sentinel-2.

---

## III. ANTECEDENTES DE LA INVENCIÓN

### Estado de la técnica

El monitoreo del estrés hídrico en cultivos es determinante para la eficiencia en el uso del agua y la calidad de la producción. El Índice de Estrés Hídrico del Cultivo (CWSI, *Crop Water Stress Index*), definido por Jackson et al. (1981) como:

```
CWSI = (ΔT_medido − ΔT_LL) / (ΔT_UL − ΔT_LL)
```

donde ΔT es la diferencia entre temperatura foliar y temperatura del aire, ΔT_LL el límite inferior (planta bien hidratada) y ΔT_UL el límite superior (estoma cerrado), se ha validado en más de 200 publicaciones científicas como indicador fisiológico confiable del estado hídrico de la planta.

Las soluciones actuales presentan limitaciones significativas:

**Sistemas UAV / drones (publicaciones 2016–2024, sin patente de sistema integrado):** Operan de forma aérea puntual, requieren operador capacitado, tienen costos operativos elevados y no proveen monitoreo continuo. No integran control de riego autónomo. Araújo-Paredes et al. (2022) reportan R² = 0.49–0.55 entre CWSI aéreo y potencial hídrico de tallo (Ψ_stem) en vid Loureiro, definiendo el rango de referencia para la tecnología aérea.

**AquaSense (2025, publicación académica, sin patente):** Combina sensor de suelo como input principal con FLIR Lepton y ESP32. La reivindicación central es el sensor de suelo; la cámara térmica es accesoria. No implementa extensometría de tronco, gimbal multi-angular ni motor fenológico autónomo.

**WISN (MDPI Sensors, 2023, sin patente):** Utiliza termómetro IR puntual MLX90614 — un único punto de temperatura foliar, sin imagen ni segmentación. No calcula CWSI desde imagen térmica completa ni integra ningún sensor fisiológico adicional.

**Patente US 11,195,015 (2021):** Cubre análisis de imágenes aéreas con IA procesada en la nube para agricultura. No contempla nodo fijo terrestre, inferencia en edge sin conectividad permanente, termografía LWIR embebida, extensometría de tronco, ni control autónomo de riego integrado en el nodo.

**Sistemas de riego inteligente existentes (Netafim CropSpec, Lindsay FieldNET, Trimble Ag):** Basan las decisiones de riego en sensores de suelo (tensiómetros, sondas capacitivas). Ninguno integra temperatura foliar LWIR como señal primaria de decisión. Ninguno incorpora fenología automática que ajuste los umbrales de riego según estadio del cultivo sin configuración manual.

**Vacío identificado:** No existe en el estado de la técnica, ni en las bases INPI Argentina, USPTO, EPO/Espacenet ni WIPO/PCT, una solución que reúna: nodo fijo autónomo en campo con cámara térmica LWIR + extensómetro de tronco + gimbal multi-angular con compensación inercial + motor fenológico GDD autónomo + HSI con confianza dinámica por viento + inferencia PINN embebida + auto-calibración dinámica del baseline + fusión nodo-satélite Sentinel-2 + control autónomo de riego, todo ello operando sin dependencia de conectividad permanente a internet.

---

## IV. DESCRIPCIÓN DETALLADA DE LA INVENCIÓN

### 4.1 Descripción general del sistema

El sistema de la invención comprende tres subsistemas integrados:

**Subsistema 1 — Nodo de campo autónomo:** Unidad hardware instalada de forma fija en el cultivo, entre plantas, sobre estaca de acero inoxidable. Opera de forma completamente autónoma mediante energía solar (panel 6 W + batería LiFePO₄ 6 Ah, autonomía mínima 120 horas sin sol). Procesa localmente todos los índices agronómicos y ejecuta acciones de riego sin requerir conexión a internet. Comunica resultados vía LoRa 915 MHz al gateway.

**Subsistema 2 — Backend de fusión y visualización:** Servidor que recibe las transmisiones LoRa, ejecuta inferencia PINN de alta precisión, fusiona con imágenes Sentinel-2 para generar mapas de estrés de lote completo, y provee dashboard web y aplicación móvil al productor.

**Subsistema 3 — Método de calibración nodo-satélite:** Procedimiento por el cual el CWSI medido en el punto de instalación del nodo se correlaciona con los índices NDWI, NDVI y NDRE de los píxeles Sentinel-2 correspondientes, extendiendo la calibración a todo el lote (~50 ha por nodo en condiciones de variabilidad moderada).

### 4.2 Hardware del nodo de campo — descripción técnica

El nodo comprende los siguientes componentes integrados en una arquitectura modular (ESP32-S3 DevKit + módulos breakout I2C/SPI en TRL4, con migración a PCB multicapa 4 capas en producción vol. 500+) con carcasa IP67 resistente a temperaturas −10°C a +55°C, humedad 10–95% y viento hasta 80 km/h:

**a) Unidad de termografía LWIR con compensación multi-angular:**

La cámara de imagen térmica es un sensor de microbolómetro de onda larga infrarroja (LWIR, 8–14 µm) con resolución mínima de 32×24 píxeles, campo visual horizontal ≥ 80°, precisión radiométrica NETD ≤ 150 mK (preferentemente ≤ 100 mK, implementado con Melexis MLX90640ESF-BAB, NETD típico 100 mK, error CWSI resultante ±0.038, dentro del umbral agronómico ±0.07 definido por Araújo-Paredes et al., 2022).

La cámara se monta sobre un sistema gimbal pan-tilt de dos ejes actuados por servomotores (implementado con 2× MG90S, controlados por señal PWM vía módulo LEDC del microcontrolador ESP32-S3). La unidad inercial ICM-42688-P, integrada en el mismo PCB, compensa las vibraciones por viento durante la captura. En cada ciclo de medición (preferentemente cada 15 minutos) se adquieren 5 posiciones angulares fijas más una adicional condicional según velocidad de viento:

| Posición | Ángulo Horizontal | Ángulo Vertical | Condición |
|---|---|---|---|
| Centro | 0° | 0° | Siempre |
| Izquierda | −20° | 0° | Siempre |
| Derecha | +20° | 0° | Siempre |
| Superior | 0° | +15° | Siempre |
| Inferior | 0° | −10° | Siempre |
| Adicional | Aleatorio | Aleatorio | Viento > 20 km/h |

La fusión de los múltiples frames se realiza localmente en el microcontrolador: para cada frame se calcula la fracción foliar (proporción de píxeles cuya temperatura se ubica en el rango percentil 20–75 del histograma térmico); se retienen los 3 frames con mayor fracción foliar; el CWSI resultante es la mediana ponderada por fracción foliar de los 3 frames retenidos.

Un sistema de limpieza piezoeléctrica (transductor Murata MZB1001T02 o equivalente, frecuencia de resonancia 1 kHz, activado por GPIO del microcontrolador) protege la ventana óptica del sensor frente a polvo, agua y aerosoles de fumigación sin partes móviles adicionales.

**b) Extensómetro de tronco (MDS — Máxima Contracción Diaria):**

Sensor de deformación (strain gauge tipo puente Wheatstone de 4 brazos, sensibilidad mínima 1 µm) con convertidor analógico-digital de 24 bits (ADS1231) y sensor de temperatura integrado (DS18B20, ±0.5°C) para corrección de la dilatación térmica del tronco. El conjunto se monta en abrazadera de aluminio anodizado ajustable al tronco de la planta. La variable medida es la contracción diaria máxima del tronco (MDS = D_máx − D_mín), correlacionada con el potencial hídrico del tallo (Ψ_stem) con R² = 0.80–0.92 (Fernández & Cuevas, 2010). El extensómetro opera de forma continua 24 horas al día, 7 días a la semana, sin requerir ventana horaria de medición, inmune a variaciones de viento y radiación.

**c) Sistema de referencia de calibración dual (paneles Dry Ref / Wet Ref):**

El nodo incorpora dos paneles de calibración físicos que permiten la medición directa de las temperaturas de referencia de la fórmula CWSI sin depender exclusivamente de coeficientes teóricos:

- **Panel Dry Ref:** superficie de aluminio negro mate (emisividad ε ≈ 0.98), sin evaporación, representando la temperatura máxima de una hoja no transpirante bajo las condiciones ambientales del momento.
- **Panel Wet Ref:** superficie de material hidrofílico poroso (fieltro técnico o similar) mantenida saturada de agua mediante una micro-bomba peristáltica de 6 V controlada por GPIO del microcontrolador y un reservorio de 10 litros con autonomía de 90–120 días sin recarga. Representa la temperatura mínima alcanzable por una hoja en máxima transpiración.

Ambos paneles son visibles simultáneamente desde la posición de reposo de la cámara LWIR. La calibración se ejecuta 96 veces por día.

**d) Sensor meteorológico integrado:**

Sensor combinado de temperatura y humedad relativa (SHT31 o equivalente, ±0.3°C, ±2% HR, interfaz I2C), sensor de precipitación tipo bascula de balancín con salida digital GPIO (resolución ≥ 0.2 mm), anemómetro ultrasónico o de cazoletas RS485 Modbus RTU (resolución ≤ 0.1 m/s, rango 0–60 m/s), y piranómetro para medición de radiación solar incidente (BPW34 o equivalente con etapa de acondicionamiento ADC).

**e) Sensor de calidad de aire (PMS5003 o equivalente):**

Sensor de partículas PM2.5/PM10 vía UART a 9600 baud. La concentración PM2.5 > 200 µg/m³ activa automáticamente un flag de invalidación de capturas térmicas y extensiométricas por la duración del evento más un período de *clearance* post-evento configurable (defecto: 4 horas para fumigación, 3 horas para lluvia con aerosol), eliminando mediciones contaminadas sin intervención humana.

**f) Geolocalización y temporización:**

Receptor GPS/GNSS (u-blox NEO-6M o compatible, interfaz UART) para georreferenciación del nodo y determinación automática del hemisferio geográfico (Norte/Sur), lo que permite el ajuste automático de la fecha de reinicio del acumulador GDD. Reloj de tiempo real (RTC DS3231 con batería de respaldo CR2032, deriva ≤ 2 ppm) para timestamping preciso de las sesiones.

**g) Comunicación LoRa:**

Módulo transceptor LoRa 915 MHz (SX1276 o SX1262, Semtech) con antena omnidireccional. Transmisión unidireccional nodo→gateway del payload de telemetría. El nodo abre una ventana de recepción (RX) de 5 segundos inmediatamente posterior a cada transmisión para recibir comandos de downlink del backend (ajuste de varietal, desactivación del actuador de riego en modo de prueba, comandos de irrigación manual de emergencia).

**h) Microcontrolador y procesamiento local:**

ESP32-S3 dual-core Xtensa LX7, 240 MHz, 8 MB Flash, 2 MB PSRAM. Ejecuta localmente: pipeline de procesamiento de imagen térmica (segmentación foliar, cálculo CWSI, fusión multi-angular), motor fenológico GDD, cálculo HSI, auto-calibración dinámica del baseline, control del gimbal, control del actuador de riego (Tier 2–3), y auto-diagnóstico del estado del nodo. Consumo en ciclo de trabajo normal (90 s activo + 810 s *deep sleep* por ciclo de 15 min): ~0.18 W promedio. Consumo en dormancia invernal (1 frame cada 6 h): ~1 µA.

**i) Sistema de energía:**

Panel solar monocristalino o policristalino de 6 W / 6 V con controlador de carga integrado en PCB. Batería LiFePO₄ de 6 Ah (22.2 Wh). Balance energético en condiciones de operación normal: +25.7 Wh/día (margen de generación 6× sobre el consumo).

**j) Actuador de riego (Tier 2–3, opcional):**

Relé de estado sólido (SSR) para 24 VAC / 2 A, controlado por GPIO del microcontrolador, para activación de electroválvula solenoide de riego por goteo de 24 VAC (Rain Bird o equivalente). El relé y el solenoide se integran en el nodo o se conectan vía cableado con conectores IP67. El nodo ejecuta de forma autónoma la decisión de riego según el HSI (ver 4.4), sin requerir instrucción del servidor.

### 4.3 Motor fenológico autónomo (GDD)

El firmware del nodo implementa un motor de acumulación de grados-día (GDD) continuo, basado en la medición de temperatura del sensor SHT31 cada 15 minutos:

```
GDD_acumulados += max(0, (T_max + T_min) / 2 − T_base)
```

donde T_base depende del cultivo configurado: 10 °C para vid (*Vitis vinifera* Malbec, Cabernet Sauvignon, Bonarda, Syrah), 12.5 °C para olivo (*Olea europaea*), 7 °C para arándano (*Vaccinium corymbosum*).

**Reinicio automático del acumulador:** El GPS determina el hemisferio geográfico al inicio de la temporada. En el hemisferio sur el acumulador se reinicia el 1 de agosto de cada año (convención INTA para modelado fenológico de vid, Catania & Avagnina, 2007); en el hemisferio norte, el 1 de febrero. La dormancia se confirma por temperatura media < T_base durante 14 días consecutivos.

**Detección automática de brotación:** Se requiere la convergencia simultánea de dos señales independientes: (1) desviación estándar de temperatura del frame térmico ≥ 0.8 °C durante 3 días consecutivos (indicador de masa foliar emergente); y (2) GDD_acumulados ≥ 80 (umbral mínimo de brotación para Malbec, Catania & Avagnina, 2007). La convergencia dual elimina falsos positivos por días cálidos aislados.

**Cambio automático de coeficientes CWSI por estadio:**

| Estadio | GDD (Malbec) | Coeficientes activos | Acción del sistema |
|---|---|---|---|
| Vegetativo | 0–350 | Set A | Umbrales estándar. Alertas estándar. |
| Floración | 350–550 | Set B | Umbrales conservadores. Estrés en floración causa caída de frutos. |
| Desarrollo | 550–1.100 | Set A (hojas maduras) | Máxima precisión del modelo. |
| Envero | 1.100–1.400 | Set C | ΔT_LL ajustado al alza. Conductancia baja naturalmente, no es estrés hídrico. |
| Pre-cosecha | 1.400–1.900 | Modo RDI | Alerta solo si CWSI > 0.85 o descenso inesperado. |
| Dormancia | T_media < T_base × 14 d | Hibernación | 1 frame cada 6 h. *Heartbeat* LoRa semanal. ~1 µA. |

Este cambio se ejecuta de forma completamente automática, sin intervención del productor, agrónomo ni conexión a internet.

### 4.4 Índice de Estrés Hídrico Compuesto con Confianza Dinámica (HSI)

El HSI (*HydroVision Stress Index*) es la fusión del CWSI (cámara térmica) y el MDS (extensómetro de tronco), con pesos adaptativos que dependen de la velocidad de viento medida en tiempo real:

```
HSI = w_cwsi(v) · CWSI + w_mds(v) · f(MDS)
```

donde:
- Si v_viento ≤ 4 m/s: w_cwsi = 0.35, w_mds = 0.65 (condiciones normales — las 9 capas de mitigación física mantienen el error CWSI en ±0.03)
- Si 4 < v_viento < 18 m/s (14-65 km/h): w_cwsi se reduce linealmente de 0.35 a 0.00 (rampa gradual — el CWSI sigue aportando señal parcial gracias al tubo colimador IR, termopar foliar, orientación a sotavento que reducen el viento efectivo en la hoja a ~30-40% del medido, y mejoras v2: fusión Kalman IR↔termopar, Muller gbh, Hampel filter)
- Si v_viento ≥ 18 m/s (65 km/h): w_cwsi = 0.00, w_mds = 1.00 (exclusión automática de CWSI — viento supera la capacidad de mitigación)

La función f(MDS) convierte la contracción diaria máxima (µm) a una escala normalizada 0–1 equivalente al CWSI, utilizando los umbrales por estadio fenológico y varietal.

**Umbral de confianza por R²(Ψ_stem):** El peso del MDS se ajusta adicionalmente por el coeficiente de correlación histórico R²(MDS→Ψ_stem) del nodo en la temporada en curso. Si R² < 0.6 (sensor degradado o mal calibrado), w_mds se reduce automáticamente y el sistema emite alerta de mantenimiento.

**Control autónomo de riego (Tier 2–3):** El firmware del nodo activa el GPIO del SSR (y por ende el solenoide) cuando HSI ≥ 0.30 durante 2 ciclos consecutivos (30 min), y desactiva cuando HSI ≤ 0.20 durante 2 ciclos consecutivos. Esta histéresis evita ciclos cortos de riego. Si el servidor emite un comando de irrigación de emergencia vía downlink LoRa (campo `command.irrigate`), el nodo activa el riego independientemente del HSI con duración configurada.

### 4.5 Auto-calibración dinámica del baseline CWSI

El cálculo del CWSI requiere los parámetros Tc_wet (temperatura de hoja bien hidratada) y Tc_dry (temperatura de hoja sin transpiración) para las condiciones locales específicas del nodo, que pueden diferir de los coeficientes teóricos de Jackson (1981) hasta ±0.15–0.20 unidades CWSI si no se calibran.

El sistema implementa una calibración dinámica automática de triple nivel:

**Nivel 1 — Panel Wet Ref (primario):** La temperatura del panel Wet Ref físico, medida 96 veces por día, provee la referencia Tc_wet con precisión RMSE < 0.5 °C. Disponible mientras el reservorio de 10 L tenga agua (recarga mensual, autonomía 90–120 días).

**Nivel 2 — Eventos climáticos (fail-safe):** Cuando el pluviómetro registra precipitación ≥ 5 mm y simultáneamente el extensómetro confirma MDS ≈ 0 (planta en máximo estado de hidratación), la temperatura foliar medida por la cámara LWIR en ese instante corresponde al Tc_wet real del nodo para las condiciones ambientales medidas. El sistema captura el par (Tc_medido, T_aire, VPD) y actualiza el offset del baseline mediante promedio móvil exponencial (EMA, learning_rate = 0.25):

```
tc_wet_offset ← 0.75 × tc_wet_offset + 0.25 × (Tc_medido − NWSB(T_aire, VPD))
```

**Nivel 3 — Coeficientes históricos + NWSB (emergencia):** Los coeficientes de Jackson (1981) ajustados por los offsets acumulados en temporadas anteriores (persistidos en JSON local en Flash del ESP32-S3) proveen baseline de emergencia cuando los niveles 1 y 2 no están disponibles.

El nivel de confianza de calibración activo se reporta en cada payload LoRa y se visualiza en el dashboard como indicador de calidad de datos.

### 4.6 Arquitectura PINN embebida (inferencia en el nodo)

En el firmware del ESP32-S3 se ejecuta una red neuronal liviana (MobileNetV3-Tiny o equivalente, cuantizada a INT8 mediante TFLite Micro) cuya función de pérdida de entrenamiento incorpora un término de residuo físico basado en la ecuación de Jackson (1981):

```
L_total = L_datos + λ · L_física
```

donde L_física penaliza predicciones de ΔT_foliar inconsistentes con el balance energético foliar bajo las condiciones meteorológicas instante a instante (T_aire, VPD, radiación). Este término actúa como regularización física, mejorando la generalización con datasets pequeños (≥ 500 frames etiquetados) — condición exacta del TRL 4.

El modelo recibe como entrada el frame térmico segmentado, los datos meteorológicos del ciclo, y las referencias de calibración de los paneles Dry/Wet Ref. La salida es un CWSI refinado y un intervalo de confianza.

En el backend se ejecuta adicionalmente una versión de mayor capacidad del modelo PINN (sin restricciones de memoria) para refinamiento de alta precisión sobre los frames transmitidos, cuyo resultado se fusiona con el CWSI calculado en el nodo y se incorpora al mapa de prescripción.

### 4.7 Fusión nodo-satélite para mapa de lote completo

El sistema implementa un método de calibración cruzada entre el punto de medición del nodo y los píxeles Sentinel-2 (resolución 10–20 m) que cubren el lote:

1. Para cada par temporal (fecha de imagen Sentinel-2 con cobertura de nubes < 20%, medición CWSI del nodo en ±3 días), se extrae del pixel Sentinel-2 correspondiente al nodo: NDWI (bandas B8–B11), NDVI (bandas B8–B4), NDRE (bandas B8A–B5).
2. Se construye un modelo de regresión local (regresión lineal múltiple o regresor en línea actualizable) entre [NDWI, NDVI, NDRE] y CWSI, entrenado con los pares disponibles de la temporada en curso.
3. El modelo calibrado se aplica a todos los píxeles del lote dentro del polígono de la zona asignada al nodo, generando un mapa CWSI de resolución Sentinel-2 para el lote completo.
4. Con 1 nodo de calibración, el método cubre aproximadamente 50 hectáreas en condiciones de variabilidad espacial moderada (CV < 30% en CWSI, Santesteban et al., 2017). En lotes con alta heterogeneidad se recomienda 1 nodo/hectárea.

---

## V. REIVINDICACIONES

### Reivindicación 1 (Independiente — Aparato)

**Nodo sensor autónomo de campo** para la medición continua del estrés hídrico en cultivos perennes, caracterizado por comprender, integrados en una carcasa con protección IP65 y sistema de energía solar autónomo:

(a) una cámara de imagen térmica infrarroja de onda larga (LWIR) con resolución mínima de 32×24 píxeles montada sobre un soporte pan-tilt motorizado de dos ejes con compensación inercial activa mediante unidad de medición inercial (IMU), adaptada para adquirir imágenes térmicas del canopeo vegetal en al menos cinco posiciones angulares fijas por ciclo de medición;

(b) un extensómetro de tronco de alta resolución, comprendiendo un sensor de deformación tipo puente Wheatstone con convertidor analógico-digital de al menos 24 bits y sensor de temperatura para corrección de dilatación térmica, montado en abrazadera sobre el tronco de la planta, para la medición continua de la máxima contracción diaria del tronco (MDS);

(c) un sistema de referencia de calibración dual comprendiendo un panel de superficie seca de alta emisividad térmica (Dry Ref) y un panel de superficie húmeda mantenida saturada mediante un sistema de micro-bomba peristáltica y reservorio de agua, ambos dentro del campo visual de la cámara LWIR, para la determinación directa en campo de los parámetros de temperatura de referencia de la fórmula CWSI;

(d) sensores meteorológicos integrados que comprenden al menos: sensor de temperatura y humedad relativa, pluviómetro de pulso digital, y anemómetro con resolución ≤ 0.5 m/s;

(e) un microcontrolador de bajo consumo programado para ejecutar localmente, sin requerir conectividad a internet: el cálculo del Índice de Estrés Hídrico del Cultivo (CWSI) según la fórmula de Jackson et al. (1981), la fusión multi-angular de frames térmicos, el motor fenológico GDD, el índice de estrés hídrico compuesto (HSI) con confianza dinámica, y la auto-calibración dinámica del baseline de temperatura de referencia; y

(f) un transceptor LoRa para transmisión del payload de telemetría y recepción de comandos de downlink.

### Reivindicación 2 (Dependiente de 1)

El nodo sensor de la reivindicación 1, caracterizado además porque el microcontrolador está programado para calcular el índice de estrés hídrico compuesto (HSI) como combinación lineal ponderada del CWSI y una función del MDS, donde los pesos de ponderación son función continua de la velocidad de viento medida en tiempo real por el anemómetro, de manera que cuando la velocidad de viento supera un umbral configurable (por defecto: 4 m/s), el peso asignado al CWSI térmico se reduce progresivamente hasta cero y el HSI resulta determinado exclusivamente por la medición extensiométrica del tronco, compensando así el sesgo sistemático que introduce el viento sobre la temperatura foliar medida por termografía.

### Reivindicación 3 (Dependiente de 1)

El nodo sensor de la reivindicación 1, caracterizado además porque el microcontrolador está programado para ejecutar un motor de acumulación de grados-día (GDD) continuo a partir de la temperatura medida por el sensor meteorológico integrado, que: (a) reinicia automáticamente el acumulador en la fecha de inicio post-dormancia correspondiente al hemisferio geográfico determinado por el receptor GPS del nodo; (b) detecta automáticamente la ocurrencia de brotación por convergencia simultánea de señal térmica (aumento de varianza espacial del frame LWIR por encima de umbral durante período mínimo configurable) y señal GDD (superación de umbral de grados-día acumulados para la varietal configurada); y (c) aplica automáticamente conjuntos diferenciados de coeficientes CWSI y umbrales de alerta según el estadio fenológico detectado, sin requerir intervención humana ni conectividad.

### Reivindicación 4 (Dependiente de 1)

El nodo sensor de la reivindicación 1, caracterizado además porque el microcontrolador está programado para actualizar dinámicamente el parámetro de temperatura de referencia de hoja bien hidratada (Tc_wet) del cálculo CWSI mediante promedio móvil exponencial, utilizando como evento de calibración la condición simultánea de: precipitación ≥ 5 mm registrada por el pluviómetro y contracción de tronco (MDS) ≈ 0 registrada por el extensómetro, siendo dicha condición indicativa del máximo estado de hidratación de la planta, de modo que la temperatura foliar medida por la cámara LWIR en ese instante constituye la referencia Tc_wet real del nodo para las condiciones ambientales del momento.

### Reivindicación 5 (Dependiente de 1)

El nodo sensor de la reivindicación 1, caracterizado además porque comprende un actuador de riego integrado comprendiendo un relé de estado sólido controlado por GPIO del microcontrolador para la activación de una electroválvula solenoide de riego por goteo, donde el microcontrolador ejecuta la decisión de activación y desactivación del riego de forma autónoma basándose exclusivamente en el HSI calculado localmente, con lógica de histéresis doble configurable para evitar ciclos cortos, sin requerir instrucción del servidor remoto para la operación de riego ordinaria.

### Reivindicación 6 (Dependiente de 1)

El nodo sensor de la reivindicación 1, caracterizado además porque la fusión multi-angular de frames térmicos en el microcontrolador comprende: calcular para cada frame adquirido en las distintas posiciones angulares una fracción foliar definida como la proporción de píxeles cuya temperatura se ubica en el rango del percentil 20 al 75 del histograma térmico del frame; seleccionar los tres frames de mayor fracción foliar; y calcular el CWSI de ciclo como la mediana ponderada por fracción foliar de los valores CWSI individuales de los tres frames seleccionados.

### Reivindicación 7 (Dependiente de 1)

El nodo sensor de la reivindicación 1, caracterizado además porque comprende un sistema de limpieza autónoma de la ventana óptica de la cámara LWIR mediante transductor piezoeléctrico actuado por GPIO del microcontrolador, programado para ejecutarse automáticamente al inicio de cada ciclo de medición y ante la detección de contaminación óptica por el procedimiento de auto-diagnóstico integrado en el firmware.

### Reivindicación 8 (Dependiente de 1)

El nodo sensor de la reivindicación 1, caracterizado además porque el firmware del microcontrolador implementa un modo de hibernación invernal activado automáticamente al detectar temperatura media inferior a la temperatura base del cultivo configurado durante un período mínimo de 14 días consecutivos, en el que la frecuencia de captura de imagen térmica se reduce a un frame cada 6 horas, la transmisión LoRa se reduce a un heartbeat semanal, y el consumo eléctrico cae a valores de orden 1 µA, con reinicio automático de la operación normal en la temporada siguiente.

### Reivindicación 9 (Independiente — Método)

**Método de calibración nodo-satélite** para la generación de mapas de estrés hídrico de lote completo en cultivos a partir de un único nodo sensor de campo, caracterizado por comprender los pasos de:

(a) para cada imagen disponible del satélite Sentinel-2 con porcentaje de cobertura de nubes inferior a un umbral configurable sobre el lote objetivo, extraer los valores de reflectancia de las bandas espectrales correspondientes a los índices NDWI, NDVI y NDRE para el píxel Sentinel-2 coincidente con las coordenadas GPS del nodo de campo;

(b) obtener el valor de CWSI medido por el nodo de campo en la fecha de la imagen Sentinel-2 correspondiente, dentro de una ventana temporal configurable;

(c) construir un modelo de regresión entre los índices espectrales Sentinel-2 extraídos y el CWSI medido por el nodo, actualizado de forma incremental a medida que se acumulan nuevos pares (imagen Sentinel-2, CWSI nodo) durante la temporada;

(d) aplicar el modelo de regresión calibrado a todos los píxeles Sentinel-2 dentro del polígono georreferenciado del lote, generando un mapa de CWSI estimado de resolución Sentinel-2 (10–20 m) para el lote completo; y

(e) combinar el mapa CWSI Sentinel-2 con el CWSI puntual del nodo mediante interpolación ponderada por distancia inversa (IDW) para generar el mapa de prescripción de riego final.

### Reivindicación 10 (Independiente — Sistema)

**Sistema integrado de monitoreo y control autónomo del estrés hídrico en cultivos** caracterizado por comprender:

(a) al menos un nodo sensor autónomo de campo según cualquiera de las reivindicaciones 1 a 8;

(b) al menos un gateway LoRa para la recepción de los payloads de telemetría de los nodos y su retransmisión al servidor de procesamiento;

(c) un servidor de procesamiento que implementa: inferencia de red neuronal informada por física (PINN) sobre los frames térmicos transmitidos por los nodos, el método de calibración nodo-satélite según la reivindicación 9, y un sistema de visualización web y/o móvil con mapas de prescripción de riego actualizables para el productor; y

(d) un protocolo de comunicación bidireccional entre el servidor y los nodos vía downlink LoRa, que permite al servidor transmitir a cada nodo: la varietal y estadio fenológico confirmado, comandos de riego de emergencia, y la habilitación o deshabilitación del actuador físico de riego.

---

## VI. RESUMEN DE LA INVENCIÓN

Sistema autónomo para el monitoreo continuo y el control de riego en cultivos, comprendiendo un nodo de campo con cámara de imagen térmica infrarroja LWIR sobre gimbal pan-tilt con compensación inercial, extensómetro de tronco de 24 bits con corrección térmica, sistema de referencia de calibración dual (paneles Dry Ref/Wet Ref), sensores meteorológicos integrados, y microcontrolador ESP32-S3 que ejecuta localmente el cálculo del CWSI, un índice de estrés hídrico compuesto (HSI) con pesos adaptativos según velocidad de viento, un motor fenológico autónomo por grados-día acumulados (GDD) con cambio automático de coeficientes sin intervención humana, auto-calibración dinámica del baseline por eventos climáticos y extensiometría, y control autónomo de riego por solenoide. El sistema incluye un método de calibración nodo-satélite que extiende la cobertura de un único nodo a aproximadamente 50 hectáreas mediante fusión con imágenes Sentinel-2. Opera sin conectividad permanente a internet, con autonomía solar de 120+ horas, a consumo promedio de 0.18 W en operación normal.

---

## VII. BREVE DESCRIPCIÓN DE LAS FIGURAS

*(Las figuras se prepararán como ilustraciones técnicas para la presentación formal ante INPI.)*

- **Figura 1:** Vista general del nodo de campo con indicación de componentes principales (cámara LWIR, gimbal, paneles Dry/Wet Ref, extensómetro, carcasa IP65, panel solar).
- **Figura 2:** Diagrama de bloques del hardware del nodo (MCU, sensores, actuadores, interfaces).
- **Figura 3:** Diagrama de flujo del firmware: ciclo de medición, cálculo CWSI, HSI, motor GDD, decisión de riego.
- **Figura 4:** Diagrama del sistema de calibración dual y la auto-calibración dinámica del baseline.
- **Figura 5:** Diagrama del método de calibración nodo-satélite Sentinel-2 para mapa de lote completo.
- **Figura 6:** Arquitectura del sistema completo: nodo → gateway LoRa → backend → dashboard.

---

## VIII. NOTAS PARA XIMENA CRESPO (AGENTE PI)

### Prioridades de protección

1. **Reivindicación 2 (HSI con confianza dinámica por viento):** Mayor novedad absoluta — no tiene anterioridad documentada en ninguna base consultada. Esta es la reivindicación más fuerte y diferenciadora.

2. **Reivindicación 3 (Motor fenológico GDD autónomo en nodo edge):** Sin anterioridad en nodo embebido. Los sistemas de GDD existentes son todos de servidor/nube.

3. **Reivindicación 4 (Auto-calibración Tc_wet por evento lluvia + MDS):** El uso del extensómetro para calibrar la cámara térmica es un enfoque original sin documentar.

4. **Reivindicación 1 (Aparato — combinación LWIR + extensómetro + dual Ref + IMU en nodo fijo):** La combinación es la clave; cada componente individual existe en la literatura pero su integración en nodo autónomo fijo es inédita.

### Diferenciación respecto al prior art conocido

| Prior Art | Diferencia central |
|---|---|
| AquaSense (2025) | AquaSense: sensor suelo primario. HydroVision: señal foliar primaria (LWIR + extensómetro) |
| WISN (2023) | WISN: termómetro puntual IR. HydroVision: imagen térmica completa + segmentación + gimbal |
| US 11,195,015 | Cubre análisis aéreo en nube. HydroVision: nodo fijo terrestre, inferencia edge, sin nube |
| Trimble/Netafim | Sensor suelo. Sin termografía foliar. Sin fenología automática. Sin PINN. |

### Elementos a excluir de la solicitud (trade secrets)

Los siguientes elementos NO deben incluirse en la solicitud de patente — se protegen como secreto comercial bajo NDA:
- Valores numéricos específicos de coeficientes CWSI calibrados por variedad (Malbec Cuyo, Cabernet, Syrah, Olivo)
- Hiperparámetros λ del término de pérdida física PINN
- Parámetros de cuantización INT8 del modelo embebido
- Pipeline de síntesis de imágenes térmicas sintéticas (simulador físico)

### Acción inmediata recomendada

1. Revisar reivindicaciones 1–10 y ajustar el alcance según criterio de patentabilidad INPI
2. Confirmar búsqueda de anterioridad extendida en WIPO/PCT y CNIPA (China)
3. Preparar figuras técnicas (César/Lucas proveen diagramas fuente)
4. Iniciar trámite en TAD (Trámites a Distancia) — plataforma INPI Argentina
5. Calcular aranceles vigentes para patente de invención nacional

### Referencias científicas clave para el examinador

- Jackson et al. (1981) — fórmula CWSI, Water Resources Research 17(4)
- Araújo-Paredes et al. (2022) — validación termografía LWIR en vid, Sensors 22, 8056
- Pires et al. (2025) — segmentación U-Net++ para CWSI, Computers and Electronics in Agriculture 239
- Zhou et al. (2022) — termografía LWIR terrestre fija, validación CWSIe vs. CWSIs, Agronomy 12
- Fernández & Cuevas (2010) — extensómetro tronco vs. Ψ_stem, Agricultural Water Management
- Santesteban et al. (2017) — variabilidad espacial CWSI en lote, justifica red nodos, Agricultural Water Management 183
