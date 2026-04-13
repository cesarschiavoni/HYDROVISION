"""
Fusión CWSI ↔ NDWI — HydroVision AG
Correlación nodo termográfico + Sentinel-2 para mapas de estrés de campo completo.

Un nodo proporciona CWSI preciso en un punto (160×120px, ±0.05°C NETD).
Sentinel-2 proporciona cobertura espacial (10m/px, cada 5 días, gratuito vía API Copernicus).

El modelo de correlación calibra el satélite con el nodo:
  - NDWI (Normalized Difference Water Index) = (Band8A - Band11) / (Band8A + Band11)
    [NIR 865nm - SWIR 1610nm] — sensible al contenido de agua en la hoja
  - NDVI = (Band8 - Band4) / (Band8 + Band4) — índice de vegetación
  - Correlación empírica: CWSI_sat ≈ f(NDWI, NDVI, VPD)

Con 1 nodo se puede mapear el estrés hídrico de 50-100 ha.
Con 3 nodos → mayor precisión y detección de heterogeneidades del suelo.

Referencia:
  González-Dugo, V. et al. (2013). Using high-resolution hyperspectral and
  thermal airborne imagery to assess physiological conditions in the context
  of wheat and barley phenotyping. Remote Sensing, 5(3), 1363-1388.
  Bellvert, J. et al. (2015). Mapping crop water stress index in a 'Pinot-noir'
  vineyard: comparing ground measurements with thermal remote sensing imagery.
  Precision Agriculture, 16(4), 361-378.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional
from sklearn.linear_model import LinearRegression, HuberRegressor
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error


@dataclass
class Sentinel2Observation:
    """Observación Sentinel-2 en el punto del nodo (pixel del satélite)."""
    fecha: str
    B4_red: float      # Banda 4 — Rojo 665nm [reflectancia 0-1]
    B8_nir: float      # Banda 8 — NIR 842nm
    B8A_nir: float     # Banda 8A — NIR estrecho 865nm
    B11_swir: float    # Banda 11 — SWIR 1610nm
    B12_swir: float    # Banda 12 — SWIR 2190nm
    VPD_kPa: float     # VPD en la fecha de adquisición [kPa]
    cwsi_nodo: Optional[float] = None  # CWSI medido por el nodo ese día (ground truth)

    @property
    def NDWI(self) -> float:
        """NDWI (Gao 1996) — contenido hídrico foliar."""
        denom = self.B8A_nir + self.B11_swir
        return (self.B8A_nir - self.B11_swir) / denom if denom > 0 else 0.0

    @property
    def NDVI(self) -> float:
        """NDVI — vigor vegetativo."""
        denom = self.B8_nir + self.B4_red
        return (self.B8_nir - self.B4_red) / denom if denom > 0 else 0.0

    @property
    def NDRE(self) -> float:
        """NDRE (Red Edge) — estrés temprano antes visible en NDVI."""
        # Aproximación usando B8A y B4 (sin banda 705nm exacta en Sentinel-2 10m)
        return (self.B8A_nir - self.B4_red) / (self.B8A_nir + self.B4_red + 1e-9)

    @property
    def features(self) -> np.ndarray:
        """Vector de features para el modelo de correlación."""
        return np.array([self.NDWI, self.NDVI, self.NDRE, self.VPD_kPa])


class CWSINDWICorrelationModel:
    """
    Modelo de correlación CWSI ↔ índices espectrales Sentinel-2.

    Flujo de calibración:
      1. Acumular observaciones donde el nodo y el satélite coinciden
         (satélite pasa cada 5 días — buscar ±2h de la captura del nodo)
      2. Ajustar regresión polinomial: CWSI = f(NDWI, NDVI, NDRE, VPD)
      3. Aplicar el modelo al lote completo (todos los píxeles del satélite)
         para generar mapa de CWSI de campo completo

    Mínimo de puntos de calibración: 10 observaciones con buena distribución
    de CWSI (0.1 - 0.9) y VPD (0.5 - 3.5 kPa).
    """

    MIN_CALIBRATION_POINTS = 10

    def __init__(self, poly_degree: int = 2):
        self.model = Pipeline([
            ("poly", PolynomialFeatures(degree=poly_degree, include_bias=False)),
            ("reg",  HuberRegressor(epsilon=1.35, max_iter=500)),
        ])
        self.is_calibrated = False
        self.calibration_score: dict = {}
        self.n_calibration_points = 0

    def calibrate(self, observations: list[Sentinel2Observation]) -> dict:
        """
        Calibra el modelo con observaciones donde cwsi_nodo está disponible.

        Parámetros
        ----------
        observations : lista de observaciones Sentinel-2 con CWSI del nodo

        Retorna
        -------
        dict con métricas de calibración
        """
        labeled = [o for o in observations if o.cwsi_nodo is not None]

        if len(labeled) < self.MIN_CALIBRATION_POINTS:
            raise ValueError(
                f"Insuficientes puntos de calibración: {len(labeled)} "
                f"(mínimo: {self.MIN_CALIBRATION_POINTS})"
            )

        X = np.array([o.features for o in labeled])
        y = np.array([o.cwsi_nodo for o in labeled])

        self.model.fit(X, y)
        y_pred = self.model.predict(X)

        self.is_calibrated = True
        self.n_calibration_points = len(labeled)
        self.calibration_score = {
            "R2": float(r2_score(y, y_pred)),
            "MAE": float(mean_absolute_error(y, y_pred)),
            "RMSE": float(np.sqrt(np.mean((y - y_pred) ** 2))),
            "n_points": len(labeled),
            "cwsi_range": [float(y.min()), float(y.max())],
            "VPD_range": [float(X[:, 3].min()), float(X[:, 3].max())],
        }
        return self.calibration_score

    def predict_cwsi(self, obs: Sentinel2Observation) -> float:
        """Predice CWSI a partir de índices espectrales y VPD."""
        if not self.is_calibrated:
            raise RuntimeError("El modelo no está calibrado. Ejecutar calibrate() primero.")
        X = obs.features.reshape(1, -1)
        cwsi_pred = float(self.model.predict(X)[0])
        return float(np.clip(cwsi_pred, 0.0, 1.0))

    def generate_field_cwsi_map(
        self,
        field_observations: list[Sentinel2Observation],
        field_coords: Optional[np.ndarray] = None,
    ) -> dict:
        """
        Genera mapa de CWSI de campo completo a partir de píxeles Sentinel-2.

        field_observations : todas las observaciones del lote (un item por pixel 10m×10m)
        field_coords       : array [N, 2] con coordenadas lat/lon de cada pixel (opcional)

        Retorna dict con CWSI por pixel y estadísticas del lote.
        """
        if not self.is_calibrated:
            raise RuntimeError("Calibrar el modelo antes de generar el mapa.")

        cwsi_values = np.array([self.predict_cwsi(o) for o in field_observations])
        ndwi_values = np.array([o.NDWI for o in field_observations])
        ndvi_values = np.array([o.NDVI for o in field_observations])

        # Solo píxeles con vegetación (NDVI > 0.3)
        veg_mask = ndvi_values > 0.30

        return {
            "cwsi_all": cwsi_values,
            "cwsi_vegetal": cwsi_values[veg_mask],
            "cwsi_mean": float(np.mean(cwsi_values[veg_mask])) if veg_mask.any() else np.nan,
            "cwsi_std":  float(np.std(cwsi_values[veg_mask]))  if veg_mask.any() else np.nan,
            "cwsi_p90":  float(np.percentile(cwsi_values[veg_mask], 90)) if veg_mask.any() else np.nan,
            "n_pixels_total": len(field_observations),
            "n_pixels_veg":   int(np.sum(veg_mask)),
            "ndwi_mean": float(np.mean(ndwi_values[veg_mask])) if veg_mask.any() else np.nan,
            "coords": field_coords,
            "veg_mask": veg_mask,
        }


def generate_synthetic_sentinel2_dataset(
    n_obs: int = 120,
    seed: int = 42
) -> list[Sentinel2Observation]:
    """
    Genera dataset sintético de observaciones Sentinel-2 con CWSI del nodo.
    Simula una temporada completa (12 meses) de paso del satélite cada 5 días.

    El CWSI del nodo se simula siguiendo la fenología Malbec (mayor estrés
    en verano, menor en dormancia) con variabilidad realista.
    """
    rng = np.random.default_rng(seed)
    observations = []

    for i in range(n_obs):
        # VPD varía por estación (mayor en verano, menor en invierno)
        mes_relativo = (i * 5 / 30) % 12  # 0-12
        VPD = 1.8 + 1.2 * np.sin(mes_relativo * np.pi / 6) + rng.normal(0, 0.3)
        VPD = float(np.clip(VPD, 0.3, 4.0))

        # CWSI sigue la fenología: mayor estrés en verano (diciembre-febrero)
        cwsi_base = 0.3 + 0.4 * np.sin(mes_relativo * np.pi / 6)
        cwsi_nodo = float(np.clip(cwsi_base + rng.normal(0, 0.12), 0.0, 1.0))

        # NDWI correlacionado inversamente con CWSI + ruido espectral
        # NDWI alto = hoja bien hidratada = CWSI bajo
        NDWI = float(np.clip(0.35 - 0.45 * cwsi_nodo + rng.normal(0, 0.04), -0.2, 0.6))
        NDVI = float(np.clip(0.70 - 0.25 * cwsi_nodo + rng.normal(0, 0.03), 0.2, 0.9))

        # Bandas espectrales Sentinel-2 aproximadas desde NDWI/NDVI
        B8A = float(np.clip(0.35 + rng.normal(0, 0.02), 0.1, 0.7))
        B11 = float(np.clip(B8A * (1 - NDWI) / (1 + NDWI), 0.05, 0.5))
        B8  = float(np.clip(0.40 + rng.normal(0, 0.02), 0.15, 0.75))
        B4  = float(np.clip(B8 * (1 - NDVI) / (1 + NDVI), 0.02, 0.3))
        B12 = float(np.clip(B11 * 0.7 + rng.normal(0, 0.01), 0.02, 0.4))

        obs = Sentinel2Observation(
            fecha=f"2026-{10 + i//6:02d}-{(i * 5 % 28) + 1:02d}",
            B4_red=B4, B8_nir=B8, B8A_nir=B8A, B11_swir=B11, B12_swir=B12,
            VPD_kPa=VPD,
            cwsi_nodo=cwsi_nodo if i % 5 != 0 else None,  # 20% sin ground truth
        )
        observations.append(obs)

    return observations


# ─────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import os

    print("=" * 60)
    print("Fusión CWSI ↔ NDWI — HydroVision AG — TRL 3")
    print("Sentinel-2 + Nodo Termográfico — Malbec Colonia Caroya")
    print("=" * 60)

    # Generar dataset
    obs_all = generate_synthetic_sentinel2_dataset(n_obs=120, seed=42)
    obs_labeled = [o for o in obs_all if o.cwsi_nodo is not None]
    print(f"\nDataset: {len(obs_all)} observaciones, {len(obs_labeled)} con CWSI del nodo")

    # Calibrar modelo (80% train)
    n_train = int(len(obs_labeled) * 0.80)
    train_obs = obs_labeled[:n_train]
    test_obs  = obs_labeled[n_train:]

    model = CWSINDWICorrelationModel(poly_degree=2)
    cal = model.calibrate(train_obs)
    print(f"\nCalibración (n={cal['n_points']}):")
    print(f"  R²   = {cal['R2']:.3f}")
    print(f"  MAE  = {cal['MAE']:.4f} CWSI units")
    print(f"  RMSE = {cal['RMSE']:.4f} CWSI units")
    print(f"  Rango CWSI calibrado: {cal['cwsi_range']}")

    # Evaluación en test
    y_true = np.array([o.cwsi_nodo for o in test_obs])
    y_pred = np.array([model.predict_cwsi(o) for o in test_obs])
    test_r2  = float(r2_score(y_true, y_pred))
    test_mae = float(mean_absolute_error(y_true, y_pred))
    print(f"\nEvaluación test (n={len(test_obs)}):")
    print(f"  R²   = {test_r2:.3f}")
    print(f"  MAE  = {test_mae:.4f} CWSI units")

    # Mapa de campo sintético (100 píxeles = lote de ~1ha a 10m/px)
    field_obs = generate_synthetic_sentinel2_dataset(n_obs=100, seed=99)
    for o in field_obs:
        o.cwsi_nodo = None  # sin ground truth en el mapa
    field_map = model.generate_field_cwsi_map(field_obs)
    print(f"\nMapa de campo (100 píxeles 10m×10m = ~1ha):")
    print(f"  CWSI medio del lote: {field_map['cwsi_mean']:.3f}")
    print(f"  Desv. std:           {field_map['cwsi_std']:.3f}")
    print(f"  CWSI P90 (zona crítica): {field_map['cwsi_p90']:.3f}")
    print(f"  Píxeles con vegetación: {field_map['n_pixels_veg']}/{field_map['n_pixels_total']}")

    # Gráfico correlación CWSI nodo vs. CWSI satélite
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Correlación CWSI↔NDWI — Nodo HydroVision AG + Sentinel-2\n"
                 "Malbec Colonia Caroya — TRL 3", fontweight="bold")

    # Panel 1: scatter calibración
    ax = axes[0]
    cwsi_train = np.array([o.cwsi_nodo for o in train_obs])
    pred_train = model.model.predict(np.array([o.features for o in train_obs]))
    ax.scatter(cwsi_train, pred_train, alpha=0.6, c="steelblue", s=40, label="Calibración")
    cwsi_test_arr = np.array([o.cwsi_nodo for o in test_obs])
    ax.scatter(cwsi_test_arr, y_pred, alpha=0.7, c="orangered", s=50,
               marker="^", label="Validación")
    ax.plot([0, 1], [0, 1], "k--", lw=1.5, label="1:1")
    ax.set_xlabel("CWSI nodo (ground truth)")
    ax.set_ylabel("CWSI estimado (Sentinel-2)")
    ax.set_title(f"Correlación CWSI nodo ↔ CWSI satélite\n"
                 f"R²={test_r2:.3f}  MAE={test_mae:.4f}")
    ax.legend()
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # Panel 2: mapa de CWSI del lote (10×10 píxeles)
    ax2 = axes[1]
    cwsi_grid = field_map["cwsi_all"].reshape(10, 10)
    im = ax2.imshow(cwsi_grid, cmap="RdYlGn_r", vmin=0, vmax=1, aspect="equal")
    plt.colorbar(im, ax=ax2, label="CWSI")
    ax2.set_title(f"Mapa CWSI lote completo (Sentinel-2)\n"
                  f"CWSI medio={field_map['cwsi_mean']:.2f} "
                  f"P90={field_map['cwsi_p90']:.2f}")
    ax2.set_xlabel("X (píxeles 10m)")
    ax2.set_ylabel("Y (píxeles 10m)")

    plt.tight_layout()
    from field_config import OUTPUT_DIR
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fig.savefig(os.path.join(OUTPUT_DIR, "cwsi_ndwi_fusion.png"),
                dpi=150, bbox_inches="tight")
    print(f"\n  Figura guardada en {OUTPUT_DIR}/cwsi_ndwi_fusion.png")
    print("\n✓ Módulo fusión CWSI↔NDWI operativo")
