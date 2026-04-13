# Identidad Visual — HydroVision AG

## 1. ADN de marca

Tres pilares que guían toda decisión visual y de comunicación:

| Pilar | Significado | Se traduce en… |
|---|---|---|
| **Precisión autónoma** | El sistema decide cuándo y cuánto regar sin intervención humana | Estética limpia, datos al frente, sin decoración superflua |
| **Arraigo territorial** | Nace en Mendoza, diseñado para viticultura de clima árido | Paleta terrosa, fotografía documental de finca, lenguaje local |
| **Transparencia operativa** | El productor ve exactamente qué mide el sensor y por qué se abre la válvula | Dashboards sin cajas negras, métricas expuestas, código abierto del algoritmo de riego |

---

## 2. Paleta de colores

### Colores primarios

| Rol | Color | Hex | Uso principal |
|---|---|---|---|
| **Verde viñedo** | Verde oscuro profundo | `#1B6B4A` | Encabezados, botones primarios, íconos de marca |
| **Gris nodo** | Gris carbón | `#2D3436` | Texto body, fondos oscuros de dashboard |
| **Blanco campo** | Blanco cálido | `#FAFAF7` | Fondos claros, cards, espacios de respiro |

### Colores secundarios (semáforo funcional)

| Estado | Hex | Contexto |
|---|---|---|
| **Óptimo** | `#27AE60` | CWSI < 0.3, riego suficiente |
| **Atención** | `#F39C12` | CWSI 0.3–0.6, estrés moderado |
| **Crítico** | `#E74C3C` | CWSI > 0.6, estrés severo |
| **Informativo** | `#2980B9` | Links, datos neutros, gráficos secundarios |

### Regla 60-30-10

- **60 %** Blanco campo (`#FAFAF7`) — fondo general
- **30 %** Gris nodo (`#2D3436`) — texto y estructura
- **10 %** Verde viñedo (`#1B6B4A`) — acentos y llamadas a la acción

---

## 3. Tipografía

| Nivel | Familia | Peso | Uso |
|---|---|---|---|
| **Títulos (H1–H3)** | Inter | SemiBold 600 | Encabezados de sección, nombre de producto |
| **Cuerpo** | IBM Plex Sans | Regular 400 | Texto corrido, descripciones |
| **Datos / tablas** | IBM Plex Sans | Medium 500 | Valores numéricos, KPI, tabular |
| **Código / técnico** | IBM Plex Mono | Regular 400 | Fragmentos de API, JSON, configuración |

**Escala tipográfica** (base 16 px):

- H1: 28 px / 36 lh
- H2: 22 px / 30 lh
- H3: 18 px / 26 lh
- Body: 16 px / 24 lh
- Small / caption: 13 px / 18 lh

---

## 4. Logotipo

### Concepto

Símbolo que fusiona una **gota de agua** con una **hoja de vid**, contenido en un contorno que evoca un **sensor/nodo IoT** (rectángulo redondeado con antena sutil).

### Variantes

| Variante | Uso |
|---|---|
| **Isotipo + wordmark horizontal** | Web, documentos, presentaciones |
| **Isotipo solo** | Favicon, ícono de app, hardware del nodo |
| **Monocromático blanco** | Sobre fondos oscuros o fotográficos |
| **Monocromático negro** | Impresión en escala de grises |

### Zona de exclusión

Mínimo 1× la altura del isotipo como margen en todos los lados.

---

## 5. Estilo visual

### Iconografía

- **Estilo**: Línea (stroke 1.5–2 px), esquemático, no ilustrativo
- **Biblioteca base**: Lucide Icons o Phosphor Icons (MIT)
- **Personalización**: Íconos específicos del dominio (sensor, electroválvula, vid, gota) diseñados con el mismo trazo

### Fotografía

- **Estilo documental**: Fotos reales de finca, sensores instalados en viñedo, manos de productor
- **Tratamiento**: Contraste natural, sin filtros saturados; leve desaturación para mantener el verde viñedo como acento
- **Prohibido**: Stock genérico de agricultura, fotos de laboratorio asépticas, drones sin contexto

### Datos y dashboards

- **Principio**: Data-first — el número o gráfico es el protagonista, no la decoración
- **Gráficos**: Línea y área para series temporales, barras horizontales para comparación por zona
- **Colores de datos**: Usar paleta semáforo funcional; nunca más de 5 series en un mismo chart
- **Cards**: Bordes sutiles (`1px solid #E0E0E0`), sombra mínima (`0 1px 3px rgba(0,0,0,0.08)`), esquinas 8 px

---

## 6. Tono de comunicación

| Dimensión | Rango |
|---|---|
| Técnico ↔ Coloquial | **70 % técnico** — el público son ingenieros agrónomos y productores experimentados |
| Formal ↔ Cercano | **60 % cercano** — tuteo, lenguaje directo, sin jerga corporativa vacía |
| Datos ↔ Narrativa | **80 % datos** — siempre respaldar con números, el relato acompaña |

### Ejemplos de tono

- **Sí**: "Tu lote Malbec perdió 2.1 % de rendimiento por estrés hídrico esta semana — 3 horas sobre CWSI 0.6 el jueves."
- **No**: "Nuestro innovador sistema detectó oportunidades de mejora en la gestión hídrica de su explotación."

---

## 7. Diferenciación visual vs. competencia

| Aspecto | Phytech / CropX (típico) | HydroVision AG |
|---|---|---|
| Paleta | Verdes brillantes + blanco tech | Verde profundo terroso + gris carbón |
| Tipografía | Sans-serif genérica | Inter + IBM Plex (identidad técnica) |
| Fotografía | Stock pulido, drones, laboratorio | Documental de campo, manos, tierra |
| Dashboard | Muchas cards decorativas | Data-first, métricas expuestas |
| Tono | Marketing corporativo | Técnico-cercano, datos primero |

---

## 8. Aplicaciones

### 8.1 Dashboard web (informe.html)

- Header: Verde viñedo `#1B6B4A` con logo blanco
- Cards de KPI: Fondo blanco campo, borde sutil, número grande (IBM Plex Sans Medium)
- Semáforo de estado: Colores funcionales con ícono + etiqueta texto
- Gráficos: Chart.js 3.9.1 con paleta semáforo, fondo transparente

### 8.2 Presentaciones ANPCyT

- Fondo blanco campo, títulos en verde viñedo
- Datos en cajas gris nodo con números destacados
- Fotografía documental como fondo a sangre en slides de impacto
- Pie de página con isotipo + "HydroVision AG — Startup 2025 TRL 3-4"

### 8.3 Hardware (nodo sensor)

- Carcasa: Gris nodo (RAL 7016 o similar)
- Serigrafía: Isotipo en blanco + QR de vinculación
- Etiqueta: Nombre de zona + número de nodo en IBM Plex Mono

### 8.4 Documentación técnica

- Formato Markdown renderizado con estilos de marca
- Diagramas en Mermaid con colores de la paleta
- Código con syntax highlighting en tema oscuro (gris nodo)

---

## 9. Assets requeridos (próximos pasos)

| Asset | Prioridad | Estado |
|---|---|---|
| Diseño de isotipo (Figma/SVG) | Alta | Pendiente |
| Favicon + ícono app (16, 32, 180, 512 px) | Alta | Pendiente |
| CSS variables de marca para dashboard | Media | Pendiente |
| Template de presentación (Google Slides / PPTX) | Media | Pendiente |
| Guía de estilo fotográfico (moodboard) | Baja | Pendiente |
| Diseño de etiqueta para nodo sensor | Baja | Pendiente |
