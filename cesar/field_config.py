"""
field_config.py — Configuración del campo y nodos HydroVision AG
Colonia Caroya, Córdoba — Viñedo experimental Malbec

CONFIGURAR ANTES DE CORRER:
  1. FIELD_BOUNDARY: reemplazar con el polígono real del lote
     (Javier marca las 4 esquinas con Google Maps → compartir ubicación)
  2. NODES: las coordenadas GPS se completan automáticamente desde
     el primer payload JSON de cada nodo (campo "gps")
  3. GEE_PROJECT: nombre del proyecto en Google Earth Engine
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────
# Proyecto GEE
# ─────────────────────────────────────────────────────────────────
GEE_PROJECT = "hydrovision-ag"   # cambiar al nombre real del proyecto GEE

# ─────────────────────────────────────────────────────────────────
# Polígono del lote (GeoJSON)
# PLACEHOLDER — coordenadas aproximadas de Colonia Caroya
# Reemplazar con el polígono real del viñedo experimental
# ─────────────────────────────────────────────────────────────────
FIELD_BOUNDARY = {
    "type": "Polygon",
    "coordinates": [[
        [-64.0930, -31.2015],   # NO
        [-64.0905, -31.2015],   # NE
        [-64.0905, -31.2033],   # SE
        [-64.0930, -31.2033],   # SO
        [-64.0930, -31.2015],   # cierre
    ]]
}

# ─────────────────────────────────────────────────────────────────
# Nodos del experimento TRL 4
# lat/lon se actualizan automáticamente desde el primer payload
# ─────────────────────────────────────────────────────────────────
NODES: dict[str, dict] = {
    # node_id: {"lat": float, "lon": float, "zona": str}
    # Se poblan automáticamente cuando el nodo envía su primer ciclo
}

# ─────────────────────────────────────────────────────────────────
# Temporada activa de monitoreo (Malbec Colonia Caroya)
# ─────────────────────────────────────────────────────────────────
SEASON_START = "10-01"   # MM-DD — inicio acumulación (1 octubre)
SEASON_END   = "03-31"   # MM-DD — fin temporada (31 marzo)

# ─────────────────────────────────────────────────────────────────
# Parámetros Sentinel-2
# ─────────────────────────────────────────────────────────────────
S2_MAX_CLOUD_PCT  = 20     # % nubosidad máxima aceptable por escena
S2_VENTANA_DIAS   = 3      # buscar imagen ±3 días de la observación del nodo
S2_SCALE_M        = 10     # resolución de muestreo en metros
S2_NDVI_VEG_UMBRAL = 0.30  # píxeles con NDVI < 0.30 se excluyen del mapa

# ─────────────────────────────────────────────────────────────────
# Directorio de salida (mapas GeoTIFF + reportes)
# ─────────────────────────────────────────────────────────────────
OUTPUT_DIR = r"D:\Models Agro\mapas_estres"


def registrar_nodo(node_id: str, lat: float, lon: float, zona: str = "") -> None:
    """Registra o actualiza la posición GPS de un nodo."""
    NODES[node_id] = {"lat": lat, "lon": lon, "zona": zona}


def nodo_conocido(node_id: str) -> bool:
    return node_id in NODES and NODES[node_id].get("lat") is not None
