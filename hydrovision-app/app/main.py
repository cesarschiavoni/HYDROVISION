"""
main.py — FastAPI application
HydroVision AG  v1.0.0

Levantar (desarrollo):
    cd hydrovision-app
    python -m uvicorn app.main:app --reload --port 8000

Producción (Docker):
    docker compose -f infra/docker-compose.yml up -d

Endpoints principales:
    GET  /                         → home (landing page)
    GET  /dashboard                → dashboard operativo
    GET  /admin                    → configuración de campo
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

from app.models import (
    APP_CONFIG_DEFAULTS, ZONE_DEFAULTS,
    AppConfig, AuditLog, Base, IrrigationLog, NodeConfig,
    SessionLocal, Telemetry, ZoneConfig, engine,
)
from app.config import HMAC_SECRET, SIMULATION_MODE, APP_TITLE, APP_VERSION

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
def _seed_defaults(db: Session, owner_id: int = None) -> None:
    """Inserta zonas y config por defecto si las tablas están vacías."""
    if not db.query(ZoneConfig).first():
        for z in ZONE_DEFAULTS:
            db.add(ZoneConfig(**z, owner_id=owner_id))

    if not db.query(AppConfig).first():
        for k, v in APP_CONFIG_DEFAULTS.items():
            db.add(AppConfig(key=k, value=v))

    db.commit()


def _seed_admin_user(db: Session) -> None:
    """Crea el usuario admin por defecto si no existe ningún usuario."""
    from app.models import User
    from app.deps import hash_password
    from app.config import ADMIN_USERNAME, ADMIN_PASSWORD
    if not db.query(User).first():
        user = User(username=ADMIN_USERNAME, password_hash=hash_password(ADMIN_PASSWORD), role="superadmin")
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    return db.query(User).first()


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
        admin = _seed_admin_user(db)   # primero — seed de zonas necesita el user_id
        _seed_defaults(db, owner_id=admin.id if admin else None)
        # Usar app.core._reload_zones para que TODOS los módulos vean las zonas
        from app.core import _reload_zones as _core_reload_zones
        _core_reload_zones(db)
        _restore_node_irrigation(db)
        _autoasignar_zonas_nodos(db)
    finally:
        db.close()

    # Iniciar consumer/publisher MQTT (background thread)
    from app.mqtt import start_mqtt, stop_mqtt
    start_mqtt()

    yield

    # Shutdown
    stop_mqtt()


app = FastAPI(title=APP_TITLE, version=APP_VERSION, lifespan=lifespan)

# ── Routers extraídos ────────────────────────────────────────────────────────
from app.routers.pages     import router as pages_router
from app.routers.api       import router as api_router
from app.routers.simulate  import router as simulate_router
from app.routers.admin     import router as admin_router
from app.routers.report    import router as report_router
from app.routers.inference import router as inference_router
from app.routers.auth        import router as auth_router
from app.routers.backoffice  import router as backoffice_router
from app.routers.emails      import router as emails_router
from app.routers.wind         import router as wind_router

app.include_router(auth_router)
app.include_router(backoffice_router)
app.include_router(pages_router)
app.include_router(api_router)
app.include_router(simulate_router)
app.include_router(admin_router)
app.include_router(report_router)
app.include_router(inference_router)
app.include_router(emails_router)
app.include_router(wind_router)

