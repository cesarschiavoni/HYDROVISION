

HydroVision AG busca convertirse en la infraestructura estándar de monitoreo hídrico en cultivos de alto valor en América Latina, con proyección global. El camino está trazado: Argentina y Chile en el período TRL 4–7, Perú en el Año 3, y los mercados vitivinícolas de Australia, Sudafrica y el mediterráneo en el horizonte de largo plazo —todos mercados donde el agua es un recurso escaso y el rendimiento de los cultivos de alto valor justifica la inversión en inteligencia agronómica.
HydroVision convierte un problema invisible y costoso en una señal clara, medible y accionable. Es una solución económicamente viable (ROI 6x en Año 1 en configuración Tier 1, vid premium; payback 2,5 años en Tier 3 alta densidad — positivo en ambos escenarios), técnicamente sólida (único PINN de CWSI con termografía embebida en Argentina), ambientalmente necesaria (reducción 15–20% del consumo de agua de riego + recuperación del 10–15% de producción perdida por estrés no detectado), y escalable (modelo de datos que mejora con cada nodo instalado). Con el financiamiento de ANPCyT, este proyecto alcanza el TRL 4 que habilita la primera validación comercial, el primer dataset propietario y la primera patente —los activos fundacionales de una empresa de base tecnológica con proyección regional.


HydroVision AG · Córdoba, Argentina · Confidencial · Marzo 2026


---

## Anexo — Avales de participantes del equipo

### Aval de participación — Dra. Mariela I. Monteoliva (INTA-CONICET)

"Estimado César, expreso mi confirmación para participar en el proyecto 'Plataforma Autónoma de Inteligencia Agronómica para Cultivos de Alto Valor mediante Termografía LWIR, Motor Fenológico Automático y Fusión Satelital con IA Edge' a ser presentado en la convocatoria ANPCyT STARTUP 2025."

Dra. Mariela I. Monteoliva
Investigadora Adjunta INTA-CONICET
Lab. MEBA, IFRGV-UDEA, CIAP, INTA-CONICET
WhatsApp: +54-9-351-225-4234


Base científica aportada por Dra. Monteoliva:

Hay 4 trabajos en los que se comparan imágenes termográficas con potencial hídrico y conductancia/transpiración en vides. Los dos primeros son los más similares a este proyecto (nodo terrestre fijo, captura a nivel de canopeo); los dos últimos corresponden a sensores aéreos (UAV/dron).

| Tipo | Referencia | Hallazgo clave | Relevancia HydroVision |
|---|---|---|---|
| **Terrestre** | Pires et al. (2025) — FLIR-A35, 35–45°, variedades portuguesas. *Computers Electronics Agric* 239, 110931 | U-Net++ F1=0.985, RMSE=0.14°C; R²=0.618 vs. ψ_stem; mejor en tarde (R²=0.663 ≥14:30hs) | Valida U-Net++ para segmentación; confirma latencia <200ms; apoya ventana 10–14hs; ángulo 35–45° es punto de partida del gimbal |
| **Terrestre** | Zhou et al. (2022) — FLIR Vue Pro R en vehículo, cv. Riesling. *Agronomy* 12, 322 | CWSIe R²=0.67; CWSIs NO correlaciona con ψ_leaf — invalida CWSI estadístico sin calibración empírica | Valida uso exclusivo de CWSIe (Jackson con T_LL/T_UL medidos); descarta CWSIs; exige segmentación foliar individual |
| **Aéreo** | Araújo-Paredes et al. (2022) — UAV DJI Matrice 210, 60m, cv. Loureiro. *Sensors* 22, 8056 | CWSIs R²=0.55 vs. ψ_stem en 60 vides · 3 fechas | Define rango de referencia UAV (±0.08–0.12 CWSI); fundamenta superioridad del gimbal fijo al igualar sin costos operativos |
| **Aéreo** | Santesteban et al. (2017) — UAV, variabilidad espacial intra-lote. *Agric Water Mgmt* 183, 49–59 | CV > 30% en CWSI entre filas — un sensor puntual no captura heterogeneidad del lote | Justifica red de nodos distribuidos + fusión Sentinel-2; fundamenta densidad 1 nodo/2ha–1 nodo/ha |

Viabilidad del proyecto (opinión Dra. Monteoliva):

El monitoreo del estrés hídrico en vides a través de imágenes térmicas ya ha sido documentado en numerosos trabajos, incluyendo diversos cultivares y regiones. Además, se ha reportado previamente una correlación aceptable entre los parámetros termométricos de las imágenes con mediciones de conductancia (pérdida de agua foliar) y potencial hídrico (agua disponible en tallos y hojas), sustentando su validez para la aplicación de estos parámetros en este proyecto.

Dra. Mariela I. Monteoliva
Investigadora Adjunta INTA-CONICET
Lab. MEBA, IFRGV-UDEA, CIAP, INTA-CONICET


## Anexo Operativo — Protocolo de Campo Simplificado
