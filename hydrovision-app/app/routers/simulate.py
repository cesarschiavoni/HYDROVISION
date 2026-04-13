"""
routers/simulate.py — Endpoints de simulación (SIMULATION_MODE)
HydroVision AG
"""

import asyncio as _asyncio
import datetime
import json
import math
import random
from typing import Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import (
    ZONES, _NODE_IRRIGATION, _NODE_SOL_SIM,
    CWSI_MEDIO, CWSI_ALTO, CWSI_IRRIGATE,
    _fusion, _vpd_kpa, _stress_label, _fenologia_zona,
    _ky_para_varietal, _ensure_node_config, _zona_para_punto,
    _reload_zones, _check_overlap, _zone_bounds, _zone_bounds_from_vertices,
    _zone_centroid_from_vertices, _area_ha_zona, _calcular_superficie_ha,
    _nodos_recomendados_zona, _resumen_varietales, _seed_defaults,
    _autoasignar_zonas_nodos, _zona_en_reposo,
)
from app.deps import get_db, check_rate_limit as _check_rate_limit, verify_hmac as _verify_hmac, audit as _audit
from app.models import (
    AppConfig, AuditLog, Base, IrrigationLog, NodeConfig,
    SessionLocal, Telemetry, ZoneConfig, engine,
    APP_CONFIG_DEFAULTS, ZONE_DEFAULTS,
)
from app.schemas import (
    NodePayload, ZoneIn, NodeConfigIn, ConfigIn,
    InferenceRequest, InferenceResponse,
)


router = APIRouter()

# Estado de la simulación
_SIM_RUNNING = False
_SIM_TASK: "Optional[_asyncio.Task]" = None

# Estado hídrico por zona o nodo: 0.0 = seco, 1.0 = saturado
# Clave: zone_id (int) para nodos con zona, "node_{node_id}" para nodos sin zona
# El CWSI se deriva como ~ (1 - water_level) con variación diurna + ruido
_SIM_WATER: dict = {}

# Perfiles de nodos simulados — cwsi_base varía lentamente con deriva diaria
_SIM_PROFILES = [
    {"node_id": "HV-A4CF12B3", "cwsi_amp": 0.06, "bat_base": 88, "zone_id": 1, "solenoid": 1},
    {"node_id": "HV-B8A21F9C", "cwsi_amp": 0.10, "bat_base": 74, "zone_id": 3, "solenoid": 2},
    {"node_id": "HV-C2D35E1A", "cwsi_amp": 0.06, "bat_base": 61, "zone_id": 5, "solenoid": 3},
    {"node_id": "HV-D7E42A0B", "cwsi_amp": 0.08, "bat_base": 82, "zone_id": 12, "solenoid": 4,
     "lat_off": -0.0010, "lon_off": -0.0015},
    {"node_id": "HV-E1F56C3D", "cwsi_amp": 0.07, "bat_base": 79, "zone_id": 12, "solenoid": 5,
     "lat_off":  0.0005, "lon_off":  0.0010},
    {"node_id": "HV-F3A89D2E", "cwsi_amp": 0.09, "bat_base": 71, "zone_id": 12, "solenoid": 6,
     "lat_off":  0.0015, "lon_off": -0.0005},
]

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


def _field_centroid() -> tuple[float, float]:
    """Centroide del campo: promedio de todas las zonas configuradas."""
    zone_list = list(ZONES.items())
    if not zone_list:
        return (-31.2010, -64.0927)  # fallback Colonia Caroya
    lat = sum(z["lat"] for _, z in zone_list) / len(zone_list)
    lon = sum(z["lon"] for _, z in zone_list) / len(zone_list)
    return (lat, lon)


def _node_fallback_latlon(node_id: str) -> tuple[float, float]:
    """Lat/lon estable para un nodo sin zona: centroide + scatter determinístico."""
    import hashlib
    h = int(hashlib.md5(node_id.encode()).hexdigest()[:8], 16)
    rng = random.Random(h)
    clat, clon = _field_centroid()
    return (round(clat + rng.uniform(-0.0008, 0.0008), 6),
            round(clon + rng.uniform(-0.0008, 0.0008), 6))


def _sim_tick(db: Session) -> dict:
    """Inserta una lectura por nodo usando el estado hídrico de cada zona.
    Actualiza water_level para TODAS las zonas (con y sin nodo):
    baja por evapotranspiración, sube por riego/lluvia.
    Nodos sin zona asignada también reciben telemetría con lat/lon del centroide."""
    zone_list = list(ZONES.items())

    def zone_for(p):
        """Resuelve zona de un perfil por zone_id."""
        zid = p.get("zone_id")
        return (zid, ZONES[zid]) if (zid and zid in ZONES) else (None, None)

    now = datetime.datetime.utcnow()
    rain_this_tick = _sim_rain_mm(now)

    # Factor diurno de evapotranspiración: máximo al mediodía, mínimo de noche
    hour_frac = now.hour + now.minute / 60
    et_diurnal = _ET_DIURNAL * max(0, math.sin(math.pi * (hour_frac - 6) / 12))

    # Perfiles a simular: hardcoded + NodeConfig sin zona no ya cubiertos
    profiles_node_ids = {p["node_id"] for p in _SIM_PROFILES}
    extra_profiles = []
    for nc in db.query(NodeConfig).filter(NodeConfig.zona_id == None).all():
        if nc.node_id not in profiles_node_ids:
            extra_profiles.append({
                "node_id": nc.node_id,
                "cwsi_amp": 0.07,
                "bat_base": 80,
                "zone_id": None,
                "solenoid": nc.solenoid,
            })
    all_profiles = list(_SIM_PROFILES) + extra_profiles

    # ── Nodos con y sin zona: insertar telemetría + actualizar water ──────
    zonas_con_nodo = set()
    for p in all_profiles:
        zona_id, zone = zone_for(p)

        if zone is not None:
            node_lat = zone["lat"] + p.get("lat_off", 0)
            node_lon = zone["lon"] + p.get("lon_off", 0)
            water_key = zona_id
            zonas_con_nodo.add(zona_id)
        else:
            # Nodo sin zona: usar centroide del campo con scatter estable
            node_lat, node_lon = _node_fallback_latlon(p["node_id"])
            water_key = f"node_{p['node_id']}"

        _ensure_node_config(db, p["node_id"], zona_id=zona_id, solenoid=p.get("solenoid"))

        # Inicializar water_level si no existe
        if water_key not in _SIM_WATER:
            _SIM_WATER[water_key] = 0.65

        # ── Actualizar estado hídrico ───────────────────────────────────
        w = _SIM_WATER[water_key]

        # Pérdida: evapotranspiración (siempre, más intensa de día)
        w -= _ET_RATE + et_diurnal

        # Ganancia: riego activo (solo si tiene zona para decidir reposo)
        if _NODE_IRRIGATION.get(p["node_id"], False):
            if zona_id and _zona_en_reposo(zona_id):
                _NODE_IRRIGATION[p["node_id"]] = False
            else:
                w += _IRRIG_RATE

        # Ganancia: lluvia
        if rain_this_tick > 0:
            w += rain_this_tick * _RAIN_RATE

        w = max(0.05, min(1.0, w))
        _SIM_WATER[water_key] = round(w, 4)

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
            lat=node_lat,
            lon=node_lon,
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


@router.post("/api/simulate/start")
async def simulate_start():
    global _SIM_RUNNING, _SIM_TASK
    if _SIM_RUNNING:
        return {"status": "already_running"}
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


@router.post("/api/simulate/stop")
async def simulate_stop():
    global _SIM_RUNNING, _SIM_TASK
    _SIM_RUNNING = False
    if _SIM_TASK:
        _SIM_TASK.cancel()
        _SIM_TASK = None
    return {"status": "stopped"}


@router.get("/api/simulate/status")
def simulate_status():
    return {"running": _SIM_RUNNING}


def _seed_history(db: Session) -> None:
    """Inserta 48 h de historial sintético usando el modelo hidrológico.
    Cada zona arranca con un nivel de agua diferente y evoluciona con
    evapotranspiración, riego automático y lluvia ocasional."""
    zone_list = list(ZONES.items())

    def zone_for(p):
        zid = p.get("zone_id")
        if zid and zid in ZONES:
            return (zid, ZONES[zid])
        return (None, None)

    now = datetime.datetime.utcnow()

    # Estado hídrico: keyed por zone_id o "node_{node_id}" para nodos sin zona
    water_levels: dict = {}
    fallback_water = [0.85, 0.55, 0.35, 0.70, 0.60, 0.45]

    # Perfiles: hardcoded + NodeConfig sin zona no cubiertos
    profiles_node_ids = {p["node_id"] for p in _SIM_PROFILES}
    extra_profiles = []
    for nc in db.query(NodeConfig).filter(NodeConfig.zona_id == None).all():
        if nc.node_id not in profiles_node_ids:
            extra_profiles.append({
                "node_id": nc.node_id, "cwsi_amp": 0.07,
                "bat_base": 80, "zone_id": None, "solenoid": nc.solenoid,
            })
    all_profiles = list(_SIM_PROFILES) + extra_profiles

    for pi, p in enumerate(all_profiles):
        zona_id, zone = zone_for(p)
        water_key = zona_id if zona_id is not None else f"node_{p['node_id']}"
        _ensure_node_config(db, p["node_id"], zona_id=zona_id, solenoid=p.get("solenoid"))
        if water_key not in water_levels:
            if zone is not None and _fusion._calibrado:
                cwsi_sat = None
                try:
                    cwsi_sat = _fusion.predecir_cwsi(
                        zona_id, vpd_kpa=1.5,
                        zona_lat=zone.get("lat"), zona_lon=zone.get("lon"),
                    )
                except Exception:
                    pass
                water_levels[water_key] = (
                    float(np.clip(1.0 - cwsi_sat + random.uniform(-0.05, 0.05), 0.05, 0.95))
                    if cwsi_sat is not None
                    else fallback_water[pi % len(fallback_water)]
                )
            else:
                water_levels[water_key] = fallback_water[pi % len(fallback_water)]

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

        for pi, p in enumerate(all_profiles):
            zona_id, zone = zone_for(p)
            water_key = zona_id if zona_id is not None else f"node_{p['node_id']}"
            if water_key not in water_levels:
                continue
            w = water_levels[water_key]

            # Evapotranspiración
            w -= _ET_RATE + et_diurnal

            # Lluvia
            if rain_mm > 0:
                w += rain_mm * _RAIN_RATE

            # Auto-riego (solo nodos con zona)
            cwsi_check = max(0.0, min(1.0, 1.0 - w))
            if zona_id and cwsi_check >= CWSI_ALTO:
                w += _IRRIG_RATE
                if i % 4 == 0:
                    db.add(IrrigationLog(node_id=p["node_id"], zona=zona_id,
                                         duration_min=30, active=True, ts=ts_dt))
                    db.add(IrrigationLog(node_id=p["node_id"], zona=zona_id,
                                         duration_min=30, active=False,
                                         ts=ts_dt + datetime.timedelta(minutes=30)))

            w = max(0.05, min(1.0, w))
            water_levels[water_key] = round(w, 4)

            # CWSI desde water_level
            diurnal_cwsi = math.sin(math.pi * (hour_frac - 6) / 12) * p["cwsi_amp"]
            cwsi = _sim_water_to_cwsi(w, diurnal_cwsi, random.uniform(-0.03, 0.03))
            t_air = round(20 + 10 * max(0, math.sin(math.pi * (hour_frac - 6) / 12))
                          + random.uniform(-1.5, 1.5), 1)
            rh = round(max(20, min(95, 60 - cwsi * 25 + random.uniform(-5, 5))), 1)

            if zone is not None:
                node_lat = zone["lat"] + p.get("lat_off", 0)
                node_lon = zone["lon"] + p.get("lon_off", 0)
            else:
                node_lat, node_lon = _node_fallback_latlon(p["node_id"])

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
                lat=node_lat,
                lon=node_lon,
                created_at=ts_dt,
            ))

    # ── Zonas sin nodo: evolucionar water_level en paralelo (sin telemetría) ─
    s2_water: dict = {}
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
    for k, w in water_levels.items():
        _SIM_WATER[k] = w
    for zona_id, w in s2_water.items():
        _SIM_WATER[zona_id] = w

