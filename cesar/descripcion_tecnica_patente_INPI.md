# DESCRIPCION TECNICA PARA SOLICITUD DE PATENTE DE INVENCION
## INPI Argentina -- HydroVision AG SAS
### Documento base para Ximena Crespo (Arteaga & Asociados)

> **Instrucciones para Ximena:** Este documento contiene la descripcion tecnica completa del sistema. Usarlo como base para redactar las reivindicaciones legales (claims). Las secciones "Reivindicacion sugerida" son orientativas -- Ximena define el alcance legal final. Cesar Schiavoni disponible para consultas tecnicas.

---

## TITULO DE LA INVENCION

**"Sistema y metodo autonomo para la estimacion en tiempo real del estado hidrico de cultivos mediante fusion de termografia infrarroja, dendrometria de tronco y red neuronal informada por fisica (PINN), con motor fenologico automatico y calibracion satelital integrada"**

### Titulo alternativo (mas corto):

**"Nodo sensor autonomo para deteccion de estres hidrico en cultivos mediante indice HSI con termografia, dendrometria y PINN"**

---

## CAMPO TECNICO DE LA INVENCION

La presente invencion se refiere al campo de la agricultura de precision, y mas particularmente a un sistema y metodo autonomo para la deteccion en tiempo real del estres hidrico en cultivos de alto valor (vid, olivo, cerezo, pistacho, nogal, citrus, arandano) mediante la fusion de multiples senales fisiologicas y ambientales procesadas por inteligencia artificial con restricciones fisicas embebidas.

---

## ANTECEDENTES DE LA INVENCION

### Problema tecnico

Los productores de cultivos de alto valor bajo riego pierden entre el 15% y el 35% del rendimiento por campana debido a estres hidrico detectado tardiamente. Los metodos existentes presentan limitaciones criticas:

1. **Tensiometros de suelo:** Miden humedad del suelo, no el estado fisiologico de la planta. Desfase de 2-5 dias entre suelo seco y dano metabolico foliar.

2. **Imagenes satelitales (Sentinel-2, Landsat):** Resolucion espacial insuficiente (10-30 m/px), mezcla suelo+planta, dependencia de condiciones de nubosidad (8-15 dias sin dato), no detectan estres foliar directo.

3. **Drones con camara termica:** Requieren operador certificado (ANAC en Argentina), condiciones climaticas especificas, frecuencia limitada a 1-2 vuelos/semana.

4. **Observacion visual:** El productor detecta marchitez 5-10 dias despues del dano fisiologico real.

5. **CWSI termico solo (estado del arte):** Alcanza R^2 = 0.62-0.67 vs potencial hidrico de tallo (psi_stem) segun literatura (Bellvert et al. 2016). Sensible a viento (enfriamiento convectivo artificial, Jones 2004). No suficiente para automatizar riego.

6. **Dendrometria sola (MDS):** R^2 = 0.80-0.92 (Fernandez & Cuevas 2010) pero respuesta lenta a cambios rapidos, sensible a temperatura del tronco, requiere correccion termica.

Ninguna solucion existente combina termografia foliar + dendrometria de tronco + motor fenologico + red neuronal con restriccion fisica + calibracion satelital en un unico nodo autonomo de campo.

---

## DESCRIPCION DETALLADA DE LA INVENCION

### Elemento 1: Nodo sensor autonomo de campo

Un dispositivo de hardware autonomo que comprende:

- **Unidad de procesamiento:** microcontrolador ESP32-S3 con conectividad LoRa (SX1276, 915 MHz)
- **Sensor termico infrarrojo:** MLX90640 (32x24 pixeles, NETD ~100 mK, FOV 110x75 grados, banda LWIR 8-14 um) montado sobre gimbal motorizado de 2 ejes (2x servos MG90S) que captura en 5 posiciones angulares fijas para cobertura multi-angular del canopeo
- **Dendrometro de tronco:** sensor strain gauge acoplado a ADC de 24 bits (ADS1231) con resolucion de 1 um y correccion termica mediante sensor DS18B20 (coeficiente de compensacion alpha = 2.5 um/C), montado en abrazadera de aluminio anodizado a 30 cm de altura en la cara norte del tronco
- **Sensores meteorologicos:** temperatura y humedad relativa del aire (SHT31), anemometro de copas (RS485 Modbus RTU), piranometro (BPW34 ADC), pluviometro de balancin (ISR con debounce), sensor de particulas PM2.5 (PMS5003 UART)
- **Referencias termicas duales:** panel de referencia seca (Dry Ref: aluminio negro mate, emisividad 0.98) y panel de referencia humeda (Wet Ref: fieltro hidrofilico con micro-bomba peristaltica de recarga) para calibracion del indice de Jones (Ig)
- **Sistema de energia:** bateria LiFePO4 6Ah + panel solar 6W + controlador MPPT, con ciclo de deep sleep (consumo ~8 uA) y watchdog TPL5010 externo
- **GPS:** u-blox NEO-6M para geolocalizacion y determinacion automatica de hemisferio

**Reivindicacion sugerida 1:** Un nodo sensor autonomo de campo que integra en un unico dispositivo: (a) camara termica infrarroja sobre gimbal multi-angular, (b) dendrometro de tronco de alta resolucion con correccion termica, (c) anemometro para determinacion de confianza dinamica de la senal termica, (d) referencias termicas duales (seca y humeda) para calibracion autonoma, y (e) sistema de energia solar con gestion de potencia ultra-baja.

### Elemento 2: Indice HSI (HydroVision Stress Index) -- fusion de senales

Un indice compuesto que fusiona dos senales fisiologicas complementarias:

```
HSI = w_cwsi * CWSI + w_mds * MDS_normalizado
```

Donde:
- **CWSI** (Crop Water Stress Index, Jackson et al. 1981) se calcula a partir de la diferencia entre temperatura foliar (medida por MLX90640) y temperatura del aire (SHT31), normalizada por los limites biofisicos del cultivo (dT_LL y dT_UL, funcion del VPD)
- **MDS** (Maximum Daily Shrinkage) se obtiene de la micro-contraccion diaria del tronco medida por el dendrometro (D_max - D_min en um), normalizado a [0, 1] por correlacion con psi_stem

**Mecanismo de confianza dinamica con mitigacion multinivel (novedad):** El sistema implementa 9 capas de defensa contra el artefacto de viento: (1) orientacion a sotavento — camara apunta al lado opuesto al viento dominante, plantas como barrera (~60-70% reduccion); (2) shelter anti-viento SHT31; (3) tubo colimador IR (PVC 110mm x 250mm); (4) termopar foliar Type T 0.1mm — ground truth por contacto, correccion IR en tiempo real; (5) buffer termico con filtro de calma (5 muestras, mediana con viento <2 m/s). Los pesos w_cwsi y w_mds se ajustan automaticamente con rampa gradual:
- Viento ≤ 4 m/s: w_cwsi = 0.35, w_mds = 0.65 (pesos nominales — las capas fisicas mantienen error CWSI en ±0.03)
- Viento 4-12 m/s (14-43 km/h): w_cwsi se reduce linealmente de 0.35 a 0 (rampa gradual)
- Viento ≥ 12 m/s (43 km/h): w_cwsi = 0, w_mds = 1.0 (conmutacion total a dendrometria)

Esto resuelve el principal artefacto del CWSI termico: el enfriamiento convectivo artificial de la hoja por viento, que produce subestimacion del estres (Jones 2004). El rango util del CWSI se extiende de 0-4 m/s a 0-8 m/s gracias a las mitigaciones fisicas.

**Reivindicacion sugerida 2:** Un metodo para estimar el estado hidrico de un cultivo que comprende: (a) calcular un indice termico (CWSI) a partir de imagenes infrarrojas de la hoja, (b) calcular un indice dendrometrico (MDS) a partir de micro-contracciones del tronco, y (c) fusionar ambos indices con pesos que se ajustan automaticamente segun la velocidad del viento medida en tiempo real, de modo que cuando el viento supera un umbral predeterminado, el peso del indice termico se reduce a cero y la estimacion se basa exclusivamente en la dendrometria.

### Elemento 3: Red neuronal informada por fisica (PINN)

El modelo de IA no es una "caja negra" convencional. La funcion de perdida incorpora la ecuacion fisica del CWSI como restriccion (physics constraint):

```
L_total = MSE(CWSI_pred, CWSI_real) + lambda * ||CWSI_pred - f(dT_pred, VPD)||^2
```

Donde f() es la ecuacion de Jackson et al. (1981):
```
f(dT, VPD) = (dT - dT_LL(VPD)) / (dT_UL - dT_LL(VPD))
```

El termino lambda penaliza predicciones que violan el balance energetico foliar. Esto garantiza:
- Predicciones fisicamente coherentes (CWSI nunca fuera del rango [0, 1])
- Mejor generalizacion con pocos datos reales de campo (680 frames)
- Robustez ante condiciones climaticas no vistas en el entrenamiento

**Arquitectura:** MobileNetV3-Tiny backbone con cabeza de regresion, cuantizado a INT8 para inferencia en edge (ESP32-S3).

**Reivindicacion sugerida 3:** Un metodo de entrenamiento de un modelo de inteligencia artificial para estimacion de estres hidrico que incorpora como restriccion en la funcion de perdida la ecuacion del balance energetico foliar (Jackson et al. 1981), de modo que el modelo no puede generar predicciones que violen las leyes de la termodinamica aplicables a la transpiracion vegetal.

### Elemento 4: Motor fenologico automatico (GDD)

El nodo determina automaticamente el estadio fenologico del cultivo mediante grados-dia acumulados (GDD):

```
GDD = sum(max(0, (T_max + T_min)/2 - T_base))
```

Con T_base especifica por cultivo (vid: 10C, olivo: 12.5C, arandano: 7C, etc.). El sistema:
- Reinicia el acumulador automaticamente segun hemisferio (GPS) y tipo de cultivo
- Detecta brotacion por convergencia de senal termica + GDD
- Cambia automaticamente los coeficientes CWSI por estadio (5 sets de coeficientes)
- Entra en modo hibernacion invernal (1 uA) y despierta automaticamente

**Reivindicacion sugerida 4:** Un sistema que ajusta automaticamente los coeficientes de un modelo de estres hidrico en funcion del estadio fenologico del cultivo, determinado en tiempo real mediante grados-dia acumulados calculados por el propio sensor de temperatura del nodo, sin intervencion humana ni configuracion manual.

### Elemento 5: Auto-calibracion del baseline termico

El sistema se auto-calibra sin visita humana:
- Cada evento de lluvia con MDS ~ 0 (tronco completamente rehidratado) actualiza el baseline Tc_wet
- Media movil exponencial (EMA, learning_rate = 0.25) para estabilidad
- Persistencia en JSON ante reinicio del nodo

**Reivindicacion sugerida 5:** Un metodo de auto-calibracion de un sensor termico de campo que utiliza la convergencia de dos senales independientes (micro-contraccion del tronco cercana a cero y precipitacion registrada por pluviometro) para identificar automaticamente condiciones de referencia (planta sin estres) y actualizar los parametros de calibracion del modelo sin intervencion humana.

### Elemento 6: Fusion con imagenes satelitales (Sentinel-2)

El nodo proporciona CWSI preciso en un punto; Sentinel-2 (gratuito, cada 5 dias, 10 m/px) proporciona cobertura espacial de todo el lote. Un modelo de correlacion CWSI <-> NDWI permite que un solo nodo calibre el satelite para 50+ ha.

**Reivindicacion sugerida 6:** Un metodo para generar mapas de estres hidrico de un lote completo que comprende: (a) obtener una medicion de estres hidrico precisa en un punto del lote mediante un nodo sensor terrestre, (b) obtener una imagen satelital multibanda del lote, (c) calcular un modelo de correlacion entre el indice de estres del nodo y un indice de vegetacion satelital, y (d) aplicar dicho modelo a todo el lote para generar un mapa espacial de estres hidrico calibrado.

### Elemento 7: Motor de alertas agronomicas

El sistema genera automaticamente 12+ tipos de alertas derivadas de los sensores:
- Estres hidrico (3 niveles: leve/moderado/severo)
- Helada tardia (con deteccion de brotes presentes)
- Estres calorico
- Riesgo de botrytis y mildiu (condiciones ambientales)
- Prediccion de fenologia (floracion, envero, cosecha)
- Ventana de desbrote
- PHI de fungicidas
- Horas de frio acumuladas
- Estado del nodo (bateria, lente, offline)

---

## RESUMEN DE REIVINDICACIONES SUGERIDAS

1. Nodo sensor integrado (termica + dendrometria + meteo + gimbal + referencias duales + solar)
2. Fusion HSI con confianza dinamica por viento
3. PINN con restriccion fisica en funcion de perdida
4. Motor fenologico automatico con cambio de coeficientes CWSI
5. Auto-calibracion sin intervencion humana (lluvia + MDS = 0)
6. Fusion nodo-satelite para mapeo de lote completo
7. Combinacion de todos los elementos anteriores en un sistema integrado

**Reivindicaciones dependientes posibles:**
- Control automatico de riego basado en HSI con histeresis (0.30/0.20)
- Cuantizacion INT8 del modelo PINN para inferencia en microcontrolador
- Deteccion automatica de fumigacion por PM2.5 con invalidacion de capturas
- Diagnostico automatico de integridad optica (ISO_nodo)

---

## DIBUJOS (a generar)

1. Diagrama de bloques del nodo sensor (componentes + conexiones)
2. Diagrama de flujo del algoritmo HSI (fusion CWSI + MDS + viento)
3. Diagrama de la arquitectura PINN (backbone + physics loss)
4. Diagrama del motor fenologico (GDD -> estadio -> coeficientes CWSI)
5. Diagrama de fusion nodo-satelite (CWSI punto + NDWI mapa -> mapa HSI)
6. Vista del nodo en campo (foto o render)

---

## CLASIFICACION INTERNACIONAL DE PATENTES (IPC) SUGERIDA

- **A01G 25/16** - Control de riego
- **G06N 3/08** - Redes neuronales (entrenamiento)
- **G01N 25/72** - Investigacion termica de materiales
- **G06T 7/00** - Analisis de imagen
- **G01B 7/16** - Medicion de deformaciones (strain gauges)

---

## ESTADO DEL ARTE vs NOVEDAD

| Aspecto | Estado del arte | HydroVision AG (novedad) |
|---------|----------------|--------------------------|
| Senal unica | CWSI termico O dendrometria O tensiometro | Fusion CWSI + MDS en un nodo |
| Confianza por viento | No existe | Conmutacion automatica CWSI -> MDS |
| Modelo IA | Caja negra (CNN/LSTM) | PINN con ecuacion fisica embebida |
| Calibracion | Manual (Scholander periodico) | Auto-calibracion por lluvia + MDS=0 |
| Fenologia | Configuracion manual del usuario | Motor GDD automatico sin configuracion |
| Cobertura espacial | Solo nodo O solo satelite | Fusion nodo-satelite calibrada |
| Autonomia | Dependiente de baterias o cableado | Solar + deep sleep + watchdog |

---

> **Para Ximena:** Cesar puede generar los dibujos tecnicos (diagramas de bloques, flujo) con Claude Code cuando los necesites. Avisar con 1 semana de anticipacion para prepararlos en formato INPI.
