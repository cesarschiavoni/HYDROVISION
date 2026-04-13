
### 11A. Qué es y para qué sirve cada componente de la fila experimental

El objetivo en una línea

Sacarle fotos térmicas a las vides bajo distintos niveles de sed y al mismo tiempo medir exactamente qué tan sedientas están. Así el modelo aprende a "ver" el estrés hídrico antes de que la planta lo muestre visualmente.

Nota clave sobre los nodos: el viñedo experimental cuenta con 5 nodos permanentes (uno por zona de régimen hídrico), cada uno montado en un bracket fijo de acero sobre poste espaldera. Los nodos operan de forma continua 24/7 capturando 7 ángulos gimbal × 96 ciclos/día. Los brackets adicionales (32 en total) son soportes fijos de acero (USD 12 cada uno) que permiten posiciones de captura complementarias. En el producto comercial, el productor instala un solo nodo permanente por zona que opera de forma completamente autónoma.

Componentes de la fila y función de cada uno

La fila de 136m dividida en 5 zonas hídricas de 27m

Las 136 vides se dividen en 5 grupos de ~27 plantas. Cada grupo recibe una cantidad diferente de agua a propósito, generando un rango completo de niveles de estrés en una sola sesión:

Zona A (0–27m): Riego normal completo — planta sana, referencia. CWSI 0.05–0.20.
Zona B (27–54m): 65% del riego normal — estrés leve. CWSI 0.25–0.40.
Zona C (54–81m): 40% del riego normal — estrés moderado. CWSI 0.45–0.60.
Zona D (81–109m): 15% del riego normal — estrés fuerte. CWSI 0.65–0.85.
Zona E (109–136m): Sin riego — estrés máximo. CWSI 0.85–1.00.

Sin esta variedad de condiciones, el modelo solo vería plantas sanas y no aprendería a detectar ni graduar el estrés.

Protocolo de rescate hídrico — protección del viñedo experimental

El diseño experimental incluye un protocolo de corte obligatorio para prevenir daño permanente al viñedo, definido y supervisado por la Dra. Monteoliva (INTA-CONICET):

Criterios de rescate (cualquiera activa riego de emergencia inmediato en la zona afectada):
· ψ_stem < −1,5 MPa medido con bomba de Scholander en cualquier planta de Zona D o E.
· Temperatura foliar > 42°C sostenida por más de 30 minutos en condiciones de VPD normal.
· 14 días consecutivos sin precipitación ni riego en Zona E durante diciembre–febrero.

Restricciones permanentes del protocolo:
· Zona E (sin riego) nunca se aplica durante floración (estadio fenológico GDD 280–420). El aborto floral por estrés severo es irreversible en esa temporada.
· El período máximo de estrés total (Zona E) es de 14 días entre sesiones de medición. Al completar la sesión, se restablece un riego de recuperación mínimo antes de iniciar el siguiente ciclo de estrés.
· Las zonas de estrés severo (D y E) rotan entre filas en distintas temporadas para que ninguna fila acumule daño permanente por repetición.

Base científica: ψ_stem < −1,5 MPa sostenido por más de 3–5 días puede generar embolia en xilema de tejido lignificado (daño parcialmente irreversible). El umbral de corte −1,5 MPa está por encima del rango de daño permanente documentado para Malbec (< −2,0 MPa según Pires et al. 2025 y Chaves et al. 2010). Las mediciones Scholander realizadas por Javier y Franco Schiavoni bajo supervisión de la Dra. Monteoliva son el sistema de alerta temprana que activa el rescate.

Cinta de goteo y solenoides

La cinta de plástico con emisores de 2L/hora corre pegada al suelo a lo largo de toda la fila. Los solenoides son válvulas eléctricas — una por zona, 5 en total — que el controlador Rain Bird abre o cierra automáticamente. Cada zona recibe exactamente la cantidad de agua planificada sin intervención manual.

Tensiómetros

Una sonda enterrada en el suelo por zona. Confirma que el régimen hídrico de cada zona es el esperado. Sus lecturas se registran en cada sesión como dato de respaldo.

Brackets con gimbal — 7 puntos cada 15 metros

Soportes de acero inoxidable atornillados a los postes de espaldera. El asistente encaja el nodo prototipo en cada bracket — rótula ajustable, reproducibilidad geométrica garantizada — a 0.8 metros del suelo apuntando al dosel a 40 grados. El gimbal motorizado gira automáticamente y captura 7 ángulos distintos antes de que el asistente avance al siguiente bracket. 7 brackets × 7 ángulos = 49 fotos por ventana horaria, toda la fila en 21 minutos.

Paneles de referencia de emisividad

Chapas de 15×15cm de negro mate (ε = 0.98 conocido) clavadas al lado de cada bracket. Aparecen en el borde de cada foto. Permiten corregir automáticamente cualquier deriva térmica de la cámara entre sesiones — equivalente a calibrar una balanza antes de pesar.

Estacas numeradas por vid

Cada vid tiene un número. Permite rastrear la misma planta a lo largo de los meses y correlacionar su temperatura con su nivel de estrés medido en distintos momentos de la temporada.

Túneles plásticos de exclusión de lluvia

Cubiertas transparentes sobre las zonas C y D. Si llueve, el agua no altera el régimen hídrico controlado de esas zonas. Se retiran 2 horas antes de cada sesión para no afectar la temperatura del dosel.

Cómo es una sesión de medición

Los 5 nodos están instalados de forma permanente, uno por zona hídrica — no se mueven en ningún momento del proyecto. El gimbal de cada nodo barre automáticamente 7 ángulos cada 15 minutos, 24/7. El asistente de campo no mueve ni reconfigura los nodos durante las sesiones.

Condición previa: lluvia reciente abre los estomas y equilibra el ψ_stem artificialmente hacia cero — la medición dejaría de representar el estrés real del régimen asignado. El pluviómetro del nodo registra la lluvia acumulada automáticamente. Umbral adaptado a Colonia Caroya (pedemonte cordobés, suelo limoso-arenoso, ETP alta, lluvias convectivas de verano):
— < 5 mm en las últimas 48hs: sin restricción — lluvia no significativa, sesión procede normalmente.
— 5–10 mm en las últimas 48hs: si la temperatura fue > 30°C en los días posteriores a la lluvia, el suelo ya drenó y la sesión puede realizarse a partir de las 36hs. Si T° ≤ 30°C: esperar las 48hs completas.
— > 10 mm en las últimas 48hs: reprogramar a +48hs mínimo.
— > 20 mm en las últimas 48hs: reprogramar a +72hs mínimo independientemente de la temperatura.

La noche anterior: verificar en el dashboard que los 5 nodos tienen D_max registrado (diámetro de tronco en máximo de recuperación nocturna, capturado automáticamente entre 5–6am). Anotar D_max de cada zona en la planilla.

Entre 10hs y 14hs — medición Scholander + verificación dendrométrica: el asistente recorre los 5 nodos fijos en secuencia. En cada nodo: (1) verifica en la app que el nodo está activo y el gimbal está capturando; (2) toma la lectura Scholander en la vid de referencia de esa zona (pasos 31–37); (3) anota el D_min parcial del día visible en el dashboard. El frame térmico asociado a cada lectura Scholander es el que el nodo capturó en ese intervalo de 15 min — sincronización automática.

A las 16hs: registrar D_min definitivo de cada nodo en la planilla (MDS del día = D_max − D_min, calculado automáticamente por el nodo y visible en el dashboard).

Resultado de una sesión: 5 lecturas Scholander × 1 frame térmico sincronizado = 5 pares calibrados directos por sesión. Con 4 sesiones OED: 20 pares Scholander directos + miles de frames etiquetados con ψ_stem estimado por MDS (captura continua 24/7) — supera con margen el target de 800 frames de entrenamiento + 120 de validación independiente.

#### 11A.1 Paso a paso del técnico de campo — Protocolo operativo completo

FASE 1 — Instalación del viñedo experimental (Mes 1–2, ~30 horas totales)

Semana 0 — Instalación del sistema de bombeo y tablero hidráulico:

DIAGRAMA OPERATIVO DEL SISTEMA DE RIEGO
(leer antes de instalar — referencia permanente en el tablero)

MODO LLENADO — durante turno de canal:

  CANAL
    |
    |--[ FILTRO MALLA ]--[ Vf ABIERTA ]--[ BOMBA ]---> TANQUE 20.000 L
                                                           (boya corta sola)
    Vr CERRADA — Rain Bird apagado — M1 M2 M3 M4 CERRADAS

MODO RIEGO — desde tanque acumulado:

  TANQUE 20.000 L
    |
    |--[ Vr ABIERTA ]--[ BOMBA ]--[ PRESOSTATO ]---> HEADER PRINCIPAL
         Vf CERRADA                                        |
                                          .________________|________________.
                                          |        |        |               |
                                     [M1+R1]  [M2+R2]  [M3+R3]        [M4+R4]
                                       FILA1    FILA2    FILA3           FILA4
                                          |        |        |               |
                                     [A][B][C] [A][B][C] [A][B][C]   [A][B][C]
                                     [D][E]    [D][E]    [D][E]      [D][E]
                                     solenoides Rain Bird (20 en total)

REFERENCIA RAPIDA — VALVULAS A OPERAR:

  Quiero...                    Abrir          Cerrar
  -------------------------------------------------------
  Llenar tanque               Vf + BOMBA     Vr, M1-M4
  Regar todas las filas       Vr + M1+M2+M3+M4   Vf
  Regar solo fila 2           Vr + M2        Vf, M1, M3, M4
  Regar filas 1 y 3           Vr + M1+M3     Vf, M2, M4
  Mas agua en fila 1          Girar R1 a la izquierda (mas caudal)
  Menos agua en fila 3        Girar R3 a la derecha (menos caudal)

  NUNCA abrir Vf y Vr al mismo tiempo.
  El Rain Bird controla los solenoides A-E automaticamente segun el programa.


0a. Instalar tanque australiano 20.000 L en ubicación fija. Conectar válvula de boya para llenado automático.
0b. Instalación eléctrica (requiere electricista matriculado para conexión al medidor EPEC):
    · Instalar disyuntor bipolar 10A en el tablero del medidor EPEC como primer punto de protección del circuito.
    · Tender cable IRAM 2×4mm² desde el medidor hasta el tablero de bomba (70m). Enterrar en caño corrugado a mínimo 40cm de profundidad, o fijar en canaleta sobre pared/poste fuera del alcance de maquinaria y personal.
    · Instalar disyuntor termomagnético 10A en el tablero de bomba como protección del motor.
    · Montar bomba Pedrollo 1HP sobre base de hormigón o estructura metálica nivelada. Conectar presostato y manómetro.
    · IMPORTANTE: no usar cable 2.5mm² — a 70m la caída de tensión supera el 3% admisible para motores y reduce su vida útil. Cable mínimo: 4mm².
0c. Instalar en el tablero hidráulico las dos válvulas de compuerta de modo:
    · Vf (LLENADO): canal → bomba → tanque. Abrir solo durante turno de canal. Tiempo de llenado: ~5.5 hs para 20.000 L.
    · Vr (RIEGO): tanque → bomba → header. Abrir solo durante riego. Nunca abrir Vf y Vr al mismo tiempo.
0d. Etiquetar claramente ambas válvulas en el tablero: "LLENADO — abrir durante turno de canal" y "RIEGO — abrir para regar". Colocar cartel: "NUNCA ABRIR LAS DOS A LA VEZ".
0e. Instalar una válvula esfera bronce 1" por fila en los ramales del header (M1, M2, M3, M4). Etiquetar: "FILA 1", "FILA 2", etc. Estas válvulas permiten seleccionar qué filas reciben agua en cada sesión de riego.
0f. Instalar un regulador de caudal inline 16mm aguas abajo de cada válvula de fila (R1, R2, R3, R4). Marcar la escala con rotulador permanente: posición completamente abierta = 100% caudal.

Semana 1 — Tendido de cinta drip y solenoides:
1. Marcar con estacas de colores los límites de las 5 zonas en cada fila: 0m, 27m, 54m, 81m, 109m, 136m.
2. Tender la cinta drip 16mm a lo largo de cada fila pegada al pie de las vides, asegurada con ganchos al suelo cada 2 metros.
3. Conectar la cinta al ramal de fila aguas abajo del regulador de caudal Ri correspondiente.
4. Instalar un solenoide 24VAC en el punto de inicio de cada zona (5 por fila × 4 filas = 20 solenoides). Etiquetar cada solenoide con cinta adhesiva: fila número + zona letra (ej. F1-A, F1-B, etc.).
5. Conectar el cable de 2 hilos de cada solenoide al controlador Rain Bird ESP-ME3 en el tablero central. Conexión por zona en paralelo: todos los solenoides A (F1-A, F2-A, F3-A, F4-A) al canal 1 del Rain Bird; todos los B al canal 2; etc.
6. Programar el Rain Bird: Zona A = 100% ETc referencia, B = 65%, C = 40%, D = 15%, E = 0 (cerrado). Duración inicial estimada: consultar con Monteoliva según datos meteorológicos locales del primer mes.

Semana 1 — Prueba de caudales:
7. Modo riego: abrir Vr, cerrar Vf. Abrir M1, cerrar M2+M3+M4. Abrir solenoide Zona A de la Fila 1 durante 10 minutos. Caminar la fila y verificar que cada emisor gotea. Registrar emisores obstruidos → reemplazar.
8. Repetir paso 7 fila por fila (M2, M3, M4), luego zona por zona. Total: 20 combinaciones fila×zona.
9. Verificar presión en el extremo más lejano de cada fila con manómetro portátil. Debe ser ≥ 0.8 bar. Si no: ajustar regulador Ri de esa fila.
9b. Prueba de riego simultáneo completo: abrir M1+M2+M3+M4, activar Zona A desde el Rain Bird. Verificar que todas las filas gotean con presión uniforme. Si alguna fila recibe notablemente más presión que las otras: reducir su regulador Ri hasta equilibrar.

Semana 2 — Montaje permanente de nodos, extensómetros y paneles:
10. Instalar 1 soporte de montaje permanente por zona (5 total, uno por zona A–E): clavar estaca inox 316 punta cónica entre las filas 1–2, en el punto medio de cada zona, a 30 cm del tronco de la vid de referencia. Verificar verticalidad con nivel de burbuja integrado.
11. Montar el nodo en la estaca. Orientar la cámara hacia el dosel a 40° con el inclinómetro de la app. Ajustar bracket angular y apretar tornillos M6 inox. El nodo queda fijo en esta posición por toda la campaña — no se retira entre sesiones.
12. Instalar extensómetro de tronco en la vid de referencia de cada zona: colocar abrazadera de aluminio anodizado a 30 cm de altura, cara norte, sobre la corteza sin herir. Conectar el cable del strain gauge (ADS1231) y el sensor DS18B20 de temperatura al puerto correspondiente del nodo. Verificar con multímetro que la resistencia base está entre 120–350 Ω. Aguardar 24–48h antes de tomar el primer D_max/D_min como válido (período de estabilización del baseline).
13. Clavar un panel de referencia de emisividad (chapa negra mate 15×15cm) en el suelo a 20 cm del nodo, visible en el campo visual del gimbal. Permite corregir derive térmica entre sesiones.
14. Numerar cada vid con estaca: Fila 1 comienza en F1-001, Fila 2 en F2-001, etc. Tomar fotos de referencia de cada vid numerada → compartir en Google Drive del proyecto.
15. Instalar túneles plásticos de exclusión de lluvia sobre las zonas C y D de las Filas 1 y 2. Asegurar con estacas metálicas cada 3 metros.

Semana 2 — Instalación de tensiómetros:
16. Enterrar 1 tensiómetro por zona en el centro de cada zona (a 11m del inicio), a 20 cm de profundidad junto a la vid más representativa. Etiquetar con el código de zona.
17. Registrar lectura inicial de los 20 tensiómetros y D_max/D_min inicial de los 5 extensómetros. Fotografiar y subir a planilla.

Semana 2 — Verificación de conectividad gateway → nube:
18. Verificar tipo de conectividad instalada: (A) Router 4G Teltonika RUT241 — confirmar LED de señal celular verde fijo, acceder a panel web 192.168.1.1 y verificar operador y nivel de señal (RSSI > −85 dBm). (B) Starlink Mini X — confirmar LED blanco fijo (conectado), verificar en app Starlink latencia < 100 ms y velocidad > 5 Mbps. Registrar tipo de conectividad y nivel de señal en planilla.
19. Verificar que el gateway RAK7268 tiene conexión Ethernet activa al router/Starlink (LED LAN encendido). Acceder a la interfaz web del gateway y confirmar que el estado ChirpStack muestra "connected".
20. Forzar un envío de telemetría desde cada nodo (botón TEST en la app o reinicio del nodo) y verificar en el dashboard web que los 5 payloads llegan al backend en < 30 segundos. Si algún nodo no reporta: verificar alcance LoRa (reubicar gateway si necesario) y señal de internet (cambiar de 4G a Starlink o viceversa).

FASE 2 — Mantenimiento rutinario (Mes 1–9, ~8 horas/mes)

Operación del sistema de riego — referencia rápida para Javier:

TURNO DE CANAL (llenar tanque):
  1. Abrir válvula Vf (LLENADO) en el tablero.
  2. Cerrar válvula Vr (RIEGO).
  3. Encender bomba. La válvula de boya corta automáticamente cuando el tanque llega a 20.000 L (~5.5 hs).
  4. Al terminar el turno: apagar bomba, cerrar Vf.
  IMPORTANTE: no abrir solenoides de riego mientras Vf está abierta.

REGAR TODAS LAS FILAS (operación normal del experimento):
  1. Abrir válvula Vr (RIEGO). Cerrar Vf.
  2. Abrir M1 + M2 + M3 + M4 (las 4 válvulas de fila).
  3. El Rain Bird ejecuta el programa automáticamente según el horario programado.

REGAR FILAS SELECCIONADAS (mantenimiento o ajuste individual):
  1. Abrir Vr. Cerrar Vf.
  2. Abrir solo las válvulas Mi de las filas que quiero regar (ej. solo M2 y M4).
  3. Iniciar el programa Rain Bird manualmente desde el tablero.

AJUSTAR CUÁNTA AGUA RECIBE CADA FILA:
  · Reguladores R1–R4 (uno por fila, aguas abajo de cada válvula Mi).
  · Girar hacia la derecha para reducir caudal, hacia la izquierda para aumentar.
  · Posición completamente abierta = máximo caudal (marcado con rotulador).
  · Si una fila recibe notablemente menos presión que las otras: abrir más su regulador Ri.

Tarea diaria (5–10 minutos):
16. Abrir app del nodo en el celular. Verificar: nodo activo, última captura recibida, lectura de pluviómetro del día. Registrar en el log de lluvia según nivel: < 5mm → sin acción; 5–10mm → anotar y notificar a César por WhatsApp con temperatura del día; > 10mm → notificar a César y Monteoliva, reprogramar próxima sesión si estaba prevista en las siguientes 48hs; > 20mm → ídem con espera mínima de 72hs.
17. Si hay alarma de riego en el Rain Bird: verificar en campo qué solenoide o válvula de fila falló. Reportar.

Tarea semanal (45–60 minutos):
18. Recorrer las 4 filas y leer los 20 tensiómetros. Registrar en planilla compartida (Google Sheets): fecha, hora, zona, lectura en centibares.
19. Inspeccionar visualmente: emisores tapados (reemplazar), túneles rotos (parchar con cinta), estacas caídas (volver a clavar).
20. Fotografiar 1 plano general de cada zona mostrando el estado de las vides. Subir a carpeta del proyecto.
21. Flush de la cinta drip: abrir el tapón del extremo de cada fila 30 segundos con el solenoide abierto para limpiar sedimentos.

FASE 3 — Sesión de captura y medición Scholander (Mes 4–9, 4 sesiones OED)

DÍA ANTERIOR A LA SESIÓN:
22. Revisar pronóstico meteorológico (app SMN o Windy). Confirmar: sin lluvia en las próximas 48 horas, viento < 20 km/h en la ventana 9–17hs, cielo despejado o nubosidad parcial (nubes densas alteran la radiación y afectan la medición).
23. Si las condiciones son buenas: confirmar sesión por WhatsApp a Monteoliva y César. Si no: reprogramar para el día siguiente.
24. Cargar la batería del nodo durante la noche.
25. Preparar el kit Scholander: cilindro de nitrógeno (verificar que tenga presión > 50 bar), cámara de presión, lupa 10×, tijera de podar limpia y afilada, bolsitas de plástico zip × 10, planilla impresa, lapicera, linterna.

MAÑANA DE LA SESIÓN — Verificación inicial (8:30–9:00hs):
26. A las 8:30hs: abrir la app del dashboard. Verificar que los 5 nodos están activos y transmitiendo. Anotar el D_max de cada zona registrado durante la madrugada (valor automático, ya en el dashboard). Si algún nodo no tiene D_max del día: anotar incidencia y notificar a César por WhatsApp.
27. A las 8:45hs: leer los tensiómetros de las 5 zonas — anotar lecturas de partida en la planilla.
28. Los nodos capturan automáticamente 7 ángulos cada 15 min — no requieren intervención. Verificar en la app que el gimbal de cada nodo está operando (ícono activo).

MEDICIÓN SCHOLANDER — Ventana 10:00–13:00hs:
31. Zona A — vid F1-010 (vid de referencia de la zona, siempre la misma): con la tijera limpia cortar una hoja adulta y sana de la parte media del dosel (no de la punta ni de hojas sombreadas). Hacer el corte limpio de un golpe. Inmediatamente envolver el peciolo cortado en la bolsita plástica y cerrar.
32. Abrir la cámara Scholander. Introducir la hoja con el peciolo atravesando el orificio del sello de goma. Apretar la tapa hasta que el sello quede hermético (sin apretar de más — verificar que la hoja no quede aplastada).
33. Abrir la válvula del cilindro de nitrógeno MUY LENTAMENTE (vuelta completa en 10 segundos). La presión debe subir a no más de 0.05 bar por segundo.
34. Con la lupa apuntada al peciolo cortado: observar el extremo del corte. En cuanto aparezca la primera gotita de savia brillante: cerrar la válvula de nitrógeno de inmediato.
35. Leer el manómetro. Anotar en la planilla: Zona A · Vid F1-010 · Hora: HH:MM · Ψstem = −X.X bar (el valor es negativo; más negativo = más estrés).
36. Liberar la presión abriendo la válvula de purga. Abrir la cámara, retirar la hoja.
37. Repetir pasos 31–36 para: Zona B (vid F1-028), Zona C (vid F1-046), Zona D (vid F1-064), Zona E (vid F1-082). Siempre la misma vid de referencia en cada zona, siempre entre las 10:00 y las 13:00hs (ventana de potencial hídrico de tallo estabilizado).
38. Fotografiar cada hoja medida con el celular junto a la planilla que muestra el valor anotado — respaldo visual del dato.

VENTANA 12hs:
39. Leer tensiómetros de las 5 zonas — anotar en planilla.
40. Revisar en la app el D_min parcial de cada nodo (la contracción máxima suele ocurrir entre 13–14hs — el valor va actualizándose en tiempo real).

VENTANA 16hs:
41. Registrar D_min definitivo de cada nodo en la planilla — el mínimo del día ya quedó asentado automáticamente. Calcular MDS del día = D_max − D_min para cada zona y anotar.
42. Leer tensiómetros finales — anotar en planilla.

CIERRE DE SESIÓN:
43. Completar la planilla digital en Google Sheets: ingresar los 5 valores de Ψstem con hora exacta, las lecturas de tensiómetros de los 3 momentos y cualquier incidencia (nube durante captura, vid con síntoma inusual, emisor tapado encontrado).
44. Enviar resumen por WhatsApp a César Schiavoni: "Sesión #N completada. Ψstem: A=−X.X / B=−X.X / C=−X.X / D=−X.X / E=−X.X bar. MDS: A=XXµm / B=XXµm / C=XXµm / D=XXµm / E=XXµm. Sin incidencias / Incidencia: [detalle]."
45. Guardar el cilindro de nitrógeno en posición vertical en lugar seco. Limpiar la cámara Scholander con paño húmedo y guardar en su estuche.

CRITERIOS DE CANCELACIÓN Y REPROGRAMACIÓN:
— Lluvia < 5mm en las últimas 48hs: sin restricción, sesión procede.
— Lluvia 5–10mm en las últimas 48hs: procede a las 36hs si T° > 30°C post-lluvia; caso contrario esperar 48hs completas.
— Lluvia > 10mm en las últimas 48hs: reprogramar +48hs mínimo.
— Lluvia > 20mm en las últimas 48hs: reprogramar +72hs mínimo. Umbral adaptado a Colonia Caroya — suelo limoso-arenoso con buen drenaje y ETP alta en verano cordobés (referencia: INIA Chile, Fernández & Cuevas 2010).
— Viento > 25 km/h sostenido durante la ventana de captura: posponer la ventana afectada pero conservar las demás.
— Temperatura ambiente > 38°C al inicio: verificar que el nodo no supere 45°C de carcasa antes de iniciar capturas (el MLX90640 pierde calibración por encima de ese límite).
— Nubosidad densa ≥ 70% durante más de 20 minutos consecutivos: anotar en planilla pero no cancelar — el modelo necesita también imágenes en condiciones de nubosidad parcial.

### 11B. Relación costo–precisión del sistema comercial

El nodo HydroVision AG entrega precisión de nivel científico a costo de producto de consumo.

FLIR A35 con trípode fijo (investigación): USD 8.000–15.000 de hardware, requiere técnico presente, cubre 1 punto fijo, precisión ±0.08 CWSI.
UAV con cámara térmica: USD 25.000–80.000, requiere piloto habilitado, máximo 1–2 vuelos por semana, precisión ±0.09 CWSI.
Tensiómetro de suelo: USD 80–200, mide humedad del suelo pero no el estado hídrico real de la planta — no detecta estrés antes del síntoma de marchitez.
Nodo HydroVision AG: USD 950–1.000 de hardware + USD 80–110/ha/año de suscripción (Tier 1 Monitoreo), opera 24/7 autónomo con energía solar, cubre 1–10 ha por nodo, precisión ±0.07–0.09 CWSI.

La precisión comparable a equipos científicos a una fracción del costo se logra porque el modelo PINN está anclado fisiológicamente mediante el protocolo Scholander — no es una estimación indirecta del suelo o del satélite, sino una medición directa del estado hídrico de la hoja extrapolada por inteligencia artificial.

En vid premium (Malbec Valle de Uco, ingreso bruto USD 9.600/ha): costo total Año 1 = USD 192/ha. Beneficio conservador por estrés evitado = USD 1.150/ha. ROI = 6x en la primera cosecha. El hardware se recupera antes de la siguiente vendimia.

---

### 11C. Estrategia de muestreo adaptativo — Dendrómetros de tronco + Diseño Óptimo de Sesiones

Esta sección describe la estrategia científica que permite reducir las sesiones de medición con bomba de Scholander de 10 a 4, sin perder rigor estadístico ni cobertura del gradiente de estrés. Es la técnica con mejor relación costo-beneficio implementable en Colonia Caroya con el técnico de campo existente.

Por qué 10 sesiones mensuales es ineficiente

El modelo de calibración del CWSI requiere estimar solo dos parámetros físicos: la pendiente (a) y el intercepto (b) de la línea base de planta sin estrés en el espacio (VPD, ΔT_dosel). La teoría de diseño óptimo de experimentos — D-optimal design, Kiefer 1959 — demuestra matemáticamente que para un modelo lineal de dos parámetros, dos condiciones contrastantes (baja VPD y alta VPD) con suficientes réplicas son tan informativas como diez sesiones uniformemente distribuidas. Diez sesiones mensuales acumulan datos redundantes en condiciones similares y no agregan información útil después de la cuarta sesión.

La solución tiene dos partes:

Parte 1 — Diseño Óptimo de Sesiones (OED): elegir 4 momentos del ciclo vegetativo que maximizan la información del modelo. No requiere nuevos instrumentos — es un cálculo previo que realiza el investigador Art. 32 antes de que empiece el experimento.

Parte 2 — Dendrómetros de tronco: sensores de bajo costo instalados por el técnico de campo que registran automáticamente el estado hídrico de la planta entre sesiones Scholander, completando la información del modelo durante los meses sin visita de Monteoliva.

Las 4 sesiones Scholander optimizadas

Sesión 1 — Post-brotación temprana, mañana (VPD < 1.5 kPa), racimos con 4-6 hojas desarrolladas.
Aporte: establece la línea base de planta sin estrés (parámetros a y b del CWSI). Es la sesión más importante del experimento — se miden las 60 vides de referencia en censo completo. Inicializa también la calibración de todos los dendrómetros.

Sesión 2 — Pre-envero, mediodía (VPD > 2.0 kPa), estrés máximo de la temporada.
Aporte: ancla el límite superior del CWSI (planta sin transpiración activa). Es el punto biológicamente más informativo del gradiente hídrico. A partir de la Sesión 2, el Active Learning selecciona las 20-25 vides más inciertas según el modelo ya inicializado — no se miden todas.

Sesión 3 — Post-envero, estrés intermedio, VPD variable.
Aporte: valida el modelo en condiciones intermedias del ciclo. Corrige la deriva acumulada de los dendrómetros con el paso del verano.

Sesión 4 — 2-3 semanas antes de cosecha.
Aporte: validación final del modelo en el estado fenológico de mayor interés comercial. Cierra la curva de calibración sobre la fenología de maduración.

Resultado: 600 mediciones Scholander originales reducidas a 120 mediciones totales. 10 viajes de Monteoliva reducidos a 4. Los dendrómetros proveen señal continua entre sesiones para que el modelo no quede sin datos entre una y otra.

Qué es un dendrómetro y qué mide

Un dendrómetro es un sensor que mide el diámetro del tronco de la planta con precisión de décimas de milímetro. Cuando una vid tiene estrés hídrico, pierde agua de sus células — incluyendo las del tronco — y el tronco se encoge. Cuando recibe agua o transpira menos (de noche), el tronco se hincha. Esta variación — llamada ciclo diurno de diámetro — es un reflejo directo del estado hídrico interno de la planta y varía en sintonía con el Ψstem medido por el Scholander.

Punto clave sobre la interpretación: el dendrómetro no mide Ψstem directamente. Mide el diámetro del tronco, que se convierte en Ψstem a través de una función de calibración de dos parámetros establecida en la Sesión 1 con la bomba de Scholander. Sin calibración, el dendrómetro entrega un número adimensional sin utilidad. Con calibración, es un monitor continuo de estrés que opera los 9 meses sin intervención especializada.

Rango de utilidad por zona hídrica:

Zona A (100% ETc): señal limpia, excelente correlación con Scholander. Proxy confiable.
Zona B (65% ETc): señal buena, correlación confiable con corrección térmica mínima.
Zona C (40% ETc): señal usable, requiere corrección de temperatura y de histeresis.
Zona D (15% ETc): señal distorsionada bajo estrés fuerte. El Scholander sigue siendo indispensable.
Zona E (sin riego): señal no confiable. Solo Scholander directo en cada sesión.

Los dendrómetros no reemplazan el Scholander en las zonas de estrés fuerte (D y E), que son las más valiosas para el entrenamiento del modelo. Reemplazan las visitas de Scholander en las zonas A, B y C durante los meses entre sesiones programadas.

Materiales necesarios — kit completo para 6 dendrómetros

Los dendrómetros se construyen con componentes de electrónica accesibles. el investigador Art. 32 arma los 6 kits en taller antes de enviarlos a Colonia Caroya.

Sensor de desplazamiento: potenciómetro lineal 10 kΩ, rango 0-50 mm (modelo SL1 o equivalente). Precio: USD 8-12/unidad. Alternativa de mayor precisión: sensor LVDT de inducción USD 25-40/unidad — recomendado si el presupuesto lo permite por su linealidad superior.

Estructura de montaje: placa de aluminio 80×30 mm, espesor 3 mm, doblada en U. Abrazadera de nylon ajustable al tronco. Brazo de contacto: perno M5 inoxidable con punta esférica que apoya sobre la corteza. Precio de materiales de ferretería: USD 3-5/unidad.

Datalogger: Arduino Nano + módulo lector de tarjeta SD + reloj de tiempo real RTC DS3231. El Arduino toma una lectura cada 10 minutos, la graba en la SD con fecha y hora exactas, y entra en modo de bajo consumo hasta la próxima lectura. Batería de litio 18650: autonomía de 45-60 días sin recarga. Precio completo: USD 12-15/unidad.

Costo total del kit de 6 dendrómetros: USD 140-190 según el tipo de sensor elegido.

Instalación paso a paso

El técnico de campo instala los 6 dendrómetros en una sola mañana de trabajo (~3 horas). Monteoliva o César Schiavoni verifican la instalación el día de la Sesión 1.

Vides a instrumentar: 1 por zona en Fila 1 (zonas A, B, C) y 1 por zona en Fila 2 (zonas A, B, C) = 6 unidades. Las zonas D y E no llevan dendrómetro permanente — se miden solo con Scholander en las 4 sesiones.

Paso D1 — Seleccionar la vid representativa de cada zona.
Criterio: vid ubicada en el centro de la zona (aproximadamente a 11 m del inicio de esa zona), sin síntomas de enfermedad, tronco recto y sin heridas visibles, grosor de tronco entre 3 y 6 cm. Marcar con cinta de colores: Zona A = azul, Zona B = verde, Zona C = amarillo, en ambas filas. Anotar el número de estaca de cada vid elegida en la planilla del proyecto.
Por qué importa: usar siempre la misma vid garantiza que las variaciones medidas reflejan el estado hídrico de esa planta a lo largo del tiempo, y no la variabilidad natural entre individuos distintos. Cambiar de vid entre sesiones invalida la serie temporal de datos.

Paso D2 — Limpiar la corteza en el punto de contacto.
Con un cepillo de cerdas suaves, frotar suavemente la corteza del tronco a 30 cm del suelo en el lado norte (para evitar exposición directa al sol de la tarde). Remover musgo, tierra o corteza suelta sin raspar hasta la madera viva.
Por qué importa: cualquier material suelto entre la punta del sensor y la corteza introduce variaciones aleatorias en la señal que el modelo no puede distinguir de variaciones hídricas reales. Un contacto limpio es el requisito mínimo de precisión del sistema.

Paso D3 — Instalar la abrazadera de base.
Colocar la abrazadera de nylon alrededor del tronco a 30 cm del suelo. Ajustar hasta que esté firme pero sin comprimir (no debe deformar la corteza ni impedir el crecimiento normal del tronco durante la temporada). Verificar que la placa de aluminio queda paralela al eje del tronco y perpendicular al suelo.
Por qué importa: la abrazadera es el punto de referencia mecánico de toda la medición. Si se mueve — por viento, animales, o crecimiento del tronco — ese movimiento aparece en los datos como una variación de diámetro falsa. La firmeza sin compresión excesiva equilibra estabilidad mecánica y posibilidad de crecimiento del tronco durante los 9 meses del experimento.

Paso D4 — Posicionar el sensor y ajustar el brazo de contacto.
Insertar el potenciómetro en el soporte de la placa. Extender el brazo con punta esférica hasta que toque suavemente la corteza del lado opuesto al montaje. El sensor debe quedar posicionado al 50% de su recorrido total (rango medio) para tener margen tanto de expansión como de contracción del tronco.
Por qué importa: un sensor posicionado al extremo de su rango saturará cuando el tronco se expanda por hidratación nocturna, produciendo lecturas de techo que enmascaran el ciclo diurno real. Centrar el sensor en el rango medio garantiza que tanto la expansión nocturna como la contracción por estrés diurno queden dentro del rango medible.

Paso D5 — Conectar el datalogger y verificar la primera grabación.
Conectar el potenciómetro al pin analógico A0 del Arduino. Encender el datalogger. El LED de confirmación parpadea una vez cada 10 minutos confirmando la grabación. Verificar espacio en la SD. Anotar en planilla: fecha, hora, Fila, Zona, número de estaca de la vid, valor ADC inicial (número entre 0 y 1023).
Por qué importa: el valor ADC inicial es el punto de referencia absoluto de toda la calibración posterior. Si el datalogger pierde este dato por un reseteo accidental antes de la Sesión 1, la calibración debe rehacerse desde cero. El respaldo manual en planilla es el seguro ante fallos electrónicos.

Paso D6 — Proteger el datalogger de la intemperie.
Colocar el datalogger dentro de su caja estanca (caja de paso eléctrica IP65, USD 2-3). Fijar la caja al poste de espaldera más cercano con brida de nylon. Verificar que el cable del sensor tiene longitud suficiente sin quedar tenso, y que no pasa por donde pueda ser cortado por maquinaria agrícola.
Por qué importa: las lluvias de verano en la región de Colonia Caroya pueden superar 80 mm en 24 horas. Un datalogger sin protección adecuada se daña de forma permanente e irrecuperable. La pérdida de un sensor a mitad de la temporada significa romper la serie temporal del modelo sin posibilidad de recuperación retroactiva.

Paso D7 — Fotografiar el montaje completo.
Tomar 3 fotos por sensor: (a) vista general de la vid mostrando la abrazadera y la caja del datalogger, (b) primer plano del contacto punta-corteza desde arriba, (c) etiqueta de zona visible junto al sensor. Subir a Google Drive con el nombre: "Dendro_Instalacion_F1_ZonaA.jpg".
Por qué importa: la foto del contacto sensor-corteza permite al investigador verificar remotamente que la instalación es correcta antes de confiar en los primeros datos. También es la referencia visual indispensable si el sensor se desplaza y hay que reposicionarlo de manera idéntica para mantener la continuidad de la serie.

Calibración — el paso más crítico de toda la estrategia

La calibración convierte el valor ADC del sensor (número adimensional 0-1023) en Ψstem en bar. Sin esta conversión, los datos del dendrómetro son inutilizables como dato científico. La calibración se realiza durante la Sesión 1 del protocolo Scholander y debe ejecutarse con el máximo cuidado — un error de calibración contamina todos los datos de ese sensor durante toda la temporada sin posibilidad de corrección retroactiva completa.

Principio de la calibración

En el momento exacto en que Monteoliva mide Ψstem con el Scholander en una vid instrumentada, el dendrómetro de esa misma vid está registrando el diámetro correspondiente a ese preciso estado hídrico. Esto genera el par (valor ADC, Ψstem medido) que ancla la función de conversión. Con dos pares de calibración tomados en condiciones contrastantes — mañana de baja VPD y mediodía de alta VPD — se obtiene la función lineal:

Ψstem = a × ADC + b

donde a es la pendiente (bar por unidad ADC) y b es el intercepto. Esta función se aplica a toda la serie de datos del dendrómetro durante la temporada. La calidad de la función depende directamente de los puntos de calibración obtenidos en la Sesión 1.

Consideración 1 — Simultaneidad estricta de la medición.
El Ψstem varía hasta 0.3 bar por hora en días de alta VPD. Un desfase de 30 minutos entre la lectura del sensor y el corte de la hoja puede invalidar el par de calibración.
Protocolo: en el momento exacto en que Monteoliva realiza el corte, el técnico anota el valor ADC de la última grabación del datalogger (no el promedio del día — el valor puntual más reciente). La hora del corte queda registrada en la planilla con precisión de minutos. Si el corte ocurre entre dos grabaciones, se interpolará linealmente entre la anterior y la siguiente.

Consideración 2 — Corrección de temperatura del tronco.
La madera se dilata con el calor. Un aumento de 5°C produce una expansión del tronco de 0.02-0.05 mm, equivalente a una variación aparente de Ψstem de 0.1-0.2 bar que no es estrés hídrico sino dilatación térmica. Si no se corrige, el modelo confunde temperatura con estrés.
Protocolo: registrar temperatura ambiente cada 30 minutos con el termómetro del nodo. el investigador aplica la corrección térmica estándar (coeficiente de expansión lineal de la madera ≈ 0.01 mm/°C) a los datos del dendrómetro antes de cada análisis. En días con variación térmica menor a 8°C la corrección es mínima. En días con variación mayor a 15°C (verano de Córdoba) es obligatoria.

Consideración 3 — Histeresis: el tronco no responde de forma simétrica.
Cuando la planta rehidrata su tronco de noche, la expansión ocurre más lentamente que la contracción durante el estrés diurno. Un par de calibración tomado durante la rehidratación nocturna no puede usarse con la misma función que un par del estrés diurno.
Protocolo: los pares de calibración se obtienen únicamente entre las 10:00 y las 13:00 horas — la misma ventana del protocolo Scholander — cuando la planta está en estrés diurno activo y el ciclo de histeresis es predecible. Nunca usar valores de madrugada, noche anterior al riego, ni primeras horas post-riego como pares de calibración.

Consideración 4 — Cada sensor tiene su propia calibración.
Dos vides de la misma zona pueden tener densidades de madera distintas y responder cuantitativamente diferente al mismo Ψstem. La función Ψstem = a × ADC + b es específica de la vid en la que está instalado ese sensor y no puede transferirse a otra vid.
Protocolo: cada uno de los 6 dendrómetros tiene su propia función de calibración, obtenida individualmente en la Sesión 1. La calibración de Zona A Fila 1 no puede aplicarse al sensor de Zona A Fila 2.

Consideración 5 — Deriva de largo plazo por crecimiento del tronco.
El tronco crece lentamente durante la temporada. La abrazadera permanece fija y el crecimiento empuja el sensor hacia el extremo de su rango. Pasados 2-3 meses, el sensor puede quedar fuera del rango útil sin que el técnico lo note.
Protocolo: en cada sesión Scholander (2, 3 y 4), antes de iniciar mediciones, verificar que el valor ADC de cada sensor está entre 200 y 800 (20-80% del rango total). Si está fuera: reposicionar el brazo de contacto hasta volver al rango medio, anotar el nuevo ADC de reposo como punto de corrección, y avisar al investigador. La corrección se aplica como offset en la serie histórica.

Protocolo de calibración en la Sesión 1 — paso a paso

Paso C1 — A las 9:00hs: encender todos los dataloggers y confirmar grabación activa. Anotar en planilla el valor ADC de los 6 sensores en este momento.
Por qué importa: establece el estado de referencia matutino (baja VPD, mayor turgencia) como primer punto de anclaje del ciclo diurno.

Paso C2 — A las 9:30hs: Monteoliva mide Ψstem con Scholander en las 6 vides instrumentadas. En el momento exacto de cada corte de hoja, el técnico anota el valor ADC de ese sensor.
Por qué importa: primer par de calibración (baja VPD, estrés leve). Ancla el extremo inferior de la curva — el tronco en su estado más turgente.

Paso C3 — A las 11:30hs: segunda ronda Scholander en las mismas 6 vides. El técnico anota el valor ADC en el momento exacto de cada corte.
Por qué importa: segundo par de calibración (VPD alta, estrés máximo del mediodía). Ancla el extremo superior — el tronco en su estado más encogido. Con dos puntos contrastantes la función lineal queda definida con los grados de libertad estadísticamente necesarios.

Paso C4 — el investigador recibe los 12 pares de calibración (6 vides × 2 momentos) y ajusta las 6 funciones individuales por regresión lineal. Entrega en menos de 24 horas: gráfico de la función de calibración de cada sensor con intervalo de confianza, RMSE por sensor, y alerta si algún sensor tiene R² < 0.85.
Por qué importa: el R² indica si la relación diámetro-Ψstem es lineal y consistente en esa vid. Un R² < 0.85 indica un problema en la simultaneidad, el posicionamiento o la elección de la vid. Detectarlo el mismo día de la Sesión 1 permite corregirlo en campo.

Paso C5 — Si alguna calibración tiene R² < 0.85: Monteoliva toma 2 mediciones Scholander adicionales en esa vid entre las 13:00 y las 14:00hs. El técnico anota los valores ADC correspondientes. el investigador repite la regresión con los pares adicionales.
Por qué importa: una calibración pobre detectada el mismo día puede corregirse en campo. Detectada en la Sesión 2, ya se perdió un mes entero de datos inutilizables de ese sensor.

Verificación de calibración en las Sesiones 2, 3 y 4

Al inicio de cada sesión, antes de medir las vides seleccionadas por Active Learning, Monteoliva mide con Scholander las 6 vides instrumentadas. el investigador compara el Ψstem medido por Scholander con el Ψstem estimado por el dendrómetro en ese instante.

Diferencia menor a 0.20 bar: calibración válida. Continuar normalmente.
Diferencia entre 0.20 y 0.40 bar: deriva aceptable. Aplicar corrección de offset lineal a los datos desde la sesión anterior.
Diferencia mayor a 0.40 bar: el sensor se desplazó. Reposicionar en campo ese mismo día, obtener 3 nuevos pares de calibración y re-escalar la serie desde la última verificación válida.

Este protocolo garantiza que los datos del dendrómetro entre sesiones son auditables y corregibles — requisito mínimo para publicación científica.

Rutina del técnico de campo con los dendrómetros

Acción mensual (15 minutos, primer lunes de cada mes):
Retirar la tarjeta SD de cada datalogger y copiar los archivos CSV al celular. Devolver la SD y verificar que el LED de confirmación parpadea nuevamente. Subir los archivos a Google Drive con el nombre del mes y zona: "Dendro_F1_ZonaA_2026-11.csv". Fotografiar el contacto sensor-corteza de cada dendrómetro. Verificar que el valor ADC está en el rango 200-800. Si está fuera de ese rango: avisar al investigador por WhatsApp antes de tocar el sensor.
Por qué importa: la foto del contacto permite al investigador detectar de forma remota si el sensor se desplazó antes de que la deriva contamine semanas de datos. La verificación del rango ADC previene la pérdida silenciosa de datos por saturación sin que nadie lo note.

Acción semanal integrada al protocolo existente:
El Paso 19 del protocolo de campo (Sección 11A.1) ya incluye el recorrido visual de las 4 filas. Durante ese recorrido verificar que ninguna abrazadera de dendrómetro se aflojó, que el cable del sensor no está dañado, y que la tapa de la caja estanca no tiene agua adentro. No requiere tiempo adicional.

Flujo de responsabilidades

Técnico de campo: instala los 6 sensores en una mañana (Semana 1). Realiza la descarga mensual (15 min/mes). Realiza la inspección visual semanal durante el recorrido ya planificado. No necesita interpretar los datos.

el investigador Art. 32: recibe los datos crudos en CSV, aplica la corrección térmica, mantiene actualizadas las 6 funciones de calibración, alimenta el modelo GP con los datos entre sesiones, detecta y corrige derivas, y alerta ante anomalías. Toda esta tarea se ejecuta de forma remota.

Monteoliva: en las Sesiones 1-4 realiza las mediciones Scholander de inicialización y verificación de calibración (6 vides instrumentadas), más las 20-25 vides por Active Learning. No requiere presencia adicional fuera de las 4 sesiones planificadas.

Resultado del sistema combinado

Con los 6 dendrómetros operativos y las 4 sesiones Scholander optimizadas por OED, el proyecto obtiene:

Cobertura continua de Ψstem estimado en zonas A, B y C durante los 9 meses de temporada, con resolución de 10 minutos.
Medición directa Scholander de alta precisión en las 4 sesiones clave, cubriendo las 5 zonas incluyendo D y E.
Un dataset de entrenamiento con 120 mediciones Scholander distribuidas en los momentos de máxima información estadística, más señal continua de dendrómetros para interpolar el modelo entre sesiones.
Documentación auditada de la deriva y corrección de cada sensor, con verificación cruzada en cada sesión, cumpliendo el requisito mínimo para publicación científica.

El costo adicional de este sistema es USD 150-190 de hardware, absorbido dentro de la partida de contingencia existente. No genera costo adicional en honorarios ni en viajes.

---

### 11D. Adaptación del protocolo de muestreo a otras variedades y regiones

El protocolo de muestreo desarrollado en Colonia Caroya está optimizado para Malbec en el clima semiárido de Córdoba central. Cuando el sistema se valide en otras variedades o regiones — por ejemplo, Cabernet Sauvignon en Mendoza o Torrontés en Cafayate — no se cambia el método, sino seis parámetros específicos que dependen de la biología de la variedad y del clima local. Esta sección detalla qué cambia, por qué cambia, quién lo ajusta y qué datos se necesitan para hacerlo.

Resumen rápido: qué cambia y qué no cambia

No cambia: la estructura del experimento (5 zonas hídricas, brackets, gimbal, protocolo Scholander, dendrómetros, OED de 4 sesiones, Active Learning). El hardware es idéntico en cualquier viñedo.

Cambia: los parámetros numéricos del modelo que dependen de la fisiología de la variedad y del clima de la región. Son 6 ajustes, todos realizados por el investigador Art. 32 de forma remota antes o durante la Sesión 1 en el nuevo sitio.

Ajuste 1 — Línea base CWSI de la nueva variedad (parámetros a y b)

Qué es: la función que define la temperatura de dosel esperada en una planta sin estrés en función de la VPD (ΔT_LL = a × VPD + b). Cada variedad tiene valores distintos porque difieren en conductancia estomática, densidad foliar y respuesta al déficit de presión de vapor.
Por qué cambia entre variedades: Malbec tiene alta sensilibilidad estomática — sus estomas se cierran rápido ante VPD elevada, lo que eleva la temperatura del dosel incluso con agua disponible. Cabernet Sauvignon es isohydric con comportamiento similar; Torrontés y Chardonnay son anisohydric y mantienen estomas más abiertos bajo estrés. Un modelo calibrado para Malbec sobreestimaría el estrés en Torrontés con los mismos parámetros.
Qué datos se necesitan: al menos 8-10 pares (VPD, ΔT_dosel) medidos en plantas sin estrés de la nueva variedad bajo condiciones de alta VPD (VPD > 1.5 kPa). Estos datos se obtienen en la Sesión 1 del nuevo sitio midiendo solo la Zona A (100% ETc) en 3 ventanas horarias distintas.
Quién lo ajusta: el investigador Art. 32, antes del inicio de la Sesión 2 en el nuevo sitio. Tiempo requerido: 2-4 horas de ajuste del modelo.
Fuente de referencia: valores publicados para las principales variedades mediterráneas (Jones et al., 2002; Bellvert et al., 2016) pueden usarse como punto de partida, pero siempre deben validarse con datos propios de la Sesión 1 porque los valores cambian también con el portainjerto y el suelo.

Ajuste 2 — Calendario fenológico de las 4 sesiones

Qué es: las fechas concretas de las 4 sesiones Scholander optimizadas (post-brotación, pre-envero, post-envero, pre-cosecha). El OED define qué estado fenológico maximiza la información, pero ese estado ocurre en fechas distintas según la variedad y la región.
Por qué cambia: Malbec en Colonia Caroya (700 m.s.n.m.) inicia brotación en septiembre y cosecha en marzo. El mismo Malbec en Luján de Cuyo (900 m.s.n.m.) anticipa la brotación 1-2 semanas pero retrasa la cosecha por las noches más frías. Torrontés en Cafayate (1.700 m.s.n.m.) cosecha en febrero — todo el ciclo se corre 3-4 semanas.
Qué datos se necesitan: el calendario fenológico histórico de la variedad en esa región (disponible en INTA EEA Mendoza, EEA La Consulta, o en el registro de la bodega del sitio de validación). Con el calendario en mano, el investigador corre el OED sobre las fechas locales y entrega el plan de sesiones antes de que empiece el experimento en ese sitio.
Quién lo ajusta: el investigador Art. 32, antes del inicio del experimento en el nuevo sitio. El técnico de campo del nuevo sitio solo necesita recibir las 4 fechas de sesión.

Ajuste 3 — Rango de VPD y corrección térmica del dendrómetro

Qué es: el coeficiente de corrección térmica (mm/°C) que el investigador aplica a la señal del dendrómetro para separar la dilatación por temperatura del encogimiento por estrés hídrico.
Por qué cambia entre regiones: Córdoba tiene variación térmica diurna moderada (15-20°C en verano). Mendoza y San Juan tienen variaciones extremas (25-32°C entre mínima y máxima en enero), lo que genera una señal de dilatación térmica 2-3 veces mayor que en Córdoba. Si se usa el coeficiente de Córdoba en Mendoza, el modelo confunde dilatación térmica con rehidratación y subestima el estrés sistemáticamente.
Qué datos se necesitan: registros horarios de temperatura ambiente del sitio nuevo durante al menos 2 semanas previas a la Sesión 1. El datalogger meteorológico del sitio de validación (o la estación INTA más cercana) provee estos datos.
Quién lo ajusta: el investigador Art. 32, recalibra el coeficiente antes de procesar los datos de cada nuevo sitio. El ajuste es automático si los datos de temperatura llegan correctamente etiquetados.

Ajuste 4 — Umbrales de estrés Ψstem por variedad

Qué es: los valores de Ψstem (en bar) que corresponden a "estrés leve", "estrés moderado" y "estrés severo" en la variedad evaluada. Estos umbrales definen cómo se etiquetan las imágenes térmicas en el dataset de entrenamiento.
Por qué cambia: Malbec en estado de estrés moderado muestra Ψstem de -0.8 a -1.0 MPa. Chardonnay entra en estrés visible con -0.6 MPa. Garnacha puede tolerar hasta -1.4 MPa sin síntoma visual. Usar los umbrales de Malbec para etiquetar imágenes de Chardonnay como "sin estrés" cuando en realidad tiene estrés moderado produce un dataset de entrenamiento con etiquetas erróneas.
Qué datos se necesitan: los umbrales publicados para la variedad (disponibles en bibliografía de fisiología vitícola: Chone et al. 2001, Deloire et al. 2004, van Leeuwen et al. 2009) y confirmación con al menos 2 puntos propios de la Sesión 1 para verificar que los umbrales publicados aplican en las condiciones locales de suelo y portainjerto.
Quién lo ajusta: Monteoliva define los umbrales fisiológicos; el investigador los codifica en el pipeline de etiquetado del dataset. Requiere una reunión de 1 hora entre ambos antes de procesar los datos del nuevo sitio.

Ajuste 5 — Calibración del dendrómetro en la nueva variedad

Qué es: la función Ψstem = a × ADC + b es específica de la especie y de la anatomía del tronco. Diferentes variedades tienen densidad de madera, composición de vasos xilemáticos y elasticidad de la corteza distintas, lo que cambia la pendiente a de la función.
Por qué cambia: Malbec tiene troncos con alta densidad de vasos xilemáticos de diámetro grande — la respuesta del diámetro al estrés hídrico es rápida y pronunciada. Cabernet Sauvignon tiene menor diámetro de vasos — la señal del dendrómetro es menos sensible por unidad de cambio de Ψstem. Usar la función calibrada en Malbec para interpretar datos de Cabernet subestimaría el estrés real.
Qué datos se necesitan: los pares de calibración de la Sesión 1 en el nuevo sitio con la nueva variedad. El protocolo de calibración es idéntico (Pasos C1 a C5 de la Sección 11C) — solo cambia la variedad instrumentada. No se reutiliza ningún parámetro de calibración de Malbec.
Quién lo ajusta: el protocolo de calibración es realizado por el técnico del nuevo sitio con el mismo procedimiento. el investigador ajusta la función individualmente para cada sensor del nuevo sitio.

Ajuste 6 — Zonas hídricas y dosis de riego (% ETc)

Qué es: los porcentajes de agua aplicada en cada zona (100%, 65%, 40%, 15%, 0%) están calculados sobre la ETc del viñedo de Colonia Caroya. La ETc depende de la evapotranspiración de referencia local (ETo) y del coeficiente de cultivo (Kc) de la variedad.
Por qué cambia: la ETo en Mendoza (zona árida, alta radiación solar, baja humedad relativa) puede ser 30-50% mayor que en Córdoba central. Con la misma dosis absoluta de agua, una zona que en Córdoba recibe el 65% de ETc podría recibir solo el 45% en Mendoza, cambiando completamente el gradiente de estrés planificado.
Qué datos se necesitan: la ETo histórica del nuevo sitio (disponible en AgroMet INTA o en el sistema SIGA de INTA) y el Kc de la variedad local. Con estos dos datos, el investigador recalcula las dosis absolutas de riego por zona para que los porcentajes de ETc se mantengan equivalentes entre sitios.
Quién lo ajusta: el investigador Art. 32, antes del inicio de cada nuevo sitio de validación. El técnico del nuevo sitio recibe el caudal en litros/hora y la duración de riego por zona — no necesita conocer el cálculo detrás.

Tabla resumen de ajustes por sitio nuevo

Ajuste / Quién ajusta / Cuándo / Datos necesarios:

Línea base CWSI (a, b) / el investigador Art. 32 / Antes de Sesión 2 / 8-10 pares (VPD, ΔT) en Zona A de la Sesión 1.
Calendario fenológico de sesiones / el investigador Art. 32 / Antes de iniciar el sitio / Calendario histórico de la variedad en esa región.
Coeficiente de corrección térmica dendrómetro / el investigador Art. 32 / Antes de procesar Sesión 1 / Temperatura horaria del sitio, 2 semanas previas.
Umbrales Ψstem por variedad / Monteoliva + el investigador / Antes de etiquetar el dataset / Bibliografía de la variedad + 2 puntos propios de Sesión 1.
Función de calibración dendrómetro / Técnico de campo + el investigador / Sesión 1 del nuevo sitio / Pares de calibración propios (protocolo C1–C5 idéntico).
Dosis de riego por zona (% ETc) / el investigador Art. 32 / Antes de iniciar el sitio / ETo histórica del nuevo sitio + Kc de la variedad.

Costo de adaptación a un nuevo sitio

Todos los ajustes son computacionales o de análisis de datos — no requieren nuevo hardware ni nuevos instrumentos. El único costo incremental es el tiempo de el investigador Art. 32 para procesar los datos de la Sesión 1 del nuevo sitio y recalibrar el modelo (~16-20 horas de trabajo por sitio nuevo). A partir de la Sesión 2, el protocolo del nuevo sitio es idéntico al de Colonia Caroya.

La reutilización del hardware (dendrómetros, brackets, gimbal, nodo) entre sitios de validación — enviando el kit completo de un sitio al siguiente una vez terminada la campaña — reduce el costo total de expansión a cero en equipamiento.



