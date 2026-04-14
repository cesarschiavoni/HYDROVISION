# HydroVision AG — Análisis Venture Architect
## Validación de Mercado y Ajuste Problema-Solución
**Documento interno de gestión · No forma parte del formulario ANPCyT**
Elaborado: abril 2026 · Metodología: Venture Architect + Business Analyst Senior

> **Para qué sirve este documento:** base de trabajo para pitch a inversores seed, preparación
> de Gate Reviews TRL 5-6, y corrección de inconsistencias en doc-06 antes de la siguiente
> convocatoria ANPCyT. Los números aquí son más precisos que los de doc-06 — si hay
> diferencia entre ambos, este documento tiene razón.

---

## ADVERTENCIA METODOLÓGICA GENERAL

Este análisis aplica dos principios que el equipo debe internalizar antes de leer los números:

**1. TAM/SAM/SOM en revenue, no en hectáreas.**
Declarar "34,5 millones de hectáreas" como TAM es el error más común en pitches AgTech. Los inversores calculan TAM como revenue anual capturables — suscripción + hardware + datos. El número en hectáreas es el denominador, no el TAM.

**2. Dolor consciente vs. dolor latente.**
Un productor con dolor consciente sabe que tiene el problema y busca solución. Con dolor latente, el problema existe pero lo atribuye al clima o la mala suerte. WTP del dolor latente es bajo hasta que alguien lo convierte en dolor consciente — y esa conversión es trabajo comercial costoso, no trabajo de producto.

---

## MÓDULO 1 — VALIDACIÓN DE MERCADO

### 1.1 TAM — Total Addressable Market

El TAM tiene tres capas de revenue con naturaleza distinta que no deben sumarse ciegamente:

| Componente | Naturaleza | Margen | Previsibilidad |
|---|---|---|---|
| Suscripción de software | Recurrente anual | ~78-81% | Alta — crece con retención |
| Venta de hardware (nodos) | One-time por unidad | ~15-20% | Lineal con nuevas ventas |
| Datos / seguros / carbono | Comisión variable | ~85-90% | No lineal, se activa en Año 2+ |

#### TAM Software (suscripción anual)

Mercado base: 34.550.000 ha de cultivos de alto valor con riego tecnificado globalmente
(vid, olivo, cereza, pistacho, nogal, citrus — todos con ingreso bruto > USD 5.000/ha).

| Escenario | Ha globales | Precio/ha/año | TAM Software ARR |
|---|---|---|---|
| Conservador (Tier 1 mínimo) | 34.550.000 | USD 80/ha | **USD 2.764 M/año** |
| Central (mix Tier 1-2) | 34.550.000 | USD 120/ha | **USD 4.146 M/año** |
| Premium (mix Tier 2-3) | 34.550.000 | USD 180/ha | **USD 6.219 M/año** |

#### TAM Hardware (venta única — ciclo de reposición 5-7 años)

```
34.550.000 ha / 1,5 ha por nodo = 23.033.333 nodos
23.033.333 nodos × USD 950 promedio = USD 21.882 M
Amortizado 5 años de ciclo de reposición = USD 4.376 M/año
```

#### TAM LATAM — el número relevante para la conversación de Series A

| Región | Ha tecnificadas | Software TAM ARR | Hardware TAM (5 años) |
|---|---|---|---|
| Argentina | 447.700 | USD 53,7 M | USD 425 M |
| Chile | 307.000 | USD 36,8 M | USD 292 M |
| Perú (Año 3) | 400.000+ | USD 48,0 M | USD 380 M |
| Colombia / Ecuador | ~200.000 | USD 24,0 M | USD 190 M |
| **LATAM TOTAL** | **~1.355.000** | **USD 162,5 M/año** | **USD 1.287 M** |

**TAM LATAM combinado (software recurrente + hardware amortizado + datos/seguros/carbono):**
```
USD 162,5 M/año + USD 257,4 M/año (HW/5) + USD 45 M/año (datos/seg.) = ~USD 465 M/año
```

#### Corrección al doc-06

El doc-06 (sección 8.3.4) declara "valor de producción en riesgo de USD 498M anuales" como
proxy del TAM. **Eso NO es el TAM** — es el problema que la solución resuelve. El TAM es la
fracción de ese valor que el mercado pagaría como servicio. La distinción es crítica ante
evaluadores ANPCyT y ante inversores seed.

---

### 1.2 SAM — Serviceable Addressable Market

**El error de construcción en doc-06:** la sección 8.3.4 define SAM como "~450.000 ha en
Argentina y Chile" pero antes afirma que Argentina + Chile tienen 850.000 ha con riego
tecnificado. La diferencia no está explicada. Un evaluador va a preguntar.

**Respuesta correcta:** el SAM no es "todas las ha con riego tecnificado" sino el segmento
que puede extraer el valor completo del sistema en los próximos 5 años.

#### Filtros de reducción aplicados al SAM

| Filtro | Reducción | Razonamiento |
|---|---|---|
| Solo riego por goteo/microaspersión (excluye manto) | −35% | Con riego a manto solo Tier 1-2. Adopción más lenta, menor LTV. |
| Superficie ≥ 5 ha (escala mínima viable económicamente) | −12% | ROI marginal en lotes < 5 ha para el costo de instalación mínima |
| Cultivos en portfolio activo HydroVision (6 cultivos) | −5% | Otros cultivos requieren calibración adicional no disponible en TRL 4-5 |
| Canal comercial disponible en regiones prioritarias | −8% | Zonas sin red de advisors activos en TRL 4-5 |

#### SAM resultante por región (Año 3 — Perú activo)

| Región | Ha base | Accesibilidad | SAM ha | Precio avg | SAM Software ARR |
|---|---|---|---|---|---|
| Argentina (vid+olivo+pistacho+cerezo) | 447.700 | 65% | 291.000 | USD 100/ha | USD 29,1 M |
| Chile (vid+olivo+arándano) | 307.000 | 70% | 214.900 | USD 105/ha | USD 22,6 M |
| Perú (arándano+espárrago) | 400.000 | 40% | 160.000 | USD 90/ha | USD 14,4 M |
| **TOTAL SAM** | **1.154.700** | | **665.900 ha** | | **USD 66,1 M/año** |

**SAM total 5 años (suscripción + hardware):**
```
Suscripción 5 años:  USD 66,1 M/año × 5 = USD 330,5 M
Hardware one-time:   665.900 ha / 1,5 × USD 950 = USD 421,7 M
SAM 5 años total:    USD 730 M
```

---

### 1.3 SOM — Serviceable Obtainable Market

**Principio:** el SOM es el único número que un inversor seed valida con el equipo actual.
Debe calcularse bottom-up desde la capacidad operativa real — no top-down desde el mercado.

#### Restricciones operativas reales (bottom-up)

| Driver | Año 1 post-TRL4 | Año 2 | Año 3 |
|---|---|---|---|
| Personal comercial activo | César + 1 advisor | +2 advisors | +4 advisors |
| Visitas de instalación | 1 nodo/2h → 4/día | 8/día | 16/día |
| Capacidad de producción nodos | 50 nodos/mes | 200 nodos/mes | 500 nodos/mes |
| Soporte técnico post-venta | Lucas + 1 técnico | +2 técnicos | +4 técnicos |

#### SOM por canal — proyección bottom-up

| Canal de adquisición | Ha Año 1 | Ha Año 2 | Ha Año 3 | Supuesto validable |
|---|---|---|---|---|
| Viñedo propio Colonia Caroya | 0,3 ha | 0,3 ha | 0,3 ha | Controlado — cero CAC |
| Convenios Sociedades Rurales / cámaras | 0 | 250 ha | 800 ha | 2 convenios Año 1, 5 prod./convenio Año 2 |
| Clientes directos via advisors Mendoza | 50 ha | 350 ha | 1.200 ha | 3 advisors × 5 clientes × 25 ha avg |
| Olivo San Juan (crisis hídrica driver) | 50 ha | 450 ha | 1.500 ha | 1 bodega piloto Año 1, 5 Año 2 |
| Cereza / pistacho (alto valor) | 0 | 80 ha | 300 ha | 1 operador cereza Año 2 |
| Chile (Año 2+ — Ley de Riego) | 0 | 200 ha | 1.500 ha | Alianza distribuidora local |
| **TOTAL SOM** | **100 ha** | **1.330 ha** | **5.300 ha** | |

#### SOM en revenue

| Año | Ha activas | ARR suscripción | Hardware | Revenue total |
|---|---|---|---|---|
| 1 (post-ANPCyT) | 100 ha | USD 9.500 | USD 60.000 (63 nodos) | **USD 69.500** |
| 2 | 1.330 ha | USD 133.000 | USD 560.000 (588 nodos) | **USD 693.000** |
| 3 | 5.300 ha | USD 583.000 | USD 1.590.000 (1.667 nodos) | **USD 2.173.000** |

**Break-even operativo:** 800 ha → alcanzado en **Q2 del Año 2** según esta proyección.

#### Reconciliación con doc-06

| Métrica | doc-06 (sección 8.3.5) | Este análisis | Diferencia |
|---|---|---|---|
| Ha Año 3 | 10.000 ha | 5.300 ha | Doc-06 más agresivo en penetración |
| ARR Año 3 | USD 1,1 M | USD 583.000 | Doc-06 = solo suscripción, scale más alto |
| Revenue total Año 3 | no declarado | USD 2,17 M | Este doc incluye hardware |
| Break-even | 800 ha | 800 ha | Consistente |

**Cuándo usar cuál:**
- Para ANPCyT: ARR puro USD 583K Año 3 (conservador, creíble)
- Para inversores seed: revenue total USD 2,17M Año 3 (incluye hardware, con mix explicado)
- Para proyección optimista (2% SAM penetración): 13.318 ha, USD 1,46M ARR Año 3

---

### 1.4 Mapa de calor del SOM — dónde concentrar primero

| Región | ROI del cliente | Disposición a pagar | Competencia local | Prioridad |
|---|---|---|---|---|
| Mendoza — Valle de Uco | 10,4x Año 1 | Alta (exportación) | Ninguna | ★★★★★ |
| San Juan — Olivo | 4,9x Año 2 | Alta (crisis agua) | Ninguna | ★★★★★ |
| Córdoba — viñedo propio | 4,6x Año 1 | Media (piloto local) | Ninguna | ★★★★☆ |
| Chile — Zona Central | 3,5x estimado | Alta (megasequía) | Baja | ★★★☆☆ |
| NOA / Patagonia | 3x estimado | Media | Ninguna | ★★☆☆☆ |

**Recomendación de foco:** los primeros 800 ha que llevan al break-even deben concentrarse
en Mendoza (Valle de Uco) y San Juan exclusivamente. Son los mercados con mayor ROI del
cliente, sin competencia directa, y con el canal comercial más accesible desde Colonia Caroya.

---

### 1.5 Resumen ejecutivo TAM/SAM/SOM

| Métrica | Software recurrente | Hardware | Total |
|---|---|---|---|
| TAM Global | USD 4.146 M/año | USD 4.376 M/año | **USD 8.522 M/año** |
| TAM LATAM | USD 162,5 M/año | USD 257 M/año | **USD 465 M/año** |
| SAM (5 años) | USD 330,5 M (5yr) | USD 399,5 M | **USD 730 M (5yr)** |
| SOM Año 3 | USD 583.000 ARR | USD 1,59 M | **USD 2,17 M Año 3** |
| Break-even ARR | USD ~80.000 (800 ha Tier 1 avg) | cubre COGS | **Q2 Año 2** |

---

### 1.6 Las 5 Oportunidades Desatendidas

Brechas de mercado activas que ningún competidor está cubriendo hoy. Si HydroVision
no las capitaliza explícitamente, se convierte en "un sensor más".

#### OD-1 — El mercado de reconversión: capturar al cliente ANTES de que el goteo llegue

**Brecha:** ~200.000 ha pasarán de riego a manto a goteo en LATAM en los próximos 5 años
(Chile: Ley de Riego activa; Argentina: programas provinciales Mendoza/San Juan).
Todas las soluciones actuales — incluyendo HydroVision en su plan actual — asumen que el
cliente YA tiene goteo. Nadie se posiciona para llegar CON la instalación del goteo.

**Mecanismo:** partnership de canal con Netafim Argentina, Rivulis, Irritrol distribuidores
regionales. El instalador de goteo ofrece HydroVision como upsell en la propuesta.
Revenue-share 10-15% al canal. CAC = USD 0 para HydroVision.

**Cuantificación:**
```
200.000 ha en reconversión × 30% penetración vía canal goteo = 60.000 ha adicionales SOM
60.000 ha × USD 120/ha ARR = USD 7,2 M ARR adicional en Año 5
```

**Acción requerida:** paquete de instalación conjunta documentado + acuerdo de canal
formalizado. Decisión de go-to-market, no de desarrollo de producto.

---

#### OD-2 — Certificación de huella hídrica: el compliance europeo como driver de adopción

**Brecha:** EU Green Claims Directive + ISO 14046 + EUDR crean obligación creciente de
verificación hídrica para exportadores de vino y AOVE a Europa. Ningún sistema en LATAM
genera registros auditables de: timestamp del riego + ψ_stem en ese momento + razón de
activación + agua ahorrada vs. riego por calendario. HydroVision los genera automáticamente.

**Producto derivado:** "Módulo HV-Water Certified" — reporte mensual de Water Stress Days
(WSD) por zona, exportable en formato ISO 14046, firmado digitalmente con validación
INTA-CONICET. Precio adicional: USD 30-50/ha/año sobre el tier base.

**Cuantificación:**
```
~500 bodegas exportadoras Mendoza con certificación activa o en proceso
× USD 800/año por certificado de lote
= USD 400.000 ARR solo compliance (sin contar los nodos que deben comprar)
Vidicultura argentina exportadora + EVOO Chile exportador = USD 8 M/año TAM
```

**Ventana de captura:** 2025-2026 (antes de que sea obligatorio = diferenciación premium).
Después de 2027 se convierte en commodity de compliance con menor WTP.

---

#### OD-3 — Diagnóstico de infraestructura de goteo: la ineficiencia invisible

**Brecha:** Drip systems tienen 90-95% de eficiencia de aplicación pero solo 70-80% de
uniformidad de distribución (INA-CRA Mendoza / Schilardi et al. 2015). El 20-30% de
emisores está distribuyendo agua desigualmente — pero el controlador solo ve el promedio
de zona. El productor que invirtió USD 8.000/ha en goteo cree que está regando uniformemente.
No está.

**Lo que HydroVision puede detectar:** a densidad 1 nodo/ha, la variabilidad espacial de
CWSI post-riego que NO se explica por suelo o fenología indica emisor obstruido o presión
diferencial. Patrón estable entre temporadas = causa de infraestructura, no climática.

**Producto derivado:** reporte automático al final de la temporada con zonas donde el CWSI
es sistemáticamente más alto de lo esperado dado el riego aplicado, probabilidad de causa
(emisor vs. suelo vs. variedad), y recomendación de inspección. Costo marginal para
HydroVision: USD 0 (el sensor ya está instalado). Valor para el cliente: evitar pérdida del
15-25% de rendimiento en las plantas afectadas por el emisor.

**Timing:** Año 2 — requiere una temporada de datos para establecer el baseline.

---

#### OD-4 — Distribución off-grid: ventaja estructural de canal, no diferencial técnico

**Brecha:** ~35% de la superficie productiva argentina en NOA, Patagonia y alta cordillera
de Cuyo no tiene cobertura celular suficiente para sistemas cloud-first. Todos los
competidores globales (Phytech, SEMIOS, CropX) necesitan conectividad constante — están
estructuralmente excluidos de estos territorios.

**Lo que HydroVision tiene:** LoRaWAN privado + edge AI + deep sleep 8µA + conectividad dual (router 4G donde hay cobertura, Starlink Mini donde no). Opera en cualquier punto del país sin infraestructura de telecomunicaciones.

**Canal derivado:** los distribuidores de agroquímicos e insumos en zonas remotas (cooperativas
agrarias locales, técnicos INTA zonales, distribuidores BASF/Syngenta rurales) no tienen
nada que ofrecer en monitoreo hídrico porque todos los sistemas disponibles necesitan internet.
HydroVision podría ser el único producto de monitoreo hídrico de planta que esos distribuidores
pueden vender — sin competencia, con máximo poder de fijación de precio.

**Cuantificación:**
```
20% de las 447.700 ha argentinas en zonas sin conectividad para competidores = 89.500 ha
89.500 ha × USD 95/ha avg = USD 8,5 M/año mercado estructuralmente exclusivo
Sin competencia efectiva = potencial de price premium 15-25% sobre precio base
```

---

#### OD-5 — Datos agroclimáticos certificados: el activo de datos no monetizado

**Brecha:** Con 50+ lotes activos, HydroVision tendrá el único dataset de correlación
directa entre temperatura foliar medida + MDS + ψ_stem + VPD + GDD + satélite para Malbec,
Olivo, Cereza y Pistacho en condiciones de Cuyo. No existe en ninguna fuente pública.

**Compradores identificados:**
- Aseguradoras (MAPFRE, La Segunda): calibración de siniestros hídricos sin peritaje manual
- Semilleras / viveros vitícolas: ensayos de tolerancia varietal al estrés hídrico
- Mercados de carbono (Verra VCS): verificación de reducción de huella hídrica
- Bodegas premium: trazabilidad de campaña por parcela para certificación export

**Modelo de monetización:** Data-as-a-Service (DaaS) con API de acceso para terceros.
Datos anonimizados y agregados — sin comprometer privacidad del productor.

**Cuantificación:**
```
50 lotes activos (Año 2) → activación del modelo de datos
Precio acceso API: USD 2.000-10.000/año por variedad/región
5 compradores × USD 5.000 avg = USD 25.000 ARR inicial Año 2
Escala con base de datos: USD 80.000-200.000 ARR en Año 4-5
```

**Requisito previo:** cláusulas de privacidad y propiedad de datos en los contratos
de suscripción desde Año 1. Si no se incluyen ahora, los datos de los primeros clientes
quedan bloqueados para monetización futura.

---

## MÓDULO 2 — AJUSTE PROBLEMA-SOLUCIÓN

### 2.1 Matriz de los 10 problemas

| # | Problema | Urgencia | WTP | Tipo de dolor | Función comercial |
|---|---|:---:|:---:|---|---|
| P1 | Estrés hídrico detectado tarde (5-10 días post-daño) | 9 | 8 | Consciente, mal atribuido | **ADQUISICIÓN** |
| P2 | Riego por calendario/suelo — señal incorrecta | 7 | 6 | Semi-latente | ADQUISICIÓN (requiere reframe) |
| P3 | Sin mapa espacial — qué zona está en estrés | 8 | 8 | Consciente | **ADQUISICIÓN** |
| P4 | Monitoreo episódico — el estrés entra en 3 días | 7 | 7 | Consciente en usuarios de drone | ADQUISICIÓN |
| P5 | Riesgo catastrófico en cultivos premium | 10 | 9 | Consciente (traumático) | **ADQUISICIÓN — mayor WTP** |
| P6 | Señal térmica corrompida por viento (Zonda) | 6 | 3 | **Latente** | Retención / credibilidad técnica |
| P7 | Estadio fenológico incorrecto → umbrales equivocados | 6 | 5 | Semi-latente | Upsell (requiere reframe) |
| P8 | Sin evidencia verificada de huella hídrica | 5→9* | 7/2** | Consciente solo en exportadores | Segmento específico |
| P9 | Blackout de datos durante fumigación | 3 | 2 | **Completamente latente** | Feature de retención invisible |
| P10 | Baseline Tc_wet deriva — recalibración cara | 5 | 4 | **Latente técnico** | Argumento win-back Phytech |

*Urgencia P8: 5/10 ahora → 9/10 post-2027 (EU Green Claims enforcement)
**WTP P8: 7/10 exportadores premium / 2/10 mercado doméstico

---

### 2.2 Análisis detallado por problema

#### P1 — Detección tardía del estrés · Urgencia 9 · WTP 8

**El problema:** La planta manifiesta daño metabólico (cierre estomático, reducción de
fotoasimilados, aborto floral) 5-10 días antes del síntoma visual. Las alternativas
existentes fallan en la ventana crítica: satélite bloqueado por nubes hasta 15 días,
drone máximo 2 veces/semana, tensiómetro mide suelo con desfase 2-5 días, inspección visual
del productor cada 7-14 días.

**Por qué WTP = 8 y no 10:** el productor atribuye la pérdida de rendimiento al clima,
no a la detección tardía. El WTP sube a 9-10 cuando se tiene un caso documentado de
"alerta preventiva específica en este lote → rendimiento recuperado medible". El viñedo
propio de Colonia Caroya debe generar ese caso en la primera temporada TRL 4. Es el
argumento de ventas más poderoso del portfolio y debe documentarse explícitamente.

**Posicionamiento correcto:** "Detectamos el evento del 15 de enero 9 días antes que el
drone semanal. El CWSI llegó a 0.67 durante 4 horas. Activamos alerta. El productor regó.
Recuperó el 12% de rendimiento que habría perdido." — no "nuestro sistema detecta antes".

---

#### P2 — Riego por señal incorrecta · Urgencia 7 · WTP 6

**El problema:** El tensiómetro mide tensión matricial del suelo, no estado hídrico de la
planta. Desfase 2-5 días entre suelo seco y daño metabólico documentado. En días de VPD
extremo (4-6 kPa en Cuyo), la planta puede entrar en estrés en < 24 horas con suelo
aparentemente bien hidratado.

**⚠️ WTP solo 6 — reframe necesario:** el productor con drip instalado cree que hace lo
correcto porque compara contra manto. Su frame es "tengo riego eficiente". No dice "mi
señal de riego está equivocada". El frame correcto: "Tienes riego de precisión instalado.
Te falta la última capa: saber si la planta recibió el agua exactamente cuando la necesitó.
HydroVision es esa última capa." Esto valida la inversión existente en lugar de cuestionarla.

---

#### P3 — Sin mapa espacial del lote · Urgencia 8 · WTP 8

**El problema:** Un lote de 50 ha no es homogéneo. Diferencias de textura de suelo,
exposición solar, y uniformidad de distribución del goteo (70-80%) generan respuesta
hídrica distinta por zona. El productor riega el lote completo con una única decisión.
Sin señal por zona, sobre-riega donde no es necesario y bajo-riega donde importa.

**Por qué WTP = 8 (muy sólido):** el productor con riego por goteo ya pagó USD 3.000-8.000/ha
por infraestructura de precisión. Decirle que sus solenoides pueden activarse por zona
según el estado real de cada planta es completar la inversión que ya hizo, no vender algo
nuevo. La fusión Sentinel-2 — un mapa de estrés del lote completo visible en el celular —
es el producto mínimo viable más convincente disponible para este problema.

**Argumento de cierre para Tier 3:** "Tienes solenoides Rain Bird instalados. HydroVision
los activa según la fisiología real de la planta en cada zona, no según un timer. Sin obra
adicional."

---

#### P4 — Monitoreo episódico vs. continuo · Urgencia 7 · WTP 7

**El problema:** Un drone vuela 1-2 veces/semana en condiciones óptimas. Un evento de
estrés que cruza el umbral de daño durante floración puede instalarse y causar aborto floral
en 48-72 horas — invisible entre dos vuelos. El costo de un vuelo no capturado durante
floración es irreversible.

**WTP = 7:** segmento con mayor WTP para este problema = productores que ya contratan
servicio de drone térmico y experimentaron la frustración de "los datos llegaron dos días
tarde". Son el cliente de conversión más fácil. Para productores que nunca usaron ningún
sistema, el argumento de continuidad requiere cuantificar el riesgo: "pierdes estadísticamente
una ventana crítica por temporada sin saberlo. El costo de esa ventana es X."

---

#### P5 — Riesgo catastrófico en cultivos premium · Urgencia 10 · WTP 9

**El problema:** En cereza de exportación, un déficit hídrico de 48 horas en el período
de engorde del fruto desclasifica el lote completo: de export-premium (USD 4-8/kg) a
industrial (USD 0.8-1.5/kg). Diferencia en 10 ha: USD 180.000-300.000 por evento.
En pistacho, el estrés durante floración produce frutos vanos (cáscara vacía, sin semilla)
con pérdida documentada 15-30% del rendimiento. Probabilidad de evento sin monitoreo: 1 cada
3 temporadas.

**WTP = 9 — el segmento con mayor WTP del portfolio:** aquí el argumento de ventas NO es
ROI ni payback. Es eliminación de riesgo catastrófico. La conversación correcta:
"Un evento de desclasificación en 12 ha de cereza cuesta USD 260.000. La suscripción Tier 3 Precisión
5 años cuesta USD 17.400. El sistema paga el seguro de un riesgo que ocurre estadísticamente
una vez cada 3 años." Cualquier productor que ya perdió un lote por estrés no detectado
paga inmediatamente.

**Acción requerida:** este segmento (cereza premium, pistacho export) debe ser el primer
cliente pagante, no el quinto. CAC es mínimo porque el dolor es máximo.

---

#### P6 — Señal térmica corrompida por viento · Urgencia 6 · WTP 3

**El problema técnico:** Viento produce enfriamiento convectivo artificial de la
hoja que reduce su temperatura 1-2°C. El CWSI calculado sub-estima el estrés real.
En San Juan, el Zonda ocurre 15-30 días/temporada. El sistema implementa 9 capas de
mitigación (orientación sotavento, shelter SHT31, tubo colimador IR, termopar foliar,
buffer térmico con filtro de calma, rampa gradual 4-18 m/s / 14-65 km/h que reduce
progresivamente el peso del CWSI, y backup 100% MDS a partir de 18 m/s / 65 km/h).

**🔴 WTP = 3 — ADVERTENCIA:**
El productor no sabe que este problema existe. Nunca recibió un CWSI corregido por viento
— no tiene referencia de lo que pierde con datos incorrectos. **Este feature no cierra
ninguna venta en la primera conversación.** Se vuelve apreciado solo después de la
instalación cuando el usuario ve días donde el sistema dijo "anemómetro activo — CWSI
suspendido — MDS como señal principal" y la planta efectivamente tenía estrés.

**Cómo posicionarlo correctamente:** no como feature a explicar, sino como garantía
incluida — "datos correctos en cualquier condición meteorológica, incluyendo viento".
El argumento Phytech sí funciona: "Phytech no tiene anemómetro. En un día de Zonda en
San Juan, ¿cómo sabes si el CWSI que te muestra es real?"

---

#### P7 — Timing fenológico impreciso · Urgencia 6 · WTP 5

**El problema:** El CWSI de alarma en floración es 0.30 (aborto floral si se supera).
El de envero es 0.60 (RDI intencional para concentración). Un umbral genérico de 0.50
aplicado a todo el ciclo sobre-alarma en envero y sub-alarma en floración — exactamente
al revés de lo que se necesita. El GDD automático detecta el estadio y ajusta el umbral
sin configuración humana.

**⚠️ WTP = 5 — condicional al reframe:**
Los productores experimentados creen que conocen su fenología mejor que cualquier sensor.
Objeción frecuente: "llevo 20 años con este viñedo, sé cuándo florece." El WTP sube de 5
a 7 cuando se conecta con variabilidad interanual: "¿Hubo algún año donde la floración
llegó 12 días antes de lo esperado por calor primaveral súbito?" La respuesta es siempre sí.
El GDD captura esa variabilidad. El productor que perdió floración temprana por imprevisión
entiende inmediatamente. Necesitas ese caso, no la explicación técnica del GDD.

---

#### P8 — Sin evidencia verificada de huella hídrica · Urgencia 5→9 · WTP 7/2

**El problema:** EU Green Claims Directive + ISO 14046 + expansión EUDR a gestión hídrica
obligan a exportadores a respaldar afirmaciones de sustentabilidad con datos verificables.
Ningún sistema en LATAM genera registros auditables de: timestamp del riego + ψ_stem en
ese momento + razón de activación + cantidad de agua ahorrada. HydroVision los genera
automáticamente en cada ciclo.

**⚠️ WTP fuertemente segmentado — advertencia:**
WTP = 7/10 para el ~20% del SAM que exporta a UE.
WTP = 2/10 para el ~80% del SAM que vende en mercado doméstico.
**Riesgo:** si HydroVision invierte recursos de desarrollo en el módulo de certificación
antes de tener contratos firmados con bodegas exportadoras, está gastando para una fracción
menor del mercado. Desarrollar este módulo solo si hay 2-3 bodegas exportadoras que
confirman WTP antes de escribir código.

**Ventana óptima:** 2025-2026 (adopción proactiva = diferenciación premium de 15-25% sobre
precio base). Post-2027 se convierte en commodity de compliance con menor margen.

---

#### P9 — Blackout de datos durante fumigación · Urgencia 3 · WTP 2

**El problema técnico:** Cada fumigación contamina el lente de la cámara térmica con
aerosol, generando lecturas corruptas por 24-48 horas. Con 8-14 fumigaciones por
temporada: 80-200 horas de datos inválidos o ausentes. El PMS5003 detecta el evento
(PM2.5 > 200 µg/m³), invalida las capturas térmicas, y el MDS continúa como señal de
respaldo verificada.

**🔴 WTP = 2 — ADVERTENCIA MUY SERIA:**
El productor nunca tuvo datos continuos durante fumigaciones — no sabe que los está
"perdiendo". La premisa de "cobertura garantizada durante fumigación" asume un frame de
referencia que el cliente todavía no tiene.

**Regla de posicionamiento:** Este es un feature de RETENCIÓN exclusivamente. No aparece
en el pitch de ventas. Aparece en el onboarding del mes 2 cuando el primer evento de
fumigación ocurre y el sistema muestra "fumigación detectada — datos térmicos suspendidos
— MDS activo como respaldo". Ese momento de fidelización tiene alto impacto en retención
pero cero impacto en adquisición.

---

#### P10 — Recalibración del baseline Tc_wet · Urgencia 5 · WTP 4

**El problema técnico:** Si el Tc_wet baseline se desplaza 0.5°C (contaminación del panel,
cambio microclima estacional), el error sistemático en CWSI es ±0.10-0.15 — suficiente
para falso-alarmas o eventos no detectados. Phytech requiere visita técnica periódica
(USD 800-1.500 en Argentina). HydroVision se auto-calibra: cada evento de lluvia con MDS≈0
recalibra el baseline via EMA sin visita humana.

**⚠️ WTP = 4 — advertencia:**
Para productores nuevos, "recalibración automática" implica que "puede descalibrarse" —
genera desconfianza si se explica mal. Para ex-usuarios de Phytech con facturas de
mantenimiento, el WTP sube a 7-8 inmediatamente.

**Cómo comunicar:** Nunca usar la palabra "calibración" en el pitch comercial masivo.
Frame correcto: "El sistema aprende tu viñedo específico durante la primera temporada. Cada
lluvia ajusta sus parámetros al microclima real de cada nodo. No necesita técnico ni genera
costos de mantenimiento imprevistos." WTP del mismo beneficio: 6.
Argumento específico para win-back Phytech: "¿Cuánto pagaste en visitas de recalibración
el año pasado?"

---

### 2.3 Priorización estratégica

#### Cuadrante de valor comercial

```
WTP
 9  │                                    [P5] Riesgo catastrófico
    │
 8  │   [P1] Detección tardía     [P3] Mapa espacial
    │
 7  │   [P4] Monitoreo continuo            [P8] Export compliance*
    │
 6  │   [P2] Riego por fisiología
    │
 5  │                  [P7] Fenología
    │
 4  │                                           [P10] Baseline
    │
 3  │             [P6] Viento
    │
 2  │                                           [P9] Fumigación
    └────────────────────────────────────────────────── Urgencia
         3    4    5    6    7    8    9   10

* WTP 7 solo para exportadores (~20% del SAM)
```

#### Los 3 problemas que cierran ventas (zona de prioridad máxima)

| Problema | Score | Razón de prioridad |
|---|---|---|
| P5 — Riesgo catastrófico | 10×9=90 | Payback < 4 meses. WTP = seguro de vida del lote. |
| P1 — Detección tardía | 9×8=72 | Core problem. Ancla toda la propuesta de valor. |
| P3 — Mapa espacial | 8×8=64 | Completa la inversión en goteo que el cliente ya hizo. |

#### Los 3 problemas que abren mercados secundarios

| Problema | Score | Condición de activación |
|---|---|---|
| P8 — Export compliance | 5×7=35 | Solo exportadores. Desarrollar post-Gate 1 con commitment previo. |
| P4 — Monitoreo continuo | 7×7=49 | WTP alto en usuarios de drone existentes. Argumento de conversión. |
| P2 — Riego por fisiología | 7×6=42 | Necesita reframe "completa tu inversión en goteo". |

#### Los 4 problemas a NO vender como beneficios primarios

| Problema | WTP | Acción recomendada |
|---|---|---|
| P6 — Viento/Zonda | 3 | Bundlear en garantía "datos correctos en cualquier condición". |
| P9 — Fumigación | 2 | Feature de retención. Comunicar en onboarding, nunca en pitch. |
| P10 — Baseline | 4 | Argumento win-back Phytech. Evitar palabra "calibración". |
| P7 — Fenología | 5 | Upsell post-instalación. Reframe como "nunca más pierdas floración por sorpresa". |

---

### 2.4 Advertencia sistémica — sesgo de construcción interna

Cuatro de los diez problemas que HydroVision resuelve tienen WTP bajo (P6, P7, P9, P10).
Todos comparten la misma raíz: **fueron descubiertos durante el desarrollo técnico, no
articulados por el cliente antes de que el producto existiera.** Eso no los hace falsos —
los hace no-vendibles de forma aislada.

La arquitectura de producto es sólida. La arquitectura del discurso de ventas debe
concentrarse en P1, P3, P5 como argumentos de cierre, y usar P6/P9/P10/P7 exclusivamente
como argumentos de credibilidad técnica y diferenciación frente a Phytech.

---

## RESUMEN EJECUTIVO — MÓDULOS 1 Y 2

### Números clave corregidos (este análisis vs. doc-06)

> **Estado abril 2026:** doc-06 sección 8.3.4 ya fue corregida en base a este análisis.
> Las columnas "doc-06 original" reflejan el texto anterior a la corrección — útiles para
> entender por qué se cambió. Los valores de "Este análisis" son ahora los vigentes en ambos documentos.

| Métrica | doc-06 original | Este análisis (vigente) | Corrección aplicada |
|---|---|---|---|
| TAM declarado | "34,5M ha" + "USD 498M valor en riesgo" — ambos presentados como TAM | USD 8.522 M/año global / USD 465 M/año LATAM (en revenue capturable) | **Corregido en doc-06:** se separó valor en riesgo (el problema) del TAM (lo que el mercado paga como servicio) |
| SAM | "~450.000 ha" (Argentina+Chile, filtros no documentados) | 665.900 ha (ARG+CHL+PER, 4 filtros explícitos) | **Corregido en doc-06:** 665.900 ha con filtros documentados, Perú incluido a partir de Año 3 |
| SOM Año 3 | "22.500 ha / USD 3,37M ARR" | 5.300 ha / USD 2,17M total (USD 583K ARR) | **Corregido en doc-06:** penetración conservadora; total incluye hardware |
| ARR puro Año 3 | USD 1,1M (en sec. 8.3.5) | USD 583.000 | Para ANPCyT: usar USD 583K (conservador). Para inversores: USD 2,17M con hardware. |
| Break-even | "1.000 ha" en algunos párrafos / "800 ha" en sec. 8.3.3 | 800 ha / Q2 Año 2 | Pendiente: verificar que ningún párrafo de doc-06 todavía diga "1.000 ha" |

### Posicionamiento central — la categoría que HydroVision debe definir

HydroVision no compite en el mercado de "sensores de riego" (Phytech compite ahí).
HydroVision define una categoría nueva: **inteligencia fisiológica de planta en tiempo
real con doble señal + fusión satelital + autonomía total**. En LATAM, esa categoría
tiene TAM de USD 465M/año y competencia efectiva cero — porque todos los actores globales
tienen al menos uno de estos tres problemas estructurales: coeficientes mal calibrados para
el hemisferio sur, dependencia de internet que los excluye geográficamente, o señal única
que los hace técnicamente inferiores.

La condición para no ser "una más": el equipo debe comunicar que está creando una
categoría nueva, no ingresando a una existente.

---

## MÓDULO 3 — ANÁLISIS COMPETITIVO

### 3.1 Las cinco fuerzas de Porter — HydroVision AG en el mercado AgTech de stress hídrico

---

#### Fuerza 1 — Amenaza de nuevos entrantes · Nivel: MEDIO (horizonte 3-5 años)

**Barreras de entrada existentes:**

| Barrera | Solidez | Argumento |
|---|---|---|
| Datos de calibración hemisferio sur | Alta | Los coeficientes VPD para Malbec/Olivo en Cuyo (4-6 kPa) tardan 2+ temporadas de campo en construirse. No existen en literatura pública con la granularidad que HydroVision ya tiene validada con Mariela Monteoliva. |
| Modelo PINN entrenado + validado | Alta | El PINN con física CWSI embedded en loss function requiere datos de campo simultáneos (Tc_wet, Tc_dry, ψ_stem, VPD real). Un competidor necesita al menos 1 temporada de datos propios para iniciar entrenamiento — y no puede usar los datos de HydroVision. |
| Red de validación institucional (INTA-CONICET) | Media-Alta | El aval de Mariela Monteoliva + protocolo de campo conjunto es una credencial que los productores reconocen. Un nuevo entrante sin validación institucional local enfrenta resistencia comercial, especialmente en segmento Tier 1-2. |
| Patente de combinación dual CWSI + MDS | Media | En proceso. Si se otorga, blinda la arquitectura de fusión de señales como diferenciador estructural. Un competidor puede hacer solo CWSI o solo MDS — la combinación con PINN es la ventaja. |
| Costo de capital inicial | Media | USD 120K de ANPCyT + USD 30K equipo ya ejecutados. Un replicador privado sin subsidio necesita financiamiento propio — posible pero no inmediato. |

**Vulnerabilidades reales de la barrera:**

- Los componentes son commodity (MLX90640 ~USD 30, SX1276 ~USD 5, STM32 ~USD 3). El hardware puede replicarse en 4-6 meses por un equipo competente.
- El software de pipeline térmico (13 módulos Python publicados en el repositorio del proyecto) podría servir de guía a un competidor si se hace público sin licencia.
- Un laboratorio universitario bien financiado (Israel Tech, Wageningen, UC Davis) podría entrar en LATAM en 2-3 años si el mercado escala.

**Conclusión Fuerza 1:** La barrera real no está en el hardware (replicable) ni en el algoritmo base (publicado en literatura). Está en los **datos de campo calibrados para el hemisferio sur** y en la **red institucional**. Ambas toman tiempo, no dinero. Ventana de exclusividad efectiva: 3-5 años si la ejecución es rápida.

---

#### Fuerza 2 — Poder de negociación de proveedores · Nivel: MEDIO-ALTO (riesgo concentrado)

**Dependencias críticas de componentes:**

| Componente | Proveedor único | Alternativa viable | Riesgo |
|---|---|---|---|
| MLX90640 (breakout integrado TRL4 / bare chip producción) | Melexis (Bélgica) | AMG8833 (8×8 px — resolución insuficiente) | **ALTO** — sin alternativa directa a 32×24 px en rango de precio |
| SX1276 LoRaWAN | Semtech (EE.UU.) | RFM95W (Hope RF, mismo chip licenciado) | BAJO — mercado commodity |
| STM32 MCU | STMicroelectronics | ESP32 (Espressif) | BAJO — sustituible con rediseño de firmware |
| Panel de referencia emisividad | Artesanal (PTFE/anodizado) | Múltiples proveedores | MUY BAJO |
| SHT40 (T/HR meteo) | Sensirion (Suiza) | HDC1080, BME280 | BAJO |

**El problema específico con Melexis:**
El MLX90640 tuvo escasez de stock en 2021-2023 (post-COVID semiconductor shortage). El precio varió de USD 28 a USD 68 en ese período. Con el modelo de negocio actual (nodo a USD 950–1.000, COGS ~USD 149), una suba del MLX90640 a USD 80+ comprime el margen de hardware en ~5 puntos porcentuales.

**Mitigación recomendada:**
1. Stock de seguridad 6 meses de MLX90640 una vez confirmado el primer contrato de volumen (≥ 50 nodos).
2. Diseño de módulo breakout alternativo para sensor térmico de resolución próxima (Heimann HMS-C11L 16×16, Melexis MLX90641 16×12) — mismo conector I2C, solo variante de firmware MicroPython.
3. Cláusula de ajuste de precio de hardware en contratos de suscripción multianual: "precio de hardware sujeto a variación de componentes ±15%".

---

#### Fuerza 3 — Poder de negociación de compradores · Nivel: BAJO-MEDIO (segmentado)

**El mercado de compradores es profundamente heterogéneo:**

| Segmento de comprador | Poder de negociación | Razón |
|---|---|---|
| Bodegueas premium integradas (Catena, Zuccardi, Peñaflor) | **ALTO** | Pueden negociar contratos de 500-2.000 ha, tienen área técnica que evalúa alternativas, pueden pedir exclusividad temporal o condiciones especiales. |
| Viticultor independiente 30-100 ha | **BAJO** | No tiene alternativa comparable disponible en LATAM. No tiene área técnica para negociar cláusulas técnicas. Precio fijado por HydroVision. |
| Cooperativas y cámaras sectoriales | **MEDIO** | Pueden negociar precio por volumen pero no tienen poder técnico para cuestionar la propuesta de valor. El convenio de canal (ver OD-1) convierte el poder del comprador en un activo de adquisición. |
| Olivicultores San Juan | **BAJO** | Sin alternativa directa. Crisis hídrica + menor sofisticación tecnológica = disposición a adoptar sin negociación agresiva. |

**Costos de switching — el argumento más poderoso contra el poder del comprador:**

Después de 2 temporadas de uso, el costo de cambiar de HydroVision a cualquier alternativa incluye:
- Pérdida del baseline Tc_wet calibrado por nodo (~2 temporadas de datos)
- Pérdida del modelo PINN ajustado a su variedad/microclima específico
- Pérdida del histórico GDD + fenología correlacionado con datos de rendimiento
- Reentrenamiento del equipo agronómico
- Período sin datos de hasta 1 temporada (ventana de instalación del competidor)

**Estimación de switching cost real:** USD 3.000-8.000 equivalente en productividad perdida y tiempo de reentrenamiento por lote de 50 ha. A ese costo, el precio de suscripción (USD 5.000/año en Tier 2 a 50 ha) resulta en un LTV/Switching Cost de ~3× — cliente altamente retenido.

---

#### Fuerza 4 — Amenaza de productos sustitutos · Nivel: MEDIO (en segmento masivo) / BAJO (en segmento premium)

**Mapa de sustitutos disponibles:**

| Sustituto | Precio referencia | Por qué sustituye | Por qué no sustituye completamente |
|---|---|---|---|
| Drone térmico + análisis manual | USD 180-300/ha/vuelo × 15-20 vuelos = USD 2.700-6.000/ha/temp | Imagen térmica de calidad, resolución alta | Episódico (2x/semana máximo), climadependiente (no vuela con viento), sin continuidad, sin integración meteo, sin MDS, latencia 24-48h para análisis |
| Tensiómetro / Watermark | USD 200-400 por punto + instalación | Medición de humedad suelo barata | Mide suelo, no planta. Desfase 2-5 días. Sin espacialización. VPD extremo en Cuyo invisible para el suelo. |
| Sap flow sensor | USD 500-800 por árbol | Señal de transpiración real de planta | No funciona en viña (flujo xilemático complejo). Requiere instalación invasiva. Mantenimiento alto. Sin mapa espacial. |
| Estación meteorológica + ET₀ (Penman-Monteith) | USD 1.500-3.000 hardware | Cobertura continua, bajo costo por ha | Modelo, no medición directa de planta. Sin señal fenotípica. Error +30-40% en eventos VPD extremo. |
| Satélite libre (Sentinel-2, NDVI/NDWI) | USD 0 | Cobertura total del lote, gratis | Resolución 10-20m (no planta individual). Revisita 5-12 días. Bloqueado por nubes 60% del tiempo en Cuyo en dic-ene. |
| Phytech Israel | USD 1.200-1.800/nodo + USD 200-350/ha/año | MDS dendrométrico real de planta | Solo MDS (sin señal térmica). Sin fusión satelital. Sin GDD automático. Requiere internet. Coeficientes calibrados para Israel (VPD 2-3 kPa) — error en Cuyo (VPD 4-6 kPa). |
| SEMIOS (Canadá) | USD 2.000-3.000/nodo + USD 400-600/ha/año | Suite completa de monitoreo | Cultivos de América del Norte. Sin validación en vid/olivo de LATAM. Sin off-grid. |
| CropX | USD 350-700/nodo + USD 80-150/ha/año | Bajo costo, sensor de suelo | Mide suelo, no planta. Sin señal fisiológica directa. Sin mapa térmico. |

**Conclusión Fuerza 4:** Ningún sustituto tiene simultaneamente: (1) señal fisiológica directa de planta, (2) continuidad 24/7, (3) fusión satelital de lote completo, (4) calibración hemisferio sur, (5) autonomía off-grid. HydroVision tiene los cinco. Cada competidor tiene como máximo dos.

En segmento Tier 1 (productores < 50 ha, bajo presupuesto), el tensiómetro + calendario sigue siendo el sustituto con mayor amenaza por precio (USD 400 vs. USD 9.500+ de HydroVision en instalación). La brecha se cierra con el argumento de ROI y gestión de riesgo catastrófico, no con comparación técnica.

---

#### Fuerza 5 — Rivalidad entre competidores existentes · Nivel: BAJO actualmente / MEDIO en 24-36 meses

**Competidores directos en LATAM con capacidades equivalentes: ninguno.**

| Actor | Presencia LATAM | Capacidades reales | Amenaza temporal |
|---|---|---|---|
| Phytech Israel | Argentina (< 30 nodos activos estimados, Mendoza) | MDS real, plataforma cloud robusta, 15 años de datos | Media — ya presente, pero sin térmica, sin off-grid, sin LATAM-calibrado |
| BASF Digital Farming (xarvio) | Regional (10 países LATAM) | Modelos agronómicos, satélite, sin hardware propio | Baja para stress hídrico físico — es software de decisión, no sensor de planta |
| John Deere Operations Center | Regional | Integración maquinaria, NDVI satélite | Baja para cultivos permanentes (foco en granos) |
| Startups locales (CONAE spinoffs, INTA incubadas) | Puntual | Prototipo académico, sin producto comercial | Baja hoy, media en 36 meses si obtienen financiamiento ANPCyT propio |
| Aerodron / drones service | Regional | Vuelo sobre demanda, imagen térmica puntual | Baja — complementario no competidor (HydroVision puede fusionar sus datos) |

**El escenario de rivalidad que más importa vigilar:**
Un competidor bien financiado no entraría construyendo el hardware (demasiado lento) sino **comprando o licenciando** la señal de planta que le falta. Escenarios concretos:
- Phytech añade cámara térmica de bajo costo a su nodo dendrométrico (factible en 12-18 meses de ingeniería)
- John Deere adquiere una startup de sensores térmicos en campo y la integra en su plataforma Operations Center
- BASF lanza un kit de hardware propio para xarvio (ya lo intentó con FieldView en 2019-2021, cancelado por márgenes)

**Acción preventiva:** patentar antes de publicar el método de fusión CWSI+MDS con PINN. El know-how en datos de campo no es patentable — el método de cómputo sí.

---

### 3.2 Canvas de Estrategia Océano Azul

La estrategia de océano azul requiere identificar qué factores de competencia se pueden eliminar, reducir, aumentar o crear para construir una curva de valor diferente a todos los actores existentes.

#### 3.2.1 Canvas ERRC — Eliminar / Reducir / Aumentar / Crear

**ELIMINAR** — factores que la industria da por obligatorios pero que tienen costo sin generar valor real:

| Factor eliminado | Quién lo mantiene (y por qué es un error) |
|---|---|
| Dependencia de conectividad celular/internet constante | Phytech, SEMIOS, CropX — diseñados para mercados con infraestructura confiable. En LATAM rural, esa dependencia excluye el 35% del territorio productivo. |
| Visitas técnicas periódicas para recalibración | Phytech requiere 1-2 visitas técnicas/año. Es ingreso para el proveedor pero costo operativo + fricción para el cliente. |
| Configuración manual del calendario fenológico | Todos los sistemas requieren que el agrónomo ingrese "estoy en floración". El GDD automático de HydroVision lo calcula sin intervención. |
| Panel de control complejo con decenas de métricas | El productor Tier 1-2 necesita una pantalla: "¿riego hoy o mañana?" — no un dashboard de telemetría industrial. |

**REDUCIR** — factores donde la industria sobreinvierte sin retorno proporcional:

| Factor reducido | Reducción HydroVision vs. industria |
|---|---|
| Costo de hardware por nodo | USD 950–1.000 vs. USD 1.200-3.000 de Phytech/SEMIOS (reducción 17-67%) |
| Tiempo de instalación por nodo | 2 horas vs. 2 días (Phytech requiere perforación de árbol para dendrometría invasiva) |
| Tasa de falsas alarmas | Dual signal CWSI+MDS reduce falsas alarmas vs. señal única (estimado: de 22% a < 5% en días de VPD extremo) |
| Latencia de detección de estrés | De 5-10 días (drone semanal) a < 6 horas (CWSI continuo + PINN) |

**AUMENTAR** — factores donde la industria opera por debajo de lo que el mercado necesita:

| Factor aumentado | Nivel HydroVision vs. industria |
|---|---|
| Precisión en condiciones VPD extremo (Cuyo) | Coeficientes calibrados para 4-6 kPa (vs. coeficientes Israel/California a 2-3 kPa de Phytech) |
| Cobertura espacial del lote | Fusión Sentinel-2: mapa de estrés de lote completo (vs. 1 punto de medición de Phytech) |
| Autonomía operativa sin técnico | Auto-calibración por lluvia + edge AI + deep sleep 8µA (vs. mantenimiento periódico requerido por competidores) |
| Continuidad durante eventos disruptivos | PMS5003 detecta fumigación, anemómetro detecta viento: datos válidos o suspensión documentada 24/7 |

**CREAR** — factores que no existen en ningún producto actual del mercado:

| Factor creado | Descripción | Valor para el cliente |
|---|---|---|
| Categoría: inteligencia fisiológica autónoma | No es sensor, no es app, no es consultoría: es un sistema que toma decisiones de riego sin intervención humana en condiciones de emergencia | El cliente no opera el sistema — el sistema opera para el cliente |
| Calibración explícita para Malbec/Olivo/Cereza en hemisferio sur | Coeficientes fenológicos + umbrales CWSI validados para variedades y condiciones que no existen en ninguna base de datos pública ni competidor | Reduce error sistemático de modelos globales en +30-40% en Cuyo |
| Registro auditable de huella hídrica compatible ISO 14046 | Timestamp + ψ_stem estimado + razón de activación de riego en cada evento — exportable para certificación | Único sistema en LATAM que habilita EU Green Claims Directive + EUDR sin trabajo adicional |
| Diagnóstico automático de infraestructura de goteo | Variabilidad espacial de CWSI post-riego → mapa de emisores con eficiencia subóptima | Protege la inversión en infraestructura de riego ya realizada — el cliente no compra un sensor, completa su sistema |
| Operación off-grid total sin compromiso de función | LoRaWAN privado + edge AI + conectividad dual (4G/Starlink) + batería 18 meses standby | Único sistema en LATAM funcional sin infraestructura de telecomunicaciones |

---

#### 3.2.2 Lienzo de estrategia — perfil de valor comparado

Escala 1 (bajo) a 5 (alto). El "perfil" es qué tan bien cada actor cubre cada factor.

```
Factor de valor                  HydroVision  Phytech   Drone     Tensiómetro  Satélite
─────────────────────────────────────────────────────────────────────────────────────────
Señal directa de planta               5          4        3           2            1
Continuidad temporal 24/7             5          4        1           3            1
Cobertura espacial del lote           4          1        5           1            4
Precisión en VPD extremo (Cuyo)       5          2        3           2            2
Autonomía sin internet                5          1        3           5            4
Costo de acceso (inverso)             4          2        2           5            5
Velocidad de instalación              4          2        5           3            5
Calibración hemisferio sur            5          1        3           2            2
Certificación hídrica (ISO 14046)     5          1        1           1            1
Diagnóstico de infraestructura        4          1        2           1            1
─────────────────────────────────────────────────────────────────────────────────────────
TOTAL                                46         19       28          25           26
```

**Lectura estratégica:** HydroVision tiene un perfil de valor con puntuación 2.4× superior al segundo competidor más fuerte (drone térmico, 28). El Drone tiene alta cobertura espacial pero sin continuidad. Phytech tiene señal de planta buena pero en prácticamente todos los demás factores queda debajo. **No hay un actor que sea simultáneamente fuerte en señal directa de planta + continuidad + cobertura espacial + off-grid + calibración local.** Esa combinación define el océano azul.

---

### 3.3 Posicionamiento diferencial por segmento

Cada segmento tiene un frame de problema distinto, una propuesta de valor distinta, y un
argumento de cierre distinto. Usar el mismo pitch para todos los segmentos es el error más
común y más costoso en ventas B2B AgTech.

---

#### Segmento A — Bodeguera premium de exportación (Catena, Zuccardi, Achaval, Clos de los 7)

**Perfil:** 200-2.000 ha propias + uvas contratadas. Mercado principal UE/EE.UU. Precio de botella ≥ USD 18 exportación. Dirección técnica (enólogo + jefe de viñedo) con presupuesto autónomo. Ya usan drone térmico esporádico o han evaluado Phytech.

**Dolor principal:** riesgo de desclasificación de parcela en cosecha (P5) + creciente obligación de evidencia de huella hídrica para mercados UE (P8).

**Propuesta de valor para este segmento:**
> "HydroVision es el único sistema en LATAM que combina monitoreo continuo de stress hídrico de planta con generación automática de registros de huella hídrica auditables bajo ISO 14046 — sin trabajo adicional. Sus parcelas de exportación quedan cubiertas frente a EU Green Claims Directive desde la próxima temporada."

**Argumento de cierre:** "Un evento de desclasificación en 20 ha de Malbec Gran Reserva cuesta en promedio USD 340.000 en diferencial de precio. El contrato Tier 3 Precisión 3 años para 200 ha cuesta USD 174.000 total. Eso es 33 centavos de seguro por cada dólar de riesgo cubierto."

**Precio:** Tier 3 — USD 189/ha/año. Paquete mínimo viable: 50 ha contrato 2 años.

**Objeción esperada:** "Ya tenemos un equipo agronómico que hace el seguimiento." Respuesta: "Su equipo agronómico puede tomar mejores decisiones con datos continuos de fisiología de planta que complementan su conocimiento del viñedo — no lo reemplaza. El sistema los hace más eficientes, no redundantes."

---

#### Segmento B — Viticultor independiente Mendoza / Valle de Uco (30-200 ha)

**Perfil:** Familia propietaria o sociedad de productores. Venta a bodegas integradas o cooperativa. Riego por goteo instalado. Budget técnico USD 5.000-20.000/año. Sin equipo técnico propio, usa servicio de asesor agronómico externo 1-2 veces/semana.

**Dolor principal:** detectar estrés antes del síntoma visual (P1) + saber qué zona del lote está en estrés real (P3).

**Propuesta de valor para este segmento:**
> "HydroVision te dice exactamente cuándo y en qué zona de tu viñedo regar, antes de que la planta muestre daño. Tu asesor recibe la misma información que tú — en el celular, en tiempo real. Instalación en 2 horas, sin obra, sin perforar árboles."

**Argumento de cierre:** "El goteo que instalaste costó USD 180.000. HydroVision te dice si cada zona lo está recibiendo en el momento que la planta lo necesita. Es la última capa que le faltaba a tu sistema de precisión."

**Precio:** Tier 1-2 — USD 95-120/ha/año. Paquete piloto: 20 ha × 1 temporada = USD 1.900-2.400 (entrada mínima para probar ROI).

**Canal:** advisors agronómicos de Mendoza (ver OD-1). El asesor existente del productor se convierte en el canal de venta — no en el comprador.

---

#### Segmento C — Olivicultor San Juan (zona de crisis hídrica crónica)

**Perfil:** Productor de olivo para aceite (EVOO o aceite grado industrial). 50-500 ha. Riego por goteo instalado en mayoría. Bajo consumo de agua del acueducto con cupos variables por decreto provincial. Asesora: INTA San Juan (relación directa posible).

**Dolor principal:** riego por fisiología vs. por suelo (P2) + detección tardía en períodos de restricción hídrica forzada (P1).

**Propuesta de valor para este segmento:**
> "San Juan tiene 40% menos disponibilidad de agua en cupos que hace 10 años. HydroVision te dice qué planta está en estrés real y cuál puede esperar 24 horas más — para que cada litro de tu cupo vaya exactamente donde lo necesita. Sin desperdiciar agua donde no es necesaria. Sin perder rendimiento donde sí lo era."

**Argumento de cierre:** "Con restricción de cupo, cada m³ mal asignado es aceite perdido. HydroVision paga su suscripción con el primer evento de restricción bien manejado."

**Precio:** Tier 1 — USD 85/ha/año (ajustado a menor ingresos/ha de olivicultura vs. vid de exportación).

**Canal:** INTA San Juan (nodo técnico de confianza para productores de la zona). Si Mariela Monteoliva puede conectar con técnicos de San Juan, la adopción es directa sin CAC de ventas.

---

#### Segmento D — Productor de cereza y pistacho export (alta cordillera Mendoza/San Juan)

**Perfil:** Operador especializado de alto valor. 15-80 ha de cereza o pistacho para exportación fresca (cereza) o gourmet (pistacho). Ingresos brutos USD 8.000-20.000/ha en años buenos. Un evento de estrés en período crítico = catástrofe económica total del lote.

**Dolor principal:** riesgo catastrófico (P5) — único y exclusivo. Todo lo demás es secundario.

**Propuesta de valor para este segmento:**
> "Una sola vez que HydroVision active una alerta real antes de que tu cereza muestre daño, el sistema se pagó para los próximos 7 años. Un solo evento de desclasificación en 15 ha de cereza premium cuesta USD 250.000. Nuestra suscripción Tier 3 Precisión para esas 15 ha cuesta USD 4.350/año."

**Argumento de cierre:** "¿Cuántas temporadas sin perder un lote necesitas para que este seguro sea aceptable? La respuesta correcta es: una."

**Precio:** Tier 2-3 — USD 140-189/ha/año. Máximo WTP del portfolio. Máxima urgencia. **Este segmento debe ser el primer cliente pagante de HydroVision** — no el quinto.

---

#### Segmento E — Productores off-grid (NOA, Patagonia, alta cordillera sin cobertura celular)

**Perfil:** Productor en zonas sin cobertura celular confiable (NOA: Salta, Jujuy, Tucumán; Patagonia: Río Negro, Neuquén; alta cordillera mendocina). Cultivos mixtos (vid, ciruela, pera, manzana, espárrago andino). Sin opción de usar ningún sistema cloud-first.

**Dolor principal:** exclusión estructural de todas las soluciones de monitoreo disponibles. Ni siquiera es un problema resuelto mal — no existe solución.

**Propuesta de valor para este segmento:**
> "Todos los sistemas de monitoreo hídrico que existen necesitan internet para funcionar. HydroVision no. Opera con LoRaWAN privado entre nodos y gateway local, guarda los datos en el dispositivo, y sincroniza cuando hay conectividad disponible (WiFi, satélite, USB). Si tienes campo, tienes sistema."

**Precio:** Base + 20% premium por off-grid configuration = USD 870/nodo + USD 95-115/ha/año.

**Canal:** distribuidores de agroquímicos e insumos rurales en zonas remotas (ver OD-4). Este canal no tiene nada que ofrecer en monitoreo hídrico — HydroVision es el único producto. El margen de canal (15%) crea alineación de intereses.

---

### 3.4 Mapa de posicionamiento competitivo — resumen visual

```
                    SEÑAL DE PLANTA
                    (fisiológica directa)
          Alta  │
                │         [HydroVision]
                │           ★ off-grid
                │           ★ calibrado Cuyo
     Phytech ●  │           ★ dual signal + fusión
                │
         Drone  │
         Térmico│
                │
          Baja  │
    Tensiómetro ●─────────────────────────── COBERTURA ESPACIAL
         Satélite              Baja         Alta
                 
   Lectura: HydroVision ocupa el cuadrante (señal alta × cobertura alta)
   que ningún competidor actual habita. Es la definición del océano azul.
```

---

### 3.5 Conclusiones del Módulo 3 — lo que el equipo debe recordar

**1. El diferenciador más defendible no es el hardware.**
Es la combinación de: datos de campo calibrados para hemisferio sur + PINN entrenado con esos datos + red institucional INTA-CONICET. Ningún competidor puede comprar eso en 6 meses.

**2. Phytech es el único competidor que merece atención estratégica.**
Todos los demás tienen sustitución parcial (drone, tensiómetro) o están en otros mercados (SEMIOS, CropX). Phytech tiene la señal de planta real — le falta la térmica, la fusión satelital y la calibración local. Si lanza esos tres en 18 meses, el posicionamiento se complica. La respuesta: patentar el método de fusión CWSI+MDS+PINN antes de esa fecha.

**3. El océano azul tiene una condición: comunicar que es una categoría nueva.**
Si el equipo vende HydroVision como "un sistema de monitoreo hídrico más barato que Phytech", compite en océano rojo y pierde en escala. Si vende "el único sistema de inteligencia fisiológica autónoma para cultivos de LATAM, calibrado para condiciones de Cuyo", crea una categoría donde no tiene competidor.

**4. El segmento D (cereza/pistacho) debe ser el primer cliente pagante.**
No el más fácil — el más estratégico. Tiene la urgencia más alta (P5), el WTP más alto (9/10), y el caso de éxito documentado en ese segmento es el argumento de ventas más poderoso para todos los demás segmentos.

---

---

## MÓDULO 4 — MODELO DE NEGOCIO PROFUNDO

### 4.1 Unit Economics — un nodo, un cliente, una hectárea

Antes de construir proyecciones de cohorte, los unit economics deben estar calculados
con precisión por tier. Si el margen por nodo o por hectárea no cierra, ninguna escala
lo arregla.

---

#### 4.1.1 Costo de un nodo — estructura real

| Componente | Costo unitario | Notas |
|---|---|---|
| MLX90640 breakout integrado (Adafruit 4407) | USD 50 | TRL4 módulo breakout. Vol. 500+: bare chip USD 22-25 + PCB custom |
| SX1276 LoRaWAN (EBYTE E32-900T20D) | USD 5 | Commodity |
| ESP32-S3 DevKit (off-the-shelf, MicroPython) | USD 10 | DevKit elimina PCB custom para TRL4 |
| SHT31 breakout (T/HR meteorológico) | USD 4 | Sensirion, I2C |
| ICM-42688-P IMU | USD 3 | SPI, detección instalación/vandalismo |
| PMS5003 (fumigación PM2.5) | USD 8 | Plantower, incluye cable |
| Panel referencia emisividad | USD 6 | PTFE + anodizado aluminio negro, artesanal |
| Extensómetro MDS (dendrómetro) | USD 18 | Banda elástica + strain gauge + ADC |
| ~~PCB custom~~ | USD 0 | **Eliminada TRL4** — DevKit + breakouts I2C/SPI. Vol. 500+: PCB custom USD 12 |
| Carcasa Hammond IP67 200×150×100mm + montaje | USD 22 | Más robusta, espacio para módulos breakout |
| Batería LiFePO4 3.2V 6Ah | USD 14 | 18+ meses en deep sleep 8µA |
| Cargador solar 6W (panel) + MPPT | USD 9 | Con regulador MPPT integrado |
| Cables I2C Stemma QT/Qwiic + conectores | USD 4 | Cableado modular plug & play |
| Tubo colimador IR (PVC 110mm×250mm) | USD 3 | Bloquea flujo lateral de aire sobre MLX90640 |
| Termopar foliar (Type T 0.1mm + MAX31855 + clip) | USD 6 | Ground truth T_leaf por contacto, corrección IR en tiempo real |
| **COGS total por nodo** | **USD 149** | Precio lote 50 unidades (arquitectura modular TRL4) |
| **COGS con volumen 500+** | **USD 121** | Bare chip + PCB custom + descuentos Melexis |

**Precio de venta:**
- Tier 1 (Monitoreo): USD 950 → margen bruto hardware = USD 810 (85%)
- Tier 2 (Automatización): USD 1.000 → margen bruto hardware = USD 860 (86%)
- Tier 3 (Precisión): USD 1.000 → margen bruto hardware = USD 844 (84%)

> Nota: COGS no incluye mano de obra de ensamblado final (Lucas + técnico: ~45 min/nodo).
> A USD 15/hora: USD 11,25 adicionales. Margen real Tier 1: ~USD 574 (79%).

---

#### 4.1.2 Costo de adquisición por cliente (CAC) — por canal

| Canal | CAC estimado | Justificación |
|---|---|---|
| Viñedo propio (Colonia Caroya) | USD 0 | Cero — el equipo es propietario |
| INTA-CONICET (Mariela Monteoliva) | USD 0 | Referencia institucional, no paga CAC |
| Advisor agronómico existente | USD 300-600 | Comisión 5-10% primer contrato + onboarding |
| Sociedad Rural / cámara sectorial | USD 800-1.500 | Costo presentación, materiales, tiempo |
| Canal goteo (Netafim/Rivulis) | USD 0-200 | Revenue share 10-15% — no es CAC, es margen cedido |
| Venta directa (Mendoza/San Juan) | USD 1.500-3.000 | Viaje + demo + seguimiento comercial |
| Chile (Año 2+) | USD 4.000-8.000 | Distribuidora local + traducción + viaje |

**CAC promedio ponderado proyectado Año 1-2:** USD 900 por cliente nuevo
(mix viñedo propio + INTA + 3 clientes directos Mendoza + 1 San Juan).

---

#### 4.1.3 LTV — Lifetime Value por cliente

Supuestos de retención: el switching cost real (ver 3.1 Fuerza 3) produce churn rate
proyectado ≤ 8%/año después de la primera temporada. Esto da una vida media del cliente
de 12,5 años (1/0,08). Para modelar conservadoramente, usar 7 años.

**LTV por hectárea (Tier 2, 50 ha, contrato 2 años mínimo):**

```
ARR suscripción:        USD 120/ha/año
Costo servicio/ha/año:  USD 12 (cloud + soporte + actualizaciones)
Margen contribución:    USD 108/ha/año
Vida media cliente:     7 años
LTV/ha:                 USD 108 × 7 = USD 756/ha

Hardware inicial (1 nodo/1,5 ha = 33 nodos):
Margen hardware:        USD 632/nodo × 33 = USD 20.856
Hardware amortizado 7 años: USD 2.979/año de margen hardware

LTV total cliente 50 ha:
Suscripción 7 años:     USD 756 × 50 = USD 37.800
Hardware inicial:       USD 20.856
Hardware reposición (Año 5): USD 9.856 margen (50% del parque)
LTV total:              ~USD 68.512 por cliente 50 ha
```

**Ratio LTV/CAC:**
- Canal advisor (CAC USD 600): LTV/CAC = 114×
- Venta directa (CAC USD 2.000): LTV/CAC = 34×
- Chile canal (CAC USD 6.000): LTV/CAC = 11×

Benchmark referencia: ratio LTV/CAC > 3× es viable. > 10× es excelente para SaaS.
HydroVision está en rango excepcional incluso con el canal más caro.

---

### 4.2 Modelo de revenue multi-capa — las tres fuentes no son intercambiables

La tentación de sumar hardware + suscripción + datos como "revenue total" oculta que
tienen lógicas completamente distintas que afectan la valoración de la empresa:

| Fuente | Tipo | Múltiplo de valoración | Previsibilidad | Acción clave |
|---|---|---|---|---|
| Suscripción SaaS | ARR recurrente | 8-15× ARR | Alta | Maximizar retención, minimizar churn |
| Venta hardware | One-time | 1-2× revenue | Lineal con nuevas ventas | Mantener margen, no subsidiar |
| Datos / DaaS | Non-recurring / comisión | 3-5× revenue | Impredecible hasta masa crítica | No vender hasta tener 50+ lotes |

**Implicación directa para el pitch a inversores:**

Un inversor seed valora una empresa con ARR USD 583K (Año 3) a ~8-12× ARR = USD 4,7-7,0M
de valoración implícita. Si además tiene USD 1,59M de hardware en ese año, no suma linealmente:
el hardware "contamina" el múltiplo. La forma correcta de presentar es:

> "ARR recurrente proyectado Año 3: USD 583K. Revenue total (incluyendo hardware one-time):
> USD 2,17M. Valoramos la empresa sobre el ARR — el hardware es upside no incluido en el múltiplo."

---

### 4.3 Análisis de cohortes — la curva de retención que importa

No hay datos históricos reales todavía (TRL 3-4). Lo siguiente es el modelo de cohortes
proyectado que debe ser validado con los primeros 5-10 clientes en TRL 5.

#### Cohorte Año 1 (primeros 5-8 clientes, ~100 ha)

| Mes | Evento esperado | Métrica de seguimiento |
|---|---|---|
| 0-1 | Instalación + onboarding | Tiempo hasta primera alerta generada (objetivo: < 14 días) |
| 1-3 | Primera temporada activa | NPS post-primera-temporada (objetivo: ≥ 70) |
| 3-6 | Renovación o churn | Tasa de renovación voluntaria (objetivo: ≥ 90%) |
| 6-12 | Expansión en mismo cliente | % clientes que amplían ha bajo contrato (objetivo: ≥ 40%) |
| 12 | Case study documentado | Al menos 1 caso con ROI medible en $$ para cada cultivo piloto |

**Los 3 indicadores leading que predicen retención:**

1. **Tiempo hasta primera alerta accionable:** si el sistema genera una alerta de estrés
   verificada en los primeros 30 días, la probabilidad de renovación sube a > 95%.
   Si no genera ninguna alerta en 60 días, el cliente asume que "no pasa nada" y el churn
   sube a 30-40%.

2. **Adopción del mapa de lote completo (Sentinel-2):** clientes que usan el mapa
   satelital tienen retención 2× mayor que los que solo ven el CWSI del nodo. El mapa
   crea comprensión espacial del lote — genera dependencia cognitiva del producto.

3. **Integración del asesor agronómico:** si el asesor del cliente adopta HydroVision
   como su herramienta de diagnóstico, el contrato se renueva automáticamente. El cliente
   no cancela el sistema que usa su asesor de confianza. Objetivo: conseguir que el
   asesor sea el campeón interno del producto.

---

### 4.4 Estructura de precios — lógica y límites

#### Por qué los tres tiers tienen sentido (y cuándo romperlos)

| Tier | Nombre | Precio/ha/año | Nodo incluye | Cliente objetivo | Condición de upgrade |
|---|---|---|---|---|---|
| 1 | Monitoreo | USD 80-110 | Sensor (sin relé) + alertas por WhatsApp / email (desactivables) + dashboard + Sentinel-2. El productor decide manualmente cuándo regar. | Productor < 30 ha, evaluación inicial, o cultivo donde el riego ya está 100% automatizado por otro sistema | Cuando quiere que el nodo decida y actúe |
| 2 | Automatización | USD 130-170 | T1 + relé SSR + solenoide. El nodo decide autónomamente cuándo regar según HSI (histéresis 0.30/0.20). Densidad 1/2-5 ha. | Productor 30-200 ha con goteo instalado | Cuando quiere máxima precisión + compliance |
| 3 | Precisión | USD 220-290 | T2 + alta densidad (1/1-2 ha) + HSI dual R²=0.90-0.95 + reporte ISO 14046 + DaaS + SLA | Bodeguera premium, cereza/pistacho export, certificación UE | Diferenciación vía contratos plurianuales |

**Cambio (abril 2026):** Tier 2 "Alerta" (LED+sirena) eliminado. El mercado objetivo es exclusivamente plantaciones con riego automatizado — alertas visuales/sonoras no aportan valor. El Tier 4 "Elite" se ofrece como add-on (dron, consultoría) sobre cualquier tier.

**Regla de pricing que no se debe romper:**
El precio mínimo de cualquier tier debe cubrir el break-even de ese cliente individualmente.
Con COGS hardware de USD 149 y COGS cloud/soporte de USD 12/ha/año, el Tier 1 a USD 80/ha/año
paga el servicio en 1.7 años y el hardware se cobra por separado al inicio.

**Actualización (abril 2026) — Modelo de comodato y precios fijos:**

El análisis de retención (ver doc-06 sección 8.2.5) y el análisis de competencia (Phytech USD 200-350/ha, CropX USD 80-150/ha) definieron los siguientes precios fijos publicados:

| Tier | Precio fijo publicado | Nodo en comodato | Justificación |
|---|---|---|---|
| 1 — Monitoreo | **USD 95/ha/año** | 1 cada 5 ha | Piso del SOM, 35% más barato que CropX, margen neto USD 83/ha |
| 2 — Automatización | **USD 150/ha/año** | 1 cada 3 ha | 30-55% más barato que Phytech, nodo se paga en 4 meses |
| 3 — Precisión | **USD 250/ha/año** | 1 cada 2 ha | Alineado a caso Luján de Cuyo (doc-06), < 3% ingreso bruto bodega premium |

**Cambio respecto al modelo anterior:** el hardware ya no se vende por separado — se entrega en comodato (propiedad de HydroVision AG). Esto elimina la barrera de entrada (el productor no paga USD 950+ de golpe), aumenta la retención (devolver nodos = alta fricción) y simplifica la propuesta comercial. El nodo (COGS USD 149) se recupera en ~4 meses de suscripción Tier 2. La regla de no subsidiar hardware se mantiene en el sentido de que el pricing cubre el COGS del nodo dentro del primer año.

**Compliance UE — oportunidad regulatoria:** La Directiva ECGT (sept 2026) prohíbe claims ambientales sin verificación independiente. HydroVision genera los datos de huella hídrica con resolución de 15 min y trazabilidad 365 días — requisito para certificación ISO 14046 / AWS v3.0 / PEF europeo. Premium de mercado verificado: +15% en precio de vino sustentable certificado. Ver doc-06 sección 8.2.4 para análisis completo.

---

## MÓDULO 5 — GO-TO-MARKET STRATEGY

### 5.1 Secuencia de mercados — el orden importa más que la velocidad

La tentación es atacar todos los mercados simultáneamente. El error es dispersar la ejecución
antes de tener un caso de éxito replicable. La regla: no pasar al siguiente mercado hasta
tener al menos 3 contratos renovados en el anterior.

#### Secuencia recomendada

```
Etapa 0 (NOW — TRL 4)     Etapa 1 (Año 1 post-TRL4)    Etapa 2 (Año 2)         Etapa 3 (Año 3+)
────────────────────────────────────────────────────────────────────────────────────────────────
Colonia Caroya             Cereza/Pistacho Mendoza       Olivo San Juan          Chile (canal goteo)
(viñedo propio)            [Segmento D — max WTP]        [Segmento C]            [distribuidora local]
                           Malbec Valle de Uco            Mendoza expansión       NOA/Patagonia off-grid
                           [Segmento B — volumen]         (Sociedades Rurales)    [Segmento E]
                                                          Bodegueras premium      Perú (Año 3)
                                                          [Segmento A — LTV alto] [espárrago/arándano]
```

**Por qué cereza/pistacho primero (Etapa 1):**
No porque sea el mercado más grande — es el más chico. Pero tiene WTP máximo (P5), el
caso de éxito documentado es el más impactante para ventas en cualquier otro segmento,
y el churn rate esperado es el más bajo del portfolio. Es el cliente perfecto para refinar
el producto y construir la primera referencia pagada.

---

### 5.2 Canales de adquisición — CAC, volumen y fit estratégico

| Canal | Tipo | CAC | Ha/año alcanzable | Fit estratégico |
|---|---|---|---|---|
| Viñedo propio | Control total | USD 0 | 0,3 ha | Referencia técnica, no escala |
| INTA/CONICET (Mariela) | Referencia institucional | USD 0 | 50-200 ha | Credibilidad en mercado conservador |
| Advisors agronómicos Mendoza | Comisión de canal | USD 300-600 | 500-2.000 ha | Escala con bajo CAC — prioridad |
| Cámaras sectoriales (COVIAR, ACOVI) | Alianza gremial | USD 1.000-2.000 (entry) | 1.000-5.000 ha | Volumen, pero ciclo largo |
| Canal goteo (Netafim/Rivulis) | Revenue share 12% | Costo oculto | 5.000-20.000 ha | OD-1: mayor escala potencial de todo el portfolio |
| Distribuidores insumos rurales | Margen 15% canal | USD 0-200 | 2.000-10.000 ha | OD-4: off-grid exclusivo, no tiene alternativa |
| Venta directa (César) | Tiempo propio | USD 1.500-3.000 | 100-500 ha | Solo para Tier 3 (LTV justifica el CAC alto) |
| Chile — distribuidora local | Alianza exclusiva | USD 5.000-8.000 setup | 3.000-15.000 ha | Año 2+, requiere acuerdo previo |

**El canal que más importa en Año 1: advisors agronómicos.**
Son el gatekeeper de decisiones tecnológicas para el 70% de productores medianos en
Mendoza. No venden — recomiendan. Si el asesor adopta HydroVision como su herramienta
de diagnóstico, el productor compra sin proceso de ventas adicional. CAC USD 300-600
con LTV USD 68K = la mejor relación del portfolio. Objetivo Año 1: 5 advisors activos.

---

### 5.3 Modelo de canal para advisors — la mecánica

El advisor agronómico no es un vendedor. Es un usuario técnico que da recomendaciones.
El modelo que funciona:

1. **Acceso gratuito al advisor:** el asesor accede al dashboard y la app SIN pagar. Su ROI
   es no tener que medir manualmente — ahorra 2-4 horas/semana de trabajo de campo en los
   lotes que asesora.

2. **El advisor no "vende" — demuestra:** en la primera visita post-instalación, el asesor
   le muestra al productor el mapa de estrés de su lote en el celular. "Mirá, esta zona
   tenía CWSI 0.62 el miércoles y no lo sabíamos." Eso convierte.

3. **Comisión por referencia:** el advisor recibe USD 300-600 por cada cliente que firma
   contrato de suscripción usando su código de referido. No es una comisión de vendedor —
   es un reconocimiento por la introducción.

4. **El advisor como soporte técnico primario:** en el modelo escalado, el advisor es la
   primera línea de soporte. HydroVision le da entrenamiento de 4 horas y acceso a la
   documentación técnica. Reduce la carga de soporte del equipo en ~60%.

**Objetivo de red de advisors:**
- Año 1: 5 advisors activos (Mendoza + San Juan)
- Año 2: 15 advisors activos (+ Valle de Uco + NOA + 2 Chile)
- Año 3: 40 advisors activos (LATAM regional)

---

### 5.4 Playbook de ventas por segmento — el proceso de 4 pasos

#### Segmentos B/C (viticultor independiente, olivicultor):

```
Paso 1 — Referencia (1 semana)
  Advisor o cámara sectorial hace la introducción.
  Sin esta referencia, el ciclo de ventas se triplica.

Paso 2 — Demo en el lote (2-4 horas)
  Llevar el nodo al campo del productor.
  Generar una imagen térmica del viñedo en 10 minutos.
  Mostrar en el celular. No hablar de CWSI todavía.
  El productor dice "eso es mi lote" — conversión en ese momento.

Paso 3 — Piloto gratuito 30 días (1 mes)
  Un nodo instalado en la zona crítica del productor.
  Sin cobro. Sin promesa de compra.
  En 30 días, el sistema genera al menos 1 evento de alerta relevante.
  Esa alerta vale más que cualquier presentación comercial.

Paso 4 — Propuesta y cierre (1 semana post-piloto)
  Mostrar el resumen de la temporada piloto: N alertas, fechas, CWSI pico.
  Proyectar el ROI con sus números reales.
  Propuesta con contrato 2 años + hardware al contado o financiado en 12 cuotas.
```

**Ciclo de ventas esperado:** 6-10 semanas con referencia / 16-24 semanas sin referencia.

#### Segmento A (bodeguera premium):

```
Paso 1 — Contacto via enólogo o jefe de viñedo (no el dueño)
  El técnico es el campeón interno. El dueño firma pero no evalúa.

Paso 2 — Presentación técnica con datos propios del lote
  Usar satélite Sentinel-2 para mostrar la variabilidad ya existente en SU lote.
  "Esta es la variabilidad térmica de su parcela Bloque 3 en diciembre pasado."
  Ese análisis previo (gratuito) demuestra que ya existe el problema.

Paso 3 — Propuesta contractual con SLA y reporte ISO 14046
  Para Tier 3 no hay piloto gratuito — proponer contrato de 1 temporada con
  devolución si la tasa de detección cae < 85%.

Paso 4 — Referencia interna para expandir a otras parcelas
  El primer contrato es 20-50 ha. El objetivo es 200-500 ha en el Año 2.
  El enólogo que ve los resultados en Bloque 3 pide expandir a toda la finca.
```

---

### 5.5 Estrategia de entrada a Chile (Año 2)

Chile tiene características que lo hacen diferente a Argentina:

| Factor | Argentina | Chile |
|---|---|---|
| Marco regulatorio hídrico | DGI provincial, cupos variables | Código de Aguas, Ley de Riego (subsidio 50% reconversión) |
| Driver de adopción | Crisis hídrica San Juan, ROI Mendoza | Megasequía activa, presión exportadora UE |
| Canal natural | Advisors agronómicos independientes | Agronomías distribuidoras integradas (venden y asesoran) |
| Barreras | Bajo contexto de adopción tecnológica en Tier 1 | Distribuidoras establecidas con poder de negociación alto |
| Precio de entrada | USD 95-120/ha | USD 105-140/ha (mayor PIB agrícola por ha) |

**Modo de entrada recomendado:** alianza exclusiva con una distribuidora agronómica
regional en la Región de O'Higgins o del Maule (ambas con alta densidad de vid y
olivicultura tecnificada). La exclusividad temporal (18 meses) a cambio de:
- Territorio asegurado sin competencia de canal
- Capacitación incluida para el equipo técnico de la distribuidora
- Revenue share 12% sobre hardware + 8% sobre suscripción por 3 años

**Precondición:** tener al menos 2 casos de éxito documentados en Argentina antes de
entrar. Un distribuidor chileno no adopta un producto nuevo sin referencias locales.

---

## MÓDULO 6 — VALIDACIÓN DE HIPÓTESIS

### 6.1 El error más caro en AgTech: construir antes de validar

HydroVision tiene 13 módulos Python, 15 drivers firmware, y un pipeline de sensores
riguroso. El riesgo no está en la tecnología — está en asumir que lo que el equipo
construyó resuelve exactamente el problema que el cliente pagaría por resolver.

Las hipótesis siguientes son suposiciones críticas que deben ser validadas con experimentos
mínimos antes de comprometer recursos de desarrollo adicionales.

---

### 6.2 Las 10 hipótesis críticas ordenadas por riesgo

| # | Hipótesis | Supuesto implícito | Experimento mínimo | Costo del error si es falsa |
|---|---|---|---|---|
| H1 | El productor actúa sobre la alerta en < 4 horas | Que hay persona disponible para responder | Medir tiempo de respuesta en piloto Colonia Caroya — 1 temporada | Si actúa en 24-48h, el CWSI continuo no da ventaja vs. drone semanal |
| H2 | El asesor agronómico adopta el dashboard sin resistencia | Que el técnico quiere más datos, no que los percibe como amenaza a su rol | Onboarding con 3 asesores reales antes del Año 1 comercial | Si el asesor resiste, el canal principal de adquisición no funciona |
| H3 | El cliente renueva el contrato después de 1 temporada | Que genera valor visible medible en 1 temporada | NPS post-primera-temporada en los primeros 5 clientes | Churn alto destruye el LTV/CAC calculado |
| H4 | El precio Tier 1 USD 80-95/ha es el punto de adopción masiva | Que USD 80 no es la barrera — que el problema es lo suficientemente urgente | Mostrar 3 propuestas sin precio y pedir al cliente que fije el precio que pagaría | Si el cliente paga espontáneamente < USD 50, el modelo no escala |
| H5 | El canal de advisors genera conversiones sin presión de ventas activa | Que la demostración en campo convierte sin pitch comercial | Medir tasa de conversión de demos sin argumento de precio | Si la demo no convierte, hay un problema de propuesta de valor, no de precio |
| H6 | La fusión CWSI+MDS reduce falsas alarmas vs. CWSI solo | Supuesto técnico central de la arquitectura dual-señal | Comparar tasa de falsas alarmas CWSI solo vs. HSI en mismos eventos de campo | Si no reduce falsas alarmas, la complejidad técnica dual no tiene justificación comercial |
| H7 | El módulo ISO 14046 tiene WTP real (no aspiracional) | Que los exportadores pagarían USD 30-50/ha/año adicional por el módulo | 3 entrevistas con directores técnicos de bodegas exportadoras con compromiso de compra condicional | Desarrollar el módulo sin commit previo = USD 20-30K de ingeniería para un mercado hipotético |
| H8 | Netafim/Rivulis actúa como canal de upsell sin fricción interna | Que el instalador de goteo quiere recomendar un producto que no fabrica | Reunión de exploración con gerente comercial de Netafim Argentina antes del Año 1 | Si Netafim rechaza la alianza, OD-1 (60.000 ha adicionales) no existe |
| H9 | El productor de cereza/pistacho identifica el riesgo catastrófico como problema principal | Que el dolor P5 es consciente y articulado, no latente | 5 entrevistas con productores que tuvieron un evento de pérdida en los últimos 3 años | Si el dolor es latente (atribuido al clima), el WTP real es < 5/10 y el segmento D deja de ser prioritario |
| H10 | El sistema puede instalarse en 2 horas sin técnico especializado | Supuesto operativo del modelo de escalado | Cronometrar la instalación con un agrónomo no técnico siguiendo el manual, sin asistencia del equipo | Si requiere 4+ horas o asistencia remota, el CAC real es 2× el proyectado |

---

### 6.3 Experimentos prioritarios — los que bloquean todo lo demás

**Experimento bloqueante #1 — H6: validación del doble-señal (ANTES de cualquier venta)**

Si HSI (CWSI+MDS) no es materialmente mejor que CWSI solo, la complejidad de la
arquitectura dual no está justificada y el pitch competitivo frente a Phytech se
debilita. Este es el único experimento técnico que debe ejecutarse en el viñedo propio
antes del primer contrato pagante.

```
Diseño: viñedo Colonia Caroya, temporada 2026-2027
- Zona A (5 plantas): CWSI solo (cámara MLX90640 sin extensómetro)
- Zona B (5 plantas): HSI = CWSI + MDS (sistema completo)
- Zona C (5 plantas): MDS solo (extensómetro sin térmica)
- Control: medición Scholander manual cada 3 días (Mariela Monteoliva)
Métrica: tasa de falsas alarmas (evento generado cuando ψ_stem > -1.0 MPa)
Umbral de éxito: HSI tiene < 50% de las falsas alarmas que CWSI solo
```

**Experimento bloqueante #2 — H1 + H5: comportamiento real del cliente bajo alerta**

No hay datos sobre qué hace el productor cuando llega una alerta. Si actúa en 4 horas,
el sistema tiene valor preventivo real. Si actúa en 2 días, el valor es principalmente
diagnóstico retroactivo (menor WTP).

```
Diseño: piloto pagante en 2-3 lotes Año 1
- Instrucción al cliente: actúa a tu ritmo habitual
- Medición: tiempo entre alerta generada y acción de riego documentada
- Encuesta post-temporada: "¿Cuántas veces la alerta llegó a tiempo para actuar?"
Umbral de éxito: > 70% de alertas respondidas en < 8 horas
```

---

### 6.4 Hipótesis que NO requieren experimento

Las siguientes hipótesis pueden considerarse validadas por proxy o por literatura:

| Hipótesis | Evidencia existente | Por qué no necesita experimento adicional |
|---|---|---|
| El CWSI detecta estrés antes del síntoma visual | Jackson et al. 1981 + 400+ papers validados | Probado en vid, olivo, frutales durante 40 años |
| La calibración Cuyo es diferente a Israel | VPD medido localmente (doc-02 sec. 3.2) | Dato físico medible, no hipótesis |
| El MDS de Malbec correlaciona con ψ_stem | Marsal & Ruiz, Fernández et al., + Monteoliva in-situ | Relación establecida en literatura + validación INTA |
| LoRaWAN funciona a 2 km en zona rural | Especificación SX1276 + mediciones campo | No es hipótesis de negocio — es física de RF |
| GDD detecta floración con error < 5 días | Winkler 1974 + ajustes DOY Cuyo en protocolo | Validable con registro histórico disponible |

---

## MÓDULO 7 — RISK REGISTER PARA INVERSORES

### 7.1 Metodología del registro

Cada riesgo se evalúa en dos dimensiones:
- **Probabilidad:** 1 (improbable) a 5 (casi certeza en 36 meses)
- **Impacto:** 1 (molestia operativa) a 5 (destruye el negocio)
- **Score = P × I** (máximo 25)
- **Riesgo residual:** después de las mitigaciones listadas

Orden de presentación: de mayor a menor Score inicial.

---

### 7.2 Riesgos técnicos

| ID | Riesgo | P | I | Score | Mitigación | Riesgo residual |
|---|---|:---:|:---:|:---:|---|:---:|
| RT-1 | MLX90640 escasez o discontinuación por Melexis | 3 | 4 | **12** | Stock 6 meses. Diseño PCB con footprint alternativo. Evaluar Heimann HMS-C11L como backup. | 6 |
| RT-2 | Calibración VPD Cuyo no generaliza a otras regiones (NOA, Chile) | 3 | 3 | **9** | Protocolo de recalibración regional (1 temporada + 5 plantas Scholander). Costo: 1 campaña de validación. | 4 |
| RT-3 | PINN over-fitting a Malbec — performance degradada en cereza/pistacho | 2 | 4 | **8** | Transfer learning desde modelo Malbec. Datos sintéticos del generador para preentrenamiento. Validación en campo Año 2 antes de venta masiva. | 3 |
| RT-4 | Extensómetro MDS falla por contaminación o vandalismo en campo | 3 | 2 | **6** | IP66 + ICM-42688 detecta vibración anómala. Respaldo CWSI como señal única si MDS no disponible. | 3 |
| RT-5 | Interferencia RF LoRaWAN 915 MHz en zonas con alta densidad de nodos | 2 | 2 | **4** | ADR (Adaptive Data Rate) en stack LoRaWAN. Máx. 200 nodos/gateway con gestión de canal. | 2 |

---

### 7.3 Riesgos de mercado

| ID | Riesgo | P | I | Score | Mitigación | Riesgo residual |
|---|---|:---:|:---:|:---:|---|:---:|
| RM-1 | Phytech lanza módulo térmico integrado y entra agresivamente en LATAM | 2 | 5 | **10** | Patentar método fusión CWSI+MDS+PINN antes de publicar. Acelerar calibración hemisferio sur como moat. Construir switching cost (datos de campo acumulados) en todos los contratos. | 6 |
| RM-2 | Adopción más lenta de lo proyectado — productores esperan referencia de par | 4 | 3 | **12** | Priorizar cereza/pistacho como primer cliente pagante (referencia de impacto máximo). Viñedo propio Colonia Caroya como demo permanente accessible. | 6 |
| RM-3 | Precio ANR ANPCyT no alcanza para completar TRL 4 según plan | 2 | 4 | **8** | Contrapartida equipo (USD 30K) como buffer. Priorizar experimentos bloqueantes H6 y H1 en TRL 4. Hardware core del nodo ya en prototipo funcional (mitigación parcial). | 4 |
| RM-4 | El canal de advisors no escala — asesores no quieren recomendar tecnología que no conocen | 3 | 3 | **9** | Onboarding técnico gratuito para advisors + acceso dashboard sin costo. Comunidad de usuarios (WhatsApp/Slack) entre advisors adoptantes. | 4 |
| RM-5 | Competidor local (spinoff INTA/CONICET) con subsidio público copia el modelo | 2 | 3 | **6** | Relación Monteoliva = primer mover advantage con el ecosistema INTA. El spinoff tendría el mismo problema de datos de calibración. Patente del método. | 3 |
| RM-6 | El módulo de compliance ISO 14046 no genera WTP real — desarrollo sin retorno | 3 | 2 | **6** | No desarrollar sin commit previo de 2-3 bodegas exportadoras (ver H7). El riesgo existe solo si se viola la regla de desarrollo condicional. | 1 |

---

### 7.4 Riesgos de equipo

| ID | Riesgo | P | I | Score | Mitigación | Riesgo residual |
|---|---|:---:|:---:|:---:|---|:---:|
| RE-1 | Concentración de conocimiento crítico en César (ML/pipeline) y Lucas (firmware) — el equipo no es redundante | 3 | 5 | **15** | Documentación técnica exhaustiva (ya iniciada — 13 módulos comentados). Incorporar 1 ML engineer junior en Año 2. Repositorio git con historial completo. | 8 |
| RE-2 | Mariela Monteoliva (INTA-CONICET) no formaliza el aval o cambia de institución | 2 | 4 | **8** | Formalizar convenio institucional INTA-UNC antes del cierre TRL 4. No depender de la persona — depender del acuerdo institucional. | 3 |
| RE-3 | Inv. Art. 32 no completa la validación estadística a tiempo para TRL 4 | 3 | 3 | **9** | Gate Review de Módulo ML en mes 6 (no esperar al mes 12). Si hay retraso, usar modelo de regresión física como fallback (menor precisión pero funcional). | 4 |
| RE-4 | Javier (app/UX) no logra interfaz adoptable para productor Tier 1 | 2 | 3 | **6** | Prototipo Figma testeable en campo antes de desarrollo. User testing con 3 productores reales en mes 4. "1 pantalla, 1 decisión" como criterio de diseño. | 2 |

---

### 7.5 Riesgos macro / contextuales

| ID | Riesgo | P | I | Score | Mitigación | Riesgo residual |
|---|---|:---:|:---:|:---:|---|:---:|
| RX-1 | Devaluación del peso argentino — encarece el hardware (MLX90640 se importa en USD) | 4 | 3 | **12** | Contratos en USD o ajustados por tipo de cambio oficial. Hardware cotizado y cobrado en USD desde el inicio. | 5 |
| RX-2 | Restricciones de importación Argentina — demora en componentes | 3 | 3 | **9** | Stock preventivo. Proveedor alternativo en Uruguay o Chile para reexportación. Evaluar importación via MERCOSUR para componentes críticos. | 4 |
| RX-3 | Temporada de sequía extrema Año 1 — baja el VPD a niveles atípicos y el CWSI pierde resolución | 1 | 2 | **2** | El CWSI pierde resolución en VPD < 1 kPa (raro en Cuyo). El MDS sigue siendo válido. El sistema no falla — degrada graciosamente. | 1 |
| RX-4 | ANPCyT cancela o retrasa el desembolso del ANR | 2 | 4 | **8** | Contrapartida del equipo (USD 30K) cubre 4-6 meses de operación mínima. Cronograma de trabajo prioriza entregables de bajo costo primero. | 4 |

---

### 7.6 Mapa de calor del risk register

```
IMPACTO
  5  │  RE-1★         RM-1          RT-1
     │  (15)          (10)          (12)
  4  │          RM-3  RE-2  RT-3    RT-2   RX-4
     │          (8)   (8)   (8)     (9)    (8)
  3  │  RM-2★   RE-3  RM-4  RX-2
     │  (12)    (9)   (9)   (9)
  2  │  RX-1    RM-5  RE-4
     │  (12)    (6)   (6)
  1  │
     └────────────────────────────── PROBABILIDAD
          1     2     3     4     5

★ = Riesgo con mayor score (requiere mitigación activa inmediata)
```

**Los 3 riesgos que deben tener plan de mitigación activo desde hoy:**

| Riesgo | Acción inmediata | Responsable | Plazo |
|---|---|---|---|
| RE-1 — Concentración de conocimiento | Completar documentación de todos los módulos críticos. Iniciar búsqueda de ML engineer junior. | César + Lucas | Mes 3 TRL 4 |
| RM-2 — Adopción lenta | Confirmar primer contrato pagante cereza/pistacho antes de cerrar TRL 4. | César | Mes 6 TRL 4 |
| RX-1 — Devaluación | Redactar todos los contratos de suscripción en USD o indexados al tipo de cambio oficial. | César + Asesor legal | Mes 1 TRL 4 |

---

## RESUMEN EJECUTIVO — MÓDULOS 4 AL 7

### Las 5 decisiones que determinan el éxito en los próximos 18 meses

| Decisión | Qué hacer | Qué no hacer |
|---|---|---|
| **D1 — Primer cliente pagante** | Cereza o pistacho premium — WTP máximo, referencia máxima | No empezar con Tier 1 solo por volumen. El primer cliente construye la narrativa. |
| **D2 — Canal principal** | Onboardear 5 advisors agronómicos antes del primer contrato masivo | No vender directamente a todos — el CAC no escala sin canal |
| **D3 — Desarrollo condicional** | No escribir código para ISO 14046 sin commit previo de 2-3 bodegas exportadoras | No desarrollar features por WTP < 5 identificado en Módulo 2 |
| **D4 — Contrato en USD** | Todos los contratos de suscripción + hardware en USD desde el Día 1 | No cobrar en pesos — la devaluación destruye el modelo de negocio |
| **D5 — Validación H6 primero** | Ejecutar el experimento de doble-señal antes del primer pitch comercial masivo | No vender la propuesta "dual signal es mejor" sin datos propios que la respalden |

---

*Documento completo — Módulos 1 al 7 ejecutados.*
*Elaborado: abril 2026 | HydroVision AG | Uso interno — no forma parte del formulario ANPCyT*
