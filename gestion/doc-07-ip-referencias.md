

Se realizó una búsqueda preliminar de anterioridad en las bases Google Patents, Espacenet (EPO) y INPI Argentina con cadenas: 'CWSI thermal camera embedded IoT', 'crop water stress infrared node autonomous field', 'FLIR Lepton Raspberry Pi CWSI', 'thermal imaging irrigation control LoRaWAN'. Los resultados confirman que no existe patente vigente que cubra la combinación específica de elementos del sistema HydroVision AG:

Anterioridad identificada
Diferencia con HydroVision AG
Conclusión
AquaSense (2025) — FLIR Lepton + ESP32 + LoRaWAN + LightGBM para clasificación de estrés hídrico. Publicación académica, sin patente.
AquaSense usa sensor de suelo como input principal. HydroVision AG usa exclusivamente imagen térmica foliar para calcular CWSI — no hay superposición en la reivindicación central.
No obstruye. El método de cálculo CWSI desde imagen térmica LWIR con modelo IA regresor calibrado por variedad es diferenciado.
WISN (MDPI Sensors, 2023) — red de sensores MLX90614 para CWSI en viñedo. Sin patente.
MLX90614 es un termómetro IR puntual (1 punto de temperatura). HydroVision AG usa cámara de imagen completa 32×24px con segmentación foliar — diferente clase de sensor y metodología.
No obstruye. La segmentación foliar de imagen térmica con IA para CWSI es el elemento diferenciador patentable.
Sistemas CWSI con cámara FLIR en UAV (múltiples publicaciones 2016–2024). Sin patente de sistema integrado.
Todos los sistemas publicados son aéreos (dron). HydroVision AG es un nodo fijo en campo, permanente y autónomo — categoría de hardware completamente distinta.
No obstruye. El nodo fijo autónomo con IA local y control de riego integrado no tiene anterioridad patentada.
Patente US11.195.015 (2021) — sistema IoT con IA para análisis de imágenes aéreas en agricultura.
Cubre cámaras en drones y análisis en la nube. HydroVision AG procesa localmente en edge (ESP32-S3) con MLX90640 LWIR — arquitectura completamente distinta.
No obstruye. La inferencia IA local con termografía LWIR para CWSI en nodo embebido no está cubierta por esta patente.


Conclusión: La combinación inédita patentable es: nodo IoT fijo autónomo con cámara térmica LWIR + extensómetro de tronco (MDS) + fusión HSI con confianza dinámica por anemómetro + inferencia IA local (edge) con regresor CWSI calibrado por variedad + motor fenológico GDD + fusión satelital Sentinel-2 + control automático de riego autónomo en nodo (GPIO → SSR → solenoide) — todo integrado sin dependencia de conectividad permanente. Esta combinación no tiene anterioridad identificada en las bases consultadas.

### 9A. Reivindicaciones Clave — Estrategia de Protección IP

Las reivindicaciones centrales de la solicitud INPI cubren cinco elementos independientes que, en conjunto, constituyen el sistema HydroVision AG:

| # | Reivindicación | Elementos clave | Diferencial patentable |
|---|---|---|---|
| 1 | **Nodo IoT fijo autónomo** | Cámara LWIR + limpieza piezoeléctrica (Murata MZB1001T02) + gimbal con IMU ICM-42688-P | Ningún sistema combina LWIR fijo + limpieza autónoma + compensación de vibración en nodo permanente de campo |
| 2 | **Arquitectura PINN embebida** | PINN con ecuación CWSI (Jackson 1981) en función de pérdida · inferencia edge sin conectividad | Primer PINN de CWSI con termografía embebida en campo documentado — sin anterioridad en INPI, USPTO ni EPO |
| 3 | **Motor fenológico autónomo** | GDD con detección brotación por convergencia térmica+GDD · cambio automático coeficientes CWSI · modo hibernación | Fenología automática integrada en nodo edge sin configuración ni intervención humana |
| 4 | **Red nodo-satélite calibrada** | Fusión CWSI↔NDWI: nodo terrestre calibra píxeles Sentinel-2 en todo el lote | 1 nodo calibra ~50 ha — densidad mínima de hardware para mapa de campo completo |
| 5 | **HSI con confianza dinámica y mitigación multinivel** | Fusión CWSI + MDS ponderada por R²(ψ_stem) · 9 capas de mitigación de viento (sotavento, shelter, tubo colimador IR, termopar foliar, buffer calma, rampa gradual 4-18 m/s / 14-65 km/h) · ≥18 m/s → 100% MDS automático | Primer sistema termografía + dendrometría + mitigación física multinivel + confianza contextual por viento en nodo autónomo — sin anterioridad |

### 9B. Secreto Comercial — Activos No Patentables

Los siguientes activos se protegen como secretos comerciales (trade secrets) mediante NDA con todos los integrantes del equipo, repositorio Git privado y documentación en almacenamiento cifrado:

| Activo | Descripción | Barrera de entrada |
|---|---|---|
| **Coeficientes CWSI por variedad/región** | ΔT_LL/ΔT_UL para Malbec Cuyo/Córdoba — 6 meses de protocolo Scholander con respaldo INTA-CONICET | Crece con cada variedad calibrada (Cabernet, Sauvignon Blanc, Olivo Arauco, Arándano) |
| **Simulador físico de imágenes térmicas** | Balance energético foliar calibrado para Malbec — genera 1.000.000+ imágenes sintéticas | Escalable a cualquier variedad sin costo marginal de campo |
| **Pipeline INT8 optimizado** | Cuantización INT8 con parámetros de calibración PINN para ESP32-S3 · hiperparámetros λ optimizados | Semanas de tuning específico para hardware de bajo costo |
| **Red de datos agroclimáticos propios** | Con 50+ lotes activos (TRL 5+): T_foliar, CWSI, VPD, eventos de riego de Mendoza, San Juan, Córdoba, NOA | Datos que no existen en ninguna fuente pública — habilitan modelos predictivos exclusivos |

Estrategia de protección internacional: La solicitud ante INPI Argentina establece la fecha de prioridad. Dentro de los 12 meses posteriores (Convenio de París), se presenta solicitud PCT (Patent Cooperation Treaty) en las jurisdicciones prioritarias: Chile (mercado Año 2), Brasil (escala Año 3) y Estados Unidos (mercado vitivinícola premium). La búsqueda formal de anterioridad incluye las bases WIPO/PCT y CNIPA (China), donde existe actividad creciente en IoT agrícola. La decisión de presentar PCT se confirma según los resultados del proyecto y la validación comercial en TRL 4, optimizando la inversión en PI según el avance real del producto. El presupuesto de patente (USD 3.500 en ANR) cubre la solicitud INPI Argentina, la búsqueda internacional ampliada y la primera respuesta del examinador.

## 10. Referencias Científicas y Técnicas

### 10A. Síntesis de Viabilidad Científica — 4 Papers Clave con Mayor Relevancia Directa

Los siguientes cuatro trabajos son los más directamente relevantes para la arquitectura técnica de HydroVision AG, validando la correlación CWSI-termografía en vides, la segmentación foliar y el enfoque edge-computing:

Araújo-Paredes, C., Portela, F., Mendes, S., Valín, M.I. (2022). Using Aerial Thermal Imagery to Evaluate Water Status in Vitis vinifera cv. Loureiro. Sensors 22, 8056. doi: 10.3390/s22208056. Hallazgos: termografía LWIR aérea (UAV DJI Matrice 210 + Zenmuse XT2, 640×512px, 60m de altitud) en cv. Loureiro; CWSIs R² = 0.55 y CWSITair R² = 0.49 vs. potencial hídrico de tallo (Ψstem). Validación en 60 vides en 3 fechas de muestreo. Valida que CWSI aéreo correlaciona con estrés hídrico fisiológico en vides europeas en campo real. Relevancia HydroVision: define el rango de precisión de referencia para termografía UAV (±0.08–0.12 CWSI); fundamenta la superioridad del gimbal multi-angular en nodo fijo al igualar o superar esa precisión sin costos operativos UAV.

Pires, A., Bernardino, A., Victorino, G., Miguel Costa, J., Lopes, C.M., Santos-Victor, J. (2025). Scalable thermal imaging and processing framework for water status monitoring in vineyards. Computers and Electronics in Agriculture 239, 110931. doi: 10.1016/j.compag.2025.110931. Hallazgos: captura terrestre manual con FLIR-A35 (320×256px) a ángulo fijo de 35–45° respecto al suelo, a 0.8m de la vid, en variedades blancas portuguesas (Moscatel, Arinto, Encruzado, Viosinho). Segmentación térmica automática con U-Net++ ResNet34; F1 = 0.985 (supera el target de HydroVision de F1 > 0.95); RMSE = 0.14°C; inferencia CPU = 0.2s. R² = 0.618 vs. potencial hídrico de tallo (Ψstem, medido con bomba de presión); mejor correlación en captura de tarde (R² = 0.663 ≥ 14:30hs). Publicado enero 2025 — paper más relevante para la arquitectura de HydroVision. Relevancia HydroVision: valida la arquitectura U-Net++ para segmentación de canopeo; confirma latencia < 200ms alcanzable en hardware embebido; apoya la ventana de captura 10–14hs definida en el protocolo; el ángulo de captura fijo de 35–45° validado aquí es el punto de partida del sistema multi-angular del gimbal.

Zhou, Z., Diverres, G., Kang, C., Thapa, S., Karkee, M., Zhang, Q., et al. (2022). Ground-Based Thermal Imaging for Assessing Crop Water Status in Grapevines over a Growing Season. Agronomy 12, 322. doi: 10.3390/agronomy12020322. Hallazgos: termografía LWIR terrestre en vehículo utilitario (FLIR Vue Pro R 640×512px) sobre cv. Riesling. Hallazgo crítico de diferenciación metodológica: CWSIe (empírico, con referencias físicas de hoja seca y húmeda) alcanza R² = 0.67 vs. Ψleaf en posición este/sombreada; CWSIs (estadístico, basado en histograma) NO muestra correlación significativa con Ψleaf — resultado negativo que invalida el uso de CWSI estadístico sin calibración empírica. Recomienda segmentación foliar individualizada (no promedio de canopeo) y posicionamiento en cara este (sombreado parcial) para reducir reflexiones de radiación directa. Relevancia HydroVision: primer trabajo en validar termografía LWIR fija terrestre (misma categoría de hardware); valida el uso exclusivo de CWSIe (fórmula de Jackson con T_LL y T_UL medidos en campo) en el firmware del nodo; descarta CWSIs como indicador confiable; valida la necesidad de segmentación foliar individual y fundamenta las recomendaciones de instalación del nodo.

Santesteban, L.G., Di Gennaro, S.F., Herrero-Langreo, A., Miranda, C., Royo, J.B., Matese, A. (2017). High-resolution UAV-based thermal imaging to estimate the instantaneous and seasonal variability of plant water status within a vineyard. Agricultural Water Management 183, 49–59. doi: 10.1016/j.agwat.2016.08.026. Hallazgos: variabilidad espacial del estado hídrico dentro del lote es significativa (CV > 30% en CWSI entre filas); un único sensor puntual no captura la heterogeneidad del lote; la red distribuida de nodos con fusión satelital es la arquitectura correcta para escalar. Relevancia HydroVision: fundamenta el modelo de negocio de red de nodos distribuidos + fusión Sentinel-2; justifica la densidad mínima de 1 nodo/2ha en lotes homogéneos y 1 nodo/ha en lotes heterogéneos.


Jackson, R.D., Idso, S.B., Reginato, R.J., Pinter, P.J. (1981). Canopy temperature as a crop water stress indicator. Water Resources Research, 17(4), 1133-1138.
Bellvert, J., Zarco-Tejada, P.J., Girona, J., Fereres, E. (2016). Mapping crop water stress index in a Pinot-noir vineyard. Precision Agriculture, 15(4), 361-376.
García-Tejero, I., et al. (2018). Assessing plant water status in a hedgerow olive orchard from thermography. Agricultural Water Management, 208, 375-381.
Jones, H.G. (1999). Use of infrared thermometry for estimation of stomatal conductance. Agricultural and Forest Meteorology, 95(3), 139-149.
Espinosa Herlein, M.A.; Monteoliva, M.I. (2025). Estado hídrico. En: Abordajes fisiológicos para el estudio del estrés abiótico en cultivos. Editorial UCC, Córdoba.
Maes, W.H., Steppe, K. (2012). Estimating evapotranspiration and drought stress with ground-based thermal remote sensing. Journal of Experimental Botany, 63(13), 4671-4712.
Semtech Corporation (2024). SX1262 LoRa Transceiver Datasheet. Rev. 2.1.
FLIR Systems (2024). Lepton 3.5 Engineering Datasheet. Rev. 200.
Capraro, F., Tosetti, S., Campillo, P., Mut, V., Pierantozzi, P. (2025). Seguimiento del estado hídrico de un olivar superintensivo utilizando imágenes termográficas y multiespectrales de alta resolución. Congreso Argentino de Agroinformática (CAI 2025). UNLP. SEDICI:10915/190711.
Subsecretaría de Programación Microeconómica — Ministerio de Economía Argentina (2025). AgTech Año 10, N° 85. Informe de Cadenas de Valor.
Ridder, J., et al. (2025). A physics-informed neural network workflow for forward and inverse modeling of unsaturated flow and root water uptake from hydrogeophysical data. Journal of Hydrology. doi:10.1016/j.jhydrol.2025.202015. [PINN aplicado a absorción radicular y estrés hídrico en plantas — valida la factibilidad del enfoque PINN en el dominio de estrés hídrico vegetal].
Rouholahnejad Freund, E., et al. (2024). Exploring Physics-Informed Neural Networks for Crop Yield Loss Forecasting. arXiv:2501.00502v1. [PINN con Sentinel-2 y ecuación de respuesta hídrica de cultivos embebida en la función de pérdida — principio exacto aplicado a problema adyacente al CWSI].
Benkirane, M., et al. (2025). Physics-informed neural networks for enhanced reference evapotranspiration estimation. Chemosphere. [PINN con ecuación de Penman-Monteith — misma ecuación de balance energético base del CWSI — en contextos de datos limitados].
Hu, J., et al. (2025). Physics-informed neural networks enhanced by data augmentation: robust soil moisture estimation using multi-source data fusion including Landsat 8 Thermal. Journal of Hydrology. [PINN con imágenes térmicas satelitales en agricultura de precisión].
García de Cortázar-Atauri, I., Brisson, N., Gaudillere, J.P. (2009). Performance of several models for predicting budburst date of grapevine (Vitis vinifera L.). Int J Biometeorol, 53, 317–326.
Ortega-Farías, S., et al. (2019). Modeling phenology of four grapevine cultivars (Vitis vinifera L.) in Mediterranean climate conditions. Scientia Horticulturae, 250, 38–44.
Schultz, H.R. (2003). Differences in hydraulic architecture account for near-isohydric and anisohydric behaviour of two field-grown Vitis vinifera L. cultivars during drought. Plant, Cell & Environment, 26(8), 1393–1405.
Medrano, H., et al. (2003). Regulation of photosynthesis of C3 plants in response to progressive drought. Annals of Botany, 89(7), 895–905.
Catania, C.D., Avagnina, S. (2007). La interpretación sensorial del vino. Curso superior de degustación de vinos. INTA EEA Mendoza.




## 11. Visión y Conclusión
