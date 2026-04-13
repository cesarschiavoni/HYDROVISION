"""
stac_s2_provider.py — Provider Sentinel-2 real vía Microsoft Planetary Computer
HydroVision AG | TRL 4

Accede a imágenes Sentinel-2 L2A (Surface Reflectance) sin necesidad de
cuenta, API key ni proyecto cloud.

Búsqueda: STAC API de Planetary Computer
Extracción: Point API de PC Data (devuelve valores directos, sin descargar COG)

Bandas extraídas:
  B04 (Red 665nm)    → B4_red   [reflectancia 0-1]
  B08 (NIR 842nm)    → B8_nir
  B8A (NIR 865nm)    → B8A_nir
  B11 (SWIR 1610nm)  → B11_swir
  B12 (SWIR 2190nm)  → B12_swir
  SCL (Scene Class)  → cloud masking per-pixel

Cadena de fallback (manejada por _SatelliteFusionService en app.py):
  1. STAC real (fresco) → 2. Cache SQLite → 3. Sintético
"""

from __future__ import annotations

import datetime
import logging
import requests as _requests

log = logging.getLogger(__name__)

# Planetary Computer STAC + Data API — no requiere autenticación
_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
_POINT_API = "https://planetarycomputer.microsoft.com/api/data/v1/item/point"
_COLLECTION = "sentinel-2-l2a"

# Sentinel-2 SCL — valores aceptables (pixel claro)
_SCL_CLEAR = {4, 5, 6}  # 4=vegetación, 5=suelo, 6=agua


class STAC_S2Provider:
    """
    Provee Sentinel2Observation reales desde Planetary Computer.
    Sin registro, sin API key, sin proyecto cloud.

    Uso:
        provider = STAC_S2Provider()
        if provider.is_available():
            obs = provider.get_observation_at_point(-31.20, -64.09, vpd=1.5)
    """

    def __init__(self, cache_ttl_days: int = 5):
        self._available = False
        self._cache_ttl = cache_ttl_days
        self._client = None

        try:
            import planetary_computer as pc
            from pystac_client import Client
            self._pc = pc
            self._client = Client.open(_STAC_URL, modifier=pc.sign_inplace)
            # Test de conectividad
            _ = self._client.get_collection(_COLLECTION)
            self._available = True
            log.info("[STAC-S2] Provider inicializado OK — Microsoft Planetary Computer")
        except Exception as e:
            log.warning(f"[STAC-S2] No disponible: {e}")

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
        """
        if not self._available:
            return None

        import sys, os
        cesar_dir = os.path.dirname(__file__)
        if cesar_dir not in sys.path:
            sys.path.insert(0, cesar_dir)
        from sentinel2_fusion import Sentinel2Observation

        fecha_str = fecha or datetime.date.today().isoformat()

        # 1. Check cache
        cached = self._check_cache(lat, lon, fecha_str)
        if cached:
            log.debug(f"[STAC-S2] Cache hit ({lat:.4f},{lon:.4f}) fecha={cached['fecha']}")
            return Sentinel2Observation(
                fecha=cached["fecha"],
                B4_red=cached["B4"], B8_nir=cached["B8"], B8A_nir=cached["B8A"],
                B11_swir=cached["B11"], B12_swir=cached["B12"],
                VPD_kPa=vpd_kpa, cwsi_nodo=cwsi_nodo,
            )

        # 2. Buscar y extraer desde STAC
        result = self._fetch(lat, lon, fecha_str, ventana_dias, max_nubes)

        # 3. Ampliar ventana progresivamente si no se encontró
        if result is None and ventana_dias < 20:
            result = self._fetch(lat, lon, fecha_str, 20, max_nubes + 10)
        if result is None:
            result = self._fetch(lat, lon, fecha_str, 30, 50.0)

        if result is None:
            log.warning(f"[STAC-S2] Sin imagen disponible para ({lat:.4f},{lon:.4f})")
            return None

        bands, img_fecha = result

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
        """Obtiene bandas S2 reales para el centroide de una zona."""
        return self.get_observation_at_point(
            lat, lon, vpd_kpa, cwsi_nodo=None, fecha=fecha,
        )

    # ── STAC fetch + Point API ───────────────────────────────────────

    def _fetch(
        self,
        lat: float,
        lon: float,
        fecha_str: str,
        ventana_dias: int,
        max_nubes: float,
    ) -> tuple[dict, str] | None:
        """
        Busca imagen S2, extrae bandas via Point API, verifica SCL.
        Retorna (bands_dict, fecha_imagen) o None.
        """
        try:
            fecha_dt = datetime.date.fromisoformat(fecha_str)
            start = (fecha_dt - datetime.timedelta(days=ventana_dias)).isoformat()
            end = (fecha_dt + datetime.timedelta(days=1)).isoformat()

            # Buscar items
            search = self._client.search(
                collections=[_COLLECTION],
                intersects={"type": "Point", "coordinates": [lon, lat]},
                datetime=f"{start}/{end}",
                query={"eo:cloud_cover": {"lt": max_nubes}},
                sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}],
                max_items=5,
            )

            items = list(search.items())
            if not items:
                log.debug(f"[STAC-S2] Sin imagenes ({lat:.4f},{lon:.4f}) "
                          f"{start}/{end} nubes<{max_nubes}%")
                return None

            # Probar cada item hasta encontrar pixel claro
            for item in items:
                # 1. Verificar SCL primero (más barato)
                scl = self._point_query(item.id, lon, lat, "SCL")
                if scl is not None:
                    scl_int = int(scl)
                    if scl_int not in _SCL_CLEAR:
                        log.debug(f"[STAC-S2] SCL={scl_int} en ({lat:.4f},{lon:.4f}), "
                                  f"descartando {item.id}")
                        continue

                # 2. Extraer bandas espectrales
                bands = {}
                all_ok = True
                for our_name, asset_name in [
                    ("B4", "B04"), ("B8", "B08"), ("B8A", "B8A"),
                    ("B11", "B11"), ("B12", "B12"),
                ]:
                    val = self._point_query(item.id, lon, lat, asset_name)
                    if val is None or val <= 0 or val > 20000:
                        all_ok = False
                        break
                    bands[our_name] = val / 10000.0  # reflectancia [0-1]

                if not all_ok:
                    continue

                img_fecha = item.datetime.strftime("%Y-%m-%d") if item.datetime else fecha_str
                log.info(
                    f"[STAC-S2] Bandas REALES ({lat:.4f},{lon:.4f}): "
                    f"B4={bands['B4']:.4f} B8={bands['B8']:.4f} "
                    f"B8A={bands['B8A']:.4f} B11={bands['B11']:.4f} "
                    f"B12={bands['B12']:.4f} fecha={img_fecha} "
                    f"item={item.id}"
                )
                return bands, img_fecha

            log.debug(f"[STAC-S2] Todos los items nublados/invalidos")
            return None

        except Exception as e:
            log.error(f"[STAC-S2] Error en fetch: {e}")
            return None

    def _point_query(
        self, item_id: str, lon: float, lat: float, asset: str,
    ) -> float | None:
        """
        Consulta el valor de un pixel via Planetary Computer Point API.
        No requiere rasterio ni GDAL — es un HTTP GET puro.

        Retorna el valor numérico crudo o None.
        """
        try:
            url = f"{_POINT_API}/{lon},{lat}"
            resp = _requests.get(url, params={
                "collection": _COLLECTION,
                "item": item_id,
                "assets": asset,
            }, timeout=15)

            if resp.status_code != 200:
                return None

            data = resp.json()
            values = data.get("values", [])
            if not values:
                return None

            return float(values[0])

        except Exception as e:
            log.debug(f"[STAC-S2] Point query error ({asset}): {e}")
            return None

    # ── Cache SQLite ─────────────────────────────────────────────────

    def _cache_key(self, lat: float, lon: float) -> tuple[float, float]:
        """Redondea a 4 decimales (~11m, resolución S2)."""
        return round(lat, 4), round(lon, 4)

    def _check_cache(self, lat: float, lon: float, fecha: str) -> dict | None:
        """Busca en cache SQLite."""
        try:
            import sys, os
            mvc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mvc"))
            if mvc_dir not in sys.path:
                sys.path.insert(0, mvc_dir)
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
            log.debug(f"[STAC-S2] Cache read error: {e}")
            return None

    def _store_cache(self, lat: float, lon: float, fecha: str, bands: dict) -> None:
        """Almacena bandas en cache SQLite."""
        try:
            import sys, os
            mvc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mvc"))
            if mvc_dir not in sys.path:
                sys.path.insert(0, mvc_dir)
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
                log.debug(f"[STAC-S2] Cache store ({rlat},{rlon}) fecha={fecha}")
            finally:
                db.close()
        except Exception as e:
            log.debug(f"[STAC-S2] Cache write error: {e}")
