"""
Motor GDD (Growing Degree Days) Multi-Varietal — HydroVision AG
Acumulación de grados-día y detección automática de estadios fenológicos
para múltiples cultivos: Vid (Malbec, Cabernet, Bonarda, Syrah),
Olivo, Arándano, Cerezo, Pistacho, Nogal, Citrus (Naranja, Limón, Pomelo).

Método: Winkler (1974) — GDD_i = max(0, (T_max + T_min)/2 − T_base)

T_base por cultivo (doc-02-tecnico.md):
  Vid:      10.0°C  (Winkler 1974; Catania & Avagnina, INTA 2007)
  Olivo:    12.5°C  (doc-02; Connor & Fereres 2005 ajustado Argentina)
  Arándano:  7.0°C  (Lobos et al. 2016; Spiers 2000)
  Cerezo:    4.5°C  (Richardson et al. 1974)
  Pistacho: 10.0°C  (Goldhamer et al. 2005)
  Nogal:    10.0°C  (Girona et al. 2006)
  Citrus:   13.0°C  (García-Tejero et al. 2011)

Estrategia de reinicio (doc-02):
  Caducifolios (vid, cerezo, pistacho, nogal): 1 agosto (sur),
    detección dormancia por T_media < T_base × 14 días.
  Semi-caducifolio (olivo): calendar-based fijo 1 julio (sur).
  Perennifolio (citrus): sin reinicio anual — modelo por evento.

Referencia:
  Winkler, A.J. et al. (1974). General Viticulture. UC Press.
  Ojeda, H. et al. (2002). AJEV 53(4), 261-267.
  Connor, D.J., Fereres, E. (2005). Aust J Agric Res 56, 1143-1153.
  García de Cortázar-Atauri, I. et al. (2009). Int J Biometeorol 53, 317-326.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class FenologiaEstadio(Enum):
    """Estadios fenológicos genéricos del ciclo vegetativo."""
    DORMANCIA         = "dormancia"
    BROTACION         = "brotacion"
    DESARROLLO_FOLIAR = "desarrollo_foliar"
    FLORACION         = "floracion"
    CUAJE             = "cuaje"
    CRECIMIENTO_FRUTO = "crecimiento_fruto"
    ENVERO            = "envero"
    MADURACION        = "maduracion"
    COSECHA           = "cosecha"
    POST_COSECHA      = "post_cosecha"


# ---------------------------------------------------------------------------
# Configuración multi-varietal — cada cultivo define:
#   t_base:     temperatura base [°C]
#   reinicio:   "dormancia" (caducifolio) | "calendar" (olivo) | "evento" (citrus)
#   reinicio_mes: mes de reinicio fijo (solo para "calendar")
#   horas_frio: True si registra horas de frío (T < 7°C durante dormancia)
#   etapas:     lista de (nombre, gdd_inicio, gdd_fin)
#   cwsi_coef:  coeficientes ΔT_LL = a + b·VPD por etapa
#   cwsi_umbral: umbral CWSI de alerta por etapa
# ---------------------------------------------------------------------------
@dataclass
class EtapaFenologica:
    nombre: str
    gdd_inicio: float
    gdd_fin: float
    cwsi_coef: dict   # {"a": float, "b": float, "ΔT_UL": float}
    cwsi_umbral: float
    ky: float = 0.85  # coeficiente de sensibilidad al déficit (FAO-56)


@dataclass
class CultivoConfig:
    nombre: str
    t_base: float
    reinicio: str  # "dormancia" | "calendar" | "evento"
    reinicio_mes: int = 8  # mes de reinicio (agosto por defecto, julio para olivo)
    horas_frio: bool = False
    etapas: list = None

    def __post_init__(self):
        if self.etapas is None:
            self.etapas = []

    def get_etapa(self, gdd_acum: float) -> Optional[EtapaFenologica]:
        for etapa in self.etapas:
            if etapa.gdd_inicio <= gdd_acum < etapa.gdd_fin:
                return etapa
        return self.etapas[0] if self.etapas else None


# ═══════════════════════════════════════════════════════════════════════════
# VID — Malbec (Colonia Caroya ~700m)
# Ref: Winkler 1974; Ojeda 2002; INTA EEA Mendoza ajuste altitudinal −15%
# ═══════════════════════════════════════════════════════════════════════════
MALBEC = CultivoConfig(
    nombre="Malbec",
    t_base=10.0,
    reinicio="dormancia",
    horas_frio=True,
    etapas=[
        EtapaFenologica("dormancia",         0,    50,  {"a": -1.97, "b": 1.49, "ΔT_UL": 3.5}, 0.90, ky=0.10),
        EtapaFenologica("brotacion",         50,   130, {"a": -2.10, "b": 1.55, "ΔT_UL": 3.2}, 0.35, ky=0.20),
        EtapaFenologica("desarrollo_foliar", 130,  280, {"a": -2.00, "b": 1.50, "ΔT_UL": 3.4}, 0.40, ky=0.70),
        EtapaFenologica("floracion",         280,  420, {"a": -1.90, "b": 1.45, "ΔT_UL": 3.5}, 0.30, ky=0.85),
        EtapaFenologica("cuaje",             420,  560, {"a": -1.95, "b": 1.48, "ΔT_UL": 3.5}, 0.35, ky=0.85),
        EtapaFenologica("crecimiento_fruto", 560,  820, {"a": -2.05, "b": 1.52, "ΔT_UL": 3.6}, 0.50, ky=0.85),
        EtapaFenologica("envero",            820,  1050,{"a": -1.80, "b": 1.40, "ΔT_UL": 3.8}, 0.60, ky=0.85),
        EtapaFenologica("maduracion",        1050, 1380,{"a": -1.70, "b": 1.35, "ΔT_UL": 4.0}, 0.65, ky=0.40),
        EtapaFenologica("cosecha",           1380, 1500,{"a": -1.65, "b": 1.30, "ΔT_UL": 4.2}, 0.75, ky=0.40),
        EtapaFenologica("post_cosecha",      1500, 9999,{"a": -1.97, "b": 1.49, "ΔT_UL": 3.5}, 0.85, ky=0.10),
    ],
)

# ═══════════════════════════════════════════════════════════════════════════
# VID — Cabernet Sauvignon (ciclo +2-3 semanas vs Malbec)
# Ref: Ortega-Farías et al. 2019
# ═══════════════════════════════════════════════════════════════════════════
CABERNET = CultivoConfig(
    nombre="Cabernet Sauvignon",
    t_base=10.0,
    reinicio="dormancia",
    horas_frio=True,
    etapas=[
        EtapaFenologica("dormancia",         0,    60,  {"a": -1.97, "b": 1.49, "ΔT_UL": 3.5}, 0.90, ky=0.10),
        EtapaFenologica("brotacion",         60,   180, {"a": -2.10, "b": 1.55, "ΔT_UL": 3.2}, 0.35, ky=0.20),
        EtapaFenologica("desarrollo_foliar", 180,  320, {"a": -2.00, "b": 1.50, "ΔT_UL": 3.4}, 0.40, ky=0.70),
        EtapaFenologica("floracion",         320,  500, {"a": -1.90, "b": 1.45, "ΔT_UL": 3.5}, 0.30, ky=0.85),
        EtapaFenologica("cuaje",             500,  650, {"a": -1.95, "b": 1.48, "ΔT_UL": 3.5}, 0.35, ky=0.85),
        EtapaFenologica("crecimiento_fruto", 650,  950, {"a": -2.05, "b": 1.52, "ΔT_UL": 3.6}, 0.50, ky=0.85),
        EtapaFenologica("envero",            950,  1200,{"a": -1.80, "b": 1.40, "ΔT_UL": 3.8}, 0.60, ky=0.85),
        EtapaFenologica("maduracion",        1200, 1550,{"a": -1.70, "b": 1.35, "ΔT_UL": 4.0}, 0.65, ky=0.40),
        EtapaFenologica("cosecha",           1550, 1750,{"a": -1.65, "b": 1.30, "ΔT_UL": 4.2}, 0.75, ky=0.40),
        EtapaFenologica("post_cosecha",      1750, 9999,{"a": -1.97, "b": 1.49, "ΔT_UL": 3.5}, 0.85, ky=0.10),
    ],
)

# ═══════════════════════════════════════════════════════════════════════════
# VID — Bonarda (ciclo similar a Malbec)
# ═══════════════════════════════════════════════════════════════════════════
BONARDA = CultivoConfig(
    nombre="Bonarda",
    t_base=10.0,
    reinicio="dormancia",
    horas_frio=True,
    etapas=[
        EtapaFenologica("dormancia",         0,    50,  {"a": -1.97, "b": 1.49, "ΔT_UL": 3.5}, 0.90, ky=0.10),
        EtapaFenologica("brotacion",         50,   130, {"a": -2.10, "b": 1.55, "ΔT_UL": 3.2}, 0.35, ky=0.20),
        EtapaFenologica("desarrollo_foliar", 130,  280, {"a": -2.00, "b": 1.50, "ΔT_UL": 3.4}, 0.40, ky=0.70),
        EtapaFenologica("floracion",         280,  420, {"a": -1.90, "b": 1.45, "ΔT_UL": 3.5}, 0.30, ky=0.85),
        EtapaFenologica("cuaje",             420,  560, {"a": -1.95, "b": 1.48, "ΔT_UL": 3.5}, 0.35, ky=0.85),
        EtapaFenologica("crecimiento_fruto", 560,  820, {"a": -2.05, "b": 1.52, "ΔT_UL": 3.6}, 0.50, ky=0.85),
        EtapaFenologica("envero",            820,  1050,{"a": -1.80, "b": 1.40, "ΔT_UL": 3.8}, 0.60, ky=0.85),
        EtapaFenologica("maduracion",        1050, 1380,{"a": -1.70, "b": 1.35, "ΔT_UL": 4.0}, 0.65, ky=0.40),
        EtapaFenologica("cosecha",           1380, 1500,{"a": -1.65, "b": 1.30, "ΔT_UL": 4.2}, 0.75, ky=0.40),
        EtapaFenologica("post_cosecha",      1500, 9999,{"a": -1.97, "b": 1.49, "ΔT_UL": 3.5}, 0.85, ky=0.10),
    ],
)

# ═══════════════════════════════════════════════════════════════════════════
# VID — Syrah (ciclo similar a Malbec)
# ═══════════════════════════════════════════════════════════════════════════
SYRAH = CultivoConfig(
    nombre="Syrah",
    t_base=10.0,
    reinicio="dormancia",
    horas_frio=True,
    etapas=[
        EtapaFenologica("dormancia",         0,    50,  {"a": -1.97, "b": 1.49, "ΔT_UL": 3.5}, 0.90, ky=0.10),
        EtapaFenologica("brotacion",         50,   130, {"a": -2.10, "b": 1.55, "ΔT_UL": 3.2}, 0.35, ky=0.20),
        EtapaFenologica("desarrollo_foliar", 130,  280, {"a": -2.00, "b": 1.50, "ΔT_UL": 3.4}, 0.40, ky=0.70),
        EtapaFenologica("floracion",         280,  420, {"a": -1.90, "b": 1.45, "ΔT_UL": 3.5}, 0.30, ky=0.85),
        EtapaFenologica("cuaje",             420,  560, {"a": -1.95, "b": 1.48, "ΔT_UL": 3.5}, 0.35, ky=0.85),
        EtapaFenologica("crecimiento_fruto", 560,  820, {"a": -2.05, "b": 1.52, "ΔT_UL": 3.6}, 0.50, ky=0.85),
        EtapaFenologica("envero",            820,  1050,{"a": -1.80, "b": 1.40, "ΔT_UL": 3.8}, 0.60, ky=0.85),
        EtapaFenologica("maduracion",        1050, 1380,{"a": -1.70, "b": 1.35, "ΔT_UL": 4.0}, 0.65, ky=0.40),
        EtapaFenologica("cosecha",           1380, 1500,{"a": -1.65, "b": 1.30, "ΔT_UL": 4.2}, 0.75, ky=0.40),
        EtapaFenologica("post_cosecha",      1500, 9999,{"a": -1.97, "b": 1.49, "ΔT_UL": 3.5}, 0.85, ky=0.10),
    ],
)

# ═══════════════════════════════════════════════════════════════════════════
# OLIVO — Semi-caducifolio, reinicio calendar 1 julio
# T_base=12.5°C (doc-02); Ref: Connor & Fereres 2005; Fernández 2012 FAO-66.
# Dormancia parcial e inconsistente → no detectable por señal térmica.
# Coef CWSI: García-Tejero et al. 2018, ajustado para Arauco.
# ═══════════════════════════════════════════════════════════════════════════
OLIVO = CultivoConfig(
    nombre="Olivo",
    t_base=12.5,
    reinicio="calendar",
    reinicio_mes=7,  # 1 julio (doc-02 línea 400)
    horas_frio=False,
    etapas=[
        EtapaFenologica("reposo_invernal",   0,    150, {"a": -1.50, "b": 1.20, "ΔT_UL": 4.0}, 0.85, ky=0.20),
        EtapaFenologica("brotacion",         150,  350, {"a": -1.80, "b": 1.35, "ΔT_UL": 3.5}, 0.40, ky=0.65),
        EtapaFenologica("floracion_cuaje",   350,  600, {"a": -1.70, "b": 1.30, "ΔT_UL": 3.3}, 0.30, ky=0.65),
        EtapaFenologica("endurecimiento",    600,  1000,{"a": -1.60, "b": 1.25, "ΔT_UL": 3.8}, 0.55, ky=0.40),
        EtapaFenologica("maduracion_cosecha",1000, 1600,{"a": -1.55, "b": 1.20, "ΔT_UL": 4.0}, 0.60, ky=0.55),
        EtapaFenologica("post_cosecha",      1600, 9999,{"a": -1.50, "b": 1.20, "ΔT_UL": 4.0}, 0.80, ky=0.20),
    ],
)

# ═══════════════════════════════════════════════════════════════════════════
# ARÁNDANO — Caducifolio, T_base=7°C
# Ref: Lobos et al. 2016; Spiers 2000; Bryla & Linderman 2007.
# Coef CWSI: extrapolados desde datos publicados de Vaccinium corymbosum.
# ═══════════════════════════════════════════════════════════════════════════
ARANDANO = CultivoConfig(
    nombre="Arándano",
    t_base=7.0,
    reinicio="dormancia",
    horas_frio=True,  # crítico: 400-1000 horas según variedad
    etapas=[
        EtapaFenologica("dormancia",       0,    100, {"a": -1.40, "b": 1.10, "ΔT_UL": 3.0}, 0.90, ky=0.20),
        EtapaFenologica("brotacion",       100,  250, {"a": -1.60, "b": 1.25, "ΔT_UL": 2.8}, 0.35, ky=0.25),
        EtapaFenologica("floracion_cuaje", 250,  450, {"a": -1.50, "b": 1.20, "ΔT_UL": 2.6}, 0.25, ky=1.00),
        EtapaFenologica("crec_bayas",      450,  800, {"a": -1.55, "b": 1.22, "ΔT_UL": 2.8}, 0.30, ky=1.05),
        EtapaFenologica("maduracion",      800,  1100,{"a": -1.45, "b": 1.15, "ΔT_UL": 3.2}, 0.50, ky=0.70),
        EtapaFenologica("post_cosecha",    1100, 9999,{"a": -1.40, "b": 1.10, "ΔT_UL": 3.0}, 0.80, ky=0.30),
    ],
)

# ═══════════════════════════════════════════════════════════════════════════
# CEREZO — Caducifolio, T_base=4.5°C
# Ref: Richardson et al. 1974; Pérez-Pastor et al. 2009; INIA Chile.
# Horas de frío: crítico (400-1200h según variedad).
# ═══════════════════════════════════════════════════════════════════════════
CEREZO = CultivoConfig(
    nombre="Cerezo",
    t_base=4.5,
    reinicio="dormancia",
    horas_frio=True,  # muy exigente: 400-1200 horas según variedad
    etapas=[
        EtapaFenologica("dormancia",       0,    80,  {"a": -1.30, "b": 1.05, "ΔT_UL": 2.5}, 0.90, ky=0.20),
        EtapaFenologica("brotacion",       80,   200, {"a": -1.50, "b": 1.15, "ΔT_UL": 2.3}, 0.30, ky=0.20),
        EtapaFenologica("floracion_cuaje", 200,  400, {"a": -1.45, "b": 1.12, "ΔT_UL": 2.2}, 0.20, ky=1.10),
        EtapaFenologica("engorde_fruto",   400,  700, {"a": -1.55, "b": 1.18, "ΔT_UL": 2.5}, 0.25, ky=1.05),
        EtapaFenologica("maduracion",      700,  950, {"a": -1.40, "b": 1.10, "ΔT_UL": 2.8}, 0.45, ky=0.45),
        EtapaFenologica("post_cosecha",    950,  9999,{"a": -1.30, "b": 1.05, "ΔT_UL": 2.5}, 0.80, ky=0.20),
    ],
)

# ═══════════════════════════════════════════════════════════════════════════
# PISTACHO — Caducifolio, T_base=10°C
# Ref: Goldhamer et al. 2005; Mirás-Avalos 2016.
# Horas de frío: muy exigente (1000+ horas).
# ═══════════════════════════════════════════════════════════════════════════
PISTACHO = CultivoConfig(
    nombre="Pistacho",
    t_base=10.0,
    reinicio="dormancia",
    horas_frio=True,  # 1000+ horas
    etapas=[
        EtapaFenologica("dormancia",         0,    200, {"a": -1.70, "b": 1.30, "ΔT_UL": 3.5}, 0.90, ky=0.10),
        EtapaFenologica("brotacion_cascara", 200,  500, {"a": -1.85, "b": 1.40, "ΔT_UL": 3.2}, 0.35, ky=0.60),
        EtapaFenologica("endurecimiento",    500,  800, {"a": -1.75, "b": 1.35, "ΔT_UL": 3.5}, 0.55, ky=0.20),
        EtapaFenologica("llenado_kernel",    800,  1200,{"a": -1.90, "b": 1.42, "ΔT_UL": 3.3}, 0.30, ky=1.10),
        EtapaFenologica("cosecha",           1200, 1500,{"a": -1.70, "b": 1.30, "ΔT_UL": 3.6}, 0.55, ky=0.55),
        EtapaFenologica("post_cosecha",      1500, 9999,{"a": -1.70, "b": 1.30, "ΔT_UL": 3.5}, 0.85, ky=0.10),
    ],
)

# ═══════════════════════════════════════════════════════════════════════════
# NOGAL — Caducifolio, T_base=10°C
# Ref: Girona et al. 2006; INTA Valle Inferior RN Iannamico 2012.
# ═══════════════════════════════════════════════════════════════════════════
NOGAL = CultivoConfig(
    nombre="Nogal",
    t_base=10.0,
    reinicio="dormancia",
    horas_frio=True,  # moderado: 600-800 horas
    etapas=[
        EtapaFenologica("dormancia",       0,    150, {"a": -1.80, "b": 1.35, "ΔT_UL": 3.5}, 0.90, ky=0.10),
        EtapaFenologica("brotacion_veg",   150,  400, {"a": -1.95, "b": 1.45, "ΔT_UL": 3.2}, 0.35, ky=0.80),
        EtapaFenologica("crec_cascara",    400,  700, {"a": -1.85, "b": 1.40, "ΔT_UL": 3.4}, 0.40, ky=0.75),
        EtapaFenologica("llenado_kernel",  700,  1200,{"a": -1.90, "b": 1.42, "ΔT_UL": 3.3}, 0.30, ky=1.10),
        EtapaFenologica("cosecha",         1200, 1500,{"a": -1.75, "b": 1.32, "ΔT_UL": 3.6}, 0.55, ky=0.65),
        EtapaFenologica("post_cosecha",    1500, 9999,{"a": -1.80, "b": 1.35, "ΔT_UL": 3.5}, 0.85, ky=0.10),
    ],
)

# ═══════════════════════════════════════════════════════════════════════════
# CITRUS — Naranja, T_base=13°C (evento-based pero simplificado a ciclo ppal)
# Ref: García-Tejero et al. 2011; FAO Crop Info Citrus.
# doc-02: "múltiples ciclos de brotación; modelo por evento TRL 5+"
# Para TRL 3-4: modelo GDD del ciclo principal (floración invierno-primavera).
# ═══════════════════════════════════════════════════════════════════════════
CITRUS_NARANJA = CultivoConfig(
    nombre="Citrus - Naranja",
    t_base=13.0,
    reinicio="evento",  # sin reinicio anual — modelo por evento
    etapas=[
        EtapaFenologica("pre_floracion",   0,    200, {"a": -1.40, "b": 1.10, "ΔT_UL": 3.5}, 0.45, ky=0.60),
        EtapaFenologica("floracion_cuaje", 200,  500, {"a": -1.35, "b": 1.05, "ΔT_UL": 3.2}, 0.25, ky=1.10),
        EtapaFenologica("crec_fruto",      500,  1200,{"a": -1.45, "b": 1.12, "ΔT_UL": 3.4}, 0.35, ky=0.90),
        EtapaFenologica("maduracion",      1200, 1800,{"a": -1.35, "b": 1.05, "ΔT_UL": 3.6}, 0.50, ky=0.65),
        EtapaFenologica("postcosecha",     1800, 9999,{"a": -1.40, "b": 1.10, "ΔT_UL": 3.5}, 0.70, ky=0.50),
    ],
)

# ═══════════════════════════════════════════════════════════════════════════
# CITRUS — Limón, T_base=13°C (poliflórido, ciclo principal + secundario)
# Ref: González-Altozano & Castel 1999; García-Tejero 2011 adaptado.
# ═══════════════════════════════════════════════════════════════════════════
CITRUS_LIMON = CultivoConfig(
    nombre="Citrus - Limón",
    t_base=13.0,
    reinicio="evento",
    etapas=[
        EtapaFenologica("floracion_ppal",  0,    300, {"a": -1.35, "b": 1.05, "ΔT_UL": 3.2}, 0.25, ky=1.00),
        EtapaFenologica("crec_fruto_ppal", 300,  800, {"a": -1.45, "b": 1.12, "ΔT_UL": 3.4}, 0.35, ky=0.85),
        EtapaFenologica("cosecha_ppal",    800,  1200,{"a": -1.35, "b": 1.05, "ΔT_UL": 3.6}, 0.50, ky=0.60),
        EtapaFenologica("flor_secundaria", 1200, 1800,{"a": -1.40, "b": 1.08, "ΔT_UL": 3.3}, 0.30, ky=0.80),
        EtapaFenologica("reposo_relativo", 1800, 9999,{"a": -1.40, "b": 1.10, "ΔT_UL": 3.5}, 0.65, ky=0.45),
    ],
)

# ═══════════════════════════════════════════════════════════════════════════
# Registro global de cultivos — lookup por nombre normalizado
# ═══════════════════════════════════════════════════════════════════════════
CULTIVOS: dict[str, CultivoConfig] = {
    "malbec":            MALBEC,
    "cabernet":          CABERNET,
    "bonarda":           BONARDA,
    "syrah":             SYRAH,
    "olivo":             OLIVO,
    "arandano":          ARANDANO,
    "cerezo":            CEREZO,
    "pistacho":          PISTACHO,
    "nogal":             NOGAL,
    "citrus - naranja":  CITRUS_NARANJA,
    "citrus - limon":    CITRUS_LIMON,
}

# Backward-compatible aliases (legacy Malbec-only API)
FENOLOGIA_GDD_THRESHOLDS = {
    FenologiaEstadio.DORMANCIA:         (0,    50),
    FenologiaEstadio.BROTACION:         (50,   130),
    FenologiaEstadio.DESARROLLO_FOLIAR: (130,  280),
    FenologiaEstadio.FLORACION:         (280,  420),
    FenologiaEstadio.CUAJE:             (420,  560),
    FenologiaEstadio.CRECIMIENTO_FRUTO: (560,  820),
    FenologiaEstadio.ENVERO:            (820,  1050),
    FenologiaEstadio.MADURACION:        (1050, 1380),
    FenologiaEstadio.COSECHA:           (1380, 1500),
    FenologiaEstadio.POST_COSECHA:      (1500, 9999),
}
CWSI_COEF_POR_ESTADIO = {
    FenologiaEstadio.BROTACION:         {"a": -2.10, "b": 1.55, "ΔT_UL": 3.2},
    FenologiaEstadio.DESARROLLO_FOLIAR: {"a": -2.00, "b": 1.50, "ΔT_UL": 3.4},
    FenologiaEstadio.FLORACION:         {"a": -1.90, "b": 1.45, "ΔT_UL": 3.5},
    FenologiaEstadio.CUAJE:             {"a": -1.95, "b": 1.48, "ΔT_UL": 3.5},
    FenologiaEstadio.CRECIMIENTO_FRUTO: {"a": -2.05, "b": 1.52, "ΔT_UL": 3.6},
    FenologiaEstadio.ENVERO:            {"a": -1.80, "b": 1.40, "ΔT_UL": 3.8},
    FenologiaEstadio.MADURACION:        {"a": -1.70, "b": 1.35, "ΔT_UL": 4.0},
    FenologiaEstadio.COSECHA:           {"a": -1.65, "b": 1.30, "ΔT_UL": 4.2},
    FenologiaEstadio.POST_COSECHA:      {"a": -1.97, "b": 1.49, "ΔT_UL": 3.5},
    FenologiaEstadio.DORMANCIA:         {"a": -1.97, "b": 1.49, "ΔT_UL": 3.5},
}
CWSI_UMBRAL_ALERTA = {
    FenologiaEstadio.BROTACION:         0.35,
    FenologiaEstadio.DESARROLLO_FOLIAR: 0.40,
    FenologiaEstadio.FLORACION:         0.30,
    FenologiaEstadio.CUAJE:             0.35,
    FenologiaEstadio.CRECIMIENTO_FRUTO: 0.50,
    FenologiaEstadio.ENVERO:            0.60,
    FenologiaEstadio.MADURACION:        0.65,
    FenologiaEstadio.COSECHA:           0.75,
    FenologiaEstadio.POST_COSECHA:      0.85,
    FenologiaEstadio.DORMANCIA:         0.90,
}


@dataclass
class DiaMeteorologico:
    """Registro meteorológico diario."""
    fecha: str
    T_max: float  # °C
    T_min: float  # °C
    precip_mm: float = 0.0
    RH_media: float = 50.0
    rad_MJ: float = 20.0  # MJ/m²/día

    @property
    def T_media(self) -> float:
        return (self.T_max + self.T_min) / 2.0

    @property
    def GDD(self) -> float:
        """GDD del día (base 10°C, método Winkler)."""
        return max(0.0, self.T_media - 10.0)


class MotorGDD:
    """
    Motor de acumulación GDD y detección fenológica automática — multi-varietal.

    El nodo HydroVision AG calcula GDD en tiempo real desde el sensor SHT31
    integrado. La brotación se detecta automáticamente por convergencia:
      - GDD_acum > umbral primera etapa activa
      - T_media > T_base por ≥3 días consecutivos
      - Verificación cruzada con calendario histórico

    Soporta tres estrategias de reinicio (doc-02):
      - "dormancia" (caducifolios): reinicio cuando T_media < T_base × 14 días
      - "calendar" (olivo): reinicio en fecha fija (1 julio)
      - "evento" (citrus): sin reinicio anual, modelo por evento fenológico

    Una vez detectada la brotación, el motor selecciona automáticamente
    los coeficientes CWSI correctos para el estadio actual.
    """

    def __init__(self, variedad: str = "Malbec"):
        key = variedad.lower().strip()
        if key in CULTIVOS:
            self.config = CULTIVOS[key]
        else:
            self.config = MALBEC
        self.variedad = self.config.nombre
        self.gdd_acumulado = 0.0
        self.dias_procesados: list[DiaMeteorologico] = []
        self.fecha_brotacion: Optional[str] = None
        self.etapa_actual: Optional[EtapaFenologica] = self.config.etapas[0] if self.config.etapas else None
        self._dias_consecutivos_calidos = 0
        self._dias_consecutivos_frios = 0
        self.horas_frio_acum = 0.0  # horas con T < 7°C durante dormancia

    def procesar_dia(self, dia: DiaMeteorologico) -> dict:
        """
        Procesa un día meteorológico: acumula GDD y detecta cambios de estadio.
        Emula el comportamiento del firmware en el nodo (corre 1x/día a medianoche).
        """
        self.dias_procesados.append(dia)
        t_base = self.config.t_base

        # Acumulación de horas de frío (T < 7°C) durante dormancia
        if self.config.horas_frio and self.fecha_brotacion is None:
            if dia.T_min < 7.0:
                horas_frio_dia = max(0, min(24, (7.0 - dia.T_media) / (dia.T_max - dia.T_min + 0.1) * 24))
                self.horas_frio_acum += min(horas_frio_dia, 24)

        # Detectar inicio de temporada (≥3 días consecutivos T_media > T_base)
        if dia.T_media > t_base:
            self._dias_consecutivos_calidos += 1
        else:
            self._dias_consecutivos_calidos = 0

        # Reinicio por dormancia (caducifolios)
        if self.config.reinicio == "dormancia":
            if dia.T_media < t_base:
                self._dias_consecutivos_frios += 1
            else:
                self._dias_consecutivos_frios = 0

        # GDD del día con T_base del cultivo
        gdd_dia = max(0.0, dia.T_media - t_base)

        # Detectar brotación
        primera_etapa_activa = self.config.etapas[1] if len(self.config.etapas) > 1 else self.config.etapas[0]
        gdd_umbral_brotacion = primera_etapa_activa.gdd_inicio

        if self.fecha_brotacion is None and self._dias_consecutivos_calidos >= 3:
            if self.gdd_acumulado >= gdd_umbral_brotacion:
                self.fecha_brotacion = dia.fecha

        # Acumular GDD
        if self.config.reinicio == "evento":
            # Citrus: acumula siempre (sin dormancia real)
            self.gdd_acumulado += gdd_dia
        elif self.fecha_brotacion is not None or self.gdd_acumulado > 0:
            self.gdd_acumulado += gdd_dia
        elif self._dias_consecutivos_calidos >= 1:
            self.gdd_acumulado += gdd_dia * 0.5

        # Detectar etapa actual
        etapa_anterior = self.etapa_actual
        self.etapa_actual = self.config.get_etapa(self.gdd_acumulado)

        cambio_etapa = (etapa_anterior is None) != (self.etapa_actual is None) or \
                       (etapa_anterior and self.etapa_actual and etapa_anterior.nombre != self.etapa_actual.nombre)

        etapa = self.etapa_actual
        return {
            "fecha": dia.fecha,
            "T_max": dia.T_max,
            "T_min": dia.T_min,
            "T_media": dia.T_media,
            "GDD_dia": gdd_dia,
            "GDD_acum": self.gdd_acumulado,
            "estadio": etapa.nombre if etapa else "desconocido",
            "cambio_estadio": cambio_etapa,
            "fecha_brotacion": self.fecha_brotacion,
            "cwsi_umbral_alerta": etapa.cwsi_umbral if etapa else 0.50,
            "cwsi_coef": etapa.cwsi_coef if etapa else {"a": -1.97, "b": 1.49, "ΔT_UL": 3.5},
            "ky": etapa.ky if etapa else 0.85,
            "horas_frio_acum": self.horas_frio_acum,
            "cultivo": self.variedad,
            "t_base": t_base,
        }

    def _detectar_estadio(self) -> FenologiaEstadio:
        """Determina el estadio actual según GDD acumulado (legacy Malbec)."""
        for estadio, (gdd_min, gdd_max) in FENOLOGIA_GDD_THRESHOLDS.items():
            if gdd_min <= self.gdd_acumulado < gdd_max:
                return estadio
        return FenologiaEstadio.DORMANCIA

    def procesar_temporada(self, datos_meteo: list[DiaMeteorologico]) -> pd.DataFrame:
        """Procesa una temporada completa. Retorna DataFrame con evolución GDD."""
        self.gdd_acumulado = 0.0
        self.dias_procesados = []
        self.fecha_brotacion = None
        self.etapa_actual = self.config.etapas[0] if self.config.etapas else None
        self._dias_consecutivos_calidos = 0
        self._dias_consecutivos_frios = 0
        self.horas_frio_acum = 0.0

        registros = [self.procesar_dia(d) for d in datos_meteo]
        return pd.DataFrame(registros)

    def hitos_fenologicos(self, df: pd.DataFrame) -> dict:
        """Extrae las fechas de los hitos fenológicos de la temporada procesada."""
        hitos = {}
        for etapa in self.config.etapas:
            mask = df["estadio"] == etapa.nombre
            if mask.any():
                hitos[etapa.nombre] = {
                    "primer_dia": df[mask]["fecha"].iloc[0],
                    "gdd_inicio": float(df[mask]["GDD_acum"].iloc[0]),
                    "duracion_dias": int(mask.sum()),
                }
        return hitos

    @staticmethod
    def cultivos_disponibles() -> list[str]:
        """Retorna los nombres de cultivos soportados."""
        return list(CULTIVOS.keys())


def generar_meteo_colonia_caroya(
    temporada: str = "2026-2027",
    seed: int = 42
) -> list[DiaMeteorologico]:
    """
    Genera datos meteorológicos sintéticos realistas para Colonia Caroya (~700m).

    Calibrado contra datos reales de INTA EEA Manfredi (estación A872907,
    2012-2026, 4.802 días, coord: -31.857°, -63.749°). Corrección altitudinal
    aplicada: Manfredi ~330m vs Colonia Caroya ~700m → −2.2°C en T_media
    (lapse rate 0.6°C/100m × 370m). Precipitación sin corrección (similar
    exposición a frentes del NE).

    Estadísticas base INTA Manfredi (2012-2026):
      Mes | T_med | T_max | T_min | RH   | Precip/mes
       1  | 24.1° | 31.6° | 17.1° | 72%  |  81 mm
       2  | 22.5° | 29.7° | 16.1° | 78%  |  99 mm
       3  | 20.6° | 28.0° | 14.3° | 80%  |  60 mm
       4  | 17.5° | 25.2° | 11.2° | 78%  |  39 mm
       5  | 13.5° | 21.2° |  7.1° | 79%  |  12 mm
       6  | 10.0° | 18.9° |  2.4° | 76%  |   8 mm
       7  |  9.5° | 18.2° |  2.1° | 75%  |   5 mm
       8  | 11.8° | 21.9° |  2.7° | 64%  |   8 mm
       9  | 14.8° | 24.3° |  6.0° | 66%  |  16 mm
      10  | 18.1° | 26.8° | 10.0° | 65%  |  55 mm
      11  | 21.5° | 29.9° | 13.5° | 65%  |  77 mm
      12  | 24.0° | 32.2° | 16.2° | 64%  |  79 mm

    Colonia Caroya (ajustado −2.2°C por altitud):
      - Temperatura media anual: ~15.8°C (vs 17.9°C en Manfredi)
      - Precipitación anual: ~539mm
      - Período libre de heladas: sep-may
      - Amplitud térmica diaria: 13-16°C
    """
    rng = np.random.default_rng(seed)

    # Temperatura media mensual [°C] — Colonia Caroya ~700m
    # Base: INTA EEA Manfredi − 2.2°C corrección altitudinal
    T_media_mensual = {
        1: 21.9,  # Enero (pico verano)
        2: 20.3,  # Febrero
        3: 18.4,  # Marzo
        4: 15.3,  # Abril
        5: 11.3,  # Mayo
        6:  7.8,  # Junio
        7:  7.3,  # Julio (mínimo invernal)
        8:  9.6,  # Agosto
        9: 12.6,  # Septiembre
        10: 15.9, # Octubre (brotación)
        11: 19.3, # Noviembre (floración)
        12: 21.8, # Diciembre (crecimiento del fruto)
    }
    amplitud_mensual = {
        # Amplitud real desde INTA Manfredi (T_max − T_min medios)
        1: 14.5, 2: 13.6, 3: 13.7, 4: 14.0, 5: 14.1,
        6: 16.5, 7: 16.1, 8: 19.2, 9: 18.3, 10: 16.8,
        11: 16.4, 12: 16.0
    }
    precip_media_mm = {
        # Precipitación mensual real de INTA Manfredi (mm/mes)
        1: 81, 2: 99, 3: 60, 4: 39, 5: 12,
        6:  8, 7:  5, 8:  8, 9: 16, 10: 55,
        11: 77, 12: 79
    }

    dias = []
    # Temporada oct 2026 – sep 2027
    meses = [(10, 2026), (11, 2026), (12, 2026),
             (1, 2027),  (2, 2027),  (3, 2027),
             (4, 2027),  (5, 2027),  (6, 2027),
             (7, 2027),  (8, 2027),  (9, 2027)]

    for mes, anio in meses:
        import calendar
        n_dias = calendar.monthrange(anio, mes)[1]
        T_base = T_media_mensual[mes]
        amp = amplitud_mensual[mes]
        precip_media = precip_media_mm[mes]

        for d in range(1, n_dias + 1):
            fecha = f"{anio}-{mes:02d}-{d:02d}"
            # Temperatura con ruido diario realista
            T_med = T_base + rng.normal(0, 1.5)
            T_max = T_med + amp / 2 + rng.normal(0, 1.0)
            T_min = T_med - amp / 2 + rng.normal(0, 1.0)

            # Precipitación: distribución Gamma (eventos esporádicos)
            precip = 0.0
            if rng.random() < precip_media / (n_dias * 8):  # prob lluvia por día
                precip = float(rng.gamma(2.0, 4.0))

            dias.append(DiaMeteorologico(
                fecha=fecha,
                T_max=float(T_max),
                T_min=float(T_min),
                precip_mm=float(precip),
                RH_media=float(np.clip(40 + rng.normal(0, 10), 20, 85)),
                rad_MJ=float(np.clip(22 - abs(mes - 1) * 0.8 + rng.normal(0, 2), 8, 30)),
            ))

    return dias


# ─────────────────────────────────────────────
# Demo multi-varietal
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("Motor GDD Multi-Varietal — HydroVision AG")
    print(f"Cultivos soportados: {', '.join(MotorGDD.cultivos_disponibles())}")
    print("=" * 70)

    datos = generar_meteo_colonia_caroya("2026-2027", seed=42)

    # Demo para cada familia de cultivo
    demo_cultivos = ["malbec", "cabernet", "olivo", "arandano", "cerezo",
                     "pistacho", "nogal", "citrus - naranja", "citrus - limon"]

    for cultivo_key in demo_cultivos:
        motor = MotorGDD(cultivo_key)
        df = motor.procesar_temporada(datos)

        print(f"\n{'─' * 70}")
        print(f"  {motor.variedad} | T_base={motor.config.t_base}°C | "
              f"Reinicio: {motor.config.reinicio}"
              f"{f' (mes {motor.config.reinicio_mes})' if motor.config.reinicio == 'calendar' else ''}")
        print(f"  GDD total: {df['GDD_acum'].max():.0f} | "
              f"Brotación: {motor.fecha_brotacion or 'N/A'}"
              f"{f' | Horas frío: {motor.horas_frio_acum:.0f}' if motor.config.horas_frio else ''}")

        hitos = motor.hitos_fenologicos(df)
        for estadio, info in hitos.items():
            print(f"    {estadio:25s} → {info['primer_dia']}  "
                  f"(GDD: {info['gdd_inicio']:>6.0f}, {info['duracion_dias']:>3d}d)")

    # Detalle Malbec con sesiones Scholander (backward-compatible)
    print(f"\n{'=' * 70}")
    print("Detalle Malbec — Sesiones Scholander sugeridas:")
    motor = MotorGDD("Malbec")
    df = motor.procesar_temporada(datos)
    malbec_etapas = [(e.nombre, e.gdd_inicio, e.gdd_fin) for e in MALBEC.etapas]
    for nombre, gdd_min, gdd_fin in [
        ("Brotación (S1)",    50,  130),
        ("Envero (S2)",       820, 1050),
        ("Pre-cosecha (S3)",  1050,1380),
        ("Cosecha (S4)",      1380,1500),
    ]:
        mask = (df["GDD_acum"] >= gdd_min) & (df["GDD_acum"] < gdd_fin)
        if mask.any():
            fecha_inicio = df[mask]["fecha"].iloc[0]
            print(f"  {nombre:30s} desde {fecha_inicio}")

    print(f"\n✓ Motor GDD multi-varietal operativo — {len(CULTIVOS)} cultivos configurados")
