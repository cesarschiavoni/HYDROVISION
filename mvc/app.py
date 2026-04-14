"""
app.py — FastAPI MVC
HydroVision AG | Demo TRL 4  v0.4.0

Levantar:
    cd c:/Temp/Agro/mvc
    python -m uvicorn app:app --reload --port 8000

Endpoints principales:
    GET  /                         → home (landing page)
    GET  /dashboard                 → dashboard operativo
    GET  /admin                    → página de configuración
    POST /ingest                   → telemetría del nodo
    GET  /api/status               → última lectura por nodo
    GET  /api/alerts               → nodos con CWSI ≥ umbral_alto
    GET  /api/history/{node_id}    → historial 48 h
    POST /api/irrigate/{node_id}   → toggle riego en nodo (requiere solenoide)
    GET  /api/zones                → estado + CWSI por zona (nodo directo o fusión S2)

Endpoints admin:
    GET  /api/admin/config                → configuración general
    PUT  /api/admin/config                → actualizar configuración
    GET  /api/admin/zones                 → lista de zonas
    POST /api/admin/zones                 → crear zona
    PUT  /api/admin/zones/{id}            → editar zona
    DELETE /api/admin/zones/{id}          → eliminar zona
    GET  /api/admin/nodes                 → nodos conocidos + metadata
    PUT  /api/admin/nodes/{node_id}       → editar nombre/zona/solenoide de nodo
"""

import csv
import datetime
import io
import json
import math
import random
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, Optional
import hashlib
import hmac as _hmac
import os
import time as _time
from collections import defaultdict

# ---------------------------------------------------------------------------
# Fusión nodo-satélite (Sentinel-2 + CWSINDWICorrelationModel)
# ---------------------------------------------------------------------------
try:
    import numpy as np
    _CESAR = Path(__file__).parent.parent / "cesar"
    if str(_CESAR) not in sys.path:
        sys.path.insert(0, str(_CESAR))
    from sentinel2_fusion import (          # noqa: E402
        CWSINDWICorrelationModel,
        Sentinel2Observation,
        generate_synthetic_sentinel2_dataset,
    )
    _S2_OK = True
except ImportError:
    _S2_OK = False

# Provider Sentinel-2 real: STAC API (Element84/AWS) — sin registro ni API key
# Fallback: GEE si STAC no disponible. Último fallback: sintético.
_S2_PROVIDER_CLASS = None
try:
    from stac_s2_provider import STAC_S2Provider
    _S2_PROVIDER_CLASS = STAC_S2Provider
except ImportError:
    try:
        from gee_s2_provider import GEE_S2Provider
        _S2_PROVIDER_CLASS = GEE_S2Provider
    except ImportError:
        pass

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    APP_CONFIG_DEFAULTS, ZONE_DEFAULTS,
    AppConfig, AuditLog, Base, IrrigationLog, NodeConfig,
    SessionLocal, Telemetry, ZoneConfig, engine,
)

# ---------------------------------------------------------------------------
# Modelos de días-grado (GDD) por variedad — fenología basada en temperatura
# ---------------------------------------------------------------------------
# GDD (Growing Degree Days) = Σ max(0, T_media_dia - T_base)
# Acumulados desde el inicio de temporada (primer día con T_media ≥ T_base en primavera).
#
# La etapa fenológica se determina por los GDD acumulados de la zona, calculados
# en tiempo real a partir de las lecturas de t_air del nodo (o temperatura media
# del campo si la zona no tiene nodo propio).
#
# Cuando no hay suficientes datos de temperatura (< GDD_MIN_READINGS días), se cae
# automáticamente al método fallback por mes del año.
#
# Estructura de _GDD_MODELS:
#   { clave_varietal: {
#       "t_base":  float,        # temperatura base [°C] — por debajo no hay desarrollo
#       "etapas": [              # ordenadas por GDD creciente
#           { "nombre": str, "gdd_inicio": float, "gdd_fin": float, "ky": float, "ref": str }
#       ]
#   } }
#
# Referencias:
#   Vid: Winkler et al. (1974) — T_base=10°C; Nendel 2010 Eur.J.Agron.
#   Olivo: T_base=12.5°C (doc-02); Connor & Fereres 2005; Fernández 2012 FAO-66.
#   Frutales: Richardson et al. 1974; Seeley 1990 Acta Hort.; INTA Mendoza.

_GDD_MODELS: dict[str, dict] = {

    # ── VID ───────────────────────────────────────────────────────────────────
    # T_base = 10°C (estándar Winkler, confirmado para Vitis vinifera Argentina)
    # Umbrales GDD (hemisferio sur, año calendario → se re-inicia en agosto):
    #   Brotación/Desborre: 0–150 GDD
    #   Desarrollo vegetativo: 150–450 GDD
    #   Floración/Cuaje (CRÍTICO): 450–750 GDD   ← Ky más alto
    #   Envero / Maduración: 750–1300 GDD
    #   Vendimia / Post-cosecha: > 1300 GDD
    # Ref: Winkler et al. 1974; Nendel 2010 Eur.J.Agron. 32:54-71;
    #      INTA Mendoza EEA La Consulta (Ojeda 2015).
    "vid - malbec": {
        "t_base": 10.0,
        "etapas": [
            {"nombre": "brotacion",         "gdd_inicio":    0, "gdd_fin":  150, "ky": 0.20},
            {"nombre": "desarrollo_veg",    "gdd_inicio":  150, "gdd_fin":  450, "ky": 0.70},
            {"nombre": "floracion_cuaje",   "gdd_inicio":  450, "gdd_fin":  750, "ky": 0.85},
            {"nombre": "envero_maduracion", "gdd_inicio":  750, "gdd_fin": 1300, "ky": 0.85},
            {"nombre": "vendimia",          "gdd_inicio": 1300, "gdd_fin": 1600, "ky": 0.40},
            {"nombre": "reposo",            "gdd_inicio": 1600, "gdd_fin": 9999, "ky": 0.10},
        ],
    },
    "vid - cabernet": {
        "t_base": 10.0,
        # Cabernet tiene ciclo más largo (+2-3 semanas): umbrales desplazados
        "etapas": [
            {"nombre": "brotacion",         "gdd_inicio":    0, "gdd_fin":  180, "ky": 0.20},
            {"nombre": "desarrollo_veg",    "gdd_inicio":  180, "gdd_fin":  500, "ky": 0.70},
            {"nombre": "floracion_cuaje",   "gdd_inicio":  500, "gdd_fin":  800, "ky": 0.85},
            {"nombre": "envero_maduracion", "gdd_inicio":  800, "gdd_fin": 1450, "ky": 0.85},
            {"nombre": "vendimia",          "gdd_inicio": 1450, "gdd_fin": 1750, "ky": 0.40},
            {"nombre": "reposo",            "gdd_inicio": 1750, "gdd_fin": 9999, "ky": 0.10},
        ],
    },
    "vid - bonarda": {
        "t_base": 10.0,
        "etapas": [
            {"nombre": "brotacion",         "gdd_inicio":    0, "gdd_fin":  150, "ky": 0.20},
            {"nombre": "desarrollo_veg",    "gdd_inicio":  150, "gdd_fin":  450, "ky": 0.70},
            {"nombre": "floracion_cuaje",   "gdd_inicio":  450, "gdd_fin":  750, "ky": 0.85},
            {"nombre": "envero_maduracion", "gdd_inicio":  750, "gdd_fin": 1300, "ky": 0.85},
            {"nombre": "vendimia",          "gdd_inicio": 1300, "gdd_fin": 1600, "ky": 0.40},
            {"nombre": "reposo",            "gdd_inicio": 1600, "gdd_fin": 9999, "ky": 0.10},
        ],
    },
    "vid - syrah": {
        "t_base": 10.0,
        "etapas": [
            {"nombre": "brotacion",         "gdd_inicio":    0, "gdd_fin":  150, "ky": 0.20},
            {"nombre": "desarrollo_veg",    "gdd_inicio":  150, "gdd_fin":  450, "ky": 0.70},
            {"nombre": "floracion_cuaje",   "gdd_inicio":  450, "gdd_fin":  750, "ky": 0.85},
            {"nombre": "envero_maduracion", "gdd_inicio":  750, "gdd_fin": 1300, "ky": 0.85},
            {"nombre": "vendimia",          "gdd_inicio": 1300, "gdd_fin": 1600, "ky": 0.40},
            {"nombre": "reposo",            "gdd_inicio": 1600, "gdd_fin": 9999, "ky": 0.10},
        ],
    },

    # ── OLIVO ─────────────────────────────────────────────────────────────────
    # T_base = 12.5°C (doc-02-tecnico.md; ajustado para Argentina)
    # Ref: Connor & Fereres 2005 (7°C vegetativo); doc-02 usa 12.5°C fenológico.
    "olivo": {
        "t_base": 12.5,
        "etapas": [
            {"nombre": "brotacion",         "gdd_inicio":    0, "gdd_fin":  200, "ky": 0.20},
            {"nombre": "floracion_cuaje",   "gdd_inicio":  200, "gdd_fin":  500, "ky": 0.65},
            {"nombre": "endurecimiento",    "gdd_inicio":  500, "gdd_fin": 1000, "ky": 0.40},
            {"nombre": "maduracion_cosecha","gdd_inicio": 1000, "gdd_fin": 1600, "ky": 0.55},
            {"nombre": "reposo",            "gdd_inicio": 1600, "gdd_fin": 9999, "ky": 0.20},
        ],
    },

    # ── CEREZO ────────────────────────────────────────────────────────────────
    # T_base = 4.5°C (Richardson et al. 1974; estándar para Prunus avium)
    # Ref: Pérez-Pastor et al. 2009; Seeley 1990 Acta Hort.; INIA Chile.
    "cerezo": {
        "t_base": 4.5,
        "etapas": [
            {"nombre": "brotacion",       "gdd_inicio":    0, "gdd_fin":  100, "ky": 0.20},
            {"nombre": "floracion_cuaje", "gdd_inicio":  100, "gdd_fin":  300, "ky": 1.10},
            {"nombre": "engorde_fruto",   "gdd_inicio":  300, "gdd_fin":  600, "ky": 1.05},
            {"nombre": "maduracion",      "gdd_inicio":  600, "gdd_fin":  900, "ky": 0.45},
            {"nombre": "reposo",          "gdd_inicio":  900, "gdd_fin": 9999, "ky": 0.20},
        ],
    },

    # ── PISTACHO ──────────────────────────────────────────────────────────────
    # T_base = 10°C (Goldhamer et al. 2005; estándar Pistacia vera)
    # Ref: Goldhamer 2005 Irrig.Sci.; Mirás-Avalos 2016.
    "pistacho": {
        "t_base": 10.0,
        "etapas": [
            {"nombre": "brotacion_cascara","gdd_inicio":    0, "gdd_fin":  400, "ky": 0.60},
            {"nombre": "endurecimiento",   "gdd_inicio":  400, "gdd_fin":  700, "ky": 0.20},
            {"nombre": "llenado_kernel",   "gdd_inicio":  700, "gdd_fin": 1100, "ky": 1.10},
            {"nombre": "cosecha",          "gdd_inicio": 1100, "gdd_fin": 1400, "ky": 0.55},
            {"nombre": "reposo",           "gdd_inicio": 1400, "gdd_fin": 9999, "ky": 0.10},
        ],
    },

    # ── ARÁNDANO ──────────────────────────────────────────────────────────────
    # T_base = 7°C (Lobos et al. 2016; Spiers 2000)
    # Ref: Spiers 2000 Irrig.Sci.; Bryla & Linderman 2007 HortSci.
    "arándano": {
        "t_base": 7.0,
        "etapas": [
            {"nombre": "brotacion",       "gdd_inicio":    0, "gdd_fin":  150, "ky": 0.25},
            {"nombre": "floracion_cuaje", "gdd_inicio":  150, "gdd_fin":  350, "ky": 1.00},
            {"nombre": "crec_bayas",      "gdd_inicio":  350, "gdd_fin":  750, "ky": 1.05},
            {"nombre": "maduracion",      "gdd_inicio":  750, "gdd_fin": 1100, "ky": 0.70},
            {"nombre": "reposo",          "gdd_inicio": 1100, "gdd_fin": 9999, "ky": 0.30},
        ],
    },

    # ── NOGAL ─────────────────────────────────────────────────────────────────
    # T_base = 10°C (Girona et al. 2006; INTA Valle Inferior RN Iannamico 2012)
    "nogal": {
        "t_base": 10.0,
        "etapas": [
            {"nombre": "brotacion_veg",   "gdd_inicio":    0, "gdd_fin":  300, "ky": 0.80},
            {"nombre": "crec_cascara",    "gdd_inicio":  300, "gdd_fin":  600, "ky": 0.75},
            {"nombre": "llenado_kernel",  "gdd_inicio":  600, "gdd_fin": 1100, "ky": 1.10},
            {"nombre": "cosecha",         "gdd_inicio": 1100, "gdd_fin": 1400, "ky": 0.65},
            {"nombre": "reposo",          "gdd_inicio": 1400, "gdd_fin": 9999, "ky": 0.10},
        ],
    },

    # ── CITRUS — NARANJA ──────────────────────────────────────────────────────
    # T_base = 13°C (García-Tejero et al. 2011; FAO Crop Info Citrus)
    "citrus - naranja": {
        "t_base": 13.0,
        "etapas": [
            {"nombre": "pre_floracion",   "gdd_inicio":    0, "gdd_fin":  200, "ky": 0.60},
            {"nombre": "floracion_cuaje", "gdd_inicio":  200, "gdd_fin":  500, "ky": 1.10},
            {"nombre": "crec_fruto",      "gdd_inicio":  500, "gdd_fin": 1200, "ky": 0.90},
            {"nombre": "maduracion",      "gdd_inicio": 1200, "gdd_fin": 1800, "ky": 0.65},
            {"nombre": "postcosecha",     "gdd_inicio": 1800, "gdd_fin": 9999, "ky": 0.50},
        ],
    },

    # ── CITRUS — LIMÓN ────────────────────────────────────────────────────────
    # T_base = 13°C; especie poliflórida → umbrales de floración se repiten
    # durante el año. Se usa el GDD del ciclo principal (floración de invierno-primavera).
    # Ref: González-Altozano & Castel 1999; García-Tejero 2011 adaptado.
    "citrus - limón": {
        "t_base": 13.0,
        "etapas": [
            {"nombre": "floracion_ppal",  "gdd_inicio":    0, "gdd_fin":  300, "ky": 1.00},
            {"nombre": "crec_fruto_ppal", "gdd_inicio":  300, "gdd_fin":  800, "ky": 0.85},
            {"nombre": "cosecha_ppal",    "gdd_inicio":  800, "gdd_fin": 1200, "ky": 0.60},
            {"nombre": "flor_secundaria", "gdd_inicio": 1200, "gdd_fin": 1800, "ky": 0.80},
            {"nombre": "reposo_relativo", "gdd_inicio": 1800, "gdd_fin": 9999, "ky": 0.45},
        ],
    },

    # ── CITRUS — POMELO ───────────────────────────────────────────────────────
    # T_base = 13°C; ciclo más largo que naranja.
    "citrus - pomelo": {
        "t_base": 13.0,
        "etapas": [
            {"nombre": "pre_floracion",   "gdd_inicio":    0, "gdd_fin":  200, "ky": 0.60},
            {"nombre": "floracion_cuaje", "gdd_inicio":  200, "gdd_fin":  500, "ky": 1.05},
            {"nombre": "crec_fruto",      "gdd_inicio":  500, "gdd_fin": 1400, "ky": 0.85},
            {"nombre": "maduracion",      "gdd_inicio": 1400, "gdd_fin": 2000, "ky": 0.60},
            {"nombre": "postcosecha",     "gdd_inicio": 2000, "gdd_fin": 9999, "ky": 0.50},
        ],
    },
}

# GDD mínimo de días de datos para confiar en el cálculo GDD vs fallback por mes
_GDD_MIN_DAYS = 14

# ---------------------------------------------------------------------------
# Tabla FAO-56: Ky por variedad y etapa fenológica

_KY_FAO56: dict[str, dict] = {
    # ── VID ──────────────────────────────────────────────────────────────────
    # Etapas FAO-33 (Doorenbos & Kassam 1979): Brotación (ago-sep) → Desarrollo
    # vegetativo (oct) → Floración/Cuaje/Envero (nov-ene) → Maduración/Vendimia
    # (feb-abr) → Reposo (may-jul). Ky global temporada: 0.85.
    # Los cuatro cultivares comparten los mismos Ky; difieren en el mes de vendimia:
    #   Malbec feb-mar | Cabernet mar-abr | Bonarda feb-mar | Syrah feb-mar
    # Ref: Doorenbos & Kassam 1979 FAO-33; FAO Crop Information – Grape.
    "vid - malbec": {
        "default": 0.85,
        "meses": {8: 0.20, 9: 0.20,                    # brotación (FAO I)
                  10: 0.70,                              # desarrollo vegetativo (FAO II)
                  11: 0.85, 12: 0.85, 1: 0.85,          # floración/cuaje/envero (FAO III)
                  2: 0.40, 3: 0.40,                      # maduración/vendimia (FAO IV) — cosecha feb-mar
                  4: 0.10, 5: 0.10, 6: 0.10, 7: 0.10},  # reposo (Fereres & Soriano 2007)
    },
    "vid - cabernet": {
        "default": 0.85,
        "meses": {8: 0.20, 9: 0.20,                    # brotación
                  10: 0.70,                              # desarrollo vegetativo
                  11: 0.85, 12: 0.85, 1: 0.85,          # floración/cuaje/envero
                  2: 0.85, 3: 0.40, 4: 0.40,             # ciclo más largo: envero feb, vendimia mar-abr
                  5: 0.10, 6: 0.10, 7: 0.10},            # reposo
    },
    "vid - bonarda": {
        "default": 0.85,
        "meses": {8: 0.20, 9: 0.20,
                  10: 0.70,
                  11: 0.85, 12: 0.85, 1: 0.85,
                  2: 0.40, 3: 0.40,
                  4: 0.10, 5: 0.10, 6: 0.10, 7: 0.10},
    },
    "vid - syrah": {
        "default": 0.85,
        "meses": {8: 0.20, 9: 0.20,
                  10: 0.70,
                  11: 0.85, 12: 0.85, 1: 0.85,
                  2: 0.40, 3: 0.40,
                  4: 0.10, 5: 0.10, 6: 0.10, 7: 0.10},
    },

    # ── OLIVO ─────────────────────────────────────────────────────────────────
    # Ky global FAO-33: 0.20 (alta tolerancia al estrés). Por etapa:
    # Ref: Doorenbos & Kassam 1979 FAO-33; Fereres & Soriano 2007 J.Exp.Bot 58:147;
    #      Fernández 2012 en FAO Paper 66; INTA La Consulta (Trentacoste).
    "olivo": {
        "default": 0.20,
        "meses": {8: 0.20, 9: 0.20,                    # brotación vegetativa
                  10: 0.65, 11: 0.65,                   # floración/cuaje (etapa crítica)
                  12: 0.40, 1: 0.40, 2: 0.40,           # endurecimiento del carozo (RDI admite déficit)
                  3: 0.55, 4: 0.55, 5: 0.55,             # maduración/cosecha
                  6: 0.20, 7: 0.20},                     # post-cosecha/reposo
    },

    # ── CEREZO ────────────────────────────────────────────────────────────────
    # FAO-33 no incluye cerezo. Valores de RDC (Riego Deficitario Controlado).
    # Floración/cuaje (sep-oct) es la etapa MÁS sensible (Ky=1.10).
    # Ref: Pérez-Pastor et al. 2009 Plants 9:94; Marsal et al. 2002 Irrig.Sci.;
    #      Ferreyra INIA Chile. Cosecha Mendoza: oct-ene según variedad.
    "cerezo": {
        "default": 0.95,
        "meses": {8: 0.20,                              # brotación
                  9: 1.10, 10: 1.10,                    # floración/cuaje (CRÍTICO)
                  11: 1.05,                              # engorde de fruto
                  12: 0.45, 1: 0.45,                    # maduración/cosecha (RDC poscosecha tolerable)
                  2: 0.20, 3: 0.20, 4: 0.20,
                  5: 0.20, 6: 0.20, 7: 0.20},           # post-cosecha/reposo invernal
    },

    # ── PISTACHO ──────────────────────────────────────────────────────────────
    # FAO-33 no incluye pistacho. Valores de RDI en España, Irán, California.
    # Llenado del kernel (nov-dic) es la etapa MÁS sensible (Ky=1.10).
    # Endurecimiento de cáscara (oct-nov): etapa más tolerante al estrés (Ky=0.20).
    # Ref: Goldhamer et al. 2005 Irrig.Sci. 24:1-9;
    #      Mirás-Avalos et al. 2016 Agr.Water Mgmt. 164:311-323.
    "pistacho": {
        "default": 0.80,
        "meses": {8: 0.60, 9: 0.60, 10: 0.60,          # brotación/crecimiento de cáscara (FAO I)
                  11: 1.10, 12: 1.10,                   # llenado del kernel (CRÍTICO — Goldhamer stage III)
                  1: 0.55, 2: 0.55,                     # cosecha
                  3: 0.10, 4: 0.10, 5: 0.10,
                  6: 0.10, 7: 0.10},                    # post-cosecha/reposo
        # Nota: oct puede ser endurecimiento de cáscara (Ky=0.20) o final de
        # brotación (Ky=0.60). Se usa 0.60 conservador (Goldhamer stage I/II overlap).
    },

    # ── ARÁNDANO ──────────────────────────────────────────────────────────────
    # FAO-33 no incluye arándano. Valores de literatura Vaccinium corymbosum.
    # Crecimiento de bayas (oct-dic) es la etapa más sensible (Ky=1.05).
    # Post-cosecha relevante: el estrés afecta la diferenciación floral del año siguiente.
    # Ref: Spiers 2000 Irrig.Sci.; Bryla & Linderman 2007 HortSci.;
    #      Lobos et al. 2016 MDPI Plants.
    "arándano": {
        "default": 1.05,
        "meses": {8: 0.25,                              # brotación vegetativa
                  9: 1.00,                              # floración/cuaje
                  10: 1.05, 11: 1.05,                   # crecimiento rápido de bayas (CRÍTICO)
                  12: 0.70, 1: 0.70,                    # maduración/cosecha
                  2: 0.30, 3: 0.30, 4: 0.30,
                  5: 0.30, 6: 0.30, 7: 0.30},           # post-cosecha/reposo (impacta próximo año)
    },

    # ── NOGAL ─────────────────────────────────────────────────────────────────
    # FAO-33 no incluye nogal. Valores de RDI en California y Argentina (INTA).
    # Llenado del kernel (nov-ene) es la etapa MÁS sensible (Ky=1.10).
    # Ref: Girona et al. 2006 Irrig.Sci.; Tixier et al. 2020 West Coast Nut;
    #      Iannamico 2012 INTA Valle Inferior RN.
    "nogal": {
        "default": 0.80,
        "meses": {8: 0.10,                              # reposo final / post-cosecha
                  9: 0.80, 10: 0.80,                    # brotación/crecimiento vegetativo + cáscara
                  11: 1.10, 12: 1.10, 1: 1.10,          # llenado del kernel (CRÍTICO)
                  2: 0.65, 3: 0.65,                     # apertura de cáscara/cosecha
                  4: 0.10, 5: 0.10, 6: 0.10, 7: 0.10}, # reposo invernal
    },

    # ── CITRUS — NARANJA ──────────────────────────────────────────────────────
    # Ky global FAO-33: 0.8–1.1. Floración/cuaje (sep-oct) es la etapa más sensible.
    # Ref: García-Tejero et al. 2011 Agron.Sust.Dev. 31:605-613;
    #      FAO Crop Information – Citrus; Doorenbos & Kassam 1979 FAO-33.
    "citrus - naranja": {
        "default": 0.85,
        "meses": {8: 0.60,                              # brotación/pre-floración
                  9: 1.10, 10: 1.10,                    # floración/cuaje (CRÍTICO: hasta 20% pérdida)
                  11: 0.90, 12: 0.90, 1: 0.90,          # crecimiento de fruto (~10% pérdida)
                  2: 0.50, 3: 0.50,                     # post-cosecha/pre-floración próxima temporada
                  4: 0.65, 5: 0.65, 6: 0.65, 7: 0.65}, # maduración/cosecha (~6% pérdida)
    },

    # ── CITRUS — LIMÓN ────────────────────────────────────────────────────────
    # El limón es poliflórido: floraciones primaveral, estival y otoñal.
    # Cualquier floración activa tiene Ky ~1.00. Reposo relativo: jun-ago.
    # Ref: González-Altozano & Castel 1999 J.Hort.Sci.Biotech. 74:706-713;
    #      García-Tejero et al. 2011 (adaptado desde naranja).
    "citrus - limón": {
        "default": 0.85,
        "meses": {8: 1.00, 9: 1.00, 10: 1.00,          # floración primaveral (especie poliflórida)
                  11: 0.85, 12: 0.85,                   # crecimiento fruto principal
                  1: 0.60, 2: 0.60, 3: 0.60,            # cosecha principal
                  4: 0.80, 5: 0.80,                     # floraciones secundarias (activas → Ky alto)
                  6: 0.45, 7: 0.45},                    # reposo relativo
    },

    # ── CITRUS — POMELO ───────────────────────────────────────────────────────
    # Ciclo similar a naranja, fruto más grande → período de crecimiento más largo.
    # Ref: García-Tejero et al. 2011 (adaptado); FAO Crop Information – Citrus;
    #      Doorenbos & Kassam 1979 FAO-33.
    "citrus - pomelo": {
        "default": 0.85,
        "meses": {8: 0.60,                              # brotación/pre-floración
                  9: 1.05, 10: 1.05,                    # floración/cuaje
                  11: 0.85, 12: 0.85, 1: 0.85, 2: 0.85, # crecimiento de fruto (ciclo más largo)
                  3: 0.50,                               # post-cosecha
                  4: 0.60, 5: 0.60, 6: 0.60, 7: 0.60}, # maduración/cosecha
    },
}
_KY_DEFAULT = 0.85   # fallback si la variedad no está en la tabla


def _calcular_gdd_zona(t_aire_dias: dict[str, list[float]], t_base: float) -> tuple[float, int]:
    """
    Calcula los GDD acumulados desde el inicio de temporada.

    El inicio de temporada se detecta automáticamente: es el primer día en que
    la temperatura media supera T_base por primera vez después del 1-julio
    (hemisferio sur — inicio de primavera agronómica).

    Args:
        t_aire_dias: { "YYYY-MM-DD": [lecturas t_air del día] }
        t_base:      temperatura base del cultivo [°C]

    Returns:
        (gdd_acumulados, n_dias_con_datos)
    """
    if not t_aire_dias:
        return 0.0, 0

    # Ordenar días disponibles
    dias = sorted(t_aire_dias.keys())

    # Detectar inicio de temporada: primer día ≥ T_base después del 1-julio
    # del año actual (o año anterior si estamos en ene-jul)
    hoy = datetime.date.today()
    # En hemisferio sur la temporada empieza en agosto (julio es el más frío)
    anio_inicio = hoy.year if hoy.month >= 7 else hoy.year - 1
    fecha_pivot = f"{anio_inicio}-07-01"

    inicio_temporada = None
    for dia in dias:
        if dia < fecha_pivot:
            continue
        t_media = sum(t_aire_dias[dia]) / len(t_aire_dias[dia])
        if t_media >= t_base:
            inicio_temporada = dia
            break

    if inicio_temporada is None:
        return 0.0, 0

    # Acumular GDD desde el inicio de temporada
    gdd = 0.0
    n_dias = 0
    for dia in dias:
        if dia < inicio_temporada:
            continue
        t_media = sum(t_aire_dias[dia]) / len(t_aire_dias[dia])
        gdd += max(0.0, t_media - t_base)
        n_dias += 1

    return gdd, n_dias


def _ky_desde_gdd(varietal: str, gdd: float) -> tuple[float, str]:
    """
    Devuelve el Ky FAO-56 para la variedad según los GDD acumulados.

    Args:
        varietal: clave de variedad (ej: "vid - malbec")
        gdd:      GDD acumulados desde inicio de temporada

    Returns:
        (ky, nombre_etapa)
    """
    model = _GDD_MODELS.get(varietal)
    if model is None:
        return _KY_DEFAULT, "desconocido"
    for etapa in model["etapas"]:
        if etapa["gdd_inicio"] <= gdd < etapa["gdd_fin"]:
            return etapa["ky"], etapa["nombre"]
    # Fallback: última etapa
    last = model["etapas"][-1]
    return last["ky"], last["nombre"]


def _ky_para_varietal(
    varietal: Optional[str],
    mes: Optional[int] = None,
    t_aire_dias: Optional[dict] = None,
) -> float:
    """
    Devuelve el Ky FAO-56 para la variedad.

    Método primario: GDD (días-grado) acumulados desde inicio de temporada,
    calculados a partir del historial de t_air de la zona/campo.

    Fallback (cuando hay < _GDD_MIN_DAYS días de datos): mes del año.

    Args:
        varietal:    variedad tal como está en la DB (ej: "Vid - Malbec")
        mes:         mes 1-12 (para fallback; None = mes actual)
        t_aire_dias: { "YYYY-MM-DD": [lecturas t_air] } para cálculo GDD

    Returns:
        Ky adimensional [0.10 - 1.15]
    """
    if not varietal:
        return _KY_DEFAULT
    key = varietal.strip().lower()

    # ── Método GDD ────────────────────────────────────────────────────────────
    model = _GDD_MODELS.get(key)
    if model and t_aire_dias:
        gdd, n_dias = _calcular_gdd_zona(t_aire_dias, model["t_base"])
        if n_dias >= _GDD_MIN_DAYS:
            ky, _ = _ky_desde_gdd(key, gdd)
            return ky

    # ── Fallback: mes del año ─────────────────────────────────────────────────
    entry = _KY_FAO56.get(key)
    if entry is None:
        return _KY_DEFAULT
    if mes is None:
        mes = datetime.datetime.utcnow().month
    return entry["meses"].get(mes, entry["default"])


def _fenologia_zona(
    varietal: Optional[str],
    t_aire_dias: Optional[dict] = None,
) -> dict:
    """
    Devuelve la etapa fenológica actual, GDD acumulados y Ky de una zona.
    Expuesto en la API para mostrarlo en el informe y dashboard.

    Returns:
        { "etapa": str, "gdd": float, "ky": float, "metodo": "gdd"|"mes", "n_dias": int }
    """
    if not varietal:
        return {"etapa": "—", "gdd": 0.0, "ky": _KY_DEFAULT, "metodo": "mes", "n_dias": 0}

    key = varietal.strip().lower()
    model = _GDD_MODELS.get(key)

    if model and t_aire_dias:
        gdd, n_dias = _calcular_gdd_zona(t_aire_dias, model["t_base"])
        if n_dias >= _GDD_MIN_DAYS:
            ky, etapa = _ky_desde_gdd(key, gdd)
            return {"etapa": etapa, "gdd": round(gdd, 1), "ky": ky,
                    "metodo": "gdd", "n_dias": n_dias}

    # Fallback mes
    entry = _KY_FAO56.get(key)
    mes = datetime.datetime.utcnow().month
    ky = entry["meses"].get(mes, entry["default"]) if entry else _KY_DEFAULT
    return {"etapa": f"mes_{mes}", "gdd": 0.0, "ky": ky,
            "metodo": "mes", "n_dias": 0 if not t_aire_dias else len(t_aire_dias)}


# ---------------------------------------------------------------------------
# Estado en memoria de zonas (cargado desde DB al iniciar)
# ---------------------------------------------------------------------------
ZONES: dict[int, dict] = {}          # {id: {name, lat, lon, ...}}
# Estado de riego por nodo (solo nodos con solenoide pueden tener True)
_NODE_IRRIGATION: dict[str, bool] = {}
# Modo simulación de solenoide por nodo (True = GPIO no se activa, solo lógica)
_NODE_SOL_SIM: dict[str, bool] = {}
CWSI_MEDIO     = 0.30
CWSI_ALTO      = 0.60
CWSI_IRRIGATE  = 0.60


# ---------------------------------------------------------------------------
# Helpers DB
# ---------------------------------------------------------------------------
def _seed_defaults(db: Session) -> None:
    """Inserta zonas y config por defecto si las tablas están vacías."""
    if not db.query(ZoneConfig).first():
        for z in ZONE_DEFAULTS:
            db.add(ZoneConfig(**z))

    if not db.query(AppConfig).first():
        for k, v in APP_CONFIG_DEFAULTS.items():
            db.add(AppConfig(key=k, value=v))

    db.commit()


_HL = 0.000117   # half-lat default ≈ 13 m
_HO = 0.000168   # half-lon default ≈ 16 m


def _zone_bounds(r: ZoneConfig) -> dict:
    return {
        "sw_lat": r.sw_lat if r.sw_lat is not None else r.lat - _HL,
        "sw_lon": r.sw_lon if r.sw_lon is not None else r.lon - _HO,
        "ne_lat": r.ne_lat if r.ne_lat is not None else r.lat + _HL,
        "ne_lon": r.ne_lon if r.ne_lon is not None else r.lon + _HO,
    }


def _zone_centroid_from_vertices(vertices_json: str) -> tuple[float, float]:
    """Calcula el centroide geométrico de un polígono dado como JSON [[lat,lon],...]."""
    import json
    pts = json.loads(vertices_json)
    lat = sum(p[0] for p in pts) / len(pts)
    lon = sum(p[1] for p in pts) / len(pts)
    return lat, lon


def _zone_bounds_from_vertices(vertices_json: str) -> dict:
    """Bounding box de un polígono dado como JSON [[lat,lon],...]."""
    import json
    pts = json.loads(vertices_json)
    lats = [p[0] for p in pts]
    lons = [p[1] for p in pts]
    return {"sw_lat": min(lats), "sw_lon": min(lons),
            "ne_lat": max(lats), "ne_lon": max(lons)}


def _area_ha_zona(z: ZoneConfig) -> float:
    """Calcula el área de una zona en hectáreas a partir de sus vértices o bounding box.
    Usa Shoelace para polígonos y ancho×alto para rectángulos, proyectando grados a metros."""
    DEG_LAT_M = 111_320.0  # metros por grado de latitud

    if z.vertices:
        pts = json.loads(z.vertices)
        # Proyección plana: lat→m, lon→m×cos(lat_media)
        lat_avg = sum(p[0] for p in pts) / len(pts)
        cos_lat = math.cos(math.radians(lat_avg))
        # Shoelace
        n = len(pts)
        area = 0.0
        for i in range(n):
            y1 = pts[i][0] * DEG_LAT_M
            x1 = pts[i][1] * DEG_LAT_M * cos_lat
            y2 = pts[(i + 1) % n][0] * DEG_LAT_M
            x2 = pts[(i + 1) % n][1] * DEG_LAT_M * cos_lat
            area += x1 * y2 - x2 * y1
        return abs(area) / 2.0 / 10_000  # m² → ha
    else:
        sw_lat = z.sw_lat if z.sw_lat is not None else z.lat - _HL
        sw_lon = z.sw_lon if z.sw_lon is not None else z.lon - _HO
        ne_lat = z.ne_lat if z.ne_lat is not None else z.lat + _HL
        ne_lon = z.ne_lon if z.ne_lon is not None else z.lon + _HO
        lat_avg = (sw_lat + ne_lat) / 2
        cos_lat = math.cos(math.radians(lat_avg))
        h = (ne_lat - sw_lat) * DEG_LAT_M
        w = (ne_lon - sw_lon) * DEG_LAT_M * cos_lat
        return h * w / 10_000  # m² → ha


def _calcular_superficie_ha(db: Session) -> float:
    """Suma el área de todas las zonas en hectáreas."""
    zones = db.query(ZoneConfig).all()
    return round(sum(_area_ha_zona(z) for z in zones), 4)


def _nodos_recomendados_zona(area_ha: float, nodos_actuales: int,
                             cv_cwsi: float | None = None) -> dict:
    """
    Calcula nodos recomendados para una zona según superficie + heterogeneidad.

    Densidad óptima (doc-02, Santesteban et al. 2017, Precision Agriculture):
      - Lote homogéneo   (CV < 15%):  1 nodo / 2 ha
      - Lote medio        (CV 15-25%): 1 nodo / 1.5 ha
      - Lote heterogéneo (CV ≥ 25%):  1 nodo / 1 ha

    cv_cwsi: coeficiente de variación (%) del CWSI entre nodos de la zona.
    Si no hay suficientes nodos para calcular CV (< 2), se usa densidad media.
    """
    if area_ha <= 0:
        return {"recomendados": 1, "minimo": 1, "actuales": nodos_actuales,
                "cobertura": "ok", "densidad_ha": 0, "area_ha": 0.0,
                "densidad_actual_ha": None, "heterogeneidad": "sin datos", "cv_cwsi": None}

    # Determinar densidad según heterogeneidad medida
    if cv_cwsi is not None:
        if cv_cwsi < 15:
            ha_por_nodo = 2.0
            heterogeneidad = "homogeneo"
        elif cv_cwsi < 25:
            ha_por_nodo = 1.5
            heterogeneidad = "medio"
        else:
            ha_por_nodo = 1.0
            heterogeneidad = "heterogeneo"
    else:
        # Sin datos de variabilidad → densidad media como criterio conservador
        ha_por_nodo = 1.5
        heterogeneidad = "sin datos"

    recomendados = max(1, math.ceil(area_ha / ha_por_nodo))
    minimo = max(1, math.ceil(area_ha / 2.0))

    if nodos_actuales >= recomendados:
        cobertura = "ok"
    elif nodos_actuales >= minimo:
        cobertura = "suficiente"
    else:
        cobertura = "insuficiente"

    return {
        "recomendados": recomendados,
        "minimo": minimo,
        "actuales": nodos_actuales,
        "cobertura": cobertura,
        "densidad_actual_ha": round(area_ha / nodos_actuales, 1) if nodos_actuales > 0 else None,
        "area_ha": round(area_ha, 2),
        "ha_por_nodo": ha_por_nodo,
        "heterogeneidad": heterogeneidad,
        "cv_cwsi": round(cv_cwsi, 1) if cv_cwsi is not None else None,
    }


def _resumen_varietales(db: Session) -> str:
    """Lista única de varietales configuradas en las zonas, separadas por coma."""
    rows = db.query(ZoneConfig.varietal).filter(ZoneConfig.varietal.isnot(None)).distinct().all()
    varietals = sorted(set(r[0].strip() for r in rows if r[0] and r[0].strip()))
    return ", ".join(varietals) if varietals else ""


def _reload_zones(db: Session) -> None:
    """Reconstruye el dict ZONES desde zone_config (preserva estado active)."""
    global ZONES
    rows = db.query(ZoneConfig).order_by(ZoneConfig.id).all()
    new_zones = {}
    for r in rows:
        bounds = _zone_bounds_from_vertices(r.vertices) if r.vertices else _zone_bounds(r)
        new_zones[r.id] = {
            "name":     r.name,
            "lat":      r.lat,
            "lon":      r.lon,
            "vertices": r.vertices,
            "varietal": r.varietal,
            **bounds,
        }
    ZONES = new_zones


def _check_overlap(new_id: int, sw_lat: float, sw_lon: float,
                   ne_lat: float, ne_lon: float, db: Session) -> str | None:
    """
    Retorna el nombre de la primera zona que se superpone con el rectángulo dado,
    o None si no hay superposición. Excluye new_id para permitir edición propia.
    """
    for r in db.query(ZoneConfig).filter(ZoneConfig.id != new_id).all():
        b = _zone_bounds(r)
        no_overlap = (ne_lat <= b["sw_lat"] or b["ne_lat"] <= sw_lat or
                      ne_lon <= b["sw_lon"] or b["ne_lon"] <= sw_lon)
        if not no_overlap:
            return r.name
    return None


def _restore_node_irrigation(db: Session) -> None:
    """Restaura estado de riego por nodo desde el último IrrigationLog."""
    nodes_with_sol = db.query(NodeConfig).filter(NodeConfig.solenoid.isnot(None)).all()
    for nc in nodes_with_sol:
        last = (
            db.query(IrrigationLog)
            .filter(IrrigationLog.node_id == nc.node_id)
            .order_by(IrrigationLog.ts.desc())
            .first()
        )
        _NODE_IRRIGATION[nc.node_id] = last.active if last else False


def _punto_en_poligono(lat: float, lon: float, vertices: list[list[float]]) -> bool:
    """
    Ray-casting algorithm — determina si (lat, lon) está dentro del polígono.
    vertices: [[lat, lon], ...] en cualquier orden (CW o CCW).
    """
    n = len(vertices)
    inside = False
    j = n - 1
    for i in range(n):
        yi, xi = vertices[i][0], vertices[i][1]
        yj, xj = vertices[j][0], vertices[j][1]
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _zona_para_punto(db: Session, lat: float, lon: float) -> int | None:
    """
    Devuelve el id de la zona que contiene (lat, lon), o None.

    Para zonas con polígono libre (vertices) usa ray-casting.
    Para zonas rectangulares (sw/ne bounds) usa bounding-box.
    Prioridad: polígono > bounding-box (más preciso primero).
    """
    zonas = db.query(ZoneConfig).all()

    # Primero zonas con polígono definido
    for z in zonas:
        if z.vertices:
            try:
                verts = json.loads(z.vertices)
                if verts and _punto_en_poligono(lat, lon, verts):
                    return z.id
            except (ValueError, TypeError, KeyError):
                pass

    # Fallback: bounding-box rectangular
    for z in zonas:
        if not z.vertices and z.sw_lat is not None and z.ne_lat is not None:
            if z.sw_lat <= lat <= z.ne_lat and z.sw_lon <= lon <= z.ne_lon:
                return z.id

    return None


def _ensure_node_config(
    db: Session,
    node_id: str,
    lat: float | None = None,
    lon: float | None = None,
    zona_id: int | None = None,
    solenoid: int | None = None,
) -> None:
    """
    Crea un NodeConfig la primera vez que se ve un node_id.

    Si se pasan lat/lon (payload real) intenta auto-asignar la zona cuyo
    bounding-box contiene el punto GPS del nodo.
    Si se pasa zona_id explícito (simulación) lo usa directamente.
    Si el NodeConfig ya existe no hace nada.
    """
    existing = db.query(NodeConfig).filter(NodeConfig.node_id == node_id).first()
    if existing:
        # Actualizar solenoide si el nodo informa uno diferente
        if solenoid is not None and existing.solenoid != solenoid:
            existing.solenoid = solenoid if solenoid > 0 else None
            db.commit()
        return
    if zona_id is None and lat is not None and lon is not None:
        zona_id = _zona_para_punto(db, lat, lon)
    db.add(NodeConfig(node_id=node_id, zona_id=zona_id, solenoid=solenoid))
    db.commit()


# ---------------------------------------------------------------------------
# Fusión nodo-satélite — estimación CWSI por zona
# ---------------------------------------------------------------------------
#
# FLUJO (idéntico en TRL 4 demo y TRL 5+, difiere solo en la fuente de datos):
#
#   1. NODO → CWSI real en su posición GPS (ground truth)
#   2. SENTINEL-2 en posición del nodo → features espectrales (NDWI, NDVI, VPD)
#        TRL 4: features SINTÉTICAS consistentes con el CWSI medido
#        TRL 5+: bandas reales extraídas de GEE con extraer_bandas_punto()
#   3. CALIBRACIÓN: CWSINDWICorrelationModel.calibrate(pares nodo-S2)
#        el modelo aprende CWSI = f(NDWI, NDRE, VPD) con el nodo como ancla
#   4. ZONA SIN NODO → features S2 propias de esa zona (NDWI, NDVI de sus píxeles)
#        TRL 4: features SINTÉTICAS con firma espectral independiente por zona_id
#        TRL 5+: bandas reales de GEE en el centroide/polígono de la zona
#   5. CWSI_zona = modelo( features_S2_zona, VPD_día )
#        la zona tiene su propio estrés, independiente del CWSI del nodo
#        el nodo solo calibró la curva CWSI↔NDWI — no ancla el resultado
#
# fuente devuelta:
#   "nodo:{id}"    → zona tiene nodo asignado con datos válidos
#   "satelite_s2"  → estimación por fusión nodo-satélite (TRL 4 sintético)
#   "sin datos"    → ningún nodo activo disponible para calibrar
# ---------------------------------------------------------------------------

class _SatelliteFusionService:
    """
    Servicio de fusión nodo-Sentinel-2 para estimar CWSI en zonas sin nodo.

    Calibración (paso 1-3):
        Recibe pares (cwsi_nodo, vpd) de lecturas reales de la DB y construye
        observaciones Sentinel-2 sintéticas con features consistentes con ese CWSI.
        En TRL 5+: reemplazar _obs_from_cwsi() con extraer_bandas_punto(GEE, lat, lon).

    Predicción (paso 4-5):
        Genera features S2 de la zona con firma espectral propia (seeded por zona_id,
        independiente del CWSI del nodo). El VPD real aporta la dimensión temporal.
        En TRL 5+: reemplazar _obs_for_zona() con extraer_bandas_punto(GEE, zona_lat, zona_lon).
    """

    _MIN_PARES = 10   # = CWSINDWICorrelationModel.MIN_CALIBRATION_POINTS

    def __init__(self) -> None:
        import logging
        self._log = logging.getLogger(__name__)
        self._model: "CWSINDWICorrelationModel | None" = None
        self._calibrado = False
        self._n_pares_calibrado = 0
        self._gee = None
        self._gee_active = False
        self._last_s2_meta: dict[int, dict] = {}

        # Intentar inicializar provider de S2 real (STAC o GEE)
        if _S2_PROVIDER_CLASS is not None:
            try:
                provider = _S2_PROVIDER_CLASS()
                if provider.is_available():
                    self._gee = provider      # nombre legacy, funciona con STAC o GEE
                    self._gee_active = True
                    self._log.info(
                        f"[FUSION] Provider S2 activo: {type(provider).__name__} "
                        "— datos Sentinel-2 reales"
                    )
            except Exception as e:
                self._log.warning(f"[FUSION] Provider S2 no disponible: {e}")

        if _S2_OK:
            # Modelo de reserva con datos sintéticos (activo hasta tener datos reales)
            self._calibrar_reserva()

    # ── Calibración ──────────────────────────────────────────────────────────

    def calibrar_con_nodos(
        self,
        pares: list[tuple[float, float]],
        nodo_coords: list[tuple[float, float]] | None = None,
    ) -> bool:
        """
        Calibra el modelo con pares (cwsi_nodo, vpd_kpa) reales de la DB.

        Si GEE está activo y se proveen coordenadas de nodos, extrae bandas
        S2 reales en la ubicación de cada nodo. Si GEE no está disponible o
        falla para algún punto, cae a features S2 sintéticas.

        Retorna True si la calibración fue exitosa.
        """
        if not _S2_OK or len(pares) < self._MIN_PARES:
            return False
        if len(pares) == self._n_pares_calibrado:
            return self._calibrado  # sin datos nuevos, no recalibrar

        # Intentar GEE primero, con fallback per-observation a sintético
        obs = []
        rng = np.random.default_rng(seed=0)
        gee_ok = 0
        for i, (cwsi, vpd) in enumerate(pares):
            real_obs = None
            if self._gee_active and nodo_coords and i < len(nodo_coords):
                lat, lon = nodo_coords[i]
                if lat and lon:
                    real_obs = self._gee.get_observation_at_point(
                        lat, lon, vpd, cwsi_nodo=cwsi,
                    )
            if real_obs:
                obs.append(real_obs)
                gee_ok += 1
            else:
                obs.append(self._obs_from_cwsi(cwsi, vpd, rng))

        if gee_ok > 0:
            self._log.info(f"[FUSION] Calibración: {gee_ok}/{len(pares)} obs con S2 real (GEE)")
        else:
            self._log.info(f"[FUSION] Calibración: {len(pares)} obs sintéticas (GEE no disponible)")
        m = CWSINDWICorrelationModel(poly_degree=2)
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                score = m.calibrate(obs)
            self._model = m
            self._calibrado = True
            self._n_pares_calibrado = len(pares)
            self._log.info(
                f"[FUSION] Calibrado con {len(pares)} lecturas reales: "
                f"R²={score['R2']:.3f}  MAE={score['MAE']:.4f}"
            )
            return True
        except ValueError as e:
            self._log.warning(f"[FUSION] Calibración fallida: {e}")
            return False

    def _calibrar_reserva(self) -> None:
        """Modelo de reserva con datos Sentinel-2 sintéticos (activo al arrancar)."""
        import warnings
        obs = generate_synthetic_sentinel2_dataset(n_obs=80, seed=42)
        labeled = [o for o in obs if o.cwsi_nodo is not None]
        m = CWSINDWICorrelationModel(poly_degree=2)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                score = m.calibrate(labeled)
            self._model = m
            self._calibrado = True
            self._log.info(
                f"[FUSION] Modelo de reserva (sintético): "
                f"R²={score['R2']:.3f}  MAE={score['MAE']:.4f}"
            )
        except ValueError as e:
            self._log.warning(f"[FUSION] Reserva fallida: {e}")

    # ── Predicción ───────────────────────────────────────────────────────────

    def predecir_cwsi(
        self,
        zona_id: int,
        vpd_kpa: float = 1.5,
        zona_lat: float | None = None,
        zona_lon: float | None = None,
    ) -> float | None:
        """
        Predice CWSI para una zona.

        Si el provider S2 está activo y se proveen coordenadas, usa bandas
        reales + modelo físico directo (NDWI→CWSI). Si no hay S2 real,
        usa el modelo polinomial calibrado con features sintéticas.
        """
        if not self._calibrado or self._model is None:
            return None

        # Intentar S2 real primero
        obs = None
        if self._gee_active and zona_lat and zona_lon:
            obs = self._gee.get_observation_for_zone(
                zona_id, zona_lat, zona_lon, vpd_kpa,
            )

        if obs is not None:
            # ── Modelo físico directo para datos S2 reales ──────────
            cwsi = self._cwsi_from_real_s2(obs)
            self._log.debug(
                f"[FUSION] Zona {zona_id}: S2 real → NDWI={obs.NDWI:.4f} "
                f"NDVI={obs.NDVI:.4f} → CWSI={cwsi}"
            )
            # Guardar metadata S2 para la API
            self._last_s2_meta[zona_id] = {
                "ndvi": round(obs.NDVI, 4),
                "ndwi": round(obs.NDWI, 4),
                "fecha_img": obs.fecha,
            }
            return round(cwsi, 3) if cwsi is not None else None

        # Fallback a sintético + modelo polinomial
        obs = self._obs_for_zona(zona_id, vpd_kpa)
        return round(float(self._model.predict_cwsi(obs)), 3)

    @staticmethod
    def _cwsi_from_real_s2(obs: "Sentinel2Observation") -> float | None:
        """
        Estimación física directa de CWSI desde bandas S2 reales.

        Retorna None solo si NDVI < 0.12 (suelo realmente desnudo).

        Viñedos en espaldera: pixel S2 de 10m mezcla hojas + suelo entre
        hileras → NDVI típico 0.15-0.35. Un NDVI=0.18 NO es "sin vegetación",
        es un viñedo normal con baja fracción de cobertura (Bellvert 2015).

        Rango NDWI en cultivos irrigados:
          Bien hidratado: 0.20 – 0.45
          Estrés leve:    0.05 – 0.20
          Estrés severo: -0.10 – 0.05

        Refs: González-Dugo et al. (2013), Bellvert et al. (2015)
        """
        ndwi = obs.NDWI
        ndvi = obs.NDVI
        vpd  = obs.VPD_kPa

        # Suelo realmente desnudo → no se puede estimar CWSI
        if ndvi < 0.12:
            return None

        # Mapeo NDWI → CWSI base (lineal en rango principal)
        # NDWI=0.40 → 0.05, NDWI=0.0 → 0.45, NDWI=-0.15 → 0.60
        cwsi_base = float(np.clip(0.45 - 1.0 * ndwi, 0.0, 0.85))

        # Ajuste por VPD (centrado en 1.5 kPa, rango típico 0.5-3.5)
        vpd_adj = 0.06 * (vpd - 1.5)

        # Ajuste por cobertura vegetal (fracción de mezcla pixel)
        # NDVI 0.12-0.25: viñedo con mucho suelo visible → atenuamos señal
        # NDVI 0.25-0.45: viñedo normal en espaldera
        # NDVI > 0.45: cobertura densa
        if ndvi < 0.25:
            veg_factor = 0.5 + (ndvi - 0.12) * 3.85  # 0.5 a 1.0
        elif ndvi < 0.45:
            veg_factor = 1.0
        else:
            veg_factor = 1.0

        cwsi = cwsi_base * veg_factor + vpd_adj
        return float(np.clip(cwsi, 0.0, 1.0))

    # ── Helpers para construir observaciones S2 ───────────────────────────────

    @staticmethod
    def _obs_from_cwsi(
        cwsi: float,
        vpd: float,
        rng: "np.random.Generator",
    ) -> "Sentinel2Observation":
        """
        Observación S2 sintética consistente con cwsi_nodo conocido.
        Simula lo que Sentinel-2 mediría en el punto del nodo.
        Relación NDWI↔CWSI: González-Dugo et al. (2013).
        """
        NDWI = float(np.clip(0.35 - 0.45 * cwsi + rng.normal(0, 0.03), -0.3, 0.60))
        NDVI = float(np.clip(0.70 - 0.25 * cwsi + rng.normal(0, 0.03),  0.2, 0.90))
        B8A  = float(np.clip(0.35 + rng.normal(0, 0.015), 0.10, 0.70))
        B11  = float(np.clip(B8A * (1 - NDWI) / (1 + NDWI + 1e-9), 0.05, 0.50))
        B8   = float(np.clip(0.40 + rng.normal(0, 0.015), 0.15, 0.75))
        B4   = float(np.clip(B8  * (1 - NDVI) / (1 + NDVI + 1e-9), 0.02, 0.30))
        B12  = float(np.clip(B11 * 0.7 + rng.normal(0, 0.008), 0.02, 0.40))
        return Sentinel2Observation(
            fecha     = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
            B4_red=B4, B8_nir=B8, B8A_nir=B8A,
            B11_swir=B11, B12_swir=B12,
            VPD_kPa=vpd, cwsi_nodo=cwsi,
        )

    @staticmethod
    def _obs_for_zona(zona_id: int, vpd_kpa: float) -> "Sentinel2Observation":
        """
        Observación S2 sintética para la zona — firma espectral propia.

        NDWI y NDVI son propios de la zona (seeded por zona_id), NO derivados
        del CWSI del nodo. Representan la reflectancia de los píxeles de esa zona.
        TRL 5+: reemplazar por extraer_bandas_punto(imagen_GEE, zona_lat, zona_lon).
        """
        rng = np.random.default_rng(seed=int(zona_id) * 7919)
        # Firma espectral de la zona: NDWI en rango típico de cultivo [−0.05, 0.45]
        NDWI = float(np.clip(rng.uniform(-0.05, 0.45), -0.3, 0.60))
        NDVI = float(np.clip(rng.uniform( 0.40, 0.80),  0.2, 0.90))
        B8A  = float(np.clip(0.35 + rng.normal(0, 0.02), 0.10, 0.70))
        B11  = float(np.clip(B8A * (1 - NDWI) / (1 + NDWI + 1e-9), 0.05, 0.50))
        B8   = float(np.clip(0.40 + rng.normal(0, 0.02), 0.15, 0.75))
        B4   = float(np.clip(B8  * (1 - NDVI) / (1 + NDVI + 1e-9), 0.02, 0.30))
        B12  = float(np.clip(B11 * 0.7 + rng.normal(0, 0.010), 0.02, 0.40))
        return Sentinel2Observation(
            fecha     = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
            B4_red=B4, B8_nir=B8, B8A_nir=B8A,
            B11_swir=B11, B12_swir=B12,
            VPD_kPa=vpd_kpa,
        )


_fusion = _SatelliteFusionService()


def _vpd_kpa(t_air: float, rh: float) -> float:
    """VPD [kPa] a partir de temperatura del aire [°C] y humedad relativa [%]."""
    es = 0.6108 * math.exp(17.27 * t_air / (t_air + 237.3))
    return es * max(0.0, 1.0 - rh / 100.0)


def _stress_label(cwsi: float) -> str:
    if cwsi < CWSI_MEDIO:
        return "Bajo"
    if cwsi < CWSI_ALTO:
        return "Medio"
    return "Alto"


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
def _autoasignar_zonas_nodos(db: Session) -> None:
    """
    Al iniciar, asigna zona a los NodeConfig que tienen zona_id=None,
    usando la última telemetría con GPS disponible de cada nodo.
    Solo actualiza — no crea registros nuevos.
    """
    sin_zona = db.query(NodeConfig).filter(NodeConfig.zona_id.is_(None)).all()
    if not sin_zona:
        return
    # Última telemetría con coordenadas por nodo
    subq = (
        db.query(Telemetry.node_id, func.max(Telemetry.id).label("max_id"))
        .filter(Telemetry.lat.isnot(None), Telemetry.lon.isnot(None))
        .group_by(Telemetry.node_id)
        .subquery()
    )
    last_gps = {
        r.node_id: r
        for r in db.query(Telemetry).join(subq, Telemetry.id == subq.c.max_id).all()
    }
    updated = 0
    for cfg in sin_zona:
        t = last_gps.get(cfg.node_id)
        if t and t.lat is not None and t.lon is not None:
            zona_id = _zona_para_punto(db, t.lat, t.lon)
            if zona_id is not None:
                cfg.zona_id = zona_id
                updated += 1
    if updated:
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _seed_defaults(db)
        _reload_zones(db)
        _restore_node_irrigation(db)
        _autoasignar_zonas_nodos(db)
    finally:
        db.close()
    yield


app = FastAPI(title="HydroVision AG — Demo TRL 4", version="0.4.0", lifespan=lifespan)

HOME_HTML      = Path("templates/home.html")
DASHBOARD_HTML = Path("templates/dashboard.html")
ADMIN_HTML     = Path("templates/admin.html")
INFORME_HTML   = Path("templates/informe.html")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------
class EnvData(BaseModel):
    t_air: float = Field(..., ge=-10.0, le=60.0)
    rh: float = Field(..., ge=0.0, le=100.0)
    wind_ms: float = Field(..., ge=0.0, le=50.0)
    rain_mm: float = Field(..., ge=0.0, le=200.0)

class ThermalData(BaseModel):
    tc_mean: float = Field(..., ge=-10.0, le=70.0)
    tc_max: float = Field(..., ge=-10.0, le=70.0)
    tc_wet: float = Field(..., ge=-10.0, le=70.0)
    tc_dry: float = Field(..., ge=-10.0, le=70.0)
    cwsi: float = Field(..., ge=0.0, le=1.0)
    valid_pixels: int = Field(..., ge=0)

class DendroData(BaseModel):
    mds_mm: float = Field(..., ge=0.0, le=2000.0)
    mds_norm: float = Field(..., ge=0.0, le=1.0)

class HsiData(BaseModel):
    value: float = Field(..., ge=0.0, le=1.0)
    w_cwsi: float = Field(..., ge=0.0, le=1.0)
    w_mds: float = Field(..., ge=0.0, le=1.0)
    wind_override: bool

class GpsData(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)

CalidadCaptura = Literal["ok", "lluvia", "post_lluvia", "fumigacion", "post_fumigacion"]

class SolenoidData(BaseModel):
    canal: int = Field(0, ge=0, le=16)            # canal Rain Bird (0 = sin solenoide)
    active: bool = False                          # estado actual del relé
    reason: str = "idle"                          # razón: hsi_alto, hsi_bajo, lluvia, etc.
    ciclos_activo: int = Field(0, ge=0, le=100)   # ciclos consecutivos encendido

class NodePayload(BaseModel):
    v: int;  node_id: str;  ts: int;  cycle: int
    env: EnvData;  thermal: ThermalData;  dendro: DendroData
    hsi: HsiData;  gps: GpsData
    bat_pct: int = Field(..., ge=0, le=100)
    pm2_5: int = Field(..., ge=0, le=1000)
    calidad_captura: CalidadCaptura
    hmac: Optional[str] = None                   # HMAC-SHA256 firma del payload
    solenoid: Optional[SolenoidData] = None      # estado solenoide (informado por el nodo)

class ZoneIn(BaseModel):
    name:             str
    lat:              float
    lon:              float
    sw_lat:           Optional[float] = None
    sw_lon:           Optional[float] = None
    ne_lat:           Optional[float] = None
    ne_lon:           Optional[float] = None
    vertices:         Optional[str]   = None   # JSON "[[lat,lon],...]" — polígono libre
    varietal:         Optional[str]   = None   # variedad/cultivo
    crop_yield_kg_ha: Optional[float] = None   # rendimiento potencial kg/ha

class NodeConfigIn(BaseModel):
    name:     Optional[str] = None
    zona_id:  Optional[int] = None

class ConfigIn(BaseModel):
    field_name:     Optional[str]   = None
    field_location: Optional[str]   = None


# ---------------------------------------------------------------------------
# Seguridad: HMAC verification + Rate limiting
# ---------------------------------------------------------------------------

# Shared secret para HMAC — cargar desde variable de entorno en producción
INGEST_SECRET = os.getenv("HYDROVISION_INGEST_SECRET", "dev-secret-change-in-production")

# Rate limiter: máximo 100 requests/minuto por node_id
_rate_limit: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT_WINDOW = 60.0   # segundos
_RATE_LIMIT_MAX = 100        # requests por ventana


def _check_rate_limit(node_id: str) -> bool:
    """Retorna True si el request está dentro del límite. False si excede."""
    now = _time.time()
    timestamps = _rate_limit[node_id]
    # Purgar timestamps fuera de la ventana
    _rate_limit[node_id] = [t for t in timestamps if now - t < _RATE_LIMIT_WINDOW]
    if len(_rate_limit[node_id]) >= _RATE_LIMIT_MAX:
        return False
    _rate_limit[node_id].append(now)
    return True


def _verify_hmac(payload: NodePayload) -> bool:
    """Verifica la firma HMAC-SHA256 del payload.
    En modo desarrollo (secret='dev-secret-change-in-production'), acepta sin HMAC.
    """
    if INGEST_SECRET == "dev-secret-change-in-production":
        return True  # Modo desarrollo: no exigir HMAC
    if not payload.hmac:
        return False
    # Reconstruir el mensaje firmado: node_id + ts + cycle
    msg = f"{payload.node_id}:{payload.ts}:{payload.cycle}".encode()
    expected = _hmac.new(INGEST_SECRET.encode(), msg, hashlib.sha256).hexdigest()
    return _hmac.compare_digest(payload.hmac, expected)


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

def _audit(db, event: str, node_id: str = None, detail: str = None, ip: str = None):
    """Registra un evento en la tabla audit_log."""
    db.add(AuditLog(event=event, node_id=node_id, detail=detail, ip=ip))
    db.commit()


# ---------------------------------------------------------------------------
# Rutas principales
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    return HOME_HTML.read_text(encoding="utf-8")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML.read_text(encoding="utf-8")


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return ADMIN_HTML.read_text(encoding="utf-8")


@app.get("/informe", response_class=HTMLResponse)
def informe_page():
    return INFORME_HTML.read_text(encoding="utf-8")


@app.post("/ingest")
def ingest(payload: NodePayload, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else None

    # Rate limiting por node_id
    if not _check_rate_limit(payload.node_id):
        _audit(db, "rate_limit", node_id=payload.node_id, ip=client_ip)
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Verificación HMAC (en producción: rechaza payloads sin firma válida)
    if not _verify_hmac(payload):
        _audit(db, "hmac_fail", node_id=payload.node_id, ip=client_ip)
        raise HTTPException(status_code=401, detail="Invalid or missing HMAC signature")

    if payload.calidad_captura != "ok":
        return {"status": "descartado", "motivo": payload.calidad_captura}

    # Extraer canal solenoide del payload (0 = sin solenoide)
    sol_canal = payload.solenoid.canal if payload.solenoid else None
    sol_canal_db = sol_canal if sol_canal and sol_canal > 0 else None

    _ensure_node_config(db, payload.node_id, lat=payload.gps.lat, lon=payload.gps.lon,
                        solenoid=sol_canal_db)

    db.add(Telemetry(
        node_id=payload.node_id, ts=payload.ts,
        cwsi=payload.thermal.cwsi, hsi=payload.hsi.value,
        mds_mm=payload.dendro.mds_mm, t_air=payload.env.t_air,
        rh=payload.env.rh, wind_ms=payload.env.wind_ms,
        rain_mm=payload.env.rain_mm, bat_pct=payload.bat_pct,
        calidad=payload.calidad_captura, origen="real",
        lat=payload.gps.lat, lon=payload.gps.lon,
    ))

    # Registrar estado de riego reportado por el nodo (decisión autónoma)
    # Si la zona está en reposo, el backend ordena apagar el solenoide.
    inhibir_riego = False
    if payload.solenoid and payload.solenoid.canal > 0:
        sol = payload.solenoid
        nc = db.query(NodeConfig).filter(NodeConfig.node_id == payload.node_id).first()

        # Verificar si la zona está en reposo/dormancia
        if nc and nc.zona_id and _zona_en_reposo(nc.zona_id):
            if sol.active:
                inhibir_riego = True
                _NODE_IRRIGATION[payload.node_id] = False
                _audit(db, "irrigate_inhibit", node_id=payload.node_id,
                       detail=f"zona={nc.zona_id} reposo_fenologico", ip=client_ip)
            else:
                _NODE_IRRIGATION[payload.node_id] = False
        else:
            # Sincronizar estado en memoria
            prev_active = _NODE_IRRIGATION.get(payload.node_id, False)
            _NODE_IRRIGATION[payload.node_id] = sol.active

            # Registrar cambio de estado en IrrigationLog
            if sol.active != prev_active:
                db.add(IrrigationLog(
                    node_id=payload.node_id,
                    zona=nc.zona_id if nc else None,
                    duration_min=sol.ciclos_activo * 15,
                    active=sol.active,
                ))
                evt = "irrigate_on" if sol.active else "irrigate_off"
                _audit(db, evt, node_id=payload.node_id,
                       detail=f"zona={nc.zona_id if nc else '?'} canal={sol.canal}", ip=client_ip)

    db.add(AuditLog(event="ingest_ok", node_id=payload.node_id, ip=client_ip))
    db.commit()
    resp = {"status": "ok", "node_id": payload.node_id}

    # Informar varietal de la zona al nodo (el nodo lo usa para GDD/fenología)
    nc_final = db.query(NodeConfig).filter(
        NodeConfig.node_id == payload.node_id).first()
    if nc_final and nc_final.zona_id and nc_final.zona_id in ZONES:
        zona_varietal = ZONES[nc_final.zona_id].get("varietal")
        if zona_varietal:
            resp["varietal"] = zona_varietal

    # Informar modo simulación de solenoide al nodo
    if _NODE_SOL_SIM.get(payload.node_id, False):
        resp["sol_sim"] = True

    if inhibir_riego:
        resp["command"] = {"irrigate": False, "reason": "reposo_fenologico"}
    return resp


@app.get("/api/status")
def status(db: Session = Depends(get_db)):
    subq = (
        db.query(Telemetry.node_id, func.max(Telemetry.id).label("max_id"))
        .group_by(Telemetry.node_id).subquery()
    )
    rows = db.query(Telemetry).join(subq, Telemetry.id == subq.c.max_id).all()
    cfgs = {c.node_id: c for c in db.query(NodeConfig).all()}
    now  = datetime.datetime.utcnow()
    return [
        {
            "node_id":    r.node_id,
            "name":       cfgs[r.node_id].name if r.node_id in cfgs else None,
            "cwsi":       round(r.cwsi, 3),
            "hsi":        round(r.hsi, 3),
            "mds_mm":     round(r.mds_mm, 3),
            "t_air":      r.t_air,
            "rh":         r.rh,
            "wind_ms":    r.wind_ms,
            "bat_pct":    r.bat_pct,
            "stress":     _stress_label(r.cwsi),
            "origen":     r.origen,
            "hace_min":   int((now - r.created_at).total_seconds() / 60),
            "lat":        r.lat,
            "lon":        r.lon,
        }
        for r in rows
    ]


@app.get("/api/alerts")
def alerts(db: Session = Depends(get_db)):
    subq = (
        db.query(Telemetry.node_id, func.max(Telemetry.id).label("max_id"))
        .group_by(Telemetry.node_id).subquery()
    )
    rows = (
        db.query(Telemetry)
        .join(subq, Telemetry.id == subq.c.max_id)
        .filter(Telemetry.cwsi >= CWSI_IRRIGATE)
        .all()
    )
    return [{"node_id": r.node_id, "cwsi": round(r.cwsi, 3)} for r in rows]


@app.get("/api/history/{node_id}")
def history(node_id: str, db: Session = Depends(get_db)):
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=48)
    rows = (
        db.query(Telemetry)
        .filter(Telemetry.node_id == node_id, Telemetry.created_at >= cutoff)
        .order_by(Telemetry.created_at).all()
    )
    return [{"ts": r.created_at.isoformat(), "cwsi": round(r.cwsi, 3), "hsi": round(r.hsi, 3)}
            for r in rows]


def _zona_en_reposo(zona_id: int) -> bool:
    """True si la zona está en periodo de reposo/dormancia (Ky ≤ 0.15)."""
    zone = ZONES.get(zona_id)
    if not zone:
        return False
    fenol = _fenologia_zona(zone.get("varietal"))
    return fenol["ky"] <= 0.15


@app.post("/api/irrigate/{node_id}")
def irrigate(node_id: str, db: Session = Depends(get_db)):
    """
    Override manual de riego desde el dashboard.

    En producción el riego lo decide el nodo autónomamente (HSI >= umbral).
    Este endpoint es un override manual para:
      - Forzar riego en modo demo/simulación (TRL 4)
      - Override de emergencia desde el dashboard (TRL 5+)

    Bloquea activación si la zona está en reposo/dormancia (Ky ≤ 0.15).
    En TRL 5+ el override se envía al nodo via MQTT/LoRa como comando.
    El nodo lo ejecuta y lo reporta en el siguiente /ingest.
    """
    nc = db.query(NodeConfig).filter(NodeConfig.node_id == node_id).first()
    if not nc:
        raise HTTPException(status_code=404, detail="Nodo no existe")
    if nc.solenoid is None:
        raise HTTPException(status_code=400, detail="Este nodo no tiene solenoide asignado")

    # Bloquear riego en reposo/dormancia
    if nc.zona_id and _zona_en_reposo(nc.zona_id):
        currently_on = _NODE_IRRIGATION.get(node_id, False)
        if not currently_on:
            # No permitir activar — solo permitir apagar si estaba encendido
            return {
                "status": "blocked", "node_id": node_id,
                "reason": "reposo",
                "detail": "La variedad está en reposo/dormancia. "
                          "Regar en este periodo es contraproducente.",
            }

    new_state = not _NODE_IRRIGATION.get(node_id, False)
    _NODE_IRRIGATION[node_id] = new_state
    db.add(IrrigationLog(
        node_id=node_id, zona=nc.zona_id,
        duration_min=30, active=new_state,
    ))
    evt = "irrigate_on" if new_state else "irrigate_off"
    _audit(db, evt, node_id=node_id, detail="source=manual_dashboard")
    db.commit()
    # TRL 5+: publicar comando MQTT override al nodo:
    #   topic:   hydrovision/{node_id}/command/irrigate
    #   payload: {"active": new_state, "source": "manual_dashboard"}
    #   El nodo lo ejecuta y lo reporta en el siguiente /ingest.
    return {"status": "ok", "node_id": node_id, "active": new_state, "source": "manual_override"}


@app.post("/api/sol_sim/{node_id}")
def toggle_sol_sim(node_id: str, db: Session = Depends(get_db)):
    """
    Activa/desactiva modo simulación del solenoide de un nodo.
    En simulación: la lógica de riego corre normalmente pero el GPIO
    del relé no se activa. Útil para pruebas de campo.
    El flag viaja al nodo en la respuesta /ingest (downlink LoRa).
    """
    nc = db.query(NodeConfig).filter(NodeConfig.node_id == node_id).first()
    if not nc:
        raise HTTPException(status_code=404, detail="Nodo no existe")
    new_state = not _NODE_SOL_SIM.get(node_id, False)
    _NODE_SOL_SIM[node_id] = new_state
    return {"status": "ok", "node_id": node_id, "sol_sim": new_state}


@app.get("/api/zones")
def get_zones(db: Session = Depends(get_db)):
    subq = (
        db.query(Telemetry.node_id, func.max(Telemetry.id).label("max_id"))
        .group_by(Telemetry.node_id).subquery()
    )
    rows = db.query(Telemetry).join(subq, Telemetry.id == subq.c.max_id).all()
    cfgs = {c.node_id: c for c in db.query(NodeConfig).all()}
    node_readings = [
        {
            "node_id": r.node_id, "lat": r.lat, "lon": r.lon,
            "cwsi": r.cwsi, "origen": r.origen,
            "t_air": r.t_air, "rh": r.rh,
        }
        for r in rows if r.lat is not None and r.lon is not None and r.cwsi is not None
    ]

    # Índice rápido: node_id → cwsi de su última lectura
    node_cwsi = {r.node_id: r.cwsi for r in rows}

    # VPD medio del campo (dimensión temporal para el modelo satelital)
    vpd_lista = [
        _vpd_kpa(n["t_air"], n["rh"])
        for n in node_readings if n["t_air"] is not None and n["rh"] is not None
    ]
    vpd_campo = (sum(vpd_lista) / len(vpd_lista)) if vpd_lista else 1.5

    # Calibrar modelo de fusión con historial real de la DB
    # (pares cwsi_nodo, vpd reales → features S2 sintéticas consistentes)
    # Solo recalibra si hay nuevos datos desde la última calibración.
    if node_readings:
        hist = (
            db.query(Telemetry.cwsi, Telemetry.t_air, Telemetry.rh,
                     Telemetry.lat, Telemetry.lon)
            .filter(Telemetry.cwsi.isnot(None),
                    Telemetry.t_air.isnot(None),
                    Telemetry.rh.isnot(None))
            .order_by(Telemetry.id.desc())
            .limit(200)
            .all()
        )
        pares = [(float(r.cwsi), _vpd_kpa(float(r.t_air), float(r.rh))) for r in hist]
        coords = [(float(r.lat), float(r.lon)) for r in hist
                   if r.lat is not None and r.lon is not None]
        _fusion.calibrar_con_nodos(
            pares,
            nodo_coords=coords if len(coords) == len(pares) else None,
        )

    LAT_M, LON_M = 111_000.0, 95_100.0

    result = []
    for zona_id, zone in ZONES.items():
        # ── Determinar CWSI de la zona ─────────────────────────────────────
        # Prioridad 1: nodo explícitamente asignado a esta zona (NodeConfig.zona_id)
        assigned_with_data = [
            nr for nr in node_readings
            if cfgs.get(nr["node_id"]) and cfgs[nr["node_id"]].zona_id == zona_id
        ]
        # Prioridad 2: nodo físicamente dentro de los bounds de la zona
        node_in_zone = None
        if not assigned_with_data:
            sw_lat = zone.get("sw_lat")
            ne_lat = zone.get("ne_lat")
            sw_lon = zone.get("sw_lon")
            ne_lon = zone.get("ne_lon")
            if None not in (sw_lat, ne_lat, sw_lon, ne_lon):
                for nr in node_readings:
                    if sw_lat <= nr["lat"] <= ne_lat and sw_lon <= nr["lon"] <= ne_lon:
                        node_in_zone = nr
                        break  # primer nodo dentro de la zona

        if assigned_with_data:
            n = assigned_with_data[0]
            cwsi   = n["cwsi"]
            fuente = f"nodo:{n['node_id']}"
            origen = n["origen"]
        elif node_in_zone:
            cwsi   = node_in_zone["cwsi"]
            fuente = f"nodo:{node_in_zone['node_id']}"
            origen = node_in_zone["origen"]
        elif _SIM_RUNNING and zona_id in _SIM_WATER:
            # Prioridad 3a: simulación activa → CWSI derivado del water_level
            # Permite que zonas S2 reflejen efecto de riego/lluvia/ET
            w = _SIM_WATER[zona_id]
            hour_frac = datetime.datetime.utcnow().hour + datetime.datetime.utcnow().minute / 60
            diurnal = math.sin(math.pi * (hour_frac - 6) / 12) * 0.06
            cwsi   = _sim_water_to_cwsi(w, diurnal, 0.0)
            fuente = "satelite_s2"
            origen = "simulado"
        elif node_readings:
            # Prioridad 3b: fusión nodo-satélite (producción, sin simulación)
            cwsi   = _fusion.predecir_cwsi(
                zona_id, vpd_campo,
                zona_lat=zone["lat"], zona_lon=zone["lon"],
            )
            if _fusion._gee_active:
                s2m = _fusion._last_s2_meta.get(zona_id, {})
                if cwsi is None:
                    fuente = "sin_cobertura"
                    origen = "real"
                else:
                    fuente = "satelite_real"
                    origen = "real"
            else:
                fuente = "satelite_s2"
                origen = "simulado"
        else:
            cwsi   = None
            fuente = "sin datos"
            origen = None

        # ── Nodos asignados a esta zona (metadata + estado riego) ─────────
        assigned = []
        zone_has_active_irrigation = False
        for node_id, cfg in cfgs.items():
            if cfg.zona_id != zona_id:
                continue
            ncwsi = node_cwsi.get(node_id)
            nr    = next((r for r in rows if r.node_id == node_id), None)
            dist_m = None
            if nr and nr.lat and nr.lon:
                dy     = (nr.lat - zone["lat"]) * LAT_M
                dx     = (nr.lon - zone["lon"]) * LON_M
                dist_m = round(math.sqrt(dx**2 + dy**2))
            # Representatividad: diferencia entre CWSI del nodo y de la zona
            rep = None
            if ncwsi is not None and cwsi is not None:
                diff = abs(ncwsi - cwsi)
                rep  = "buena" if diff < 0.10 else ("moderada" if diff < 0.20 else "baja")
            node_active = _NODE_IRRIGATION.get(node_id, False)
            if node_active:
                zone_has_active_irrigation = True
            assigned.append({
                "node_id": node_id,
                "name":    cfg.name or node_id,
                "cwsi":    round(ncwsi, 3) if ncwsi is not None else None,
                "dist_m":  dist_m,
                "representatividad": rep,
                "solenoid": cfg.solenoid,
                "irrigating": node_active,
                "sol_sim": _NODE_SOL_SIM.get(node_id, False),
            })

        # ── Auto-desactivación: CWSI volvió a verde → cortar riego ────
        if cwsi is not None and cwsi < CWSI_MEDIO:
            for an in assigned:
                if an["irrigating"]:
                    _NODE_IRRIGATION[an["node_id"]] = False
                    an["irrigating"] = False
                    db.add(IrrigationLog(
                        node_id=an["node_id"], zona=zona_id,
                        duration_min=0, active=False,
                        ts=datetime.datetime.utcnow(),
                    ))
            if zone_has_active_irrigation:
                zone_has_active_irrigation = False
                db.commit()

        tiene_nodo = fuente.startswith("nodo:")

        # Calcular área, CV intra-zona y densidad de nodos recomendada
        zone_obj = db.query(ZoneConfig).filter(ZoneConfig.id == zona_id).first()
        area_ha = _area_ha_zona(zone_obj) if zone_obj else 0.0

        # CV de CWSI entre nodos asignados (heterogeneidad intra-zona)
        node_cwsis = [n["cwsi"] for n in assigned if n["cwsi"] is not None]
        if len(node_cwsis) >= 2:
            mean_c = sum(node_cwsis) / len(node_cwsis)
            std_c = (sum((x - mean_c) ** 2 for x in node_cwsis) / len(node_cwsis)) ** 0.5
            cv_cwsi = (std_c / mean_c * 100) if mean_c > 0 else 0.0
        else:
            cv_cwsi = None  # no hay suficientes nodos para calcular variabilidad

        densidad = _nodos_recomendados_zona(area_ha, len(assigned), cv_cwsi)

        # Fenología → inhibir sugerencia de riego en reposo/dormancia
        fenol = _fenologia_zona(zone.get("varietal"))
        en_reposo = fenol["ky"] <= 0.15

        result.append({
            "id": zona_id, "name": zone["name"],
            "lat": zone["lat"], "lon": zone["lon"],
            "sw_lat": zone.get("sw_lat"), "sw_lon": zone.get("sw_lon"),
            "ne_lat": zone.get("ne_lat"), "ne_lon": zone.get("ne_lon"),
            "vertices": zone.get("vertices"),
            "varietal": zone.get("varietal"),
            "active": zone_has_active_irrigation, "cwsi": cwsi,
            "stress": _stress_label(cwsi) if cwsi is not None else None,
            "fuente": fuente, "origen": origen,
            "s2_meta": _fusion._last_s2_meta.get(zona_id),
            "tiene_nodo": tiene_nodo,
            "sugerir_riego": cwsi is not None and cwsi >= CWSI_IRRIGATE and not en_reposo,
            "en_reposo": en_reposo,
            "fenologia": fenol["etapa"],
            "assigned_nodes": assigned,
            "densidad_nodos": densidad,
        })
    return result


# ---------------------------------------------------------------------------
# Simulación continua — loop en background
# ---------------------------------------------------------------------------
import asyncio as _asyncio

_SIM_RUNNING   = False   # estado actual
_SIM_TASK: "Optional[_asyncio.Task]" = None

# Perfiles de nodos simulados — cwsi_base varía lentamente con deriva diaria
_SIM_PROFILES = [
    {"node_id": "HV-A4CF12B3", "cwsi_amp": 0.06, "bat_base": 88, "zone_id": 1, "solenoid": 1},
    {"node_id": "HV-B8A21F9C", "cwsi_amp": 0.10, "bat_base": 74, "zone_id": 3, "solenoid": 2},
    {"node_id": "HV-C2D35E1A", "cwsi_amp": 0.06, "bat_base": 61, "zone_id": 5, "solenoid": 3},
    # Lote Sur (20 ha) — 3 nodos de 8 necesarios (cobertura insuficiente)
    # lat/lon_offset distribuyen los nodos dentro del polígono
    {"node_id": "HV-D7E42A0B", "cwsi_amp": 0.08, "bat_base": 82, "zone_id": 12, "solenoid": 4,
     "lat_off": -0.0010, "lon_off": -0.0015},  # sector norte
    {"node_id": "HV-E1F56C3D", "cwsi_amp": 0.07, "bat_base": 79, "zone_id": 12, "solenoid": 5,
     "lat_off":  0.0005, "lon_off":  0.0010},   # sector central
    {"node_id": "HV-F3A89D2E", "cwsi_amp": 0.09, "bat_base": 71, "zone_id": 12, "solenoid": 6,
     "lat_off":  0.0015, "lon_off": -0.0005},   # sector sur
]

# Estado hídrico por zona: 0.0 = seco, 1.0 = saturado
# El CWSI se deriva como ~ (1 - water_level) con variación diurna + ruido
_SIM_WATER: dict[int, float] = {}

# Tasas del modelo hidrológico simplificado (por tick de 30 s)
_ET_RATE       = 0.008   # evapotranspiración base por tick (pierde agua)
_ET_DIURNAL    = 0.006   # componente diurna extra (mediodía evapora más)
_IRRIG_RATE    = 0.035   # ganancia de agua por tick cuando el riego está activo
_RAIN_RATE     = 0.05    # ganancia de agua por mm de lluvia


def _sim_rain_mm(ts_dt: datetime.datetime) -> float:
    """Genera lluvia ocasional: ~10% de probabilidad por hora, solo de noche o mañana."""
    if ts_dt.minute != 0:
        return 0.0
    if 8 <= ts_dt.hour <= 18:
        prob = 0.04
    else:
        prob = 0.12
    if random.random() > prob:
        return 0.0
    return round(random.uniform(1.5, 12.0), 1)


def _sim_water_to_cwsi(water: float, diurnal: float, noise: float) -> float:
    """Convierte nivel de agua [0-1] a CWSI [0-1].
    Agua alta → CWSI bajo (sin estrés). Agua baja → CWSI alto (estrés severo)."""
    base = 1.0 - water  # inversión directa
    return round(max(0.0, min(1.0, base + diurnal + noise)), 3)


def _sim_tick(db: Session) -> dict:
    """Inserta una lectura por nodo usando el estado hídrico de cada zona.
    Actualiza water_level para TODAS las zonas (con y sin nodo):
    baja por evapotranspiración, sube por riego/lluvia."""
    zone_list = list(ZONES.items())
    if len(zone_list) < 3:
        return {"ok": False}

    def zone_for(p):
        """Resuelve zona de un perfil por zone_id."""
        zid = p["zone_id"]
        return (zid, ZONES[zid]) if zid in ZONES else (None, None)

    now = datetime.datetime.utcnow()
    rain_this_tick = _sim_rain_mm(now)

    # Factor diurno de evapotranspiración: máximo al mediodía, mínimo de noche
    hour_frac = now.hour + now.minute / 60
    et_diurnal = _ET_DIURNAL * max(0, math.sin(math.pi * (hour_frac - 6) / 12))

    # ── Zonas con nodo: insertar telemetría + actualizar water ──────────
    zonas_con_nodo = set()
    for p in _SIM_PROFILES:
        zona_id, zone = zone_for(p)
        if zona_id is None:
            continue
        zonas_con_nodo.add(zona_id)
        _ensure_node_config(db, p["node_id"], zona_id=zona_id, solenoid=p.get("solenoid"))

        # Inicializar water_level si no existe
        if zona_id not in _SIM_WATER:
            _SIM_WATER[zona_id] = 0.65

        # ── Actualizar estado hídrico ───────────────────────────────────
        w = _SIM_WATER[zona_id]

        # Pérdida: evapotranspiración (siempre, más intensa de día)
        w -= _ET_RATE + et_diurnal

        # Ganancia: riego activo en este nodo (tiene solenoide y está regando)
        # Inhibido en reposo/dormancia — el nodo no debería regar
        if _NODE_IRRIGATION.get(p["node_id"], False):
            if _zona_en_reposo(zona_id):
                _NODE_IRRIGATION[p["node_id"]] = False
            else:
                w += _IRRIG_RATE

        # Ganancia: lluvia
        if rain_this_tick > 0:
            w += rain_this_tick * _RAIN_RATE

        # Clampar a [0.05, 1.0] — nunca llega a 0 absoluto
        w = max(0.05, min(1.0, w))
        _SIM_WATER[zona_id] = round(w, 4)

        # ── Calcular CWSI desde water_level ─────────────────────────────
        diurnal_cwsi = math.sin(math.pi * (hour_frac - 6) / 12) * p["cwsi_amp"]
        cwsi = _sim_water_to_cwsi(w, diurnal_cwsi, random.uniform(-0.02, 0.02))

        t_air = round(20 + 10 * max(0, math.sin(math.pi * (hour_frac - 6) / 12))
                       + random.uniform(-1.5, 1.5), 1)
        rh    = round(max(20, min(95, 60 - cwsi * 25 + random.uniform(-5, 5))), 1)

        db.add(Telemetry(
            node_id=p["node_id"], ts=int(now.timestamp()),
            cwsi=cwsi,
            hsi=round(min(1.0, cwsi * 0.70 + random.uniform(0, 0.06)), 3),
            mds_mm=round(0.08 + cwsi * 0.28 + random.uniform(-0.01, 0.01), 3),
            t_air=t_air, rh=rh,
            wind_ms=round(random.uniform(0.3, 3.5), 1),
            rain_mm=rain_this_tick,
            bat_pct=p["bat_base"] + random.randint(-3, 1),
            calidad="ok", origen="simulado",
            lat=zone["lat"] + p.get("lat_off", 0),
            lon=zone["lon"] + p.get("lon_off", 0),
            created_at=now,
        ))

    # ── Zonas SIN nodo: solo actualizar water_level (sin telemetría) ────
    for zona_id, zone in zone_list:
        if zona_id in zonas_con_nodo:
            continue
        if zona_id not in _SIM_WATER:
            _SIM_WATER[zona_id] = 0.55

        w = _SIM_WATER[zona_id]
        w -= _ET_RATE + et_diurnal
        # Zonas sin nodo no tienen solenoide → no pueden recibir riego
        if rain_this_tick > 0:
            w += rain_this_tick * _RAIN_RATE
        w = max(0.05, min(1.0, w))
        _SIM_WATER[zona_id] = round(w, 4)

    db.commit()
    return {"ok": True}


async def _sim_loop():
    """Loop principal: tick cada 30 s. El estado hídrico evoluciona solo."""
    global _SIM_RUNNING
    while _SIM_RUNNING:
        db = SessionLocal()
        try:
            _sim_tick(db)
        finally:
            db.close()
        await _asyncio.sleep(30)
    _SIM_RUNNING = False


@app.post("/api/simulate/start")
async def simulate_start():
    global _SIM_RUNNING, _SIM_TASK
    if _SIM_RUNNING:
        return {"status": "already_running"}
    if len(ZONES) < 3:
        raise HTTPException(status_code=400, detail="Se necesitan al menos 3 zonas configuradas")
    # Carga histórica inicial (48 h) si la DB está vacía
    db = SessionLocal()
    try:
        from sqlalchemy import func as _func
        count = db.query(_func.count(Telemetry.id)).scalar()
        if count == 0:
            _seed_history(db)
        # Inicializar water_level desde CWSI satelital actual de cada zona.
        # water = 1 - cwsi (inversión directa del modelo hidrológico).
        # Si no hay dato satelital disponible, usar fallback fijo por posición.
        fallback = [0.80, 0.55, 0.35, 0.70, 0.45]
        for i, (zid, zone) in enumerate(ZONES.items()):
            if zid in _SIM_WATER:
                continue  # ya inicializado (simulación que se reinicia)
            cwsi_sat = None
            if _fusion._calibrado:
                try:
                    cwsi_sat = _fusion.predecir_cwsi(
                        zid, vpd_kpa=1.5,
                        zona_lat=zone.get("lat"), zona_lon=zone.get("lon"),
                    )
                except Exception:
                    pass
            if cwsi_sat is not None:
                # Invertir CWSI → water_level, con pequeño ruido para no arrancar
                # todas las zonas con el mismo valor exacto si el satélite da similar
                _SIM_WATER[zid] = float(np.clip(1.0 - cwsi_sat + random.uniform(-0.03, 0.03), 0.05, 0.95))
            else:
                _SIM_WATER[zid] = fallback[i % len(fallback)]
    finally:
        db.close()
    _SIM_RUNNING = True
    _SIM_TASK    = _asyncio.create_task(_sim_loop())
    return {"status": "started"}


@app.post("/api/simulate/stop")
async def simulate_stop():
    global _SIM_RUNNING, _SIM_TASK
    _SIM_RUNNING = False
    if _SIM_TASK:
        _SIM_TASK.cancel()
        _SIM_TASK = None
    return {"status": "stopped"}


@app.get("/api/simulate/status")
def simulate_status():
    return {"running": _SIM_RUNNING}


def _seed_history(db: Session) -> None:
    """Inserta 48 h de historial sintético usando el modelo hidrológico.
    Cada zona arranca con un nivel de agua diferente y evoluciona con
    evapotranspiración, riego automático y lluvia ocasional."""
    zone_list = list(ZONES.items())

    def zone_for(p):
        if "zone_id" in p:
            zid = p["zone_id"]
            return (zid, ZONES[zid]) if zid in ZONES else (None, None)
        idx = p["zone_idx"]
        if idx == "mid":
            return zone_list[len(zone_list) // 2]
        return zone_list[idx]

    now = datetime.datetime.utcnow()

    # Estado hídrico inicial: derivado del CWSI satelital actual de cada zona.
    # El historial de 48h arranca desde el estado real y evoluciona hacia atrás.
    water_levels: dict[int, float] = {}
    fallback_water = [0.85, 0.55, 0.35, 0.70, 0.60, 0.45]

    for pi, p in enumerate(_SIM_PROFILES):
        zona_id, zone = zone_for(p)
        if zona_id is None:
            continue
        _ensure_node_config(db, p["node_id"], zona_id=zona_id, solenoid=p.get("solenoid"))
        if zona_id not in water_levels:
            cwsi_sat = None
            if _fusion._calibrado:
                try:
                    cwsi_sat = _fusion.predecir_cwsi(
                        zona_id, vpd_kpa=1.5,
                        zona_lat=zone.get("lat"), zona_lon=zone.get("lon"),
                    )
                except Exception:
                    pass
            if cwsi_sat is not None:
                water_levels[zona_id] = float(np.clip(1.0 - cwsi_sat + random.uniform(-0.05, 0.05), 0.05, 0.95))
            else:
                water_levels[zona_id] = fallback_water[pi % len(fallback_water)]

    # Evento de lluvia hace ~30 h
    rain_event_start = 30

    for i in range(96):  # 96 × 30 min = 48 h
        hours_ago = 48 - i * 0.5
        ts_dt = now - datetime.timedelta(hours=hours_ago)
        hour_frac = ts_dt.hour + ts_dt.minute / 60

        # Factor diurno de evapotranspiración
        et_diurnal = _ET_DIURNAL * max(0, math.sin(math.pi * (hour_frac - 6) / 12))

        # Lluvia: evento de 5-8 mm hace ~30 h, duración 2 h
        rain_mm = 0.0
        if rain_event_start - 1 <= hours_ago <= rain_event_start + 1:
            rain_mm = round(random.uniform(2.0, 4.0), 1)

        for pi, p in enumerate(_SIM_PROFILES):
            zona_id, zone = zone_for(p)
            if zona_id is None:
                continue
            w = water_levels[zona_id]

            # Evapotranspiración
            w -= _ET_RATE + et_diurnal

            # Lluvia
            if rain_mm > 0:
                w += rain_mm * _RAIN_RATE

            # Auto-riego: si CWSI > umbral alto, activar riego por 3 ticks (~1.5 min sim)
            cwsi_check = max(0.0, min(1.0, 1.0 - w))
            if cwsi_check >= CWSI_ALTO:
                w += _IRRIG_RATE
                if i % 4 == 0:  # registrar evento cada 2 h aprox
                    db.add(IrrigationLog(node_id=p["node_id"], zona=zona_id,
                                         duration_min=30, active=True, ts=ts_dt))
                    db.add(IrrigationLog(node_id=p["node_id"], zona=zona_id,
                                         duration_min=30, active=False,
                                         ts=ts_dt + datetime.timedelta(minutes=30)))

            w = max(0.05, min(1.0, w))
            water_levels[zona_id] = round(w, 4)

            # CWSI desde water_level
            diurnal_cwsi = math.sin(math.pi * (hour_frac - 6) / 12) * p["cwsi_amp"]
            cwsi = _sim_water_to_cwsi(w, diurnal_cwsi, random.uniform(-0.03, 0.03))
            t_air = round(20 + 10 * max(0, math.sin(math.pi * (hour_frac - 6) / 12))
                          + random.uniform(-1.5, 1.5), 1)
            rh = round(max(20, min(95, 60 - cwsi * 25 + random.uniform(-5, 5))), 1)

            db.add(Telemetry(
                node_id=p["node_id"], ts=int(ts_dt.timestamp()),
                cwsi=cwsi,
                hsi=round(min(1.0, cwsi * 0.70 + random.uniform(0, 0.08)), 3),
                mds_mm=round(0.08 + cwsi * 0.28 + random.uniform(-0.015, 0.015), 3),
                t_air=t_air, rh=rh,
                wind_ms=round(random.uniform(0.4, 3.5), 1),
                rain_mm=rain_mm if pi == 0 else 0.0,
                bat_pct=p["bat_base"] + random.randint(-5, 5),
                calidad="ok", origen="simulado",
                lat=zone["lat"] + p.get("lat_off", 0),
                lon=zone["lon"] + p.get("lon_off", 0),
                created_at=ts_dt,
            ))

    # ── Zonas sin nodo: evolucionar water_level en paralelo (sin telemetría) ─
    # Inicializar con valores variados
    s2_water: dict[int, float] = {}
    for zona_id, zone in zone_list:
        if zona_id not in water_levels:
            s2_water[zona_id] = 0.50 + random.uniform(-0.15, 0.15)

    if s2_water:
        for i in range(96):
            hours_ago = 48 - i * 0.5
            ts_dt = now - datetime.timedelta(hours=hours_ago)
            hour_frac_s = ts_dt.hour + ts_dt.minute / 60
            et_d = _ET_DIURNAL * max(0, math.sin(math.pi * (hour_frac_s - 6) / 12))

            rain_s2 = 0.0
            if rain_event_start - 1 <= hours_ago <= rain_event_start + 1:
                rain_s2 = round(random.uniform(2.0, 4.0), 1)

            for zona_id in s2_water:
                w = s2_water[zona_id]
                w -= _ET_RATE + et_d
                if rain_s2 > 0:
                    w += rain_s2 * _RAIN_RATE
                cwsi_ck = max(0.0, min(1.0, 1.0 - w))
                if cwsi_ck >= CWSI_ALTO:
                    w += _IRRIG_RATE
                w = max(0.05, min(1.0, w))
                s2_water[zona_id] = round(w, 4)

    # Guardar estado final como estado inicial del sim en tiempo real
    for zona_id, w in water_levels.items():
        _SIM_WATER[zona_id] = w
    for zona_id, w in s2_water.items():
        _SIM_WATER[zona_id] = w

    db.commit()


# Mantener /api/simulate como alias de start para compatibilidad
@app.post("/api/simulate")
async def simulate_compat():
    return await simulate_start()


# ---------------------------------------------------------------------------
# Rutas admin
# ---------------------------------------------------------------------------

@app.get("/api/admin/config")
def admin_get_config(db: Session = Depends(get_db)):
    cfg = {r.key: r.value for r in db.query(AppConfig).all()}
    # Valores derivados de las zonas (no editables)
    cfg["field_varietal"] = _resumen_varietales(db)
    cfg["field_area_ha"]  = str(_calcular_superficie_ha(db))
    cfg["cwsi_medio"]     = str(CWSI_MEDIO)
    cfg["cwsi_alto"]      = str(CWSI_ALTO)
    return cfg


@app.put("/api/admin/config")
def admin_update_config(data: ConfigIn, db: Session = Depends(get_db)):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    for k, v in updates.items():
        row = db.query(AppConfig).filter(AppConfig.key == k).first()
        if row:
            row.value = str(v)
        else:
            db.add(AppConfig(key=k, value=str(v)))
    _audit(db, "config_change", detail=json.dumps(updates))
    db.commit()
    return {"status": "ok"}


@app.get("/api/admin/zones")
def admin_get_zones(db: Session = Depends(get_db)):
    rows = db.query(ZoneConfig).order_by(ZoneConfig.id).all()
    result = []
    for r in rows:
        bounds = _zone_bounds_from_vertices(r.vertices) if r.vertices else _zone_bounds(r)
        result.append({
            "id": r.id, "name": r.name, "lat": r.lat, "lon": r.lon,
            "vertices": r.vertices,
            "varietal": r.varietal,
            "crop_ky": _ky_para_varietal(r.varietal),   # calculado automáticamente
            "crop_yield_kg_ha": r.crop_yield_kg_ha,
            **bounds,
        })
    return result


def _bounds_from_zone_in(data: ZoneIn) -> dict:
    """Calcula bounding box desde vertices (si hay) o desde lat/lon con fallback."""
    if data.vertices:
        return _zone_bounds_from_vertices(data.vertices)
    return {
        "sw_lat": data.sw_lat if data.sw_lat is not None else data.lat - _HL,
        "sw_lon": data.sw_lon if data.sw_lon is not None else data.lon - _HO,
        "ne_lat": data.ne_lat if data.ne_lat is not None else data.lat + _HL,
        "ne_lon": data.ne_lon if data.ne_lon is not None else data.lon + _HO,
    }


@app.post("/api/admin/zones", status_code=201)
def admin_create_zone(data: ZoneIn, db: Session = Depends(get_db)):
    b = _bounds_from_zone_in(data)
    conflict = _check_overlap(-1, b["sw_lat"], b["sw_lon"], b["ne_lat"], b["ne_lon"], db)
    # Advertencia (no bloqueo): superposición es válida en viticultura

    existing_ids = {r.id for r in db.query(ZoneConfig.id).all()}
    new_id = max(existing_ids) + 1 if existing_ids else 1
    db.add(ZoneConfig(id=new_id, name=data.name, lat=data.lat, lon=data.lon,
                      sw_lat=b["sw_lat"], sw_lon=b["sw_lon"],
                      ne_lat=b["ne_lat"], ne_lon=b["ne_lon"],
                      vertices=data.vertices,
                      varietal=data.varietal,
                      crop_yield_kg_ha=data.crop_yield_kg_ha))
    _audit(db, "zone_create", detail=f"id={new_id} name={data.name}")
    db.commit()
    _reload_zones(db)
    # Devuelve warning si hay superposición (no bloquea)
    return {"status": "ok", "id": new_id, "warning": f"Se superpone con '{conflict}'" if conflict else None}


@app.put("/api/admin/zones/{zone_id}")
def admin_update_zone(zone_id: int, data: ZoneIn, db: Session = Depends(get_db)):
    row = db.query(ZoneConfig).filter(ZoneConfig.id == zone_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Zona no encontrada")

    b = _bounds_from_zone_in(data)
    conflict = _check_overlap(zone_id, b["sw_lat"], b["sw_lon"], b["ne_lat"], b["ne_lon"], db)

    row.name = data.name; row.lat = data.lat; row.lon = data.lon
    row.sw_lat = b["sw_lat"]; row.sw_lon = b["sw_lon"]
    row.ne_lat = b["ne_lat"]; row.ne_lon = b["ne_lon"]
    row.vertices = data.vertices
    row.varietal         = data.varietal
    row.crop_yield_kg_ha = data.crop_yield_kg_ha
    _audit(db, "zone_update", detail=f"id={zone_id} name={data.name}")
    db.commit()
    _reload_zones(db)
    return {"status": "ok", "warning": f"Se superpone con '{conflict}'" if conflict else None}


@app.delete("/api/admin/zones/{zone_id}")
def admin_delete_zone(zone_id: int, db: Session = Depends(get_db)):
    row = db.query(ZoneConfig).filter(ZoneConfig.id == zone_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Zona no encontrada")
    _audit(db, "zone_delete", detail=f"id={zone_id} name={row.name}")
    db.delete(row)
    db.commit()
    _reload_zones(db)
    return {"status": "ok"}


@app.get("/api/admin/nodes")
def admin_get_nodes(db: Session = Depends(get_db)):
    """Nodos conocidos: une NodeConfig con su última telemetría."""
    subq = (
        db.query(Telemetry.node_id, func.max(Telemetry.id).label("max_id"))
        .group_by(Telemetry.node_id).subquery()
    )
    last_telem = {
        r.node_id: r
        for r in db.query(Telemetry).join(subq, Telemetry.id == subq.c.max_id).all()
    }
    cfgs = {c.node_id: c for c in db.query(NodeConfig).all()}

    all_ids = set(last_telem.keys()) | set(cfgs.keys())
    zones   = {z.id: z.name for z in db.query(ZoneConfig).all()}
    now     = datetime.datetime.utcnow()

    result = []
    for nid in sorted(all_ids):
        t   = last_telem.get(nid)
        cfg = cfgs.get(nid)
        result.append({
            "node_id":  nid,
            "name":     cfg.name     if cfg else None,
            "zona_id":  cfg.zona_id  if cfg else None,
            "zona_name": zones.get(cfg.zona_id) if cfg and cfg.zona_id else None,
            "solenoid": cfg.solenoid if cfg else None,
            "sol_sim":  _NODE_SOL_SIM.get(nid, False),
            "cwsi":     round(t.cwsi, 3) if t else None,
            "origen":   t.origen         if t else None,
            "bat_pct":  t.bat_pct        if t else None,
            "hace_min": int((now - t.created_at).total_seconds() / 60) if t else None,
        })
    return result


@app.put("/api/admin/nodes/{node_id}")
def admin_update_node(node_id: str, data: NodeConfigIn, db: Session = Depends(get_db)):
    row = db.query(NodeConfig).filter(NodeConfig.node_id == node_id).first()
    if not row:
        row = NodeConfig(node_id=node_id)
        db.add(row)
    if data.name     is not None: row.name     = data.name
    if data.zona_id  is not None: row.zona_id  = data.zona_id
    # solenoid no es editable — lo informa el nodo vía /ingest
    _audit(db, "node_update", node_id=node_id,
           detail=f"name={data.name} zona_id={data.zona_id}")
    db.commit()
    return {"status": "ok"}


@app.get("/api/admin/audit")
def admin_get_audit(
    limit: int = Query(100, ge=1, le=1000),
    event: str = Query(None),
    node_id: str = Query(None),
    db: Session = Depends(get_db),
):
    """Últimos eventos de auditoría. Filtrable por event y node_id."""
    q = db.query(AuditLog).order_by(AuditLog.ts.desc())
    if event:
        q = q.filter(AuditLog.event == event)
    if node_id:
        q = q.filter(AuditLog.node_id == node_id)
    rows = q.limit(limit).all()
    return [
        {"id": r.id, "ts": r.ts.isoformat(), "event": r.event,
         "node_id": r.node_id, "detail": r.detail, "ip": r.ip}
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Informe / Report API — análisis y valor para el productor
# ---------------------------------------------------------------------------

# Caudal estimado por zona [m³/h] — en TRL 5+ se configura por zona en admin
_FLOW_RATE_M3H = 10.0

# Baselines industria para comparación (fuentes: FAO-56, INTA ProRiego)
_BASELINE_TRADITIONAL = {
    "method":             "Calendario / inspección visual",
    "water_m3_ha_year":   6500,
    "irrigations_week":   7,
    "stress_detect_h":    48,
    "coverage_pct":       0,
    "precision":          "Nula — riego fijo sin dato de planta",
}
_BASELINE_COMPETITION = {
    "method":             "Sonda de humedad de suelo",
    "water_m3_ha_year":   5200,
    "irrigations_week":   5,
    "stress_detect_h":    12,
    "coverage_pct":       30,
    "precision":          "Parcial — mide suelo, no planta",
}


@app.get("/api/report/summary")
def report_summary(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """KPIs agregados para el período seleccionado."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    # Telemetry en el rango
    telem = (
        db.query(Telemetry)
        .filter(Telemetry.created_at >= cutoff)
        .all()
    )
    # Config
    cfg = {r.key: r.value for r in db.query(AppConfig).all()}
    area_ha = _calcular_superficie_ha(db) or 0.33
    n_zones = db.query(ZoneConfig).count() or 1

    # Métricas de telemetría
    cwsi_vals = [t.cwsi for t in telem if t.cwsi is not None]
    rain_vals = [t.rain_mm for t in telem if t.rain_mm is not None]
    temp_vals = [t.t_air for t in telem if t.t_air is not None]
    rh_vals   = [t.rh for t in telem if t.rh is not None]

    cwsi_avg = round(sum(cwsi_vals) / len(cwsi_vals), 3) if cwsi_vals else None
    cwsi_max = round(max(cwsi_vals), 3) if cwsi_vals else None
    rain_total = round(sum(rain_vals), 1)
    temp_avg   = round(sum(temp_vals) / len(temp_vals), 1) if temp_vals else None
    rh_avg     = round(sum(rh_vals) / len(rh_vals), 1) if rh_vals else None

    stress_high = sum(1 for v in cwsi_vals if v >= CWSI_ALTO)
    stress_med  = sum(1 for v in cwsi_vals if CWSI_MEDIO <= v < CWSI_ALTO)

    # Nodos activos únicos
    node_ids = list({t.node_id for t in telem})

    # Riego en el rango
    irrig = (
        db.query(IrrigationLog)
        .filter(IrrigationLog.ts >= cutoff)
        .all()
    )
    activations   = [r for r in irrig if r.active]
    deactivations = [r for r in irrig if not r.active]
    total_irrig_events = len(activations)
    total_irrig_min    = sum(r.duration_min or 30 for r in activations)
    water_m3           = round(total_irrig_min / 60 * _FLOW_RATE_M3H, 1)

    # Ahorro vs calendario ingenuo (riega 30 min/día/zona sin importar CWSI)
    baseline_min    = days * n_zones * 30
    baseline_m3     = round(baseline_min / 60 * _FLOW_RATE_M3H, 1)
    savings_pct     = round((1 - total_irrig_min / baseline_min) * 100, 1) if baseline_min > 0 else 0

    # Cobertura de datos: % de horas con al menos una lectura
    total_hours     = days * 24
    hours_with_data = len({
        t.created_at.strftime("%Y-%m-%d %H") for t in telem if t.created_at
    })
    coverage_pct = round(hours_with_data / total_hours * 100, 1) if total_hours > 0 else 0

    # Tendencia: comparar promedio CWSI de la primera y segunda mitad del período
    mid = cutoff + datetime.timedelta(days=days / 2)
    first_half  = [t.cwsi for t in telem if t.created_at and t.created_at < mid and t.cwsi is not None]
    second_half = [t.cwsi for t in telem if t.created_at and t.created_at >= mid and t.cwsi is not None]
    if first_half and second_half:
        trend = round(sum(second_half) / len(second_half) - sum(first_half) / len(first_half), 3)
    else:
        trend = 0

    # ── Horas de estrés hídrico ─────────────────────────────────────────────
    # Agrupamos lecturas por hora (bucket) y tomamos el máximo CWSI de esa hora.
    # Así evitamos contar múltiples nodos como horas duplicadas.
    hour_cwsi: dict[str, list[float]] = {}
    for t in telem:
        if t.cwsi is None or t.created_at is None:
            continue
        key = t.created_at.strftime("%Y-%m-%d %H")
        hour_cwsi.setdefault(key, []).append(t.cwsi)

    # CWSI representativo por hora = promedio de todos los nodos en esa hora
    hours_total          = len(hour_cwsi)
    hours_stress_any     = sum(1 for vals in hour_cwsi.values() if max(vals) >= CWSI_MEDIO)
    hours_stress_high    = sum(1 for vals in hour_cwsi.values() if max(vals) >= CWSI_ALTO)
    hours_optimal        = hours_total - hours_stress_any  # CWSI < 0.30

    # ── Pérdida de producción — promedio ponderado de las zonas ────────────
    # Se calcula por zona en /api/report/zone-performance (cada zona tiene su
    # propio Ky según variedad + fenología). Aquí promediamos para el campo.
    zone_perf = report_zone_performance(days=days, db=db)
    zones_with_loss = [z for z in zone_perf if z["loss_pct"] is not None and z["readings"] > 0]
    if zones_with_loss:
        total_readings = sum(z["readings"] for z in zones_with_loss)
        loss_pct = round(sum(z["loss_pct"] * z["readings"] for z in zones_with_loss) / total_readings, 1)
        loss_kg_ha = round(sum(z["loss_kg_ha"] * z["readings"] for z in zones_with_loss) / total_readings, 0)
    else:
        loss_pct = 0.0
        loss_kg_ha = 0.0
    yield_kg_ha = float(cfg.get("crop_yield_kg_ha", "8000"))
    loss_kg_total = round(loss_kg_ha * area_ha, 0)
    # Ky representativo del campo: promedio ponderado por lecturas
    KY = round(sum(z["crop_ky"] * z["readings"] for z in zones_with_loss) / max(1, sum(z["readings"] for z in zones_with_loss)), 2) if zones_with_loss else 0.85
    fenol_campo = zones_with_loss[0]["fenologia"] if len(zones_with_loss) == 1 else {"etapa": "mixto", "gdd": 0, "ky": KY, "metodo": "zona_avg", "n_dias": 0}

    return {
        "days":               days,
        "total_readings":     len(telem),
        "active_nodes":       len(node_ids),
        "node_ids":           node_ids,
        "cwsi_avg":           cwsi_avg,
        "cwsi_max":           cwsi_max,
        "trend":              trend,
        "stress_high_count":  stress_high,
        "stress_med_count":   stress_med,
        "rain_total_mm":      rain_total,
        "temp_avg":           temp_avg,
        "rh_avg":             rh_avg,
        "total_irrig_events": total_irrig_events,
        "total_irrig_min":    total_irrig_min,
        "water_m3":           water_m3,
        "baseline_m3":        baseline_m3,
        "savings_pct":        savings_pct,
        "coverage_pct":       coverage_pct,
        "n_zones":            n_zones,
        "area_ha":            area_ha,
        # Estrés hídrico
        "hours_total":        hours_total,
        "hours_optimal":      hours_optimal,
        "hours_stress_any":   hours_stress_any,
        "hours_stress_high":  hours_stress_high,
        "stress_pct":         round(hours_stress_any / hours_total * 100, 1) if hours_total else 0,
        # Pérdida de producción estimada
        "stress_integral":    0,
        "loss_pct":           loss_pct,
        "loss_kg_ha":         loss_kg_ha,
        "loss_kg_total":      loss_kg_total,
        "yield_kg_ha":        yield_kg_ha,
        "crop_ky":            KY,
        "crop_ky_varietal":   "promedio zonas",
        "fenologia":          fenol_campo,   # { etapa, gdd, ky, metodo, n_dias }
    }


@app.get("/api/report/cwsi-history")
def report_cwsi_history(
    days: int = Query(default=7, ge=1, le=90),
    resolution: str = Query(default="hourly"),
    db: Session = Depends(get_db),
):
    """Series temporales de CWSI por nodo, agrupadas por hora o día."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    rows = (
        db.query(Telemetry)
        .filter(Telemetry.created_at >= cutoff, Telemetry.cwsi.isnot(None))
        .order_by(Telemetry.created_at)
        .all()
    )
    cfgs = {c.node_id: (c.name or c.node_id) for c in db.query(NodeConfig).all()}

    # Agrupar por bucket temporal + nodo
    buckets: dict[str, dict[str, list[float]]] = {}
    for r in rows:
        if resolution == "daily":
            key = r.created_at.strftime("%Y-%m-%d")
        else:
            key = r.created_at.strftime("%Y-%m-%d %H:00")
        if key not in buckets:
            buckets[key] = {}
        if r.node_id not in buckets[key]:
            buckets[key][r.node_id] = []
        buckets[key][r.node_id].append(r.cwsi)

    labels = sorted(buckets.keys())
    node_ids = sorted({r.node_id for r in rows})

    datasets = []
    for nid in node_ids:
        values = []
        for lbl in labels:
            vals = buckets.get(lbl, {}).get(nid, [])
            values.append(round(sum(vals) / len(vals), 3) if vals else None)
        datasets.append({
            "node_id": nid,
            "name":    cfgs.get(nid, nid),
            "values":  values,
        })

    return {"labels": labels, "datasets": datasets}


@app.get("/api/report/zone-history")
def report_zone_history(
    days: int = Query(default=7, ge=1, le=90),
    resolution: str = Query(default="hourly"),
    db: Session = Depends(get_db),
):
    """Series temporales por zona: CWSI promedio, minutos de riego y lluvia acumulada."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    cfgs  = {c.node_id: c for c in db.query(NodeConfig).all()}
    zones = db.query(ZoneConfig).order_by(ZoneConfig.id).all()
    zone_map = {z.id: z.name for z in zones}

    # Mapear nodo → zona
    node_zone: dict[str, int] = {}
    for nid, cfg in cfgs.items():
        if cfg.zona_id:
            node_zone[nid] = cfg.zona_id

    # Telemetría
    telem = (
        db.query(Telemetry)
        .filter(Telemetry.created_at >= cutoff, Telemetry.cwsi.isnot(None))
        .order_by(Telemetry.created_at)
        .all()
    )

    # Riego
    irrig = (
        db.query(IrrigationLog)
        .filter(IrrigationLog.ts >= cutoff, IrrigationLog.active == True)
        .order_by(IrrigationLog.ts)
        .all()
    )

    fmt = "%Y-%m-%d" if resolution == "daily" else "%Y-%m-%d %H:00"

    # CWSI + lluvia por (zona, bucket)
    cwsi_buckets: dict[int, dict[str, list[float]]] = {z.id: {} for z in zones}
    rain_buckets: dict[str, float] = {}

    for t in telem:
        zid = node_zone.get(t.node_id)
        if not zid or zid not in cwsi_buckets:
            continue
        key = t.created_at.strftime(fmt)
        cwsi_buckets[zid].setdefault(key, []).append(t.cwsi)
        if t.rain_mm and t.rain_mm > 0:
            rain_buckets[key] = rain_buckets.get(key, 0) + t.rain_mm

    # Riego por (zona, bucket) → minutos
    irrig_buckets: dict[int, dict[str, int]] = {z.id: {} for z in zones}
    for e in irrig:
        key = e.ts.strftime(fmt)
        irrig_buckets[e.zona][key] = irrig_buckets[e.zona].get(key, 0) + (e.duration_min or 30)

    # Labels: unión de todos los buckets
    all_keys: set[str] = set()
    for zdata in cwsi_buckets.values():
        all_keys.update(zdata.keys())
    for zdata in irrig_buckets.values():
        all_keys.update(zdata.keys())
    all_keys.update(rain_buckets.keys())
    labels = sorted(all_keys)

    # Construir datasets por zona
    zone_datasets = []
    for z in zones:
        cwsi_vals = []
        irrig_vals = []
        for lbl in labels:
            vals = cwsi_buckets[z.id].get(lbl, [])
            cwsi_vals.append(round(sum(vals) / len(vals), 3) if vals else None)
            irrig_vals.append(irrig_buckets[z.id].get(lbl, 0))
        zone_datasets.append({
            "zone_id": z.id,
            "name": z.name,
            "cwsi": cwsi_vals,
            "irrigation_min": irrig_vals,
        })

    # Lluvia global
    rain_vals = [round(rain_buckets.get(lbl, 0), 1) for lbl in labels]

    return {
        "labels": labels,
        "zones": zone_datasets,
        "rain_mm": rain_vals,
    }


@app.get("/api/report/irrigation-history")
def report_irrigation_history(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """Historial de riego agrupado por zona y fecha."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    events = (
        db.query(IrrigationLog)
        .filter(IrrigationLog.ts >= cutoff, IrrigationLog.active == True)
        .order_by(IrrigationLog.ts)
        .all()
    )
    zones_map = {z.id: z.name for z in db.query(ZoneConfig).all()}

    # Agrupar por (zona, fecha)
    from collections import defaultdict
    zone_day: dict[int, dict[str, dict]] = defaultdict(lambda: defaultdict(lambda: {"count": 0, "min": 0}))
    daily_totals: dict[str, int] = defaultdict(int)

    for e in events:
        day = e.ts.strftime("%Y-%m-%d")
        zone_day[e.zona][day]["count"] += 1
        zone_day[e.zona][day]["min"]   += e.duration_min or 30
        daily_totals[day]              += e.duration_min or 30

    zones_result = []
    for zid in sorted(zone_day.keys()):
        days_data = [
            {"date": d, "activations": v["count"], "total_min": v["min"]}
            for d, v in sorted(zone_day[zid].items())
        ]
        zones_result.append({"id": zid, "name": zones_map.get(zid, f"Zona {zid}"), "events": days_data})

    daily = [{"date": d, "total_min": m} for d, m in sorted(daily_totals.items())]

    return {"zones": zones_result, "daily_totals": daily}


@app.get("/api/report/zone-performance")
def report_zone_performance(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """Rendimiento por zona: CWSI promedio, riego, comparativa."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    cfgs   = {c.node_id: c for c in db.query(NodeConfig).all()}
    zones  = db.query(ZoneConfig).order_by(ZoneConfig.id).all()

    telem = (
        db.query(Telemetry)
        .filter(Telemetry.created_at >= cutoff, Telemetry.cwsi.isnot(None))
        .all()
    )
    irrig = (
        db.query(IrrigationLog)
        .filter(IrrigationLog.ts >= cutoff, IrrigationLog.active == True)
        .all()
    )

    # Mapear nodo → zona (explícito + bounds)
    node_zone: dict[str, int] = {}
    for nid, cfg in cfgs.items():
        if cfg.zona_id:
            node_zone[nid] = cfg.zona_id

    # Bounds-based: última lectura de cada nodo para lat/lon
    last_pos: dict[str, tuple] = {}
    for t in telem:
        if t.lat is not None and t.lon is not None:
            last_pos[t.node_id] = (t.lat, t.lon)

    zone_bounds = {}
    for z in zones:
        b = _zone_bounds_from_vertices(z.vertices) if z.vertices else _zone_bounds(z)
        zone_bounds[z.id] = b
        # Asignar nodo a zona si está dentro de los bounds y no tiene asignación explícita
        for nid, (lat, lon) in last_pos.items():
            if nid in node_zone:
                continue
            if b["sw_lat"] <= lat <= b["ne_lat"] and b["sw_lon"] <= lon <= b["ne_lon"]:
                node_zone[nid] = z.id

    # Agrupar telemetría por zona (via nodo asignado o bounds)
    # zone_cwsi_raw: todas las lecturas para cálculo de avg/min/max
    # zone_hour_cwsi: bucketeado por hora para cálculo de horas de estrés (evita duplicar nodos)
    zone_cwsi: dict[int, list[float]] = {z.id: [] for z in zones}
    zone_hour_cwsi: dict[int, dict[str, list[float]]] = {z.id: {} for z in zones}
    for t in telem:
        zid = node_zone.get(t.node_id)
        if zid and zid in zone_cwsi:
            zone_cwsi[zid].append(t.cwsi)
            if t.created_at:
                key = t.created_at.strftime("%Y-%m-%d %H")
                zone_hour_cwsi[zid].setdefault(key, []).append(t.cwsi)

    # Riego por zona
    zone_irrig: dict[int, int] = {z.id: 0 for z in zones}
    zone_events: dict[int, int] = {z.id: 0 for z in zones}
    for e in irrig:
        if e.zona in zone_irrig:
            zone_irrig[e.zona]  += e.duration_min or 30
            zone_events[e.zona] += 1

    # Nodos con zona (explícita o bounds)
    zone_has_node: dict[int, bool] = {z.id: False for z in zones}
    for nid, zid in node_zone.items():
        if zid in zone_has_node:
            zone_has_node[zid] = True

    # VPD medio del campo para fusión satelital (zonas sin nodo)
    vpd_lista = [
        _vpd_kpa(t.t_air, t.rh)
        for t in telem if t.t_air is not None and t.rh is not None
    ]
    vpd_campo = (sum(vpd_lista) / len(vpd_lista)) if vpd_lista else 1.5

    # Rendimiento por defecto global (fallback si la zona no tiene el suyo)
    global_cfg   = {r.key: r.value for r in db.query(AppConfig).all()}
    yield_global = float(global_cfg.get("crop_yield_kg_ha", "8000"))
    # Mes actual — solo para fallback cuando hay < _GDD_MIN_DAYS días de datos
    mes_actual = datetime.datetime.utcnow().month

    # Construir historial de temperatura por zona para cálculo GDD
    # Necesitamos datos suficientes: consultar los últimos 365 días de t_air
    cutoff_gdd  = datetime.datetime.utcnow() - datetime.timedelta(days=365)
    telem_gdd   = (
        db.query(Telemetry)
        .filter(Telemetry.created_at >= cutoff_gdd, Telemetry.t_air.isnot(None))
        .all()
    )
    # t_aire_por_zona[zona_id] = { "YYYY-MM-DD": [lecturas t_air] }
    t_aire_por_zona: dict[int, dict[str, list[float]]] = {z.id: {} for z in zones}
    # t_aire_campo (para zonas sin nodo propio) = todas las lecturas de t_air del campo
    t_aire_campo: dict[str, list[float]] = {}
    for t in telem_gdd:
        zid = node_zone.get(t.node_id)
        dia = t.created_at.strftime("%Y-%m-%d")
        if zid and zid in t_aire_por_zona:
            t_aire_por_zona[zid].setdefault(dia, []).append(t.t_air)
        t_aire_campo.setdefault(dia, []).append(t.t_air)

    result = []
    for z in zones:
        vals = zone_cwsi[z.id]
        avg  = round(sum(vals) / len(vals), 3) if vals else None
        mx   = round(max(vals), 3) if vals else None
        mn   = round(min(vals), 3) if vals else None

        has_node  = zone_has_node[z.id]
        irrig_min = zone_irrig[z.id]
        water_m3  = round(irrig_min / 60 * _FLOW_RATE_M3H, 1)

        # Zonas sin nodo: estimar CWSI por fusión satélite
        fuente = "nodo" if has_node else "satelite_s2"
        if not has_node and avg is None and telem:
            sat_cwsi = _fusion.predecir_cwsi(
                z.id, vpd_campo, zona_lat=z.lat, zona_lon=z.lon,
            )
            if _fusion._gee_active:
                if sat_cwsi is not None:
                    avg = sat_cwsi
                    mx  = sat_cwsi
                    mn  = sat_cwsi
                    fuente = "satelite_real"
                else:
                    fuente = "sin_cobertura"
            elif sat_cwsi is not None:
                avg = sat_cwsi
                mx  = sat_cwsi
                mn  = sat_cwsi

        # Pérdida de producción por zona — Ky determinado por GDD (días-grado) o mes fallback
        t_aire_z   = t_aire_por_zona.get(z.id) or t_aire_campo  # usa campo si zona sin nodo
        fenol      = _fenologia_zona(z.varietal, t_aire_z)
        ky_zona    = fenol["ky"]
        yield_zona = z.crop_yield_kg_ha if z.crop_yield_kg_ha is not None else yield_global

        # Integral de estrés de la zona (cada lectura = 0.5 h)
        stress_int_z = sum(max(0.0, v - CWSI_MEDIO) * 0.5 for v in vals) if vals else 0.0
        period_h     = days * 24
        loss_pct_z   = round(min(40.0, ky_zona * stress_int_z / period_h * 100), 1) if period_h > 0 else 0.0
        loss_kg_ha_z = round(yield_zona * loss_pct_z / 100, 0)

        # Horas de estrés por zona (bucketeado por hora para no duplicar nodos)
        hbuckets       = zone_hour_cwsi[z.id]
        hours_total_z  = len(hbuckets)
        hours_any_z    = sum(1 for hvals in hbuckets.values() if max(hvals) >= CWSI_MEDIO)
        hours_high_z   = sum(1 for hvals in hbuckets.values() if max(hvals) >= CWSI_ALTO)
        hours_opt_z    = hours_total_z - hours_any_z
        stress_pct_z   = round(hours_any_z / hours_total_z * 100, 1) if hours_total_z else 0

        result.append({
            "id":              z.id,
            "name":            z.name,
            "varietal":        z.varietal or "",
            "crop_ky":         ky_zona,
            "crop_yield_kg_ha": yield_zona,
            "fenologia":       fenol,
            "has_node":        has_node,
            "fuente":          fuente,
            "readings":        len(vals),
            "cwsi_avg":        avg,
            "cwsi_max":        mx,
            "cwsi_min":        mn,
            "stress":          _stress_label(avg) if avg is not None else None,
            "irrig_events":    zone_events[z.id],
            "irrig_min":       irrig_min,
            "water_m3":        water_m3,
            "loss_pct":        loss_pct_z,
            "loss_kg_ha":      loss_kg_ha_z,
            # horas de estrés por zona
            "hours_total":       hours_total_z,
            "hours_stress_any":  hours_any_z,
            "hours_stress_high": hours_high_z,
            "hours_optimal":     hours_opt_z,
            "stress_pct":        stress_pct_z,
        })
    return result


@app.get("/api/report/comparison")
def report_comparison(db: Session = Depends(get_db)):
    """Comparación HydroVision vs métodos tradicionales y competencia."""
    area_ha = _calcular_superficie_ha(db) or 0.33

    # Datos reales del sistema (últimos 30 días)
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=30)
    irrig  = (
        db.query(IrrigationLog)
        .filter(IrrigationLog.ts >= cutoff, IrrigationLog.active == True)
        .all()
    )
    total_min = sum(r.duration_min or 30 for r in irrig)
    water_m3  = round(total_min / 60 * _FLOW_RATE_M3H, 1)

    n_zones = db.query(ZoneConfig).count() or 1
    n_nodes = db.query(NodeConfig).count() or 0

    telem_count = (
        db.query(func.count(Telemetry.id))
        .filter(Telemetry.created_at >= cutoff)
        .scalar() or 0
    )

    # Si hay riego real, usar datos reales; si no, estimar a partir del CWSI
    has_real_irrig = total_min > 0
    if has_real_irrig:
        water_m3_year = round(water_m3 * (365 / 30), 0)
        irrig_per_week = round(len(irrig) / 4.3, 1)
    else:
        # Estimación: con riego CWSI-guiado, se riega cuando CWSI >= umbral alto.
        # Basado en literatura (FAO-56 + CWSI scheduling): ahorro típico 30-45% vs calendario.
        # Usamos el CWSI promedio del campo para estimar frecuencia de riego necesaria.
        cwsi_rows = (
            db.query(Telemetry.cwsi)
            .filter(Telemetry.created_at >= cutoff, Telemetry.cwsi.isnot(None))
            .all()
        )
        if cwsi_rows:
            cwsi_avg = sum(r.cwsi for r in cwsi_rows) / len(cwsi_rows)
            # % de lecturas que superan umbral = frecuencia relativa de riego necesario
            above_threshold = sum(1 for r in cwsi_rows if r.cwsi >= CWSI_ALTO) / len(cwsi_rows)
            # Riego inteligente: solo las zonas que lo necesitan, solo cuando CWSI > umbral
            # vs tradicional que riega todas las zonas todos los días
            estimated_ratio = max(0.10, above_threshold * 0.7)  # factor 0.7: no todas las alertas requieren riego completo
            water_m3_year = round(_BASELINE_TRADITIONAL["water_m3_ha_year"] * area_ha * estimated_ratio, 0)
            irrig_per_week = round(_BASELINE_TRADITIONAL["irrigations_week"] * estimated_ratio, 1)
        else:
            water_m3_year = 0
            irrig_per_week = 0

    water_m3_ha = round(water_m3_year / area_ha, 0) if area_ha > 0 else 0

    hydrovision = {
        "method":             "CWSI de precision (nodo + Sentinel-2)",
        "water_m3_ha_year":   water_m3_ha,
        "irrigations_week":   irrig_per_week,
        "stress_detect_h":    0.5,
        "coverage_pct":       100,
        "precision":          "Planta + satelite — estres real medido",
        "nodes":              n_nodes,
        "zones":              n_zones,
        "readings_30d":       telem_count,
        "estimated":          not has_real_irrig,
    }

    # Ahorro vs cada baseline
    savings_vs_trad = round(
        (1 - water_m3_ha / _BASELINE_TRADITIONAL["water_m3_ha_year"]) * 100, 1
    ) if water_m3_ha > 0 else 0
    savings_vs_comp = round(
        (1 - water_m3_ha / _BASELINE_COMPETITION["water_m3_ha_year"]) * 100, 1
    ) if water_m3_ha > 0 else 0

    return {
        "field_area_ha":    area_ha,
        "hydrovision":      hydrovision,
        "traditional":      _BASELINE_TRADITIONAL,
        "competition":      _BASELINE_COMPETITION,
        "savings_vs_trad":  savings_vs_trad,
        "savings_vs_comp":  savings_vs_comp,
    }


@app.get("/api/report/export/csv")
def report_export_csv(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """Exporta telemetría cruda del período como CSV."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    rows = (
        db.query(Telemetry)
        .filter(Telemetry.created_at >= cutoff)
        .order_by(Telemetry.created_at)
        .all()
    )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "timestamp", "node_id", "cwsi", "hsi", "mds_mm",
        "t_air", "rh", "wind_ms", "rain_mm", "bat_pct", "origen",
    ])
    for r in rows:
        writer.writerow([
            r.created_at.isoformat() if r.created_at else "",
            r.node_id, r.cwsi, r.hsi, r.mds_mm,
            r.t_air, r.rh, r.wind_ms, r.rain_mm, r.bat_pct, r.origen,
        ])

    buf.seek(0)
    filename = f"hydrovision_telemetry_{days}d.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ═══════════════════════════════════════════════════════════════════════════
# PINN Inference endpoint — Inv. Art. 32 #5
# POST /api/inference: envía imagen térmica → recibe CWSI estimado
# ═══════════════════════════════════════════════════════════════════════════
_PINN_MODEL = None
_PINN_AVAILABLE = False

try:
    import torch
    _TORCH_OK = True
except ImportError:
    _TORCH_OK = False


def _load_pinn_model():
    """Carga lazy del modelo PINN (INT8 o FP32 según disponibilidad)."""
    global _PINN_MODEL, _PINN_AVAILABLE
    if not _TORCH_OK:
        return

    _INVESTIGADOR_PATH = Path(__file__).parent.parent / "investigador"
    model_paths = [
        _INVESTIGADOR_PATH / "models" / "edge" / "hydrovision_cwsi_int8.tflite",
        _INVESTIGADOR_PATH / "models" / "checkpoints" / "best_finetune.pt",
        _INVESTIGADOR_PATH / "models" / "checkpoints" / "best_synthetic.pt",
    ]

    for mp in model_paths:
        if mp.exists():
            try:
                import sys
                if str(_INVESTIGADOR_PATH / "02_modelo") not in sys.path:
                    sys.path.insert(0, str(_INVESTIGADOR_PATH / "02_modelo"))
                from pinn_model import HydroVisionPINN

                if mp.suffix == ".pt":
                    ckpt = torch.load(mp, map_location="cpu", weights_only=False)
                    model = HydroVisionPINN(pretrained=False)
                    model.load_state_dict(ckpt.get("model_state", ckpt))
                    model.eval()
                    _PINN_MODEL = model
                    _PINN_AVAILABLE = True
                    return
            except Exception:
                continue


class InferenceRequest(BaseModel):
    thermal_image: list[list[float]]  # 120×160 thermal image (°C)
    t_air: float = 25.0               # ambient temperature [°C]
    rh: float = 50.0                   # relative humidity [%]
    wind_ms: float = 1.0               # wind speed [m/s]


class InferenceResponse(BaseModel):
    cwsi: float
    delta_t: float
    latency_ms: float
    model_type: str


@app.post("/api/inference", response_model=InferenceResponse)
def post_inference(req: InferenceRequest):
    """
    Inferencia PINN: recibe imagen térmica 120×160 y retorna CWSI estimado.
    Latencia objetivo: < 1s en CPU (< 200ms en ESP32-S3 con INT8).
    """
    if not _TORCH_OK:
        raise HTTPException(503, "PyTorch no disponible en este servidor")

    if _PINN_MODEL is None:
        _load_pinn_model()

    if not _PINN_AVAILABLE:
        raise HTTPException(503, "Modelo PINN no encontrado — ejecutar train.py primero")

    import time as _time
    try:
        img = torch.tensor(req.thermal_image, dtype=torch.float32)
        if img.shape != (120, 160):
            raise HTTPException(
                422, f"Imagen debe ser 120x160, recibida: {list(img.shape)}"
            )
        img = img.unsqueeze(0).unsqueeze(0)  # (1, 1, 120, 160)

        t0 = _time.perf_counter()
        with torch.no_grad():
            out = _PINN_MODEL(img)
        t1 = _time.perf_counter()

        cwsi_val = out[0].item() if isinstance(out, tuple) else out.item()
        delta_t = out[1].item() if isinstance(out, tuple) and len(out) > 1 else 0.0

        return InferenceResponse(
            cwsi=round(cwsi_val, 4),
            delta_t=round(delta_t, 2),
            latency_ms=round((t1 - t0) * 1000, 1),
            model_type="PINN-FP32-CPU",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error en inferencia: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# Validation report endpoint — César #3
# GET /api/validacion/reporte: CSV con HSI vs ψ_stem para validación TRL 4
# ═══════════════════════════════════════════════════════════════════════════
@app.get("/api/validacion/reporte")
def get_validacion_reporte(
    days: int = Query(default=30, ge=1, le=365),
    node_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Genera CSV de validación HSI vs telemetría para correlación con ψ_stem Scholander.

    Columnas: timestamp, node_id, cwsi, hsi, mds_mm, t_air, rh, wind_ms,
              bat_pct, calidad, origen, estadio_fenologico, ky,
              psi_stem_estimado (MPa, estimado por HSI→ψ_stem calibración Malbec)

    La columna psi_stem_estimado se calcula como:
      ψ_stem ≈ -0.2 - 1.8 × HSI  (R² ≈ 0.80, Scholander Malbec Colonia Caroya)
    Este valor es la estimación del nodo — la validación requiere medir ψ_stem
    real con bomba de presión en campo y comparar.
    """
    since = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    q = db.query(Telemetry).filter(Telemetry.created_at >= since)
    if node_id:
        q = q.filter(Telemetry.node_id == node_id)
    q = q.order_by(Telemetry.created_at.asc())
    rows = q.all()

    if not rows:
        raise HTTPException(404, "Sin datos de telemetría en el período")

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "timestamp", "node_id", "cwsi", "hsi", "mds_mm",
        "t_air", "rh", "wind_ms", "bat_pct", "calidad", "origen",
        "psi_stem_estimado_MPa",
    ])
    for r in rows:
        # Estimación ψ_stem desde HSI (calibración lineal Malbec)
        psi_stem_est = round(-0.2 - 1.8 * r.hsi, 3) if r.hsi is not None else ""
        writer.writerow([
            r.created_at.isoformat() if r.created_at else "",
            r.node_id, r.cwsi, r.hsi, r.mds_mm,
            r.t_air, r.rh, r.wind_ms, r.bat_pct, r.calidad, r.origen,
            psi_stem_est,
        ])

    buf.seek(0)
    filename = f"validacion_hsi_psi_stem_{days}d.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ═══════════════════════════════════════════════════════════════════════════
# Nodo latest endpoint — César #3
# GET /api/nodos/{node_id}/latest: última lectura de un nodo específico
# ═══════════════════════════════════════════════════════════════════════════
@app.get("/api/nodos/{node_id}/latest")
def get_nodo_latest(node_id: str, db: Session = Depends(get_db)):
    """Última lectura de telemetría de un nodo específico."""
    row = (
        db.query(Telemetry)
        .filter(Telemetry.node_id == node_id)
        .order_by(Telemetry.created_at.desc())
        .first()
    )
    if not row:
        raise HTTPException(404, f"Nodo '{node_id}' sin datos")
    return {
        "node_id": row.node_id,
        "timestamp": row.created_at.isoformat() if row.created_at else None,
        "cwsi": row.cwsi,
        "hsi": row.hsi,
        "mds_mm": row.mds_mm,
        "t_air": row.t_air,
        "rh": row.rh,
        "wind_ms": row.wind_ms,
        "rain_mm": row.rain_mm,
        "bat_pct": row.bat_pct,
        "calidad": row.calidad,
        "origen": row.origen,
    }
