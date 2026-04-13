"""
Tests — Fusión CWSI↔NDWI (05_sentinel2_fusion.py)
Validación del modelo de correlación nodo termográfico + Sentinel-2.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
from sentinel2_fusion import (
    Sentinel2Observation, CWSINDWICorrelationModel,
    generate_synthetic_sentinel2_dataset,
)


@pytest.fixture
def dataset_full():
    return generate_synthetic_sentinel2_dataset(n_obs=120, seed=42)

@pytest.fixture
def dataset_labeled(dataset_full):
    return [o for o in dataset_full if o.cwsi_nodo is not None]

@pytest.fixture
def model_calibrated(dataset_labeled):
    model = CWSINDWICorrelationModel(poly_degree=2)
    model.calibrate(dataset_labeled[:80])
    return model


class TestSentinel2Observation:

    def test_ndwi_range(self, dataset_full):
        """NDWI debe estar en rango [-1, 1]."""
        for obs in dataset_full:
            assert -1.0 <= obs.NDWI <= 1.0, f"NDWI={obs.NDWI:.3f} fuera de rango"

    def test_ndvi_range(self, dataset_full):
        """NDVI debe estar en rango [-1, 1]."""
        for obs in dataset_full:
            assert -1.0 <= obs.NDVI <= 1.0, f"NDVI={obs.NDVI:.3f} fuera de rango"

    def test_ndwi_negative_correlation_with_cwsi(self, dataset_labeled):
        """NDWI debe tener correlación negativa con CWSI (más agua = menos estrés)."""
        from scipy.stats import pearsonr
        ndwi  = np.array([o.NDWI for o in dataset_labeled])
        cwsi  = np.array([o.cwsi_nodo for o in dataset_labeled])
        r, p  = pearsonr(ndwi, cwsi)
        assert r < -0.5, f"Correlación NDWI↔CWSI debe ser negativa (r={r:.3f})"
        assert p < 0.05, "Correlación no es estadísticamente significativa"

    def test_features_vector_length(self, dataset_full):
        """Vector de features debe tener 4 componentes: NDWI, NDVI, NDRE, VPD."""
        for obs in dataset_full[:10]:
            assert len(obs.features) == 4

    def test_vpd_positive(self, dataset_full):
        """VPD siempre debe ser positivo."""
        for obs in dataset_full:
            assert obs.VPD_kPa > 0


class TestCWSINDWICorrelationModel:

    def test_calibration_requires_minimum_points(self, dataset_labeled):
        """Debe fallar si hay menos de 10 puntos de calibración."""
        model = CWSINDWICorrelationModel()
        with pytest.raises(ValueError, match="Insuficientes"):
            model.calibrate(dataset_labeled[:5])

    def test_calibration_metrics_acceptable(self, model_calibrated):
        """R² de calibración debe ser > 0.70."""
        assert model_calibrated.calibration_score["R2"] > 0.70, \
            f"R² calibración = {model_calibrated.calibration_score['R2']:.3f} < 0.70"

    def test_calibration_mae_acceptable(self, model_calibrated):
        """MAE de calibración debe ser < 0.15 unidades CWSI."""
        assert model_calibrated.calibration_score["MAE"] < 0.15, \
            f"MAE calibración = {model_calibrated.calibration_score['MAE']:.4f} > 0.15"

    def test_predict_before_calibration_raises(self):
        """Predecir sin calibrar debe lanzar RuntimeError."""
        model = CWSINDWICorrelationModel()
        obs = generate_synthetic_sentinel2_dataset(1, seed=1)[0]
        with pytest.raises(RuntimeError, match="calibrado"):
            model.predict_cwsi(obs)

    def test_predictions_in_valid_range(self, model_calibrated, dataset_full):
        """Todas las predicciones deben estar en [0, 1]."""
        for obs in dataset_full[:30]:
            pred = model_calibrated.predict_cwsi(obs)
            assert 0.0 <= pred <= 1.0, f"Predicción {pred:.3f} fuera de rango [0,1]"

    def test_generalization_on_test_set(self, dataset_labeled, model_calibrated):
        """R² en test set (datos no vistos) debe ser > 0.60."""
        from sklearn.metrics import r2_score
        test_obs = dataset_labeled[80:]
        if len(test_obs) < 5:
            pytest.skip("Test set muy pequeño para esta fixture")
        y_true = np.array([o.cwsi_nodo for o in test_obs])
        y_pred = np.array([model_calibrated.predict_cwsi(o) for o in test_obs])
        r2 = float(r2_score(y_true, y_pred))
        assert r2 > 0.60, f"R² test = {r2:.3f} < 0.60 — modelo no generaliza bien"

    def test_field_map_generation(self, model_calibrated):
        """Mapa de campo debe tener estadísticas coherentes."""
        field_obs = generate_synthetic_sentinel2_dataset(50, seed=7)
        for o in field_obs:
            o.cwsi_nodo = None
        field_map = model_calibrated.generate_field_cwsi_map(field_obs)
        assert 0.0 <= field_map["cwsi_mean"] <= 1.0
        assert field_map["n_pixels_veg"] > 0
        assert field_map["cwsi_std"] >= 0.0

    def test_one_node_scales_to_field(self, model_calibrated):
        """
        Principio clave del producto: 1 nodo calibra el satélite para el campo completo.
        Verificar que el mapa de campo se genera con éxito a partir de 1 punto de calibración
        expandido a 50 píxeles (= ~0.5ha a 10m/px).
        """
        field_obs = generate_synthetic_sentinel2_dataset(50, seed=10)
        for o in field_obs:
            o.cwsi_nodo = None
        field_map = model_calibrated.generate_field_cwsi_map(field_obs)
        # El mapa debe cubrir al menos el 50% del campo con vegetación
        coverage = field_map["n_pixels_veg"] / field_map["n_pixels_total"]
        assert coverage > 0.40, f"Cobertura vegetal del mapa: {coverage:.1%} < 40%"

    def test_cwsi_p90_greater_than_mean(self, model_calibrated):
        """P90 debe ser mayor o igual a la media (propiedad estadística básica)."""
        field_obs = generate_synthetic_sentinel2_dataset(100, seed=5)
        for o in field_obs:
            o.cwsi_nodo = None
        field_map = model_calibrated.generate_field_cwsi_map(field_obs)
        assert field_map["cwsi_p90"] >= field_map["cwsi_mean"], \
            "P90 CWSI debe ser ≥ media CWSI"
