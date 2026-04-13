"""
routers/admin.py — Endpoints de administración /api/admin/*
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
    _autoasignar_zonas_nodos, _HL, _HO,
)
from app.deps import get_db, check_rate_limit as _check_rate_limit, verify_hmac as _verify_hmac, audit as _audit, user_only_dep
from app.models import (
    AppConfig, AuditLog, Base, IrrigationLog, NodeConfig,
    ServicePlan, SessionLocal, Telemetry, ZoneConfig, User, engine,
    APP_CONFIG_DEFAULTS, ZONE_DEFAULTS,
)
from app.schemas import (
    NodePayload, ZoneIn, NodeConfigIn, ConfigIn,
    InferenceRequest, InferenceResponse,
)


router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ha_contratadas(user_id: int, db: Session) -> float | None:
    """Devuelve las ha contratadas del plan activo del usuario, o None si no tiene plan."""
    plan = db.query(ServicePlan).filter(
        ServicePlan.user_id == user_id, ServicePlan.activo == True
    ).first()
    return plan.ha_contratadas if plan else None


def _ha_usadas(user_id: int, db: Session, exclude_zone_id: int = None) -> float:
    """Suma el área de todas las zonas del usuario (excluyendo una zona si se está editando)."""
    q = db.query(ZoneConfig).filter(ZoneConfig.owner_id == user_id)
    if exclude_zone_id is not None:
        q = q.filter(ZoneConfig.id != exclude_zone_id)
    return sum(_area_ha_zona(z) for z in q.all())


def _check_ha_limit(user_id: int, nueva_ha: float, db: Session, exclude_zone_id: int = None):
    """Lanza 400 si agregar nueva_ha supera las ha contratadas.
    ha_contratadas == 0 se trata como sin límite (plan activo sin cupo fijo)."""
    contratadas = _ha_contratadas(user_id, db)
    if contratadas is None:
        raise HTTPException(400, "El usuario no tiene un plan de servicio activo")
    if contratadas == 0:
        return  # 0 = sin límite configurado
    usadas = _ha_usadas(user_id, db, exclude_zone_id=exclude_zone_id)
    if usadas + nueva_ha > contratadas + 0.01:   # 0.01 ha de tolerancia por redondeo
        disponibles = max(0.0, round(contratadas - usadas, 2))
        raise HTTPException(
            400,
            f"Límite de plan excedido: {round(usadas,2)} ha usadas + {round(nueva_ha,2)} ha nuevas "
            f"> {contratadas} ha contratadas. Disponibles: {disponibles} ha."
        )


# ---------------------------------------------------------------------------
# Rutas admin
# ---------------------------------------------------------------------------

@router.get("/api/admin/config")
def admin_get_config(db: Session = Depends(get_db), current_user: User = Depends(user_only_dep)):
    cfg = {r.key: r.value for r in db.query(AppConfig).all()}
    # Valores derivados de las zonas (no editables)
    cfg["field_varietal"] = _resumen_varietales(db)
    cfg["field_area_ha"]  = str(_calcular_superficie_ha(db))
    cfg["cwsi_medio"]     = str(CWSI_MEDIO)
    cfg["cwsi_alto"]      = str(CWSI_ALTO)
    return cfg


@router.put("/api/admin/config")
def admin_update_config(data: ConfigIn, db: Session = Depends(get_db), current_user: User = Depends(user_only_dep)):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    for k, v in updates.items():
        row = db.query(AppConfig).filter(AppConfig.key == k).first()
        if row:
            row.value = str(v)
        else:
            db.add(AppConfig(key=k, value=str(v)))
    _audit(db, "config_change", detail=json.dumps(updates), user_id=current_user.id)
    db.commit()
    return {"status": "ok"}


@router.get("/api/admin/zones")
def admin_get_zones(db: Session = Depends(get_db), current_user: User = Depends(user_only_dep)):
    rows = db.query(ZoneConfig).filter(ZoneConfig.owner_id == current_user.id).order_by(ZoneConfig.id).all()
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


@router.post("/api/admin/zones", status_code=201)
def admin_create_zone(data: ZoneIn, db: Session = Depends(get_db), current_user: User = Depends(user_only_dep)):
    b = _bounds_from_zone_in(data)
    conflict = _check_overlap(-1, b["sw_lat"], b["sw_lon"], b["ne_lat"], b["ne_lon"], db)

    # Verificar límite de ha contratadas
    zona_tmp = ZoneConfig(lat=data.lat, lon=data.lon, vertices=data.vertices,
                          sw_lat=b["sw_lat"], sw_lon=b["sw_lon"],
                          ne_lat=b["ne_lat"], ne_lon=b["ne_lon"])
    nueva_ha = _area_ha_zona(zona_tmp)
    _check_ha_limit(current_user.id, nueva_ha, db)

    existing_ids = {r.id for r in db.query(ZoneConfig.id).all()}
    new_id = max(existing_ids) + 1 if existing_ids else 1
    db.add(ZoneConfig(id=new_id, name=data.name, lat=data.lat, lon=data.lon,
                      sw_lat=b["sw_lat"], sw_lon=b["sw_lon"],
                      ne_lat=b["ne_lat"], ne_lon=b["ne_lon"],
                      vertices=data.vertices,
                      varietal=data.varietal,
                      crop_yield_kg_ha=data.crop_yield_kg_ha,
                      owner_id=current_user.id))
    _audit(db, "zone_create", detail=f"id={new_id} name={data.name}", user_id=current_user.id)
    db.commit()
    _reload_zones(db)
    # Devuelve warning si hay superposición (no bloquea)
    return {"status": "ok", "id": new_id, "warning": f"Se superpone con '{conflict}'" if conflict else None}


@router.put("/api/admin/zones/{zone_id}")
def admin_update_zone(zone_id: int, data: ZoneIn, db: Session = Depends(get_db), current_user: User = Depends(user_only_dep)):
    row = db.query(ZoneConfig).filter(ZoneConfig.id == zone_id, ZoneConfig.owner_id == current_user.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Zona no encontrada")

    b = _bounds_from_zone_in(data)
    conflict = _check_overlap(zone_id, b["sw_lat"], b["sw_lon"], b["ne_lat"], b["ne_lon"], db)

    # Verificar límite de ha contratadas (excluyendo la zona actual que se va a reemplazar)
    zona_tmp = ZoneConfig(lat=data.lat, lon=data.lon, vertices=data.vertices,
                          sw_lat=b["sw_lat"], sw_lon=b["sw_lon"],
                          ne_lat=b["ne_lat"], ne_lon=b["ne_lon"])
    nueva_ha = _area_ha_zona(zona_tmp)
    _check_ha_limit(current_user.id, nueva_ha, db, exclude_zone_id=zone_id)

    row.name = data.name; row.lat = data.lat; row.lon = data.lon
    row.sw_lat = b["sw_lat"]; row.sw_lon = b["sw_lon"]
    row.ne_lat = b["ne_lat"]; row.ne_lon = b["ne_lon"]
    row.vertices = data.vertices
    row.varietal         = data.varietal
    row.crop_yield_kg_ha = data.crop_yield_kg_ha
    _audit(db, "zone_update", detail=f"id={zone_id} name={data.name}", user_id=current_user.id)
    db.commit()
    _reload_zones(db)
    return {"status": "ok", "warning": f"Se superpone con '{conflict}'" if conflict else None}


@router.delete("/api/admin/zones/{zone_id}")
def admin_delete_zone(zone_id: int, db: Session = Depends(get_db), current_user: User = Depends(user_only_dep)):
    row = db.query(ZoneConfig).filter(ZoneConfig.id == zone_id, ZoneConfig.owner_id == current_user.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Zona no encontrada")
    _audit(db, "zone_delete", detail=f"id={zone_id} name={row.name}", user_id=current_user.id)
    db.delete(row)
    db.commit()
    _reload_zones(db)
    return {"status": "ok"}


@router.get("/api/admin/nodes")
def admin_get_nodes(db: Session = Depends(get_db), current_user: User = Depends(user_only_dep)):
    """Nodos conocidos: une NodeConfig con su última telemetría."""
    subq = (
        db.query(Telemetry.node_id, func.max(Telemetry.id).label("max_id"))
        .group_by(Telemetry.node_id).subquery()
    )
    last_telem = {
        r.node_id: r
        for r in db.query(Telemetry).join(subq, Telemetry.id == subq.c.max_id).all()
    }
    cfgs = {c.node_id: c for c in db.query(NodeConfig).filter(NodeConfig.owner_id == current_user.id).all()}

    all_ids = set(cfgs.keys())
    zones   = {z.id: z.name for z in db.query(ZoneConfig).filter(ZoneConfig.owner_id == current_user.id).all()}
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


@router.put("/api/admin/nodes/{node_id}")
def admin_update_node(node_id: str, data: NodeConfigIn, db: Session = Depends(get_db), current_user: User = Depends(user_only_dep)):
    row = db.query(NodeConfig).filter(NodeConfig.node_id == node_id).first()
    if not row or row.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Nodo no encontrado o no pertenece a este usuario")
    if data.name     is not None: row.name     = data.name
    if data.zona_id  is not None: row.zona_id  = data.zona_id
    # solenoid no es editable — lo informa el nodo vía /ingest
    _audit(db, "node_update", node_id=node_id,
           detail=f"name={data.name} zona_id={data.zona_id}", user_id=current_user.id)
    db.commit()
    return {"status": "ok"}


@router.get("/api/admin/audit")
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
