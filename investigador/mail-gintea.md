# Mail — G.In.T.E.A UTN FRC

**Para:** ccenteno@frc.utn.edu.ar
**CC:** gintea@frc.utn.edu.ar
**Asunto:** Oportunidad de investigación ANPCyT — señales agronómicas + sensores — búsqueda de investigador Art. 32

---

Estimado Ing. Centeno,

Mi nombre es César Schiavoni, egresado de Ingeniería en Sistemas de UTN FRC (promoción 2016). Lucas Bergon, egresado de Ingeniería Electrónica de esta facultad y fundador de MBG Controls, es mi socio en el proyecto.

Nos comunicamos porque estamos buscando un investigador para incorporarse a un proyecto de I+D financiado por ANPCyT (Convocatoria STARTUP 2025 TRL 3-4 / FONARSEC-BID) y creemos que el perfil que trabaja en G.In.T.E.A encaja muy bien con lo que necesitamos.

**El proyecto**

Desarrollamos una plataforma autónoma de detección de estrés hídrico en cultivos de alto valor (vid, olivo, citrus) usando termografía infrarroja embebida en nodos IoT de campo. El nodo captura imágenes térmicas del dosel de la planta, segmenta las hojas automáticamente y estima el Crop Water Stress Index (CWSI) en tiempo real en un ESP32-S3, sin nube.

**El problema de investigación**

El sistema está construido e instrumentado. Lo que define si funciona es validar con datos reales de campo:

*¿El CWSI calculado por el nodo a partir de la temperatura del dosel predice con precisión el potencial hídrico foliar real de la planta (medido con bomba de Scholander)?*

La validación combina tres señales: temperatura del dosel (cámara térmica), variación de diámetro de tronco —MDS, señal ADC continua— y Ψstem (bomba de Scholander, ejecutada por la Dra. Mariela Monteoliva de INTA-CONICET). El trabajo estadístico involucra análisis de correlaciones de campo CWSI↔MDS↔Ψstem, calibración por regresión lineal individual de 5 sensores dendrómetro (5 funciones Ψstem = a·ADC + b, con corrección de deriva térmica), diseño óptimo de experimentos (OED, 4 sesiones D-optimal), y validación de métricas TRL 4 (R²≥0.75, MAE≤0.08 CWSI) con plots Bland-Altman sobre datos independientes. Es exactamente el tipo de problema de adquisición y procesamiento de señales en el que G.In.T.E.A tiene trayectoria.

**Lo que ofrecemos**

- Honorarios de USD 6.000 (USD 500/mes × 12 meses), financiados íntegramente por ANR ANPCyT
- Dedicación de ~5 horas/semana promedio (~177 horas totales), modalidad mayormente remota
- Co-autoría garantizada en revista indexada Q1/Q2 (Agricultural Water Management / Biosystems Engineering / Computers and Electronics in Agriculture) — el costo de publicación (APC) ya está presupuestado en el proyecto
- Dataset único: ~800 frames térmicos etiquetados con Ψstem (Scholander) — dato escaso en Argentina para viticultura
- Métricas TRL 4 a certificar: R²≥0.75 y MAE≤0.08 CWSI sobre conjunto de validación independiente
- Inicio estimado: Octubre 2026

El requisito formal de la convocatoria (Art. 32° Bases ANPCyT) es que la persona desarrolle actividades de investigación y/o formación de recursos humanos en una institución reconocida — perfil que cumple cualquier integrante activo de G.In.T.E.A.

**¿Podría haber interés en el grupo?**

Adjunto la convocatoria completa con el detalle técnico del problema, el desglose de tareas y la declaración de participación. Si algún integrante del grupo — o un becario de posgrado supervisado por usted — tiene disponibilidad y le resulta atractivo, con mucho gusto coordinamos una reunión breve para presentar el proyecto en detalle.

El plazo límite para incorporarse es el **16 de mayo de 2026**.

Quedo a disposición por este medio o al 3525-448154.

Muchas gracias por su tiempo.

Saludos cordiales,

**César Schiavoni**
Director Técnico / Project Leader ANPCyT
HydroVision AG
schiavonicesar@gmail.com · 3525-448154

*[Adjunto: convocatoria-investigador-art32.pdf]*
