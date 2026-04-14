"""
wind_analysis.py — Analisis de viento dominante por zona y varietal
HydroVision AG

Usa Open-Meteo Archive API (gratis, sin API key) para obtener datos
historicos de viento horario. Filtra por los meses con hojas segun
la variedad/cultivo de la zona y calcula la rosa de vientos.

Uso:
  from app.services.wind_analysis import fetch_wind_rose, leaf_on_months
  data = fetch_wind_rose(lat=-31.20, lon=-64.09, crop="vid - malbec")
  months = leaf_on_months("vid - malbec")  # [9,10,11,12,1,2,3,4,5]
"""

from __future__ import annotations

import json
import urllib.request
from collections import defaultdict
from datetime import date, timedelta

from app.services.phenology import get_crop_group, GROUP_PHASES

# 16 sectores de la brujula (cada 22.5 grados)
DIRECTIONS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]

MONTH_NAMES_ES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}


def leaf_on_months(crop: str | None) -> list[int]:
    """Retorna los meses (1-12) en que el cultivo tiene hojas."""
    group = get_crop_group(crop)
    phases = GROUP_PHASES.get(group, GROUP_PHASES["vid"])

    # Olivo es perennifolio
    if group == "olivo":
        return list(range(1, 13))

    # Para caducifolios: los meses de dormancia NO tienen hojas
    dormancy_months: set[int] = set()
    for p in phases:
        if p.name == "dormancia":
            if p.month_start <= p.month_end:
                dormancy_months.update(range(p.month_start, p.month_end + 1))
            else:
                dormancy_months.update(range(p.month_start, 13))
                dormancy_months.update(range(1, p.month_end + 1))
            break

    return [m for m in range(1, 13) if m not in dormancy_months]


def _direction_sector(degrees: float) -> int:
    """Convierte grados (0-360) a indice de sector (0-15)."""
    return round(degrees / 22.5) % 16


def fetch_wind_rose(
    lat: float,
    lon: float,
    crop: str | None = None,
    years: int = 3,
    hours: str = "all",
) -> dict:
    """
    Obtiene la rosa de vientos para una ubicacion, filtrada por los
    meses con hojas del cultivo especificado.

    Usa Open-Meteo Archive API — gratis, sin API key, datos ERA5.

    hours: "all" (24h), "dia" (6-20 hs, relevante para CWSI),
           "noche" (21-5 hs, relevante para heladas).

    Retorna dict con: sectors, dominant, calm_pct, leaf_months, etc.
    """
    months = leaf_on_months(crop)
    group = get_crop_group(crop)

    end = date.today() - timedelta(days=7)
    start = end.replace(year=end.year - years)

    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={start.isoformat()}&end_date={end.isoformat()}"
        "&hourly=wind_speed_10m,wind_direction_10m"
        "&timezone=America/Argentina/Cordoba"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "HydroVision-AG/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    times = data["hourly"]["time"]
    speeds = data["hourly"]["wind_speed_10m"]
    dirs = data["hourly"]["wind_direction_10m"]

    # Filtrar por meses con hojas + franja horaria
    months_set = set(months)
    sector_speeds: dict[int, list[float]] = defaultdict(list)
    total = 0
    calm = 0
    CALM_THRESHOLD = 0.5  # m/s

    for t, spd, d in zip(times, speeds, dirs):
        if spd is None or d is None:
            continue
        month = int(t[5:7])
        hour = int(t[11:13])
        if month not in months_set:
            continue
        if hours == "dia" and (hour < 6 or hour > 20):
            continue
        if hours == "noche" and 6 <= hour <= 20:
            continue
        total += 1
        if spd < CALM_THRESHOLD:
            calm += 1
            continue
        sector = _direction_sector(d)
        sector_speeds[sector].append(spd)

    hours_label = {"all": "24 hs", "dia": "6–20 hs (dia)", "noche": "21–5 hs (noche)"}
    if total == 0:
        return {
            "lat": lat, "lon": lon, "crop": crop or "vid",
            "crop_group": group,
            "hours": hours,
            "hours_label": hours_label.get(hours, hours),
            "leaf_months": months,
            "leaf_months_names": [MONTH_NAMES_ES[m] for m in months],
            "years_analyzed": years,
            "total_hours": 0,
            "calm_pct": 0,
            "dominant": "N/A",
            "dominant_pct": 0,
            "avg_speed_ms": 0,
            "sectors": [],
        }

    sectors = []
    best_dir = 0
    best_count = 0
    all_speeds: list[float] = []

    for i, name in enumerate(DIRECTIONS):
        slist = sector_speeds.get(i, [])
        count = len(slist)
        freq = (count / total) * 100
        avg_s = sum(slist) / count if count > 0 else 0
        max_s = max(slist) if slist else 0
        sectors.append({
            "dir": name,
            "freq_pct": round(freq, 1),
            "avg_speed": round(avg_s, 1),
            "max_speed": round(max_s, 1),
            "count": count,
        })
        all_speeds.extend(slist)
        if count > best_count:
            best_count = count
            best_dir = i

    return {
        "lat": lat,
        "lon": lon,
        "crop": crop or "vid",
        "crop_group": group,
        "hours": hours,
        "hours_label": hours_label.get(hours, hours),
        "leaf_months": months,
        "leaf_months_names": [MONTH_NAMES_ES[m] for m in months],
        "years_analyzed": years,
        "total_hours": total,
        "calm_pct": round((calm / total) * 100, 1),
        "dominant": DIRECTIONS[best_dir],
        "dominant_pct": round((best_count / total) * 100, 1),
        "avg_speed_ms": round(sum(all_speeds) / len(all_speeds), 1) if all_speeds else 0,
        "sectors": sectors,
    }
