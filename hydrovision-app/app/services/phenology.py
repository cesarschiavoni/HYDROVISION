"""
phenology.py — Calendario fenológico por grupo varietal
HydroVision AG

Tres grupos varietales con fases, calendario de emails y textos adaptados.
Fuente: FAO-56, ensayos Scholander doc-09, INTA Colonia Caroya.

Uso:
  from app.services.phenology import get_crop_group, get_phase, get_email_schedule
  group = get_crop_group("vid - malbec")       # → "vid"
  phase = get_phase("vid", month=2)            # → {...fase actual...}
  schedule = get_email_schedule("vid")          # → [{"month":10, "type":...}, ...]
"""

from __future__ import annotations
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Grupos varietales
# ---------------------------------------------------------------------------

CROP_GROUPS: dict[str, str] = {
    # vid
    "vid": "vid", "malbec": "vid", "cabernet": "vid", "bonarda": "vid",
    "syrah": "vid", "sauvignon": "vid", "tempranillo": "vid",
    "chardonnay": "vid", "torrontes": "vid", "pinot": "vid",
    # olivo
    "olivo": "olivo", "oliva": "olivo", "aceituna": "olivo",
    "arauco": "olivo", "arbequina": "olivo", "frantoio": "olivo",
    # cerezo / frutales de carozo
    "cerezo": "cerezo", "cereza": "cerezo", "cherry": "cerezo",
    "durazno": "cerezo", "ciruela": "cerezo", "damasco": "cerezo",
}

DEFAULT_GROUP = "vid"


def get_crop_group(crop: str | None) -> str:
    """Determina el grupo varietal a partir del string de cultivo."""
    if not crop:
        return DEFAULT_GROUP
    # "vid - malbec" → buscar "malbec", luego "vid"
    tokens = [t.strip().lower() for t in crop.replace("-", " ").split()]
    for token in reversed(tokens):
        if token in CROP_GROUPS:
            return CROP_GROUPS[token]
    for token in tokens:
        if token in CROP_GROUPS:
            return CROP_GROUPS[token]
    return DEFAULT_GROUP


# ---------------------------------------------------------------------------
# Fases fenológicas
# ---------------------------------------------------------------------------

@dataclass
class Phase:
    """Una fase fenológica con metadata para emails."""
    name: str              # nombre técnico: "brotacion", "envero", etc.
    display: str           # nombre para mostrar: "Brotación"
    description: str       # texto corto para emails
    risk: str | None       # riesgo principal en esta fase (o None)
    stress_note: str       # qué significa el estrés hídrico en esta fase
    month_start: int
    month_end: int


# Vid (Malbec, Cabernet, Bonarda, Syrah) — Colonia Caroya
VID_PHASES: list[Phase] = [
    Phase("dormancia", "Dormancia invernal", "Tus plantas están en reposo invernal — el sistema monitorea heladas y acumula horas de frío para predecir la brotación.",
          "Heladas severas pueden dañar yemas", "No aplica — la planta está en dormancia", 6, 8),
    Phase("brotacion", "Brotación", "Los brotes están emergiendo. El sistema está calibrando el baseline CWSI para esta temporada.",
          "Heladas tardías pueden destruir brotes nuevos", "Estrés temprano puede retrasar el desarrollo vegetativo", 9, 10),
    Phase("floracion", "Floración y cuajado", "Tu viñedo está en plena floración. Es un momento crítico — el estrés hídrico ahora reduce directamente la cantidad de bayas por racimo.",
          "Estrés hídrico reduce el cuajado (menos bayas)", "Cada evento de estrés en floración puede reducir el rendimiento 5-15%", 11, 11),
    Phase("crecimiento_baya", "Crecimiento de baya", "Las bayas están en crecimiento activo. El riego debe mantener el suelo sin déficit — la demanda hídrica aumenta cada semana.",
          "Déficit hídrico produce bayas pequeñas", "Estrés moderado es aceptable en RDI controlado, pero el sistema alerta si supera los umbrales", 12, 12),
    Phase("envero", "Envero", "Las bayas están cambiando de color — envero. Un déficit hídrico moderado ahora mejora la concentración de azúcares y polifenoles.",
          "Estrés excesivo puede pasar la fruta", "Estrés moderado (CWSI 0.3-0.5) es deseable en vid para calidad; el sistema alerta solo si supera tu umbral", 1, 1),
    Phase("maduracion", "Maduración", "Tus uvas están madurando. El VPD es alto y el riesgo de golpe de calor es máximo — el sistema actúa para proteger la fruta.",
          "Golpe de calor (>40°C) daña bayas irreversiblemente", "Estrés severo en maduración destruye compuestos aromáticos y degrada antocianos", 2, 2),
    Phase("cosecha", "Pre-cosecha y cosecha", "Tu viñedo está listo para cosechar. El sistema sigue monitoreando para proteger los últimos días de maduración.",
          "Lluvia pre-cosecha puede provocar podredumbre", "El riego debe cortarse — estrés leve favorece la concentración final", 3, 4),
    Phase("postcosecha", "Post-cosecha", "La cosecha terminó. Las plantas acumulan reservas antes de entrar en dormancia.",
          None, "No crítico — la planta se prepara para el reposo", 5, 5),
]

# Olivo — perenne, cosecha otoño-invierno
OLIVO_PHASES: list[Phase] = [
    Phase("reposo", "Reposo vegetativo", "Tus olivos están en reposo relativo. El sistema monitorea condiciones del suelo y detecta heladas.",
          "Heladas severas dañan ramas jóvenes", "No aplica — crecimiento mínimo", 7, 8),
    Phase("brotacion", "Brotación y floración", "Tus olivos están brotando y entrando en floración. El cuajado depende del riego — déficit ahora reduce la carga de frutos.",
          "Estrés en floración reduce el cuajado drásticamente", "Cada evento de estrés en floración puede reducir la carga de frutos 10-20%", 9, 10),
    Phase("cuajado", "Cuajado y crecimiento", "Los frutos están cuajando y creciendo. La demanda hídrica aumenta — el sistema mantiene el suelo sin déficit crítico.",
          "Déficit hídrico produce aceitunas pequeñas con bajo rendimiento graso", "Estrés moderado es normal, pero déficit prolongado reduce el rendimiento en aceite", 11, 12),
    Phase("crecimiento_fruto", "Crecimiento de fruto", "Las aceitunas están en crecimiento activo. Es la época de mayor demanda hídrica del olivo.",
          "Calor extremo + déficit hídrico causa caída de frutos", "Estrés severo en verano puede provocar caída prematura de frutos", 1, 2),
    Phase("endurecimiento", "Endurecimiento de carozo", "Los carozos se están endureciendo. La demanda hídrica baja levemente pero el monitoreo sigue activo.",
          None, "Estrés moderado es tolerable — el fruto ya tiene tamaño definido", 3, 3),
    Phase("maduracion", "Maduración", "Tus aceitunas están madurando. El contenido de aceite aumenta cada semana — el sistema protege los últimos meses antes de cosecha.",
          "Heladas tempranas dañan frutos en maduración", "Estrés hídrico moderado concentra el aceite, pero excesivo arruga el fruto", 4, 4),
    Phase("cosecha", "Cosecha", "Es época de cosecha de aceitunas. El sistema registra condiciones para trazabilidad del lote.",
          "Lluvia durante cosecha dificulta la recolección", "No crítico — la cosecha define el fin del ciclo productivo", 5, 6),
]

# Cerezo / frutales de carozo — brotación temprana, cosecha en primavera-verano
CEREZO_PHASES: list[Phase] = [
    Phase("dormancia", "Dormancia invernal", "Tus cerezos están en dormancia profunda. El sistema cuenta las horas de frío acumuladas — tu variedad necesita 800-1000 horas para una brotación uniforme.",
          "Falta de frío causa brotación despareja", "No aplica — la planta está dormida", 5, 7),
    Phase("brotacion", "Brotación", "Los cerezos están brotando. Es el momento más sensible a heladas tardías — una noche bajo cero puede destruir la cosecha.",
          "Heladas tardías destruyen flores y brotes", "Estrés hídrico temprano retrasa la brotación y debilita la floración", 8, 8),
    Phase("floracion", "Floración", "Tus cerezos están en plena flor. La polinización necesita clima seco — lluvia o helada ahora destruyen la cosecha directamente.",
          "Lluvia en floración reduce polinización; helada mata flores", "Estrés hídrico en floración reduce el cuajado — mantener suelo húmedo", 9, 9),
    Phase("cuajado", "Cuajado y crecimiento", "Los frutos cuajaron y están creciendo. La demanda hídrica es máxima — déficit ahora produce cerezas pequeñas y rajadas.",
          "Déficit hídrico seguido de lluvia causa cracking (rajado)", "Estrés hídrico produce frutos pequeños; riego irregular causa rajado", 10, 10),
    Phase("envero", "Envero y maduración", "Las cerezas están cambiando de color. Cada día cuenta — el sistema protege la fruta del calor y detecta condiciones de cracking.",
          "Calor excesivo ablanda fruta; lluvia causa rajado", "Estrés moderado concentra azúcares pero excesivo deshidrata la cereza", 11, 11),
    Phase("cosecha", "Cosecha", "Tus cerezas están listas. La ventana de cosecha es corta (10-15 días) — el sistema monitorea lluvia y temperatura para optimizar el timing.",
          "Lluvia post-madurez causa pérdida total por cracking", "No regar — la fruta debe estar firme para la cosecha", 12, 12),
    Phase("postcosecha", "Post-cosecha", "La cosecha terminó. Los cerezos acumulan reservas y el sistema empieza a contar horas de frío para la próxima temporada.",
          None, "Riego de mantenimiento — la planta se prepara para dormancia", 1, 4),
]

GROUP_PHASES: dict[str, list[Phase]] = {
    "vid": VID_PHASES,
    "olivo": OLIVO_PHASES,
    "cerezo": CEREZO_PHASES,
}


def get_phase(group: str, month: int) -> Phase:
    """Retorna la fase fenológica actual para un grupo en un mes dado."""
    phases = GROUP_PHASES.get(group, VID_PHASES)
    for p in phases:
        if p.month_start <= p.month_end:
            if p.month_start <= month <= p.month_end:
                return p
        else:  # wrap around (ej: month_start=11, month_end=2)
            if month >= p.month_start or month <= p.month_end:
                return p
    return phases[0]


def get_next_phase(group: str, month: int) -> Phase | None:
    """Retorna la siguiente fase fenológica."""
    phases = GROUP_PHASES.get(group, VID_PHASES)
    current = get_phase(group, month)
    idx = phases.index(current)
    if idx + 1 < len(phases):
        return phases[idx + 1]
    return phases[0]


# ---------------------------------------------------------------------------
# Calendario de emails por grupo
# ---------------------------------------------------------------------------

EMAIL_SCHEDULES: dict[str, list[dict]] = {
    "vid": [
        {"month": 10, "type": "campaign_start",  "description": "Brotación — tu sistema arrancó la campaña"},
        {"month": 12, "type": "first_report",     "description": "Crecimiento de baya — primer corte de datos"},
        {"month":  2, "type": "peak_heat",         "description": "Maduración — pico de calor, riesgo golpe de sol"},
        {"month":  4, "type": "campaign_end",      "description": "Post-cosecha — resumen de campaña"},
        {"month":  6, "type": "offseason",          "description": "Dormancia — heladas y horas de frío"},
        {"month":  8, "type": "pre_campaign",       "description": "Pre-brotación — el modelo está listo"},
        {"month": 11, "type": "annual_report",      "description": "Informe anual completo con ROI y benchmarking"},
    ],
    "olivo": [
        {"month":  9, "type": "campaign_start",  "description": "Brotación/floración — tu sistema arrancó"},
        {"month": 11, "type": "first_report",     "description": "Cuajado — primer corte de datos"},
        {"month":  1, "type": "peak_heat",         "description": "Crecimiento de fruto — pico de calor"},
        {"month":  5, "type": "campaign_end",      "description": "Cosecha — resumen de temporada"},
        {"month":  7, "type": "offseason",          "description": "Reposo vegetativo — monitoreo continuo"},
        {"month":  8, "type": "pre_campaign",       "description": "Pre-floración — el modelo está listo"},
        {"month":  6, "type": "annual_report",      "description": "Informe anual: rendimiento graso y ROI"},
    ],
    "cerezo": [
        {"month":  8, "type": "campaign_start",  "description": "Brotación — tus cerezos despertaron"},
        {"month": 10, "type": "first_report",     "description": "Cuajado — primer corte de datos"},
        {"month": 11, "type": "peak_heat",         "description": "Envero — riesgo de cracking y calor"},
        {"month": 12, "type": "campaign_end",      "description": "Cosecha — resumen de temporada"},
        {"month":  4, "type": "offseason",          "description": "Dormancia — acumulación de horas de frío"},
        {"month":  7, "type": "pre_campaign",       "description": "Fin de dormancia — horas de frío y predicción"},
        {"month":  1, "type": "annual_report",      "description": "Informe anual: rendimiento, cracking y ROI"},
    ],
}


def get_email_schedule(group: str) -> list[dict]:
    """Retorna el calendario de emails para un grupo varietal."""
    return EMAIL_SCHEDULES.get(group, EMAIL_SCHEDULES["vid"])


# ---------------------------------------------------------------------------
# Nombres de grupo para UI
# ---------------------------------------------------------------------------

GROUP_DISPLAY_NAMES = {
    "vid": "Vid (vinifera)",
    "olivo": "Olivo",
    "cerezo": "Cerezo / frutales de carozo",
}
