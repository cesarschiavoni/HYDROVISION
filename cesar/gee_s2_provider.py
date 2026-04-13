"""
gee_s2_provider.py — Provider Sentinel-2 real vía Google Earth Engine
HydroVision AG | TRL 4

Adaptador entre gee_connector.py (llamadas crudas a GEE) y
_SatelliteFusionService (consumidor en app.py).

Funcionalidad:
  - Extrae bandas S2 reales en un punto (nodo o centroide de zona)
  - Masking per-pixel con banda SCL (Scene Classification Layer)
  - Cache SQLite para evitar llamadas repetidas a GEE
  - Fallback graceful: retorna None si GEE no está disponible

Cadena de fallback (manejada por _SatelliteFusionService en app.py):
  1. GEE real (fresco)  →  2. Cache (stale)  →  3. Sintético
"""

from __future__ import annotations

import datetime
import logging
from typing import Optional

log = logging.getLogger(__name__)

# Sentinel-2 SCL — valores aceptables (pixel claro)
_SCL_CLEAR = {4, 5, 6}  # 4=vegetación, 5=suelo, 6=agua


class GEE_S2Provider:
    """
    Provee Sentinel2Observation reales desde Google Earth Engine.

    Uso:
        provider = GEE_S2Provider(project="hydrovision-ag")
        if provider.is_available():
            obs = provider.get_observation_at_point(lat, lon, vpd, cwsi_nodo=0.45)
    """

    def __init__(
        self,
        project: str = "hydrovision-ag",
        cache_ttl_days: int = 5,
    ):
        self._available = False
        self._project = project
        self._cache_ttl = cache_ttl_days

        try:
            import os
            from gee_connector import init_gee
            # Proyecto GCloud: env var > parámetro > default
            gee_project = os.environ.get("GEE_PROJECT", project)
            self._available = init_gee(gee_project)
            if self._available:
                log.info("[GEE-S2] Provider inicializado OK")
        except Exception as e:
            log.warning(f"[GEE-S2] No disponible: {e}")

    def is_available(self) -> bool:
        return self._available

    # ── API principal ────────────────────────────────────────────────

    def get_observation_at_point(
        self,
        lat: float,
        lon: float,
        vpd_kpa: float,
        cwsi_nodo: float | None = None,
        fecha: str | None = None,
        ventana_dias: int = 10,
        max_nubes: float = 30.0,
    ):
        """
        Obtiene bandas S2 reales en un punto.

        Retorna Sentinel2Observation o None.
        Intenta: cache → GEE fresco → ventana ampliada → None.
        """
        if not self._available:
            return None

        from sentinel2_fusion import Sentinel2Observation

        fecha_str = fecha or datetime.date.today().isoformat()

        # 1. Check cache
        cached = self._check_cache(lat, lon, fecha_str)
        if cached:
            log.debug(f"[GEE-S2] Cache hit ({lat:.4f},{lon:.4f}) fecha={cached['fecha']}")
            return Sentinel2Observation(
                fecha=cached["fecha"],
                B4_red=cached["B4"], B8_nir=cached["B8"], B8A_nir=cached["B8A"],
                B11_swir=cached["B11"], B12_swir=cached["B12"],
                VPD_kPa=vpd_kpa, cwsi_nodo=cwsi_nodo,
            )

        # 2. Buscar imagen en GEE
        bands, img_fecha = self._fetch_from_gee(
            lat, lon, fecha_str, ventana_dias, max_nubes
        )

        # 3. Si no hay, ampliar ventana a 20 y luego 30 días
        if bands is None and ventana_dias < 20:
            bands, img_fecha = self._fetch_from_gee(
                lat, lon, fecha_str, 20, max_nubes + 10
            )
        if bands is None and ventana_dias < 30:
            bands, img_fecha = self._fetch_from_gee(
                lat, lon, fecha_str, 30, 50.0
            )

        if bands is None:
            log.warning(f"[GEE-S2] Sin imagen disponible para ({lat:.4f},{lon:.4f})")
            return None

        # 4. Guardar en cache
        self._store_cache(lat, lon, img_fecha, bands)

        return Sentinel2Observation(
            fecha=img_fecha,
            B4_red=bands["B4"], B8_nir=bands["B8"], B8A_nir=bands["B8A"],
            B11_swir=bands["B11"], B12_swir=bands["B12"],
            VPD_kPa=vpd_kpa, cwsi_nodo=cwsi_nodo,
        )

    def get_observation_for_zone(
        self,
        zona_id: int,
        lat: float,
        lon: float,
        vpd_kpa: float,
        fecha: str | None = None,
    ):
        """
        Obtiene bandas S2 reales para el centroide de una zona.
        TRL 4: usa extracción puntual en el centroide.
        TRL 5+: promediar píxeles del polígono completo.
        """
        return self.get_observation_at_point(
            lat, lon, vpd_kpa, cwsi_nodo=None, fecha=fecha,
        )

    # ── GEE fetch ────────────────────────────────────────────────────

    def _fetch_from_gee(
        self,
        lat: float,
        lon: float,
        fecha_str: str,
        ventana_dias: int,
        max_nubes: float,
    ) -> tuple[dict | None, str]:
        """
        Busca imagen S2, extrae bandas, verifica SCL.
        Retorna (bands_dict, fecha_imagen) o (None, "").
        """
        try:
            import ee
            from gee_connector import buscar_imagen_s2, extraer_bandas_punto

            # Geometría mínima alrededor del punto (buffer ~500m)
            punto = ee.Geometry.Point([lon, lat])
            boundary = punto.buffer(500).bounds().getInfo()

            imagen = buscar_imagen_s2(
                fecha_iso=fecha_str,
                boundary_geojson=boundary,
                ventana_dias=ventana_dias,
                max_nubes=max_nubes,
            )
            if imagen is None:
                return None, ""

            # Verificar SCL en el punto (cloud masking per-pixel)
            if not self._check_scl(imagen, lat, lon):
                log.info(f"[GEE-S2] Pixel nublado/sombra en ({lat:.4f},{lon:.4f}), descartando")
                return None, ""

            # Extraer bandas
            bands = extraer_bandas_punto(imagen, lat, lon, escala_m=20)
            if bands is None:
                return None, ""

            # Fecha de la imagen
            props = imagen.getInfo()["properties"]
            img_fecha = props.get("GENERATION_TIME", fecha_str)[:10]

            log.info(
                f"[GEE-S2] Bandas reales ({lat:.4f},{lon:.4f}): "
                f"B4={bands['B4']:.4f} B8={bands['B8']:.4f} B8A={bands['B8A']:.4f} "
                f"B11={bands['B11']:.4f} B12={bands['B12']:.4f} fecha={img_fecha}"
            )
            return bands, img_fecha

        except Exception as e:
            log.error(f"[GEE-S2] Error en fetch: {e}")
            return None, ""

    def _check_scl(self, imagen, lat: float, lon: float) -> bool:
        """
        Verifica Scene Classification Layer en el punto.
        Retorna True si el pixel es claro (vegetación/suelo).
        """
        try:
            import ee
            punto = ee.Geometry.Point([lon, lat])
            scl_sample = (
                imagen.select("SCL")
                .sample(region=punto, scale=20, numPixels=1)
                .first()
                .getInfo()
            )
            if scl_sample is None:
                return False
            scl_val = scl_sample.get("properties", {}).get("SCL", 0)
            clear = scl_val in _SCL_CLEAR
            if not clear:
                log.debug(f"[GEE-S2] SCL={scl_val} en ({lat:.4f},{lon:.4f}) — no claro")
            return clear
        except Exception as e:
            log.warning(f"[GEE-S2] Error leyendo SCL: {e}")
            return False

    # ── Cache SQLite ─────────────────────────────────────────────────

    def _cache_key(self, lat: float, lon: float) -> tuple[float, float]:
        """Redondea a 4 decimales (~11m, resolución S2)."""
        return round(lat, 4), round(lon, 4)

    def _check_cache(self, lat: float, lon: float, fecha: str) -> dict | None:
        """Busca en cache SQLite. Retorna dict con bandas o None."""
        try:
            import sys, os
            mvc_dir = os.path.join(os.path.dirname(__file__), "..", "mvc")
            if mvc_dir not in sys.path:
                sys.path.insert(0, os.path.abspath(mvc_dir))
            from models import SessionLocal, S2Cache

            db = SessionLocal()
            try:
                rlat, rlon = self._cache_key(lat, lon)
                cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=self._cache_ttl)
                row = (
                    db.query(S2Cache)
                    .filter(S2Cache.lat == rlat, S2Cache.lon == rlon)
                    .filter(S2Cache.fetched_at >= cutoff)
                    .order_by(S2Cache.fetched_at.desc())
                    .first()
                )
                if row:
                    return {
                        "fecha": row.fecha, "B4": row.B4, "B8": row.B8,
                        "B8A": row.B8A, "B11": row.B11, "B12": row.B12,
                    }
                return None
            finally:
                db.close()
        except Exception as e:
            log.debug(f"[GEE-S2] Cache read error: {e}")
            return None

    def _store_cache(self, lat: float, lon: float, fecha: str, bands: dict) -> None:
        """Almacena bandas en cache SQLite."""
        try:
            import sys, os
            mvc_dir = os.path.join(os.path.dirname(__file__), "..", "mvc")
            if mvc_dir not in sys.path:
                sys.path.insert(0, os.path.abspath(mvc_dir))
            from models import SessionLocal, S2Cache

            db = SessionLocal()
            try:
                rlat, rlon = self._cache_key(lat, lon)
                entry = S2Cache(
                    lat=rlat, lon=rlon, fecha=fecha,
                    B4=bands["B4"], B8=bands["B8"], B8A=bands["B8A"],
                    B11=bands["B11"], B12=bands["B12"],
                )
                db.add(entry)
                db.commit()
                log.debug(f"[GEE-S2] Cache store ({rlat},{rlon}) fecha={fecha}")
            finally:
                db.close()
        except Exception as e:
            log.debug(f"[GEE-S2] Cache write error: {e}")
