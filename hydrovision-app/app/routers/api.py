"""
routers/api.py — Endpoints core de telemetría y control
HydroVision AG
"""

import datetime
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
    _autoasignar_zonas_nodos, process_ingest, _zona_en_reposo,
)
from app.deps import get_db, check_rate_limit as _check_rate_limit, verify_hmac as _verify_hmac, audit as _audit, user_only_dep
from app.models import (
    AppConfig, AuditLog, Base, IrrigationLog, NodeConfig,
    SessionLocal, Telemetry, ZoneConfig, User, engine,
    APP_CONFIG_DEFAULTS, ZONE_DEFAULTS,
)
from app.schemas import (
    NodePayload, ZoneIn, NodeConfigIn, ConfigIn,
    InferenceRequest, InferenceResponse,
)


router = APIRouter()

@router.post("/ingest")
def ingest(payload: NodePayload, request: Request, db: Session = Depends(get_db)):
    """Endpoint HTTP de telemetría (fallback). El flujo principal es MQTT."""
    client_ip = request.client.host if request.client else None

    # Verificación HMAC (solo en HTTP — MQTT usa TLS del broker)
    if not _verify_hmac(payload):
        _audit(db, "hmac_fail", node_id=payload.node_id, ip=client_ip)
        raise HTTPException(status_code=401, detail="Invalid or missing HMAC signature")

    resp = process_ingest(payload.model_dump(), db, ip=client_ip)
    if resp.get("status") == "rejected":
        raise HTTPException(status_code=429, detail=resp.get("reason", "rate_limit"))
    return resp


@router.get("/api/status")
def status(db: Session = Depends(get_db), current_user: User = Depends(user_only_dep)):
    owned_node_ids = {
        c.node_id for c in db.query(NodeConfig).filter(NodeConfig.owner_id == current_user.id).all()
    }
    subq = (
        db.query(Telemetry.node_id, func.max(Telemetry.id).label("max_id"))
        .group_by(Telemetry.node_id).subquery()
    )
    rows = db.query(Telemetry).join(subq, Telemetry.id == subq.c.max_id).all()
    cfgs = {c.node_id: c for c in db.query(NodeConfig).filter(NodeConfig.owner_id == current_user.id).all()}
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
        for r in rows if r.node_id in owned_node_ids
    ]


@router.get("/api/alerts")
def alerts(db: Session = Depends(get_db), current_user: User = Depends(user_only_dep)):
    owned_node_ids = {
        c.node_id for c in db.query(NodeConfig).filter(NodeConfig.owner_id == current_user.id).all()
    }
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
    return [{"node_id": r.node_id, "cwsi": round(r.cwsi, 3)}
            for r in rows if r.node_id in owned_node_ids]


@router.get("/api/history/{node_id}")
def history(node_id: str, db: Session = Depends(get_db), current_user: User = Depends(user_only_dep)):
    cfg = db.query(NodeConfig).filter(
        NodeConfig.node_id == node_id,
        NodeConfig.owner_id == current_user.id,
    ).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=48)
    rows = (
        db.query(Telemetry)
        .filter(Telemetry.node_id == node_id, Telemetry.created_at >= cutoff)
        .order_by(Telemetry.created_at).all()
    )
    return [{"ts": r.created_at.isoformat(), "cwsi": round(r.cwsi, 3), "hsi": round(r.hsi, 3)}
            for r in rows]


@router.post("/api/irrigate/{node_id}")
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

    # Publicar comando MQTT al nodo (downlink vía gateway LoRa)
    from app.mqtt import publish_command
    publish_command(node_id, {"irrigate": new_state, "source": "manual_dashboard"})

    return {"status": "ok", "node_id": node_id, "active": new_state, "source": "manual_override"}


@router.post("/api/sol_sim/{node_id}")
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


@router.get("/api/zones")
def get_zones(db: Session = Depends(get_db), current_user: User = Depends(user_only_dep)):
    # Nodos: solo los propios del usuario
    all_cfgs = db.query(NodeConfig).filter(NodeConfig.owner_id == current_user.id).all()
    owned_node_ids = {c.node_id for c in all_cfgs}
    # Zonas: las del usuario + las que tienen nodos propios asignados
    user_zone_ids = {
        z.id for z in db.query(ZoneConfig).filter(ZoneConfig.owner_id == current_user.id).all()
    }
    node_zone_ids = {c.zona_id for c in all_cfgs if c.zona_id is not None}
    owned_zone_ids = user_zone_ids | node_zone_ids
    subq = (
        db.query(Telemetry.node_id, func.max(Telemetry.id).label("max_id"))
        .group_by(Telemetry.node_id).subquery()
    )
    rows = db.query(Telemetry).join(subq, Telemetry.id == subq.c.max_id).all()
    rows = [r for r in rows if r.node_id in owned_node_ids]
    cfgs = {c.node_id: c for c in all_cfgs}
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
        if zona_id not in owned_zone_ids:
            continue
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

    # ── Nodos sin zona asignada ────────────────────────────────────────────
    unzoned = []
    for node_id, cfg in cfgs.items():
        if cfg.zona_id is not None:
            continue
        ncwsi = node_cwsi.get(node_id)
        node_active = _NODE_IRRIGATION.get(node_id, False)
        unzoned.append({
            "node_id":   node_id,
            "name":      cfg.name or node_id,
            "cwsi":      round(ncwsi, 3) if ncwsi is not None else None,
            "solenoid":  cfg.solenoid,
            "irrigating": node_active,
            "sol_sim":   _NODE_SOL_SIM.get(node_id, False),
        })

    return {"zones": result, "unzoned_nodes": unzoned}


# Simulación: variables y perfiles en routers/simulate.py
from app.routers.simulate import _SIM_RUNNING, _SIM_WATER, _sim_water_to_cwsi

