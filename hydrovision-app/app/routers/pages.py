"""
routers/pages.py — Rutas de páginas HTML
HydroVision AG
"""

from pathlib import Path

from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.deps import get_db, decode_session_token
from app.models import User

router = APIRouter()

_TEMPLATES = Path(__file__).parent.parent / "templates"


@router.get("/favicon.ico", include_in_schema=False)
def favicon():
    svg = (_TEMPLATES / "favicon.svg").read_bytes()
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/", response_class=HTMLResponse)
def home():
    return (_TEMPLATES / "home.html").read_text(encoding="utf-8")


def _require_user(hv_session: str | None = Cookie(default=None), db=Depends(get_db)):
    """Permite acceso solo a usuarios con role='user'. Superadmin → /backoffice."""
    if not hv_session:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    user_id = decode_session_token(hv_session)
    if user_id is None:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    if user.role == "superadmin":
        raise HTTPException(status_code=302, headers={"Location": "/backoffice"})
    return user


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(_=Depends(_require_user)):
    return (_TEMPLATES / "dashboard.html").read_text(encoding="utf-8")


@router.get("/admin", response_class=HTMLResponse)
def admin_page(_=Depends(_require_user)):
    return (_TEMPLATES / "admin.html").read_text(encoding="utf-8")


@router.get("/informe", response_class=HTMLResponse)
def informe_page(_=Depends(_require_user)):
    return (_TEMPLATES / "informe.html").read_text(encoding="utf-8")


@router.get("/trazabilidad", response_class=HTMLResponse)
def traceability_page(_=Depends(_require_user)):
    return (_TEMPLATES / "trazabilidad.html").read_text(encoding="utf-8")


@router.get("/viento", response_class=HTMLResponse)
def viento_page(_=Depends(_require_user)):
    return (_TEMPLATES / "viento.html").read_text(encoding="utf-8")


@router.get("/backoffice", response_class=HTMLResponse)
def backoffice_page(
    hv_session: str | None = Cookie(default=None),
    db=Depends(get_db),
):
    if not hv_session:
        return RedirectResponse("/login", status_code=302)
    user_id = decode_session_token(hv_session)
    if user_id is None:
        return RedirectResponse("/login", status_code=302)
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != "superadmin":
        return HTMLResponse("<h1>403 — Acceso denegado</h1>", status_code=403)
    return (_TEMPLATES / "backoffice.html").read_text(encoding="utf-8")
