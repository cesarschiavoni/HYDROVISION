"""
Tests — Módulo FusionEngine (fusion_engine.py)
Validación del motor de fusión HSI con regresión lineal online adaptativa.
HydroVision AG — TRL 3, Colonia Caroya, Córdoba.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import tempfile
import json
from datetime import datetime
from fusion_engine import (
    FusionEngine, FusionResult, RegressionWindow,
    WINDOW_SIZE, MDS_MATURITY_FULL, CWSI_CONFIDENCE_THRESHOLD,
    DIVERGENCE_THRESHOLD, WIND_OVERRIDE_MS,
    DEFAULT_ALPHA, DEFAULT_BETA,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def eng(tmp_dir):
    return FusionEngine("N01", storage_dir=tmp_dir)


# ─────────────────────────────────────────────
# Tests — RegressionWindow
# ─────────────────────────────────────────────

class TestRegressionWindow:

    def test_add_and_count(self):
        w = RegressionWindow()
        for i in range(10):
            w.add(float(i) / 10, float(i) / 10 * 0.9)
        assert w.n == 10

    def test_window_cap(self):
        w = RegressionWindow()
        for i in range(WINDOW_SIZE + 20):
            w.add(float(i) / 100, float(i) / 100 * 0.85)
        assert w.n == WINDOW_SIZE

    def test_fit_defaults_few_samples(self):
        w = RegressionWindow()
        w.add(0.3, 0.4)
        w.add(0.5, 0.6)
        alpha, beta = w.fit()
        assert alpha == DEFAULT_ALPHA
        assert beta == DEFAULT_BETA

    def test_fit_perfect_linear(self):
        """y = 0.1 + 0.8x → α≈0.1, β≈0.8."""
        w = RegressionWindow()
        for i in range(20):
            x = i / 20.0
            y = 0.1 + 0.8 * x
            w.add(x, y)
        alpha, beta = w.fit()
        assert alpha == pytest.approx(0.1, abs=0.02)
        assert beta == pytest.approx(0.8, abs=0.02)

    def test_r_squared_perfect_fit(self):
        w = RegressionWindow()
        for i in range(20):
            x = i / 20.0
            y = 0.05 + 0.9 * x
            w.add(x, y)
        r2 = w.r_squared()
        assert r2 == pytest.approx(1.0, abs=0.01)

    def test_r_squared_no_data(self):
        w = RegressionWindow()
        assert w.r_squared() == 0.0

    def test_r_squared_constant_x(self):
        """Varianza nula en x → defaults, R²=0."""
        w = RegressionWindow()
        for _ in range(10):
            w.add(0.5, 0.5)
        alpha, beta = w.fit()
        assert alpha == DEFAULT_ALPHA
        assert beta == DEFAULT_BETA


# ─────────────────────────────────────────────
# Tests — FusionEngine.fuse() básico
# ─────────────────────────────────────────────

class TestFuseBasic:

    def test_hsi_within_bounds(self, eng):
        result = eng.fuse(cwsi=0.5, mds_norm=0.5)
        assert 0.0 <= result.hsi <= 1.0

    def test_hsi_is_float(self, eng):
        result = eng.fuse(cwsi=0.4, mds_norm=0.6)
        assert isinstance(result.hsi, float)

    def test_weights_sum_to_one(self, eng):
        result = eng.fuse(cwsi=0.5, mds_norm=0.5)
        assert result.weight_cwsi + result.weight_mds == pytest.approx(1.0, abs=0.001)

    def test_weights_mds_dominant(self, eng):
        """El peso MDS debe ser mayor que CWSI por diseño (65% base)."""
        result = eng.fuse(cwsi=0.5, mds_norm=0.5)
        assert result.weight_mds > result.weight_cwsi

    def test_timestamp_present(self, eng):
        result = eng.fuse(cwsi=0.5, mds_norm=0.5)
        assert result.timestamp != ""

    def test_custom_timestamp(self, eng):
        ts = datetime(2025, 12, 1, 13, 0, 0)
        result = eng.fuse(cwsi=0.5, mds_norm=0.5, timestamp=ts)
        assert "2025-12-01" in result.timestamp


# ─────────────────────────────────────────────
# Tests — Wind override
# ─────────────────────────────────────────────

class TestWindOverride:

    def test_wind_override_activates(self, eng):
        result = eng.fuse(cwsi=0.8, mds_norm=0.5,
                          wind_speed_ms=WIND_OVERRIDE_MS + 1.0)
        assert result.wind_override is True

    def test_wind_override_forces_100_mds(self, eng):
        result = eng.fuse(cwsi=0.8, mds_norm=0.5,
                          wind_speed_ms=WIND_OVERRIDE_MS + 1.0)
        assert result.weight_mds == pytest.approx(1.0, abs=0.001)
        assert result.weight_cwsi == pytest.approx(0.0, abs=0.001)

    def test_wind_override_hsi_equals_mds(self, eng):
        """Con wind override, HSI debe ser igual a mds_norm."""
        result = eng.fuse(cwsi=0.9, mds_norm=0.55,
                          wind_speed_ms=WIND_OVERRIDE_MS + 2.0)
        assert result.hsi == pytest.approx(0.55, abs=0.001)

    def test_wind_below_threshold_no_override(self, eng):
        result = eng.fuse(cwsi=0.5, mds_norm=0.5,
                          wind_speed_ms=WIND_OVERRIDE_MS - 0.1)
        assert result.wind_override is False

    def test_wind_override_no_window_update(self, eng):
        """Wind override no debe actualizar la ventana de regresión."""
        eng.fuse(cwsi=0.5, mds_norm=0.5, wind_speed_ms=WIND_OVERRIDE_MS + 1.0)
        assert eng._window.n == 0


# ─────────────────────────────────────────────
# Tests — Imputación CWSI
# ─────────────────────────────────────────────

class TestImputation:

    def test_low_confidence_triggers_imputation(self, eng):
        result = eng.fuse(cwsi=0.5, mds_norm=0.6,
                          cwsi_confidence=CWSI_CONFIDENCE_THRESHOLD - 0.1)
        assert result.imputed is True

    def test_high_confidence_no_imputation(self, eng):
        result = eng.fuse(cwsi=0.5, mds_norm=0.6,
                          cwsi_confidence=CWSI_CONFIDENCE_THRESHOLD + 0.1)
        assert result.imputed is False

    def test_imputed_cwsi_within_bounds(self, eng):
        result = eng.fuse(cwsi=0.5, mds_norm=0.7,
                          cwsi_confidence=0.1)
        assert 0.0 <= result.cwsi_used <= 1.0

    def test_imputation_no_window_update(self, eng):
        """Datos imputados no deben entrar en la ventana de regresión."""
        eng.fuse(cwsi=0.5, mds_norm=0.6, cwsi_confidence=0.1)
        assert eng._window.n == 0  # ventana vacía, no se actualizó


# ─────────────────────────────────────────────
# Tests — Divergencia
# ─────────────────────────────────────────────

class TestDivergence:

    def test_divergence_alert_large_delta(self, eng):
        result = eng.fuse(cwsi=0.9, mds_norm=0.1,   # delta = 0.8 > 0.35
                          cwsi_confidence=1.0)
        assert result.divergence_alert is True
        assert result.divergence_delta == pytest.approx(0.8, abs=0.01)

    def test_no_divergence_small_delta(self, eng):
        result = eng.fuse(cwsi=0.5, mds_norm=0.5,
                          cwsi_confidence=1.0)
        assert result.divergence_alert is False

    def test_divergence_threshold_boundary(self, eng):
        # Justo por encima del umbral (0.5 + threshold + epsilon)
        result = eng.fuse(cwsi=0.5 + DIVERGENCE_THRESHOLD + 0.01,
                          mds_norm=0.5,
                          cwsi_confidence=1.0)
        # > umbral → alerta
        assert result.divergence_alert is True

    def test_wind_override_no_divergence_alert(self, eng):
        """Con wind override no debe haber alerta de divergencia."""
        result = eng.fuse(cwsi=0.9, mds_norm=0.1,
                          wind_speed_ms=WIND_OVERRIDE_MS + 1.0)
        assert result.divergence_alert is False


# ─────────────────────────────────────────────
# Tests — MDS Maturity
# ─────────────────────────────────────────────

class TestMDSMaturity:

    def test_zero_sessions_zero_maturity(self, eng):
        assert eng.mds_maturity == pytest.approx(0.0, abs=0.001)

    def test_partial_maturity(self, eng):
        for _ in range(10):
            eng.register_scholander_session()
        assert eng.mds_maturity == pytest.approx(10.0 / MDS_MATURITY_FULL, abs=0.001)

    def test_maturity_capped_at_one(self, eng):
        for _ in range(MDS_MATURITY_FULL + 10):
            eng.register_scholander_session()
        assert eng.mds_maturity == pytest.approx(1.0, abs=0.001)

    def test_maturity_affects_mds_weight(self, tmp_dir):
        """Mayor madurez → mayor peso MDS (hasta cap)."""
        eng_low = FusionEngine("LOW", storage_dir=tmp_dir)
        eng_high = FusionEngine("HIGH", storage_dir=tmp_dir)
        for _ in range(MDS_MATURITY_FULL):
            eng_high.register_scholander_session()
        r_low = eng_low.fuse(cwsi=0.5, mds_norm=0.5)
        r_high = eng_high.fuse(cwsi=0.5, mds_norm=0.5)
        assert r_high.weight_mds >= r_low.weight_mds


# ─────────────────────────────────────────────
# Tests — Regresión online (ventana)
# ─────────────────────────────────────────────

class TestOnlineRegression:

    def test_window_grows_with_real_data(self, eng):
        for i in range(10):
            eng.fuse(cwsi=0.3 + i * 0.03, mds_norm=0.3 + i * 0.025,
                     cwsi_confidence=1.0)
        assert eng._window.n == 10

    def test_alpha_beta_update_after_training(self, eng):
        # Entrenar con relación lineal conocida
        for i in range(30):
            x = 0.1 + i * 0.02
            y = 0.05 + 0.85 * x
            eng.fuse(cwsi=y, mds_norm=x, cwsi_confidence=1.0)
        r = eng.fuse(cwsi=0.5, mds_norm=0.5)
        # α ≈ 0.05, β ≈ 0.85
        assert r.alpha == pytest.approx(0.05, abs=0.1)
        assert r.beta == pytest.approx(0.85, abs=0.1)
        assert r.r2 > 0.95


# ─────────────────────────────────────────────
# Tests — Persistencia
# ─────────────────────────────────────────────

class TestPersistence:

    def test_save_creates_file(self, tmp_dir):
        eng = FusionEngine("N05", storage_dir=tmp_dir)
        eng.fuse(cwsi=0.5, mds_norm=0.5)
        eng.save()
        path = os.path.join(tmp_dir, "fusion_N05.json")
        assert os.path.exists(path)

    def test_roundtrip_preserves_sessions(self, tmp_dir):
        eng = FusionEngine("N06", storage_dir=tmp_dir)
        eng.register_scholander_session()
        eng.register_scholander_session()
        eng.save()
        eng2 = FusionEngine("N06", storage_dir=tmp_dir)
        assert eng2._state.n_scholander_sessions == 2

    def test_roundtrip_preserves_window(self, tmp_dir):
        eng = FusionEngine("N07", storage_dir=tmp_dir)
        for i in range(15):
            eng.fuse(cwsi=0.3 + i * 0.02, mds_norm=0.3 + i * 0.02,
                     cwsi_confidence=1.0)
        n_before = eng._window.n
        eng.save()
        eng2 = FusionEngine("N07", storage_dir=tmp_dir)
        assert eng2._window.n == n_before

    def test_corrupted_file_starts_fresh(self, tmp_dir):
        path = os.path.join(tmp_dir, "fusion_N99.json")
        with open(path, "w") as f:
            f.write("corrupted{")
        eng = FusionEngine("N99", storage_dir=tmp_dir)
        assert eng._state.n_fusion_calls == 0


# ─────────────────────────────────────────────
# Tests — summary()
# ─────────────────────────────────────────────

class TestSummary:

    def test_summary_keys(self, eng):
        eng.fuse(cwsi=0.5, mds_norm=0.5)
        s = eng.summary()
        for key in ("node_id", "n_fusion_calls", "mds_maturity",
                    "window_samples", "regression", "divergence_count",
                    "imputation_count", "wind_override_count"):
            assert key in s

    def test_summary_n_fusion_calls_increments(self, eng):
        for _ in range(5):
            eng.fuse(cwsi=0.5, mds_norm=0.5)
        assert eng.summary()["n_fusion_calls"] == 5
