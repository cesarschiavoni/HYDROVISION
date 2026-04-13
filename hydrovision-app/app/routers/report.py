"""
routers/report.py — Endpoints de informes /api/report/*
HydroVision AG
"""

import csv
import datetime
import io
import json
import math
import random
from typing import Optional

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
    _autoasignar_zonas_nodos,
)
from app.deps import get_db, check_rate_limit as _check_rate_limit, verify_hmac as _verify_hmac, audit as _audit, current_user_dep, user_only_dep
from app.models import (
    AppConfig, AuditLog, Base, IrrigationLog, NodeConfig,
    SessionLocal, ServicePlan, Telemetry, User, ZoneConfig, engine,
    APP_CONFIG_DEFAULTS, ZONE_DEFAULTS,
)
from app.schemas import (
    NodePayload, ZoneIn, NodeConfigIn, ConfigIn,
    InferenceRequest, InferenceResponse,
)


router = APIRouter()

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


@router.get("/api/report/summary")
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


@router.get("/api/report/cwsi-history")
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


@router.get("/api/report/zone-history")
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


@router.get("/api/report/irrigation-history")
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


@router.get("/api/report/zone-performance")
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


@router.get("/api/report/comparison")
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


@router.get("/api/report/export/csv")
def report_export_csv(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(user_only_dep),
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


# ── Plan del usuario autenticado ────────────────────────────────────────────

@router.get("/api/user/plan")
def user_plan(
    current_user: User = Depends(user_only_dep),
    db: Session = Depends(get_db),
):
    """Devuelve el tier del plan activo del usuario autenticado."""
    plan = (
        db.query(ServicePlan)
        .filter(ServicePlan.user_id == current_user.id, ServicePlan.activo == True)
        .order_by(ServicePlan.id.desc())
        .first()
    )
    return {"tier": plan.tier if plan else 0}


# ── Trazabilidad de riego — ISO 14046 / PEF ────────────────────────────────

@router.get("/api/report/traceability")
def irrigation_traceability(
    days: int = Query(365, ge=1, le=1095),
    zone_id: Optional[int] = None,
    fmt: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(user_only_dep),
):
    """
    Reporte de trazabilidad de riego auditable.
    Compatible con ISO 14046 (huella hídrica) y PEF/PEFCR europeo.

    Cada registro incluye: cuándo se regó, cuánto, por qué (CWSI trigger),
    y la cadena de datos que justifica la decisión.
    Requiere Plan Tier 3.
    """
    plan = (
        db.query(ServicePlan)
        .filter(ServicePlan.user_id == current_user.id, ServicePlan.activo == True)
        .order_by(ServicePlan.id.desc())
        .first()
    )
    if not plan or plan.tier < 3:
        raise HTTPException(status_code=403, detail="El informe de trazabilidad hídrica requiere Plan Tier 3")

    since = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    # Eventos de riego
    q = db.query(IrrigationLog).filter(IrrigationLog.ts >= since).order_by(IrrigationLog.ts.asc())
    if zone_id:
        q = q.filter(IrrigationLog.zona == zone_id)
    irrigation_events = q.all()

    # Telemetría asociada a cada evento de riego
    records = []
    for evt in irrigation_events:
        if not evt.node_id:
            continue
        # Buscar telemetría más cercana al momento del riego
        telem = db.query(Telemetry).filter(
            Telemetry.node_id == evt.node_id,
            Telemetry.created_at <= evt.ts,
            Telemetry.created_at >= evt.ts - datetime.timedelta(minutes=30),
        ).order_by(Telemetry.created_at.desc()).first()

        node_cfg = db.query(NodeConfig).filter(NodeConfig.node_id == evt.node_id).first()
        zone_cfg = None
        if node_cfg and node_cfg.zona_id:
            zone_cfg = db.query(ZoneConfig).filter(ZoneConfig.id == node_cfg.zona_id).first()

        records.append({
            "timestamp": evt.ts.isoformat() if evt.ts else None,
            "node_id": evt.node_id,
            "zone": zone_cfg.name if zone_cfg else None,
            "varietal": zone_cfg.varietal if zone_cfg else None,
            "action": "riego_on" if evt.active else "riego_off",
            "duration_min": evt.duration_min,
            "trigger_cwsi": round(telem.cwsi, 3) if telem else None,
            "trigger_hsi": round(telem.hsi, 3) if telem else None,
            "t_air_c": round(telem.t_air, 1) if telem else None,
            "rh_pct": round(telem.rh, 1) if telem else None,
            "wind_ms": round(telem.wind_ms, 1) if telem else None,
            "rain_mm": round(telem.rain_mm, 1) if telem else None,
            "data_quality": telem.calidad if telem else None,
            "data_origin": telem.origen if telem else None,
        })

    # Resumen por zona
    zones_summary = {}
    for r in records:
        zn = r["zone"] or "Sin zona"
        if zn not in zones_summary:
            zones_summary[zn] = {"activations": 0, "total_min": 0, "varietal": r["varietal"]}
        if r["action"] == "riego_on":
            zones_summary[zn]["activations"] += 1
            zones_summary[zn]["total_min"] += r["duration_min"] or 0

    # Agua estimada (m3) — simplificado: caudal goteo típico 4 L/h/gotero, 2500 goteros/ha
    water_per_min_m3_ha = (4 * 2500) / 60 / 1000  # ~0.167 m3/min/ha

    # Config de campo
    field_name = "Campo"
    field_loc = ""
    cfg_name = db.query(AppConfig).filter(AppConfig.key == "field_name").first()
    cfg_loc = db.query(AppConfig).filter(AppConfig.key == "field_location").first()
    if cfg_name: field_name = cfg_name.value
    if cfg_loc: field_loc = cfg_loc.value

    # Total telemetría en el período
    total_readings = db.query(func.count(Telemetry.id)).filter(
        Telemetry.created_at >= since
    ).scalar() or 0

    payload = {
        "report_type": "irrigation_traceability",
        "standard": "ISO 14046:2014 / PEF-PEFCR (EU)",
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "period": {"days": days, "from": since.isoformat()[:10], "to": datetime.datetime.utcnow().isoformat()[:10]},
        "field": {"name": field_name, "location": field_loc},
        "methodology": {
            "stress_index": "CWSI (Jackson et al. 1981) + HSI fusion (CWSI + MDS dendrométrico)",
            "measurement_frequency": "Cada 15 minutos, 365 días/año",
            "satellite_complement": "Sentinel-2 NDWI cada 5 días — fusión nodo+satélite",
            "decision_protocol": "Activación automática por HSI > umbral con histéresis 0.30/0.20",
            "data_integrity": f"{total_readings:,} mediciones en el período",
        },
        "summary": {
            "total_irrigation_events": sum(z["activations"] for z in zones_summary.values()),
            "total_irrigation_min": sum(z["total_min"] for z in zones_summary.values()),
            "zones": [
                {
                    "zone": zn,
                    "varietal": info["varietal"],
                    "activations": info["activations"],
                    "total_min": info["total_min"],
                    "estimated_water_m3_ha": round(info["total_min"] * water_per_min_m3_ha, 1),
                }
                for zn, info in zones_summary.items()
            ],
        },
        "events": records,
        "audit_note": "Cada evento incluye la cadena de datos completa (CWSI, HSI, T aire, HR, viento, lluvia) "
                      "que justifica la decisión de riego. Datos generados por sensores IoT in situ con "
                      "transmisión cada 15 minutos vía LoRa/MQTT. Trazabilidad continua desde el sensor hasta "
                      "la activación del solenoide.",
    }

    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "timestamp", "node_id", "zone", "varietal", "action",
            "duration_min", "trigger_cwsi", "trigger_hsi",
            "t_air_c", "rh_pct", "wind_ms", "rain_mm", "data_quality", "data_origin",
        ])
        for ev in payload["events"]:
            writer.writerow([
                ev["timestamp"], ev["node_id"], ev["zone"], ev["varietal"], ev["action"],
                ev["duration_min"], ev["trigger_cwsi"], ev["trigger_hsi"],
                ev["t_air_c"], ev["rh_pct"], ev["wind_ms"], ev["rain_mm"],
                ev["data_quality"], ev["data_origin"],
            ])
        buf.seek(0)
        fname = f"hydrovision_trazabilidad_{days}d.csv"
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={fname}"},
        )

    return payload

