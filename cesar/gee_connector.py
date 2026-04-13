"""
gee_connector.py — Conector Google Earth Engine para HydroVision AG
Descarga índices espectrales Sentinel-2 y VPD ERA5 sin bajar imágenes completas.

Satélites disponibles a futuro (mismo conector, cambiar ImageCollection):
  Sentinel-2 SR  →  'COPERNICUS/S2_SR_HARMONIZED'   (actual, TRL 3-4)
  Sentinel-1 SAR →  'COPERNICUS/S1_GRD'              (fallback nubes, TRL 5)
  Landsat 9      →  'LANDSAT/LC09/C02/T1_L2'         (histórico R15, TRL 5)
  MODIS NDVI     →  'MODIS/061/MOD13Q1'               (escala regional, TRL 6)

Setup inicial (una sola vez):
  pip install earthengine-api
  earthengine authenticate        ← abre browser, ingresar cuenta Google
  earthengine set_project hydrovision-ag

Uso posterior (automático):
  from gee_connector import init_gee
  init_gee()   ← usa credenciales cacheadas
"""

from __future__ import annotations

import math
import logging
from datetime import datetime, timedelta
from typing import Optional

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Inicialización
# ─────────────────────────────────────────────────────────────────

def init_gee(project: str = "hydrovision-ag") -> bool:
    """
    Inicializa GEE. Si no hay credenciales cacheadas, lanza el flujo de
    autenticación en el browser.

    Returns True si OK, False si hay error.
    """
    try:
        import ee
        try:
            ee.Initialize(project=project)
        except ee.EEException:
            log.info("[GEE] Credenciales no encontradas — iniciando autenticación...")
            ee.Authenticate()
            ee.Initialize(project=project)
        log.info(f"[GEE] OK — proyecto: {project}")
        return True
    except ImportError:
        log.error("[GEE] earthengine-api no instalado. Ejecutar: pip install earthengine-api")
        return False
    except Exception as e:
        log.error(f"[GEE] Error de inicialización: {e}")
        return False


# ─────────────────────────────────────────────────────────────────
# Sentinel-2
# ─────────────────────────────────────────────────────────────────

def buscar_imagen_s2(
    fecha_iso: str,
    boundary_geojson: dict,
    ventana_dias: int = 3,
    max_nubes: float = 20.0,
) -> Optional[object]:
    """
    Busca la imagen Sentinel-2 SR con menor nubosidad dentro de
    ±ventana_dias días alrededor de fecha_iso, sobre el lote indicado.

    Args:
        fecha_iso:       fecha en formato 'YYYY-MM-DD'
        boundary_geojson: polígono GeoJSON del lote
        ventana_dias:    días de búsqueda hacia atrás y adelante
        max_nubes:       % máximo de nubosidad aceptable

    Returns:
        ee.Image o None si no hay imagen disponible
    """
    import ee

    fecha  = ee.Date(fecha_iso)
    geom   = ee.Geometry(boundary_geojson)

    col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(
            fecha.advance(-ventana_dias, "day"),
            fecha.advance( ventana_dias, "day"),
        )
        .filterBounds(geom)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_nubes))
        .sort("CLOUDY_PIXEL_PERCENTAGE")   # mejor imagen primero
    )

    n = col.size().getInfo()
    if n == 0:
        log.warning(f"[GEE] Sin imagen S2 para {fecha_iso} ±{ventana_dias}d (nubes<{max_nubes}%)")
        return None

    imagen = col.first()
    props  = imagen.getInfo()["properties"]
    fecha_img = props.get("GENERATION_TIME", "")
    nubes     = props.get("CLOUDY_PIXEL_PERCENTAGE", "?")
    log.info(f"[GEE] Imagen S2 encontrada: {fecha_img[:10]}  nubes={nubes:.1f}%")
    return imagen


def extraer_bandas_punto(
    imagen,
    lat: float,
    lon: float,
    escala_m: int = 20,
) -> Optional[dict]:
    """
    Extrae valores de bandas B4, B8, B8A, B11, B12 en el punto (lat, lon).
    Usa escala 20m para B8A/B11 (resolución nativa de SWIR).

    Returns dict con reflectancias [0-1] o None si el punto cae fuera del imagen.
    """
    import ee

    punto = ee.Geometry.Point([lon, lat])
    bandas = ["B4", "B8", "B8A", "B11", "B12"]

    try:
        resultado = (
            imagen.select(bandas)
            .sample(region=punto, scale=escala_m, numPixels=1)
            .first()
            .getInfo()
        )
    except Exception as e:
        log.error(f"[GEE] Error extrayendo bandas en ({lat:.4f},{lon:.4f}): {e}")
        return None

    if resultado is None:
        log.warning(f"[GEE] Punto ({lat:.4f},{lon:.4f}) fuera del imagen o sin datos")
        return None

    props = resultado["properties"]
    # S2 SR: valores escalados ×10000 → dividir para reflectancia [0-1]
    return {
        "B4":  props.get("B4",  0) / 10000.0,
        "B8":  props.get("B8",  0) / 10000.0,
        "B8A": props.get("B8A", 0) / 10000.0,
        "B11": props.get("B11", 0) / 10000.0,
        "B12": props.get("B12", 0) / 10000.0,
    }


def extraer_bandas_campo(
    imagen,
    boundary_geojson: dict,
    escala_m: int = 10,
) -> list[dict]:
    """
    Extrae valores de bandas para TODOS los píxeles dentro del lote.
    Cada píxel es un punto de 10m×10m = un item en la lista retornada.

    Para 1/3 ha ≈ 33 píxeles → respuesta en ~2-5 segundos.
    Para 100 ha ≈ 10.000 píxeles → usar ee.batch.Export (ver nota).

    Returns lista de dicts {lat, lon, B4, B8, B8A, B11, B12}
    """
    import ee

    geom   = ee.Geometry(boundary_geojson)
    bandas = ["B4", "B8", "B8A", "B11", "B12"]

    try:
        pixels = (
            imagen.select(bandas)
            .sample(region=geom, scale=escala_m, geometries=True)
        )
        features = pixels.getInfo()["features"]
    except Exception as e:
        log.error(f"[GEE] Error extrayendo campo completo: {e}")
        return []

    resultados = []
    for f in features:
        props  = f["properties"]
        coords = f["geometry"]["coordinates"]   # [lon, lat]
        resultados.append({
            "lat": coords[1],
            "lon": coords[0],
            "B4":  props.get("B4",  0) / 10000.0,
            "B8":  props.get("B8",  0) / 10000.0,
            "B8A": props.get("B8A", 0) / 10000.0,
            "B11": props.get("B11", 0) / 10000.0,
            "B12": props.get("B12", 0) / 10000.0,
        })

    log.info(f"[GEE] Extraídos {len(resultados)} píxeles del lote")
    return resultados


# ─────────────────────────────────────────────────────────────────
# VPD desde ERA5 (para la fecha de la imagen Sentinel-2)
# ─────────────────────────────────────────────────────────────────

def obtener_vpd_era5(fecha_iso: str, lat: float, lon: float) -> float:
    """
    Obtiene VPD [kPa] del reanálisis ERA5 Daily para una fecha y ubicación.

    ERA5 en GEE: 'ECMWF/ERA5/DAILY'
      - mean_2m_air_temperature   [K]
      - dewpoint_2m_temperature   [K]

    VPD = es(T) - ea(Td)   donde es y ea se calculan con Magnus (Tetens):
      e = 0.6108 * exp(17.27 * T_C / (T_C + 237.3))   [kPa]

    Returns VPD en kPa. Fallback 2.0 kPa si ERA5 no tiene datos.
    """
    import ee

    fecha = ee.Date(fecha_iso)
    punto = ee.Geometry.Point([lon, lat])

    try:
        era5 = (
            ee.ImageCollection("ECMWF/ERA5/DAILY")
            .filterDate(fecha, fecha.advance(1, "day"))
            .select(["mean_2m_air_temperature", "dewpoint_2m_temperature"])
            .first()
        )
        vals = era5.sample(region=punto, scale=27830).first().getInfo()
    except Exception as e:
        log.warning(f"[GEE] ERA5 no disponible ({e}) — usando VPD=2.0 kPa")
        return 2.0

    if vals is None:
        return 2.0

    props = vals["properties"]
    T_k  = props.get("mean_2m_air_temperature",  298.0)
    Td_k = props.get("dewpoint_2m_temperature",   290.0)

    T_c  = T_k  - 273.15
    Td_c = Td_k - 273.15

    es  = 0.6108 * math.exp(17.27 * T_c  / (T_c  + 237.3))
    ea  = 0.6108 * math.exp(17.27 * Td_c / (Td_c + 237.3))
    vpd = max(0.0, round(es - ea, 3))

    log.info(f"[GEE] ERA5 VPD={vpd:.2f} kPa  T={T_c:.1f}°C  Td={Td_c:.1f}°C")
    return vpd


# ─────────────────────────────────────────────────────────────────
# Sentinel-1 SAR (fallback para días nublados) — TRL 5
# ─────────────────────────────────────────────────────────────────

def buscar_imagen_s1(
    fecha_iso: str,
    boundary_geojson: dict,
    ventana_dias: int = 6,
) -> Optional[object]:
    """
    Busca imagen Sentinel-1 SAR (banda C, VV+VH) como fallback cuando
    Sentinel-2 no tiene imagen útil por nubosidad.

    S1 no depende de luz solar ni condiciones atmosféricas.
    Sensible a humedad de suelo superficial (0-5cm) — proxy de riego reciente.

    Disponible en TRL 5 — activar cuando buscar_imagen_s2() retorna None.
    """
    import ee

    fecha = ee.Date(fecha_iso)
    geom  = ee.Geometry(boundary_geojson)

    col = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterDate(
            fecha.advance(-ventana_dias, "day"),
            fecha.advance( ventana_dias, "day"),
        )
        .filterBounds(geom)
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .sort("system:time_start", False)
    )

    n = col.size().getInfo()
    if n == 0:
        log.warning(f"[GEE] Sin imagen S1 para {fecha_iso} ±{ventana_dias}d")
        return None

    return col.first()
