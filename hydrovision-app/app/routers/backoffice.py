"""
routers/backoffice.py — API back-office HydroVision AG
Acceso restringido a superadmin.
"""

import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.deps import get_db, hash_password, verify_password, superadmin_dep, audit as _audit
from app.models import AuditLog, NodeConfig, ServicePlan, Telemetry, User, ZoneConfig, TIER_NAMES, TIER_PRICE_RANGE, TIER_PRICE_BASE

router = APIRouter(prefix="/api/backoffice")


# ── Schemas ──────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    agronomist_name: Optional[str] = None
    agronomist_email: Optional[str] = None


class UserUpdate(BaseModel):
    current_password: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    agronomist_name: Optional[str] = None
    agronomist_email: Optional[str] = None
    email_lifecycle: Optional[bool] = None
    email_reports: Optional[bool] = None
    alert_email: Optional[bool] = None
    alert_whatsapp: Optional[bool] = None


class PlanCreate(BaseModel):
    user_id: int
    tier: int
    vence_at: Optional[str] = None     # ISO date "YYYY-MM-DD"


class PlanUpdate(BaseModel):
    tier: Optional[int] = None
    vence_at: Optional[str] = None


class NodeAssign(BaseModel):
    owner_id: Optional[int] = None    # None = desasignar


# ── Catálogo ──────────────────────────────────────────────────────────────────

@router.get("/catalog")
def get_catalog(_=Depends(superadmin_dep)):
    return {
        "tiers": [
            {
                "id": t, "name": TIER_NAMES[t],
                "precio_min": TIER_PRICE_RANGE[t][0],
                "precio_max": TIER_PRICE_RANGE[t][1],
                "precio_base": TIER_PRICE_BASE[t],
            }
            for t in (1, 2, 3)
        ],
    }


# ── Usuarios ──────────────────────────────────────────────────────────────────

@router.get("/users")
def list_users(db: Session = Depends(get_db), current=Depends(superadmin_dep)):
    users = db.query(User).order_by(User.created_at).all()
    # Derivar cultivo predominante y región de las zonas asignadas
    from app.models import AppConfig
    field_location = db.query(AppConfig).filter(AppConfig.key == "field_location").first()
    region_val = field_location.value if field_location else None
    result = []
    for u in users:
        plan = db.query(ServicePlan).filter(ServicePlan.user_id == u.id, ServicePlan.activo == True).first()
        nodes = db.query(NodeConfig).filter(NodeConfig.owner_id == u.id).count()
        user_zones = db.query(ZoneConfig).filter(ZoneConfig.owner_id == u.id).all()
        # Cultivo predominante: varietal más frecuente entre las zonas del usuario
        varietals = [z.varietal for z in user_zones if z.varietal]
        crop = max(set(varietals), key=varietals.count) if varietals else None
        result.append({
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "company": u.company,
            "total_ha": u.total_ha,
            "crop": crop,
            "region": region_val,
            "agronomist_name": u.agronomist_name,
            "agronomist_email": u.agronomist_email,
            "email_lifecycle": u.email_lifecycle,
            "email_reports": u.email_reports,
            "alert_email": u.alert_email,
            "alert_whatsapp": u.alert_whatsapp,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "plan": {
                "id": plan.id,
                "tier": plan.tier,
                "tier_name": TIER_NAMES.get(plan.tier, "?"),
                "activo": plan.activo,
                "starts_at": plan.starts_at.isoformat()[:10] if plan.starts_at else None,
                "vence_at": plan.vence_at.isoformat()[:10] if plan.vence_at else None,
                "days_remaining": plan.days_remaining,
                "is_expired": plan.is_expired,
            } if plan else None,
            "nodos": nodes,
            "zonas": len(user_zones),
        })
    return result


@router.post("/users", status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db), current=Depends(superadmin_dep)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "El usuario ya existe")
    if data.role not in ("user", "superadmin"):
        raise HTTPException(400, "Role inválido")
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        role=data.role,
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        company=data.company,
        agronomist_name=data.agronomist_name,
        agronomist_email=data.agronomist_email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _audit(db, "user_create", detail=f"username={user.username} role={user.role}", user_id=current.id)
    return {"id": user.id, "username": user.username, "role": user.role}


@router.put("/users/{user_id}")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), current=Depends(superadmin_dep)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    if data.password:
        if not data.current_password:
            raise HTTPException(400, "Debe ingresar la contraseña actual")
        if not verify_password(data.current_password, user.password_hash):
            raise HTTPException(400, "Contraseña actual incorrecta")
        user.password_hash = hash_password(data.password)
        _audit(db, "user_password_change", detail=f"username={user.username}", user_id=current.id)
    if data.role is not None and data.role != user.role:
        raise HTTPException(400, "No se puede cambiar el rol de un usuario")
    # Campos de perfil
    if data.full_name is not None:       user.full_name = data.full_name
    if data.email is not None:           user.email = data.email
    if data.phone is not None:           user.phone = data.phone
    if data.company is not None:         user.company = data.company
    if data.agronomist_name is not None: user.agronomist_name = data.agronomist_name
    if data.agronomist_email is not None: user.agronomist_email = data.agronomist_email
    if data.email_lifecycle is not None: user.email_lifecycle = data.email_lifecycle
    if data.email_reports is not None:   user.email_reports = data.email_reports
    if data.alert_email is not None:     user.alert_email = data.alert_email
    if data.alert_whatsapp is not None:  user.alert_whatsapp = data.alert_whatsapp
    db.commit()
    _audit(db, "user_update", detail=f"username={user.username}", user_id=current.id)
    return {"status": "ok"}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current=Depends(superadmin_dep)):
    if user_id == current.id:
        raise HTTPException(400, "No podés eliminar tu propio usuario")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    # Desasignar nodos y zonas antes de eliminar
    db.query(NodeConfig).filter(NodeConfig.owner_id == user_id).update({"owner_id": None})
    db.query(ZoneConfig).filter(ZoneConfig.owner_id == user_id).update({"owner_id": None})
    db.query(ServicePlan).filter(ServicePlan.user_id == user_id).delete()
    _audit(db, "user_delete", detail=f"username={user.username} role={user.role}", user_id=current.id)
    db.delete(user)
    db.commit()
    return {"status": "ok"}


# ── Nodos ─────────────────────────────────────────────────────────────────────

@router.get("/nodes")
def list_all_nodes(db: Session = Depends(get_db), _=Depends(superadmin_dep)):
    cfgs = db.query(NodeConfig).all()
    users = {u.id: u.username for u in db.query(User).all()}
    # Última telemetría por nodo
    from sqlalchemy import func
    subq = db.query(Telemetry.node_id, func.max(Telemetry.id).label("max_id")).group_by(Telemetry.node_id).subquery()
    last = {r.node_id: r for r in db.query(Telemetry).join(subq, Telemetry.id == subq.c.max_id).all()}
    import datetime as dt
    now = dt.datetime.utcnow()
    result = []
    for c in cfgs:
        t = last.get(c.node_id)
        result.append({
            "node_id": c.node_id,
            "name": c.name,
            "owner_id": c.owner_id,
            "owner_username": users.get(c.owner_id) if c.owner_id else None,
            "zona_id": c.zona_id,
            "solenoid": c.solenoid,
            "last_cwsi": round(t.cwsi, 3) if t else None,
            "last_seen_min": int((now - t.created_at).total_seconds() / 60) if t and t.created_at else None,
        })
    return result


@router.put("/nodes/{node_id}/assign")
def assign_node(node_id: str, data: NodeAssign, db: Session = Depends(get_db), current=Depends(superadmin_dep)):
    node = db.query(NodeConfig).filter(NodeConfig.node_id == node_id).first()
    if not node:
        raise HTTPException(404, "Nodo no encontrado")
    if data.owner_id is not None:
        if not db.query(User).filter(User.id == data.owner_id).first():
            raise HTTPException(404, "Usuario no encontrado")
    prev_owner = node.owner_id
    node.owner_id = data.owner_id
    action = "node_assign" if data.owner_id else "node_unassign"
    _audit(db, action, node_id=node_id,
           detail=f"prev_owner={prev_owner} new_owner={data.owner_id}", user_id=current.id)
    db.commit()
    return {"status": "ok", "node_id": node_id, "owner_id": data.owner_id}


# ── Planes de servicio ────────────────────────────────────────────────────────

@router.post("/plans", status_code=201)
def create_plan(data: PlanCreate, db: Session = Depends(get_db), current=Depends(superadmin_dep)):
    if not db.query(User).filter(User.id == data.user_id).first():
        raise HTTPException(404, "Usuario no encontrado")
    if data.tier not in (1, 2, 3):
        raise HTTPException(400, "Tier debe ser 1, 2 o 3")
    # Desactivar plan anterior si existe
    db.query(ServicePlan).filter(ServicePlan.user_id == data.user_id, ServicePlan.activo == True).update({"activo": False})
    # Contrato anual: si no se especifica vence_at, se calcula starts_at + 1 año
    now = datetime.datetime.utcnow()
    starts = now
    if data.vence_at:
        vence = datetime.datetime.fromisoformat(data.vence_at)
    else:
        vence = datetime.datetime(now.year + 1, now.month, now.day, now.hour, now.minute)
    # Determinar precio base del tier
    precio_base = {1: 95, 2: 150, 3: 255}.get(data.tier, 150)
    plan = ServicePlan(
        user_id=data.user_id,
        tier=data.tier,
        nodos_max=0,              # Sin límite (administrado por HydroVision)
        ha_contratadas=0,          # Será actualizado después basado en zonas
        precio_ha_usd=precio_base,
        activo=True,
        starts_at=starts,
        vence_at=vence,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    _audit(db, "plan_create", detail=f"user_id={data.user_id} tier={data.tier} vence={vence.date()}", user_id=current.id)
    return {"id": plan.id, "starts_at": starts.isoformat()[:10], "vence_at": vence.isoformat()[:10], "status": "ok"}


@router.put("/plans/{plan_id}")
def update_plan(plan_id: int, data: PlanUpdate, db: Session = Depends(get_db), _=Depends(superadmin_dep)):
    plan = db.query(ServicePlan).filter(ServicePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "Plan no encontrado")
    if data.tier is not None:
        if data.tier not in (1, 2, 3): raise HTTPException(400, "Tier inválido")
        plan.tier = data.tier
    if data.vence_at is not None:
        plan.vence_at = datetime.datetime.fromisoformat(data.vence_at) if data.vence_at else None
    db.commit()
    return {"status": "ok"}


# ── Stats globales ────────────────────────────────────────────────────────────

@router.get("/stats")
def global_stats(db: Session = Depends(get_db), _=Depends(superadmin_dep)):
    total_users   = db.query(User).filter(User.role == "user").count()
    total_nodes   = db.query(NodeConfig).count()
    unowned_nodes = db.query(NodeConfig).filter(NodeConfig.owner_id == None).count()
    active_plans  = db.query(ServicePlan).filter(ServicePlan.activo == True).count()
    ha_total      = db.query(ServicePlan).filter(ServicePlan.activo == True).all()
    ha_sum        = sum(p.ha_contratadas for p in ha_total)
    arr_usd       = sum(p.ha_contratadas * p.precio_ha_usd for p in ha_total)
    return {
        "clientes": total_users,
        "nodos_totales": total_nodes,
        "nodos_sin_asignar": unowned_nodes,
        "planes_activos": active_plans,
        "ha_contratadas": round(ha_sum, 1),
        "arr_usd_anual": round(arr_usd, 0),
    }


# ── Auditoría ────────────────────────────────────────────────────────────────

@router.get("/audit")
def get_audit(
    limit: int = Query(100, ge=1, le=1000),
    event: str = Query(None),
    node_id: str = Query(None),
    db: Session = Depends(get_db),
    _=Depends(superadmin_dep),
):
    q = db.query(AuditLog).order_by(AuditLog.ts.desc())
    if event:
        q = q.filter(AuditLog.event == event)
    if node_id:
        q = q.filter(AuditLog.node_id == node_id)
    rows = q.limit(limit).all()
    users = {u.id: u.username for u in db.query(User).all()}
    return [
        {"id": r.id, "ts": r.ts.isoformat() if r.ts else None, "event": r.event,
         "user": users.get(r.user_id) if r.user_id else None,
         "node_id": r.node_id, "detail": r.detail, "ip": r.ip}
        for r in rows
    ]
