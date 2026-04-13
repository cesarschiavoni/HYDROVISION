"""
pipeline_satelital.py — Pipeline de extrapolación satelital HydroVision AG

Integra datos de nodos de campo con Sentinel-2 via GEE para generar
mapas de estrés hídrico de campo completo.

Flujo completo:
    1. Recibe payload JSON del nodo (MQTT backend → aquí)
    2. Registra posición GPS del nodo (primer payload)
    3. Busca imagen Sentinel-2 coincidente (±3 días, nubes < 20%)
    4. Extrae bandas espectrales en la ubicación del nodo
    5. Obtiene VPD del día desde ERA5 (misma fuente climática)
    6. Acumula par (CWSI_nodo, NDWI/NDRE/VPD) para calibración
    7. Recalibra el modelo cuando hay ≥ 10 pares
    8. Genera mapa CWSI de campo completo en cada nueva imagen

Uso:
    from pipeline_satelital import PipelineSatelital

    pipeline = PipelineSatelital()
    pipeline.procesar_payload(payload_json_string)   # llamar por cada mensaje MQTT
    mapa = pipeline.generar_mapa_hoy()               # mapa del día si hay imagen nueva
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from field_config import (
    FIELD_BOUNDARY, NODES, OUTPUT_DIR,
    S2_MAX_CLOUD_PCT, S2_VENTANA_DIAS, S2_SCALE_M, S2_NDVI_VEG_UMBRAL,
    GEE_PROJECT, registrar_nodo, nodo_conocido,
)
from gee_connector import (
    init_gee, buscar_imagen_s2, extraer_bandas_punto,
    extraer_bandas_campo, obtener_vpd_era5,
)
from sentinel2_fusion import Sentinel2Observation, CWSINDWICorrelationModel

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class PipelineSatelital:
    """
    Orquesta la calibración y extrapolación CWSI↔Sentinel-2.

    Mantiene un modelo por nodo (cada zona hídrica tiene su propia
    correlación CWSI↔NDWI porque el suelo y microclima varían).
    """

    def __init__(self, gee_project: str = GEE_PROJECT):
        self._gee_ok = init_gee(gee_project)
        # Un modelo de correlación por nodo
        self._modelos: dict[str, CWSINDWICorrelationModel] = {}
        # Observaciones acumuladas por nodo: {node_id: [Sentinel2Observation]}
        self._observaciones: dict[str, list[Sentinel2Observation]] = {}
        # Cache de última imagen S2 procesada (evita llamadas duplicadas)
        self._ultima_imagen_fecha: Optional[str] = None
        self._ultima_imagen_obj = None

        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # ─────────────────────────────────────────────────────────────
    # Ingesta de telemetría del nodo
    # ─────────────────────────────────────────────────────────────

    def procesar_payload(self, payload_raw: str | dict) -> Optional[Sentinel2Observation]:
        """
        Procesa un payload JSON del nodo.
        Si hay imagen S2 disponible para esa fecha, genera un par de calibración.

        Args:
            payload_raw: string JSON o dict del payload v1 del nodo

        Returns:
            Sentinel2Observation con cwsi_nodo si se encontró imagen S2,
            None si no hay imagen disponible o calidad_captura != 'ok'.
        """
        if not self._gee_ok:
            log.error("GEE no inicializado — no se puede procesar payload")
            return None

        payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw

        # Validar calidad de captura
        calidad = payload.get("calidad_captura", "ok")
        if calidad != "ok":
            log.info(f"[PIPE] Payload {payload.get('node_id')} ignorado — calidad={calidad}")
            return None

        node_id = payload.get("node_id", "")
        ts      = payload.get("ts", 0)
        fecha   = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")

        # GPS del nodo
        gps     = payload.get("gps", {})
        lat     = gps.get("lat")
        lon     = gps.get("lon")
        if lat is None or lon is None:
            log.warning(f"[PIPE] {node_id}: sin GPS en payload")
            return None

        # Registrar posición del nodo si es nuevo
        if not nodo_conocido(node_id):
            registrar_nodo(node_id, lat, lon)
            log.info(f"[PIPE] Nodo registrado: {node_id} ({lat:.5f}, {lon:.5f})")

        # CWSI del nodo
        thermal = payload.get("thermal", {})
        cwsi    = thermal.get("cwsi")
        if cwsi is None or cwsi < 0:
            log.info(f"[PIPE] {node_id}: CWSI no disponible (baselines no calibrados)")
            return None

        # Buscar imagen Sentinel-2
        imagen = self._obtener_imagen_s2(fecha)
        if imagen is None:
            return None

        # Extraer bandas en el punto del nodo
        bandas = extraer_bandas_punto(imagen, lat, lon, escala_m=S2_SCALE_M)
        if bandas is None:
            return None

        # VPD del día (ERA5)
        vpd = obtener_vpd_era5(fecha, lat, lon)

        # Construir observación
        obs = Sentinel2Observation(
            fecha    = fecha,
            B4_red   = bandas["B4"],
            B8_nir   = bandas["B8"],
            B8A_nir  = bandas["B8A"],
            B11_swir = bandas["B11"],
            B12_swir = bandas["B12"],
            VPD_kPa  = vpd,
            cwsi_nodo = float(cwsi),
        )

        # Acumular
        if node_id not in self._observaciones:
            self._observaciones[node_id] = []
        self._observaciones[node_id].append(obs)

        n = len(self._observaciones[node_id])
        log.info(
            f"[PIPE] {node_id}: par #{n} — CWSI={cwsi:.3f} "
            f"NDWI={obs.NDWI:.3f} VPD={vpd:.2f}kPa"
        )

        # Recalibrar modelo si hay suficientes pares
        self._recalibrar(node_id)

        return obs

    # ─────────────────────────────────────────────────────────────
    # Generación del mapa de campo completo
    # ─────────────────────────────────────────────────────────────

    def generar_mapa(
        self,
        fecha: Optional[str] = None,
        guardar: bool = True,
    ) -> Optional[dict]:
        """
        Genera mapa CWSI de campo completo para la fecha dada
        (o la última imagen disponible si fecha=None).

        Requiere que al menos UN nodo tenga el modelo calibrado.

        Returns:
            dict con cwsi_mean, cwsi_std, cwsi_p90, n_pixels_veg,
            y array cwsi_all (un valor por píxel del lote)
        """
        if not self._gee_ok:
            return None

        modelos_ok = {nid: m for nid, m in self._modelos.items() if m.is_calibrated}
        if not modelos_ok:
            log.warning("[PIPE] Ningún modelo calibrado aún — se necesitan ≥10 pares")
            return None

        fecha_buscar = fecha or datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        imagen = self._obtener_imagen_s2(fecha_buscar)
        if imagen is None:
            return None

        # Extraer todos los píxeles del lote
        pixels = extraer_bandas_campo(imagen, FIELD_BOUNDARY, escala_m=S2_SCALE_M)
        if not pixels:
            log.warning("[PIPE] Sin píxeles extraídos del lote")
            return None

        # Obtener VPD del centroide del lote
        coords = FIELD_BOUNDARY["coordinates"][0]
        lat_c  = sum(c[1] for c in coords) / len(coords)
        lon_c  = sum(c[0] for c in coords) / len(coords)
        vpd    = obtener_vpd_era5(fecha_buscar, lat_c, lon_c)

        # Construir observaciones para cada píxel
        obs_campo = [
            Sentinel2Observation(
                fecha    = fecha_buscar,
                B4_red   = p["B4"],
                B8_nir   = p["B8"],
                B8A_nir  = p["B8A"],
                B11_swir = p["B11"],
                B12_swir = p["B12"],
                VPD_kPa  = vpd,
            )
            for p in pixels
        ]

        # Usar el mejor modelo disponible (mayor R²)
        mejor_modelo = max(
            modelos_ok.values(),
            key=lambda m: m.calibration_score.get("R2", 0),
        )
        mejor_nodo = max(
            modelos_ok.keys(),
            key=lambda nid: modelos_ok[nid].calibration_score.get("R2", 0),
        )

        coords_campo = [(p["lat"], p["lon"]) for p in pixels]
        mapa = mejor_modelo.generate_field_cwsi_map(
            obs_campo,
            field_coords=coords_campo,
        )
        mapa["fecha"] = fecha_buscar
        mapa["modelo_nodo"] = mejor_nodo
        mapa["modelo_r2"] = mejor_modelo.calibration_score.get("R2", None)
        mapa["vpd_dia"] = vpd
        mapa["n_nodos_calibrados"] = len(modelos_ok)

        log.info(
            f"[PIPE] Mapa generado {fecha_buscar}: "
            f"CWSI_medio={mapa['cwsi_mean']:.3f} "
            f"P90={mapa['cwsi_p90']:.3f} "
            f"({mapa['n_pixels_veg']} píxeles veg) "
            f"R²_modelo={mapa['modelo_r2']:.3f}"
        )

        if guardar:
            self._guardar_reporte(mapa)

        return mapa

    # ─────────────────────────────────────────────────────────────
    # Estado del pipeline
    # ─────────────────────────────────────────────────────────────

    def estado(self) -> dict:
        """Retorna el estado de calibración de todos los nodos."""
        return {
            node_id: {
                "n_pares":    len(self._observaciones.get(node_id, [])),
                "calibrado":  self._modelos[node_id].is_calibrated if node_id in self._modelos else False,
                "R2":         self._modelos[node_id].calibration_score.get("R2") if node_id in self._modelos else None,
                "lat":        NODES.get(node_id, {}).get("lat"),
                "lon":        NODES.get(node_id, {}).get("lon"),
            }
            for node_id in set(list(self._observaciones.keys()) + list(self._modelos.keys()))
        }

    # ─────────────────────────────────────────────────────────────
    # Internos
    # ─────────────────────────────────────────────────────────────

    def _obtener_imagen_s2(self, fecha: str):
        """Usa cache para no llamar GEE dos veces para la misma fecha."""
        if fecha == self._ultima_imagen_fecha and self._ultima_imagen_obj is not None:
            return self._ultima_imagen_obj
        imagen = buscar_imagen_s2(
            fecha, FIELD_BOUNDARY,
            ventana_dias=S2_VENTANA_DIAS,
            max_nubes=S2_MAX_CLOUD_PCT,
        )
        self._ultima_imagen_fecha = fecha
        self._ultima_imagen_obj   = imagen
        return imagen

    def _recalibrar(self, node_id: str) -> None:
        """Recalibra el modelo del nodo si hay suficientes observaciones."""
        obs = self._observaciones.get(node_id, [])
        min_pts = CWSINDWICorrelationModel.MIN_CALIBRATION_POINTS

        if len(obs) < min_pts:
            return

        if node_id not in self._modelos:
            self._modelos[node_id] = CWSINDWICorrelationModel(poly_degree=2)

        try:
            score = self._modelos[node_id].calibrate(obs)
            log.info(
                f"[PIPE] Modelo {node_id} recalibrado: "
                f"R²={score['R2']:.3f} MAE={score['MAE']:.4f} "
                f"n={score['n_points']}"
            )
        except ValueError as e:
            log.warning(f"[PIPE] No se pudo calibrar {node_id}: {e}")

    def _guardar_reporte(self, mapa: dict) -> None:
        """Guarda reporte JSON del mapa generado."""
        fname = Path(OUTPUT_DIR) / f"mapa_{mapa['fecha']}.json"
        reporte = {
            "fecha":             mapa["fecha"],
            "cwsi_mean":         mapa["cwsi_mean"],
            "cwsi_std":          mapa["cwsi_std"],
            "cwsi_p90":          mapa["cwsi_p90"],
            "n_pixels_total":    mapa["n_pixels_total"],
            "n_pixels_veg":      mapa["n_pixels_veg"],
            "vpd_dia":           mapa["vpd_dia"],
            "modelo_nodo":       mapa["modelo_nodo"],
            "modelo_r2":         mapa["modelo_r2"],
            "n_nodos_calibrados": mapa["n_nodos_calibrados"],
        }
        with open(fname, "w") as f:
            json.dump(reporte, f, indent=2)
        log.info(f"[PIPE] Reporte guardado: {fname}")


# ─────────────────────────────────────────────────────────────────
# Demo / test con datos sintéticos
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from sentinel2_fusion import generate_synthetic_sentinel2_dataset

    print("=" * 60)
    print("Pipeline Satelital HydroVision AG — Demo sintético")
    print("=" * 60)

    # Simular payloads de 2 nodos durante una temporada
    import random
    random.seed(42)
    pipeline = PipelineSatelital.__new__(PipelineSatelital)
    pipeline._gee_ok = False   # modo offline con datos sintéticos
    pipeline._modelos = {}
    pipeline._observaciones = {}
    pipeline._ultima_imagen_fecha = None
    pipeline._ultima_imagen_obj = None

    # Generar observaciones sintéticas y cargarlas directamente
    obs_sinteticas = generate_synthetic_sentinel2_dataset(n_obs=60, seed=42)

    for nodo in ["HV-A1B2C3D4E5", "HV-F6G7H8I9J0"]:
        pipeline._observaciones[nodo] = obs_sinteticas[:50]
        pipeline._modelos[nodo] = CWSINDWICorrelationModel(poly_degree=2)
        score = pipeline._modelos[nodo].calibrate(obs_sinteticas[:50])
        print(f"\nNodo {nodo}:")
        print(f"  R²   = {score['R2']:.3f}")
        print(f"  MAE  = {score['MAE']:.4f}")
        print(f"  Pares calibración = {score['n_points']}")

    print("\nEstado del pipeline:")
    for nid, est in pipeline.estado().items():
        print(f"  {nid}: calibrado={est['calibrado']} R²={est['R2']:.3f} pares={est['n_pares']}")

    print("\n✓ Pipeline satelital operativo (GEE se activa con credenciales reales)")
