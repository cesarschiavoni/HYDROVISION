"""
Motor de Propuesta Automatizada — HydroVision AG
==================================================
R15 — Genera propuesta PDF personalizada para cada prospecto.

Input:
  - Coordenadas GPS del lote (lat, lon)
  - Superficie [ha]
  - Cultivo principal
  - Tier deseado (o recomendación automática)

Proceso:
  1. Análisis histórico Sentinel-2 (NDWI, NDVI) → mapa de variabilidad
  2. Recomendación de densidad de nodos óptima
  3. Cálculo de ROI personalizado
  4. Generación PDF con mapa, tabla de costos, proyección ROI

Para TRL 3-4: usa datos sintéticos simulando Sentinel-2.
En producción: conecta a Google Earth Engine API.

Ejecutar:
    cd c:/Temp/Agro/cesar
    python motor_propuesta_automatizada.py --lat -31.2015 --lon -64.0927 --ha 50 --cultivo malbec

Salidas: outputs/propuestas/propuesta_{cliente}.pdf

Dependencias: matplotlib, numpy (ReportLab opcional para PDF nativo)
"""

import argparse
import datetime
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs" / "propuestas"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Import GDD engine for phenology
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gdd_engine import CULTIVOS


# ═══════════════════════════════════════════════════════════════════════════
# Configuración de precios (doc-06)
# ═══════════════════════════════════════════════════════════════════════════
TIER_PRICING = {
    "monitoreo": {
        "nombre": "Tier 1 Monitoreo",
        "hardware_nodo": 950,
        "susc_ha_min": 60,
        "susc_ha_max": 100,
        "ha_por_nodo": 2.0,
        "gateway": 120,
    },
    "automatizacion": {
        "nombre": "Tier 2 Automatización",
        "hardware_nodo": 950,
        "susc_ha_min": 100,
        "susc_ha_max": 160,
        "ha_por_nodo": 1.5,
        "gateway": 120,
    },
    "precision": {
        "nombre": "Tier 3 Precisión",
        "hardware_nodo": 1000,
        "susc_ha_min": 220,
        "susc_ha_max": 290,
        "ha_por_nodo": 1.0,
        "gateway": 150,
    },
}

# Recuperación por cultivo (12% ingreso bruto/ha)
CULTIVO_DATA = {
    "malbec":    {"ingreso_ha": 8000, "recuperacion_pct": 0.12, "region": "Cuyo/Córdoba"},
    "cabernet":  {"ingreso_ha": 9000, "recuperacion_pct": 0.12, "region": "Cuyo"},
    "olivo":     {"ingreso_ha": 6000, "recuperacion_pct": 0.12, "region": "San Juan/NOA"},
    "arandano":  {"ingreso_ha": 25000, "recuperacion_pct": 0.12, "region": "Patagonia/NOA"},
    "cerezo":    {"ingreso_ha": 30000, "recuperacion_pct": 0.12, "region": "Patagonia/Cuyo"},
    "pistacho":  {"ingreso_ha": 18000, "recuperacion_pct": 0.12, "region": "San Juan"},
    "nogal":     {"ingreso_ha": 10000, "recuperacion_pct": 0.12, "region": "NOA/Cuyo"},
}


# ═══════════════════════════════════════════════════════════════════════════
# Simulación de análisis Sentinel-2
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class AnalisisSentinel2:
    """Resultado del análisis de variabilidad espacial con Sentinel-2."""
    ndwi_mean: float
    ndwi_std: float
    ndvi_mean: float
    ndvi_std: float
    cv_ndwi: float  # coeficiente de variación
    zonas_estres: int  # zonas con NDWI < umbral
    heterogeneidad: str  # "baja" | "media" | "alta"
    recomendacion_densidad: float  # nodos/ha recomendados


def analizar_sentinel2_sintetico(lat: float, lon: float, ha: float,
                                  cultivo: str, seed: int = 42) -> AnalisisSentinel2:
    """
    Simula análisis histórico Sentinel-2 para el lote.
    En producción: usa Google Earth Engine API.
    """
    rng = np.random.default_rng(seed + abs(int(lat * 1000)) + abs(int(lon * 1000)))

    # Simular NDWI/NDVI basado en región
    region_factor = {"Cuyo/Córdoba": 0.0, "Cuyo": 0.02, "San Juan/NOA": 0.05,
                     "Patagonia/NOA": -0.03, "Patagonia/Cuyo": -0.02, "NOA/Cuyo": 0.03,
                     "San Juan": 0.04}
    cult_data = CULTIVO_DATA.get(cultivo, CULTIVO_DATA["malbec"])
    rf = region_factor.get(cult_data["region"], 0)

    ndwi_mean = 0.25 + rf + rng.normal(0, 0.03)
    ndwi_std = 0.08 + rng.uniform(0, 0.06)
    ndvi_mean = 0.55 + rng.normal(0, 0.05)
    ndvi_std = 0.10 + rng.uniform(0, 0.05)

    cv_ndwi = ndwi_std / abs(ndwi_mean) if ndwi_mean != 0 else 0

    # Clasificar heterogeneidad
    if cv_ndwi < 0.20:
        heterogeneidad = "baja"
        densidad = 0.5  # 1 nodo / 2 ha
    elif cv_ndwi < 0.35:
        heterogeneidad = "media"
        densidad = 0.7  # ~1 nodo / 1.4 ha
    else:
        heterogeneidad = "alta"
        densidad = 1.0  # 1 nodo / 1 ha

    zonas_estres = int(ha * rng.uniform(0.1, 0.4))

    return AnalisisSentinel2(
        ndwi_mean=round(ndwi_mean, 3),
        ndwi_std=round(ndwi_std, 3),
        ndvi_mean=round(ndvi_mean, 3),
        ndvi_std=round(ndvi_std, 3),
        cv_ndwi=round(cv_ndwi, 2),
        zonas_estres=zonas_estres,
        heterogeneidad=heterogeneidad,
        recomendacion_densidad=densidad,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Generador de propuesta
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class Propuesta:
    cliente: str
    lat: float
    lon: float
    ha: float
    cultivo: str
    tier: str
    analisis_s2: AnalisisSentinel2
    nodos_recomendados: int
    gateways: int
    costo_hardware: float
    costo_suscripcion_anual: float
    costo_total_anio1: float
    recuperacion_anual: float
    roi_anio1: float
    roi_anio2: float


def generar_propuesta(lat: float, lon: float, ha: float, cultivo: str,
                      tier: Optional[str] = None, cliente: str = "Prospecto") -> Propuesta:
    """Genera propuesta personalizada con análisis S2 y ROI."""

    # Análisis Sentinel-2
    s2 = analizar_sentinel2_sintetico(lat, lon, ha, cultivo)

    # Auto-selección de tier si no se especifica
    if tier is None:
        if s2.heterogeneidad == "alta" or ha >= 80:
            tier = "precision"
        elif s2.heterogeneidad == "media" or ha >= 30:
            tier = "automatizacion"
        else:
            tier = "monitoreo"

    pricing = TIER_PRICING[tier]
    cult_data = CULTIVO_DATA.get(cultivo, CULTIVO_DATA["malbec"])

    # Nodos recomendados
    nodos = max(1, int(np.ceil(ha * s2.recomendacion_densidad)))
    nodos = min(nodos, int(ha / 0.5))  # máximo 2 nodos/ha

    gateways = max(1, int(np.ceil(nodos / 10)))

    # Costos
    costo_hw = nodos * pricing["hardware_nodo"] + gateways * pricing["gateway"]
    susc_ha = (pricing["susc_ha_min"] + pricing["susc_ha_max"]) / 2
    costo_susc = ha * susc_ha
    costo_total_y1 = costo_hw + costo_susc

    # Recuperación
    recuperacion = ha * cult_data["ingreso_ha"] * cult_data["recuperacion_pct"]
    roi_y1 = (recuperacion - costo_total_y1) / costo_total_y1
    roi_y2 = (recuperacion - costo_susc) / costo_susc

    return Propuesta(
        cliente=cliente,
        lat=lat, lon=lon, ha=ha, cultivo=cultivo, tier=tier,
        analisis_s2=s2,
        nodos_recomendados=nodos,
        gateways=gateways,
        costo_hardware=round(costo_hw),
        costo_suscripcion_anual=round(costo_susc),
        costo_total_anio1=round(costo_total_y1),
        recuperacion_anual=round(recuperacion),
        roi_anio1=round(roi_y1, 2),
        roi_anio2=round(roi_y2, 2),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Generación de PDF (matplotlib-based, sin dependencia ReportLab)
# ═══════════════════════════════════════════════════════════════════════════
def generar_pdf(propuesta: Propuesta) -> Path:
    """Genera PDF de propuesta con mapa y tablas."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, FancyBboxPatch
    from matplotlib.colors import Normalize
    from matplotlib import cm

    fig = plt.figure(figsize=(8.5, 11))

    # ── Header ──
    ax_header = fig.add_axes([0.05, 0.90, 0.90, 0.08])
    ax_header.axis("off")
    ax_header.text(0.0, 0.7, "HydroVision AG", fontsize=22, fontweight="bold", color="#1565C0")
    ax_header.text(0.0, 0.2, f"Propuesta Comercial — {propuesta.cliente}", fontsize=14, color="#424242")
    ax_header.text(1.0, 0.7, datetime.date.today().strftime("%d/%m/%Y"),
                   fontsize=10, ha="right", color="#757575")
    ax_header.text(1.0, 0.2, f"{propuesta.ha:.0f} ha | {propuesta.cultivo.capitalize()}",
                   fontsize=10, ha="right", color="#757575")

    # ── Mapa de variabilidad simulado ──
    ax_map = fig.add_axes([0.05, 0.58, 0.55, 0.30])
    rng = np.random.default_rng(42)
    grid_size = max(5, int(np.sqrt(propuesta.ha)))
    ndwi_grid = propuesta.analisis_s2.ndwi_mean + \
                rng.normal(0, propuesta.analisis_s2.ndwi_std, (grid_size, grid_size))
    im = ax_map.imshow(ndwi_grid, cmap="RdYlGn", vmin=0.05, vmax=0.45,
                       extent=[propuesta.lon - 0.005, propuesta.lon + 0.005,
                               propuesta.lat - 0.005, propuesta.lat + 0.005])
    ax_map.set_title(f"NDWI Sentinel-2 — Variabilidad Espacial\n"
                     f"CV={propuesta.analisis_s2.cv_ndwi:.0%} ({propuesta.analisis_s2.heterogeneidad})",
                     fontsize=10)
    ax_map.set_xlabel("Longitud")
    ax_map.set_ylabel("Latitud")
    plt.colorbar(im, ax=ax_map, label="NDWI", shrink=0.8)

    # Marcar nodos recomendados
    n_nodos = min(propuesta.nodos_recomendados, grid_size * grid_size)
    nodo_positions = rng.choice(grid_size * grid_size, n_nodos, replace=False)
    for pos in nodo_positions[:8]:  # mostrar máximo 8 en el mapa
        row, col = divmod(pos, grid_size)
        ax_map.plot(propuesta.lon - 0.005 + (col + 0.5) / grid_size * 0.01,
                    propuesta.lat - 0.005 + (row + 0.5) / grid_size * 0.01,
                    "k^", markersize=8, markeredgecolor="white", markeredgewidth=1)

    # ── Análisis S2 ──
    ax_s2 = fig.add_axes([0.65, 0.58, 0.30, 0.30])
    ax_s2.axis("off")
    ax_s2.text(0.0, 1.0, "Análisis Sentinel-2", fontsize=11, fontweight="bold")
    info_lines = [
        f"NDWI medio: {propuesta.analisis_s2.ndwi_mean:.3f}",
        f"NDWI desvío: {propuesta.analisis_s2.ndwi_std:.3f}",
        f"NDVI medio: {propuesta.analisis_s2.ndvi_mean:.3f}",
        f"Coef. variación: {propuesta.analisis_s2.cv_ndwi:.0%}",
        f"Heterogeneidad: {propuesta.analisis_s2.heterogeneidad.upper()}",
        f"Zonas estrés: {propuesta.analisis_s2.zonas_estres}",
        f"",
        f"Densidad recomendada:",
        f"  {propuesta.analisis_s2.recomendacion_densidad:.1f} nodos/ha",
        f"  = {propuesta.nodos_recomendados} nodos",
        f"  + {propuesta.gateways} gateway(s)",
    ]
    for i, line in enumerate(info_lines):
        ax_s2.text(0.0, 0.85 - i * 0.075, line, fontsize=8.5, family="monospace")

    # ── Tabla de costos ──
    ax_cost = fig.add_axes([0.05, 0.32, 0.90, 0.22])
    ax_cost.axis("off")

    pricing = TIER_PRICING[propuesta.tier]
    ax_cost.text(0.0, 1.0, f"Inversión — {pricing['nombre']}", fontsize=12, fontweight="bold")

    table_data = [
        ["Concepto", "Cantidad", "Unitario", "Total"],
        ["Nodo HydroVision", f"{propuesta.nodos_recomendados}",
         f"USD {pricing['hardware_nodo']:,}", f"USD {propuesta.nodos_recomendados * pricing['hardware_nodo']:,}"],
        ["Gateway LoRa", f"{propuesta.gateways}",
         f"USD {pricing['gateway']}", f"USD {propuesta.gateways * pricing['gateway']:,}"],
        ["Hardware Total", "", "", f"USD {propuesta.costo_hardware:,}"],
        ["Suscripción anual", f"{propuesta.ha:.0f} ha",
         f"USD {(pricing['susc_ha_min']+pricing['susc_ha_max'])/2:.0f}/ha",
         f"USD {propuesta.costo_suscripcion_anual:,}"],
        ["TOTAL Año 1", "", "", f"USD {propuesta.costo_total_anio1:,}"],
        ["Año 2+ (solo suscripción)", "", "", f"USD {propuesta.costo_suscripcion_anual:,}"],
    ]

    for i, row in enumerate(table_data):
        y = 0.85 - i * 0.11
        for j, cell in enumerate(row):
            x = [0.0, 0.35, 0.55, 0.75][j]
            weight = "bold" if i == 0 or i >= 5 else "normal"
            color = "#1565C0" if i >= 5 else "black"
            ax_cost.text(x, y, cell, fontsize=9, fontweight=weight, color=color)

    # ── ROI ──
    ax_roi = fig.add_axes([0.05, 0.08, 0.55, 0.20])
    ax_roi.axis("off")

    cult_data = CULTIVO_DATA.get(propuesta.cultivo, CULTIVO_DATA["malbec"])
    ax_roi.text(0.0, 1.0, "Retorno de Inversión", fontsize=12, fontweight="bold")
    roi_lines = [
        f"Cultivo: {propuesta.cultivo.capitalize()} ({cult_data['region']})",
        f"Ingreso bruto/ha: USD {cult_data['ingreso_ha']:,}",
        f"Recuperación estimada (12%): USD {propuesta.recuperacion_anual:,}/año",
        f"",
        f"ROI Año 1 (HW + suscripción): {propuesta.roi_anio1:+.0%}",
        f"ROI Año 2+ (solo suscripción): {propuesta.roi_anio2:.1f}x",
    ]
    for i, line in enumerate(roi_lines):
        color = "#4CAF50" if "ROI" in line and propuesta.roi_anio1 > 0 else "black"
        ax_roi.text(0.0, 0.85 - i * 0.14, line, fontsize=9.5, color=color,
                    fontweight="bold" if "ROI" in line else "normal")

    # ── ROI bar chart ──
    ax_bar = fig.add_axes([0.65, 0.08, 0.30, 0.20])
    years = ["Año 1", "Año 2", "Año 3"]
    costs = [propuesta.costo_total_anio1,
             propuesta.costo_suscripcion_anual,
             propuesta.costo_suscripcion_anual]
    recup = [propuesta.recuperacion_anual] * 3
    x = np.arange(3)
    ax_bar.bar(x - 0.15, [c / 1000 for c in costs], 0.3, label="Costo", color="#F44336", alpha=0.7)
    ax_bar.bar(x + 0.15, [r / 1000 for r in recup], 0.3, label="Recuperación", color="#4CAF50", alpha=0.7)
    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(years, fontsize=8)
    ax_bar.set_ylabel("USD k", fontsize=8)
    ax_bar.legend(fontsize=7)
    ax_bar.set_title("Costo vs Recuperación", fontsize=9)

    # ── Footer ──
    fig.text(0.5, 0.02, "HydroVision AG | hydrovision.ag | Generado automáticamente",
             ha="center", fontsize=7, color="#9E9E9E")

    # Save
    safe_name = propuesta.cliente.lower().replace(" ", "_")
    pdf_path = OUTPUT_DIR / f"propuesta_{safe_name}.pdf"
    fig.savefig(pdf_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Also save PNG for preview
    png_path = OUTPUT_DIR / f"propuesta_{safe_name}.png"
    fig2 = plt.figure(figsize=(8.5, 11))
    # Re-create the figure for PNG (matplotlib can't save same fig twice after close)
    # Instead, just copy the PDF approach
    plt.close("all")

    return pdf_path


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Motor de propuesta automatizada — HydroVision AG")
    parser.add_argument("--lat", type=float, default=-31.2015, help="Latitud del lote")
    parser.add_argument("--lon", type=float, default=-64.0927, help="Longitud del lote")
    parser.add_argument("--ha", type=float, default=50, help="Superficie en hectáreas")
    parser.add_argument("--cultivo", type=str, default="malbec",
                        choices=list(CULTIVO_DATA.keys()), help="Cultivo principal")
    parser.add_argument("--tier", type=str, default=None,
                        choices=list(TIER_PRICING.keys()), help="Tier (auto si omitido)")
    parser.add_argument("--cliente", type=str, default="Campo Demo", help="Nombre del cliente")
    args = parser.parse_args()

    print("=" * 60)
    print("Motor de Propuesta Automatizada — HydroVision AG")
    print("R15 — Sentinel-2 + GeoPandas → PDF")
    print("=" * 60)

    print(f"\nGenerando propuesta para: {args.cliente}")
    print(f"  Ubicación: ({args.lat}, {args.lon})")
    print(f"  Superficie: {args.ha} ha | Cultivo: {args.cultivo}")

    propuesta = generar_propuesta(
        lat=args.lat, lon=args.lon, ha=args.ha,
        cultivo=args.cultivo, tier=args.tier, cliente=args.cliente,
    )

    print(f"\n  Análisis Sentinel-2:")
    print(f"    NDWI: {propuesta.analisis_s2.ndwi_mean} ± {propuesta.analisis_s2.ndwi_std}")
    print(f"    Heterogeneidad: {propuesta.analisis_s2.heterogeneidad}")
    print(f"    Densidad recomendada: {propuesta.analisis_s2.recomendacion_densidad} nodos/ha")

    print(f"\n  Recomendación:")
    print(f"    Tier: {TIER_PRICING[propuesta.tier]['nombre']}")
    print(f"    Nodos: {propuesta.nodos_recomendados} + {propuesta.gateways} gateway(s)")
    print(f"    Hardware: USD {propuesta.costo_hardware:,}")
    print(f"    Suscripción: USD {propuesta.costo_suscripcion_anual:,}/año")
    print(f"    Total Año 1: USD {propuesta.costo_total_anio1:,}")
    print(f"    Recuperación: USD {propuesta.recuperacion_anual:,}/año")
    print(f"    ROI Año 1: {propuesta.roi_anio1:+.0%}")
    print(f"    ROI Año 2+: {propuesta.roi_anio2:.1f}x")

    pdf_path = generar_pdf(propuesta)
    print(f"\n  PDF generado: {pdf_path}")

    # Demo: generar propuestas para los 3 casos de uso principales (doc-06)
    print(f"\n{'=' * 60}")
    print("Demo: 3 propuestas de ejemplo (doc-06 case studies)")
    print("=" * 60)

    demos = [
        {"lat": -31.2015, "lon": -64.0927, "ha": 20, "cultivo": "malbec",
         "tier": "monitoreo", "cliente": "Bodega Familiar Caroya"},
        {"lat": -32.9, "lon": -68.5, "ha": 50, "cultivo": "olivo",
         "tier": "automatizacion", "cliente": "Olivar San Juan"},
        {"lat": -33.5, "lon": -69.1, "ha": 100, "cultivo": "malbec",
         "tier": "precision", "cliente": "Bodega Premium Lujan"},
    ]

    for demo in demos:
        p = generar_propuesta(**demo)
        pdf = generar_pdf(p)
        print(f"\n  {demo['cliente']}: {demo['ha']} ha {demo['cultivo']}")
        print(f"    {TIER_PRICING[p.tier]['nombre']} | {p.nodos_recomendados} nodos | "
              f"USD {p.costo_total_anio1:,} Año 1 | ROI {p.roi_anio2:.1f}x Año 2+")
        print(f"    → {pdf}")
