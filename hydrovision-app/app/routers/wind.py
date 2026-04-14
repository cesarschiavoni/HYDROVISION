"""
routers/wind.py — Analisis de viento dominante por zona
HydroVision AG

GET /api/wind-rose?zone_id=N   — rosa de vientos para una zona
GET /api/wind-rose?lat=X&lon=Y&varietal=vid-malbec  — para coordenadas libres
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.deps import get_db, user_only_dep
from app.models import ZoneConfig, User

router = APIRouter(tags=["wind"])


@router.get("/api/wind-rose")
def wind_rose(
    zone_id: int | None = Query(None, description="ID de zona"),
    lat: float | None = Query(None),
    lon: float | None = Query(None),
    varietal: str | None = Query(None, description="Varietal (ej: vid - malbec)"),
    years: int = Query(3, ge=1, le=5, description="Anos de datos historicos"),
    hours: str = Query("dia", description="Franja: dia (6-20, default — CWSI), all (24h), noche (21-5)"),
    _user: User = Depends(user_only_dep),
    db: Session = Depends(get_db),
):
    """Rosa de vientos filtrada por meses con hojas del cultivo."""
    from app.services.wind_analysis import fetch_wind_rose

    if zone_id is not None:
        zone = db.query(ZoneConfig).filter(
            ZoneConfig.id == zone_id,
            ZoneConfig.owner_id == _user.id,
        ).first()
        if not zone:
            raise HTTPException(404, "Zona no encontrada")
        lat = zone.lat
        lon = zone.lon
        varietal = varietal or zone.varietal
    elif lat is None or lon is None:
        raise HTTPException(400, "Indicar zone_id o lat+lon")

    try:
        if hours not in ("all", "dia", "noche"):
            hours = "all"
        return fetch_wind_rose(lat, lon, varietal, years, hours)
    except Exception as e:
        raise HTTPException(502, f"Error al consultar datos de viento: {e}")
