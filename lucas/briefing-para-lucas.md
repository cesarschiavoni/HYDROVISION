# Documentos para Lucas Bergon — HydroVision AG
**Fecha:** 08 de Abril de 2026

---

## Lo que necesitamos que Lucas nos envíe

| # | Documento | Estado |
|---|---|---|
| 1 | DNI ambas caras | ✅ Entregado (`lucas/DNI Bergon Lucas Martin (2025)_fisico.pdf`) |
| 2 | CUIT + constancia AFIP actualizada | ✅ CUIL: 20-32426266-1 — constancia AFIP pendiente |
| 3 | Domicilio completo (calle, número, localidad, CP) | ✅ Pedro Patat Norte 522, Colonia Caroya, Colón, Córdoba |
| 4 | Estado civil y profesión declarada ante AFIP | ✅ Casado — Técnico Electrónico / Integrador de Sistemas |
| 5 | **CBU y alias de cuenta bancaria** | ✅ CBU: 0110108530010821273133 |
| 6 | **CV profesional** | Incluido abajo |
| 7 | Confirmación y respaldo de aportes en especie (equipamiento MBG Controls USD 710 + herramientas USD 400) | Pendiente |
| 8 | **Carta de compromiso de dedicación** | Pre-redactada abajo — solo necesita firma |
| 9 | **Nota de conformidad como co-inventor (INPI)** | Pre-redactada abajo — solo necesita firma |

---

## DOCUMENTO 6 — Currículum Vitae

**Lucas Martín Bergon**
Automatista / Diseñador de Máquinas / Integrador
Córdoba, Argentina
Lucasmartinbergon@gmail.com · lucasb_221@hotmail.com
www.linkedin.com/in/lucasmartinbergon
www.mbg-controls.com.ar

---

### Perfil profesional

Perfil técnico orientado al diseño y desarrollo de proyectos en múltiples escalas, con alta capacidad de aprendizaje y resolución de problemas, e interés especial por la aplicación de tecnologías actuales y eficientes. Fundador de MBG Controls, empresa de ingeniería en automatización y control industrial con más de 15 años de trayectoria y 150+ proyectos industriales entregados.

### Competencias técnicas

**Automatización y control industrial**
Diseño y cálculo de sistemas eléctricos; montaje de tableros industriales de potencia y control; integración PLC Siemens, Rockwell, Schneider, Omron, Festo, Mitsubishi; sistemas SCADA; comunicaciones industriales: Ethernet/IP, ProfiNet, ProfiNet, Modbus RTU/TCP, AS-i, DeviceNet; variadores de velocidad multimarca; servocontroles multiejes; instrumentación y lazos de control; planos eléctricos EPLAN, ElecWorks, SeeElectrical; dataloggers; sistemas de visión artificial; retrofitting y migraciones; robótica industrial y colaborativa; software Industria 4.0.

**Desarrollo electrónico**
Diseño de circuitos impresos multicapa (PCB); montaje superficial (SMD); programación PIC, ARM, Freescale, FPGA; sistemas embebidos ARM e i.MX; displays LCD/TFT; comunicaciones seriales CAN, I2C, RS232/422/485, USB; protocolo Ethernet. Más de 50 proyectos de electrónica realizados.

**Sistemas mecánicos**
Diseño 2D/3D; simulación; desarrollo de máquinas completas; planos de fabricación; montaje electromecánico; selección de motorreductores; sistemas de transmisión. Software: Inventor.

**Idiomas:** Español (nativo) — Inglés (profesional completo)

---

### Experiencia profesional

**MBG Controls** — Fundador / Ingeniería en Automatización y Control Industrial
*2011 – Presente (15 años) · Córdoba, Argentina*
Fundador y director técnico de empresa de servicios de automatización y control industrial. Más de 150 proyectos realizados en diversas industrias. www.mbg-controls.com.ar

**Comau** — Técnico de Mantenimiento
*2012 · Córdoba, Argentina*
Mantenimiento preventivo y correctivo (eléctrico, electrónico y software) de equipamiento industrial en la planta de montaje de Fiat Córdoba.

**Ares SA** — Técnico de Laboratorio y Desarrollo
*2006 – 2012 (6 años) · Córdoba, Argentina*
Coordinación de grupos de trabajo; desarrollo de proyectos de control y automatización; dirección técnica en restauración electromecánica de maquinaria de gran porte; capacitación de personal.

---

### Formación académica

| Institución | Título | Período |
|---|---|---|
| Universidad Siglo 21 | Ingeniería en Sistemas | 2013–2019 |
| Universidad Tecnológica Nacional (UTN) | Ingeniería Electrónica | 2005–2012 |
| Fundación E+E | Capacitación a Emprendedores | 2013 |
| IPEM 69 | Técnico en Electricidad y Electrónica | 2002–2004 |

---

### Reconocimientos y publicaciones

- Premio: Robot Bluetooth
- Publicación: *Automatización Industrial* — MBG Controls

---

## DOCUMENTO 8 — Carta de Compromiso de Dedicación al Proyecto

---

**Córdoba, [Fecha]**

**A:** Agencia Nacional de Promoción de la Investigación, el Desarrollo Tecnológico y la Innovación (ANPCyT) — FONARSEC

**Ref.:** Convocatoria Startup 2025 TRL 3-4 — Proyecto HydroVision AG

---

Yo, **Lucas Martín Bergon**, DNI N° 32.426.266, CUIL N° 20-32426266-1, con domicilio en Pedro Patat Norte 522, Colonia Caroya, Provincia de Córdoba, en mi carácter de **Co-fundador y COO (Chief Operating Officer)** de HydroVision AG S.A.S., me comprometo formalmente a participar en el proyecto denominado:

**"Plataforma Autónoma de Inteligencia Agronómica para Cultivos de Alto Valor mediante Termografía LWIR, Dendrometría de Tronco, Motor Fenológico Automático y Fusión Satelital con IA Edge"**

en los siguientes términos:

**Rol en el proyecto:** Líder técnico de Hardware, Firmware y Sistemas Embebidos. Responsable de la arquitectura modular TRL4 (ESP32-S3 DevKit + breakouts I2C/SPI), firmware MicroPython, integración LoRaWAN y testing de campo.

**Dedicación comprometida:**
- Meses 1 al 6: **50%** de mi tiempo laboral (~20 horas semanales)
- Meses 7 al 12: **25%** de mi tiempo laboral (~10 horas semanales)

**Período:** 12 meses contados desde la firma del Convenio de Ejecución con ANPCyT.

**Actividades principales:**
- Diseño del sistema modular TRL4 (ESP32-S3 DevKit + breakouts I2C/SPI + carcasa Hammond IP67) para el nodo sensor HydroVision
- Implementación de drivers MicroPython para sensores MLX90640, SHT31, GPS, IMU y servos del gimbal
- Integración ChirpStack/LoRaWAN en gateway RAK7268
- Protocolo MQTT entre nodo y servidor
- Testing de hardware: autonomía solar, deep sleep RTC, watchdog TPL5010
- Validación e integración de campo en viñedo experimental Colonia Caroya

Declaro conocer y aceptar las condiciones establecidas en las Bases y Condiciones de la Convocatoria Startup 2025 TRL 3-4 y en el Plan de Trabajo presentado.

---

Firma: ___________________________

**Lucas Martín Bergon**
DNI N° 32.426.266
Co-fundador y COO — HydroVision AG S.A.S.
Lucasmartinbergon@gmail.com
MBG Controls — www.mbg-controls.com.ar

---

## DOCUMENTO 9 — Nota de Conformidad como Co-Inventor (INPI)

---

**Córdoba, [Fecha]**

**A:** Ximena Crespo — Agente de la Propiedad Industrial
Arteaga y Asociados

**Ref.:** Solicitud de Patente de Invención ante INPI Argentina — HydroVision AG S.A.S.

---

Yo, **Lucas Martín Bergon**, DNI N° 32.426.266, CUIL N° 20-32426266-1, con domicilio en Pedro Patat Norte 522, Colonia Caroya, Provincia de Córdoba, declaro:

**1.** Que he participado activamente en la concepción, diseño y desarrollo de la invención denominada:

> *"Nodo sensor autónomo de campo con termografía LWIR, extensometría de tronco y fusión de índice hídrico adaptativo para control de riego en cultivos perennes, y sistema de calibración nodo-satélite asociado"*

**2.** Que mis contribuciones inventivas comprenden específicamente:
- Diseño del hardware del nodo sensor (arquitectura modular ESP32-S3 DevKit + breakouts I2C/SPI, selección y disposición de componentes)
- Arquitectura de integración de sensores LWIR, extensómetro de tronco, IMU y sistema de gimbal motorizado
- Firmware embebido de bajo consumo para operación autónoma solar (deep sleep, watchdog, RTC)
- Sistema de comunicación LoRaWAN campo-servidor
- Diseño del sistema mecánico de montaje en campo (soporte, orientación, protección IP67)

**3.** Que **presto mi conformidad expresa** para que la solicitud de patente de invención sea presentada ante el INPI Argentina con los siguientes datos:

- **Solicitante (titular):** HydroVision AG S.A.S.
- **Inventores:** César Schiavoni y Lucas Martín Bergon
- **Agente de PI:** Ximena Crespo (Arteaga y Asociados)

**4.** Que cedo a **HydroVision AG S.A.S.** todos los derechos patrimoniales derivados de la presente invención, en los términos establecidos en el Pacto de Socios suscripto entre las partes.

**5.** Que autorizo a la Agente de PI Ximena Crespo a gestionar la solicitud, incluyendo la respuesta a observaciones del examinador INPI y la eventual extensión internacional mediante solicitud PCT en Chile, Brasil y Estados Unidos.

---

Firma: ___________________________

**Lucas Martín Bergon**
DNI N° 32.426.266
Co-inventor — Co-fundador HydroVision AG S.A.S.
Lucasmartinbergon@gmail.com

---

*Documentos internos HydroVision AG — Confidencial*
*Generado: 08 de Abril de 2026*
