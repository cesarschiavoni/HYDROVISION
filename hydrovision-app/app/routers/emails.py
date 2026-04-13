"""
emails.py — Router de emails lifecycle y reportes
HydroVision AG

Endpoints:
  POST /api/emails/preview/{email_type}   → previsualizar email (devuelve HTML)
  POST /api/emails/send/{email_type}      → enviar email a un cliente
  POST /api/emails/annual-report          → generar y enviar informe anual
  GET  /api/emails/schedule               → ver programacion de emails lifecycle
  POST /api/emails/schedule/run           → ejecutar ciclo de emails programados

Requiere autenticacion admin (cookie de sesion).
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from app.services.email_service import EmailService, ClientInfo, ZoneInfo
from app.services.phenology import get_crop_group, get_email_schedule, GROUP_DISPLAY_NAMES, EMAIL_SCHEDULES

router = APIRouter(prefix="/api/emails", tags=["emails"])

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=True)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ZonePayload(BaseModel):
    zone_id: int
    zone_name: str
    varietal: str
    node_ids: list[str] = []

class ClientPayload(BaseModel):
    name: str
    email: str
    crop: str = "Malbec"
    total_ha: float = 50
    tier: int = 2
    region: str = "Valle de Uco, Mendoza"
    node_ids: list[str] = []
    zones: list[ZonePayload] = []
    agronomist_email: Optional[str] = None

class SendRequest(BaseModel):
    client: ClientPayload
    campaign_year: int = 2025
    extra: dict = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_email_service() -> EmailService:
    return EmailService(_jinja_env)


def _to_client_info(p: ClientPayload) -> ClientInfo:
    return ClientInfo(
        name=p.name,
        email=p.email,
        crop=p.crop,
        total_ha=p.total_ha,
        tier=p.tier,
        region=p.region,
        node_ids=p.node_ids,
        zones=[ZoneInfo(zone_id=z.zone_id, zone_name=z.zone_name, varietal=z.varietal, node_ids=z.node_ids) for z in p.zones],
        agronomist_email=p.agronomist_email,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/preview/{email_type}")
async def preview_email(email_type: str, body: SendRequest):
    """Previsualizar un email lifecycle o annual_report (devuelve HTML renderizado)."""
    svc = _get_email_service()
    client = _to_client_info(body.client)

    if email_type == "annual_report":
        stats = svc.get_campaign_stats(
            node_ids=client.node_ids,
            start=datetime(body.campaign_year, 10, 1),
            end=datetime(body.campaign_year + 1, 3, 31),
            tier=client.tier,
            total_ha=client.total_ha,
            crop=client.crop,
        )
        html = svc.render_annual_report(client, stats, body.campaign_year)
    else:
        _, html = svc.render_lifecycle(client, email_type, campaign_year=body.campaign_year, **body.extra)

    return HTMLResponse(content=html)


@router.post("/send/{email_type}")
async def send_email(email_type: str, body: SendRequest):
    """Enviar un email lifecycle a un cliente."""
    svc = _get_email_service()
    client = _to_client_info(body.client)

    if email_type == "annual_report":
        ok = await svc.send_annual_report(client, body.campaign_year)
    else:
        ok = await svc.send_lifecycle_email(client, email_type, campaign_year=body.campaign_year, **body.extra)

    if not ok:
        raise HTTPException(status_code=502, detail="No se pudo enviar el email (ver logs SMTP)")
    return {"status": "sent", "to": client.email, "type": email_type}


@router.get("/schedule")
async def get_schedule(crop_group: str = "vid"):
    """Calendario de emails lifecycle por grupo varietal (vid, olivo, cerezo)."""
    schedule = get_email_schedule(crop_group)
    return {
        "crop_group": crop_group,
        "crop_group_name": GROUP_DISPLAY_NAMES.get(crop_group, crop_group),
        "available_groups": list(EMAIL_SCHEDULES.keys()),
        "schedule": schedule,
    }
