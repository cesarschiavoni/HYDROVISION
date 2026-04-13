"""
Tests — Módulo OpticalHealthMonitor (optical_health.py)
Validación del índice ISO_nodo de salud óptica del nodo HydroVision AG.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import math
import tempfile
import json
from datetime import datetime
from optical_health import (
    OpticalHealthMonitor, OpticalHealthResult,
    _compute_std_dev, _histogram_score, _expected_dry_ref_temp,
    _emissivity_score,
    ALERT_THRESHOLD_ISO, STD_DEV_MIN_HEALTHY, STD_DEV_MAX_HEALTHY,
    DRY_REF_EMISSIVITY_DEVIATION,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def mon(tmp_dir):
    return OpticalHealthMonitor("N01", storage_dir=tmp_dir)


def healthy_image(n: int = 32 * 24, mean: float = 28.0, std: float = 4.0):
    """Imagen sintética con distribución normal de temperatura."""
    import random
    random.seed(1)
    return [random.gauss(mean, std) for _ in range(n)]


# ─────────────────────────────────────────────
# Tests — Funciones auxiliares
# ─────────────────────────────────────────────

class TestComputeStdDev:

    def test_constant_image(self):
        pixels = [25.0] * 100
        assert _compute_std_dev(pixels) == pytest.approx(0.0, abs=1e-6)

    def test_known_std(self):
        # Valores con std conocido
        vals = [0.0, 2.0, 4.0, 6.0, 8.0]  # media=4, std≈3.162
        result = _compute_std_dev(vals)
        assert result == pytest.approx(math.sqrt(10.0), abs=0.001)

    def test_single_pixel(self):
        assert _compute_std_dev([25.0]) == 0.0

    def test_empty(self):
        assert _compute_std_dev([]) == 0.0


class TestHistogramScore:

    def test_healthy_range_max_score(self):
        mid = (STD_DEV_MIN_HEALTHY + STD_DEV_MAX_HEALTHY) / 2
        assert _histogram_score(mid) == pytest.approx(100.0, abs=0.1)

    def test_very_low_std_zero_score(self):
        assert _histogram_score(0.0) == pytest.approx(0.0, abs=0.1)

    def test_very_high_std_zero_score(self):
        assert _histogram_score(100.0) == pytest.approx(0.0, abs=0.1)

    def test_at_min_boundary(self):
        assert _histogram_score(STD_DEV_MIN_HEALTHY) == pytest.approx(100.0, abs=0.1)

    def test_at_max_boundary(self):
        assert _histogram_score(STD_DEV_MAX_HEALTHY) == pytest.approx(100.0, abs=0.1)

    def test_score_between_0_and_100(self):
        for std in [0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 25.0]:
            score = _histogram_score(std)
            assert 0.0 <= score <= 100.0


class TestExpectedDryRefTemp:

    def test_night_returns_ta_plus_offset(self):
        t = _expected_dry_ref_temp(ta_celsius=20.0, solar_irradiance_wm2=5.0)
        assert t == pytest.approx(20.5, abs=0.1)

    def test_high_irradiance_increases_temp(self):
        t_low = _expected_dry_ref_temp(20.0, 200.0)
        t_high = _expected_dry_ref_temp(20.0, 1000.0)
        assert t_high > t_low

    def test_hot_day_greater_than_ta(self):
        """Panel negro en verano debe ser más caliente que el aire (absorbe radiación)."""
        t = _expected_dry_ref_temp(30.0, 800.0)
        assert t > 30.0


class TestEmissivityScore:

    def test_zero_deviation_max_score(self):
        assert _emissivity_score(0.0) == pytest.approx(100.0, abs=0.1)

    def test_at_threshold_max_score(self):
        assert _emissivity_score(DRY_REF_EMISSIVITY_DEVIATION) == pytest.approx(100.0, abs=0.1)

    def test_double_threshold_zero_score(self):
        assert _emissivity_score(2.0 * DRY_REF_EMISSIVITY_DEVIATION) == pytest.approx(0.0, abs=0.1)

    def test_large_deviation_zero_score(self):
        assert _emissivity_score(20.0) == pytest.approx(0.0, abs=0.1)


# ─────────────────────────────────────────────
# Tests — OpticalHealthMonitor.evaluate()
# ─────────────────────────────────────────────

class TestEvaluateHealthy:

    def test_healthy_iso_near_100(self, mon):
        img = healthy_image(std=4.5)
        ta = 30.0
        t_dry_expected = _expected_dry_ref_temp(ta, 800.0)
        result = mon.evaluate(
            pixel_temps=img,
            ta_celsius=ta,
            dry_ref_temp_measured=t_dry_expected + 0.5,  # desviación < umbral
            solar_irradiance_wm2=800.0,
        )
        assert result.iso_nodo >= 80.0
        assert result.iso_alert is False

    def test_healthy_no_alerts(self, mon):
        img = healthy_image(std=4.5)
        ta = 28.0
        t_dry = _expected_dry_ref_temp(ta, 700.0)
        result = mon.evaluate(img, ta, t_dry + 0.3, 700.0)
        assert result.obstruction_alert is False
        assert result.emissivity_alert is False
        assert result.alert_message == "OK"


class TestEvaluateObstruction:

    def test_low_std_triggers_obstruction_alert(self, mon):
        # Imagen completamente uniforme (todos los píxeles iguales) → std = 0
        img = [28.0] * (32 * 24)
        # Usar temperatura del panel cercana a la esperada para aislar el test de histograma
        ta = 28.0
        t_dry = _expected_dry_ref_temp(ta, 800.0)
        result = mon.evaluate(img, ta_celsius=ta,
                              dry_ref_temp_measured=t_dry + 0.5,
                              solar_irradiance_wm2=800.0)
        assert result.obstruction_alert is True
        assert result.std_dev_measured < STD_DEV_MIN_HEALTHY

    def test_high_std_triggers_obstruction_alert(self, mon):
        import random
        random.seed(42)
        img = [random.gauss(28.0, 20.0) for _ in range(32 * 24)]  # std >> max
        result = mon.evaluate(img, ta_celsius=28.0,
                              dry_ref_temp_measured=40.0,
                              solar_irradiance_wm2=800.0)
        assert result.obstruction_alert is True
        assert result.std_dev_measured > STD_DEV_MAX_HEALTHY

    def test_obstruction_reduces_iso(self, mon):
        img_healthy = healthy_image(std=4.5)
        img_dirty = healthy_image(std=0.2)
        ta = 28.0
        t_dry = _expected_dry_ref_temp(ta, 700.0)
        r_healthy = mon.evaluate(img_healthy, ta, t_dry + 0.5, 700.0)
        r_dirty = mon.evaluate(img_dirty, ta, t_dry + 0.5, 700.0)
        assert r_dirty.iso_nodo < r_healthy.iso_nodo


class TestEvaluateEmissivity:

    def test_panel_deviation_triggers_alert(self, mon):
        img = healthy_image(std=4.0)
        ta = 28.0
        t_dry_expected = _expected_dry_ref_temp(ta, 700.0)
        # Panel medido con desviación de 3× el umbral → alerta segura
        deviation = DRY_REF_EMISSIVITY_DEVIATION * 3
        result = mon.evaluate(img, ta,
                              dry_ref_temp_measured=t_dry_expected - deviation,
                              solar_irradiance_wm2=700.0)
        assert result.emissivity_alert is True
        assert result.dry_ref_deviation > DRY_REF_EMISSIVITY_DEVIATION

    def test_panel_ok_no_alert(self, mon):
        img = healthy_image(std=4.0)
        ta = 28.0
        t_dry_expected = _expected_dry_ref_temp(ta, 700.0)
        # Desviación mínima (0.1°C) bien dentro del umbral
        result = mon.evaluate(img, ta,
                              dry_ref_temp_measured=t_dry_expected + 0.1,
                              solar_irradiance_wm2=700.0)
        assert result.emissivity_alert is False


class TestEvaluateDoubleFailure:

    def test_double_failure_low_iso(self, mon):
        """Lente sucia + panel sucio → ISO muy bajo."""
        img = [28.0] * (32 * 24)   # std=0 → obstrucción
        ta = 28.0
        t_dry_expected = _expected_dry_ref_temp(ta, 700.0)
        deviation = DRY_REF_EMISSIVITY_DEVIATION * 5
        result = mon.evaluate(img, ta,
                              dry_ref_temp_measured=t_dry_expected - deviation,
                              solar_irradiance_wm2=700.0)
        assert result.iso_nodo < ALERT_THRESHOLD_ISO
        assert result.iso_alert is True
        assert result.obstruction_alert is True
        assert result.emissivity_alert is True


# ─────────────────────────────────────────────
# Tests — ISO_nodo composición
# ─────────────────────────────────────────────

class TestISOComposition:

    def test_iso_within_bounds(self, mon):
        img = healthy_image(std=4.0)
        ta = 28.0
        t_dry = _expected_dry_ref_temp(ta, 700.0)
        result = mon.evaluate(img, ta, t_dry, 700.0)
        assert 0.0 <= result.iso_nodo <= 100.0

    def test_iso_alert_threshold(self, mon):
        """ISO < ALERT_THRESHOLD_ISO debe generar iso_alert=True."""
        img = [28.0] * (32 * 24)   # std=0 → score_hist=0 → ISO≈50 si emis OK
        ta = 28.0
        t_dry = _expected_dry_ref_temp(ta, 700.0)
        result = mon.evaluate(img, ta, t_dry + 0.5, 700.0)
        # score_hist=0 → ISO ≈ 50 → alerta
        assert result.iso_alert == (result.iso_nodo < ALERT_THRESHOLD_ISO)


# ─────────────────────────────────────────────
# Tests — Estado acumulado
# ─────────────────────────────────────────────

class TestStateAccumulation:

    def test_n_evaluations_increments(self, mon):
        img = healthy_image(std=4.5)
        ta = 28.0
        t_dry = _expected_dry_ref_temp(ta, 700.0)
        for _ in range(5):
            mon.evaluate(img, ta, t_dry + 0.5, 700.0)
        assert mon._state.n_evaluations == 5

    def test_n_alerts_counted(self, mon):
        # Crear condición de alerta: imagen uniforme (std=0) → obstruction alert
        img = [28.0] * (32 * 24)
        ta = 28.0
        t_dry = _expected_dry_ref_temp(ta, 700.0)
        for _ in range(3):
            mon.evaluate(img, ta, t_dry + 0.1, 700.0)
        assert mon._state.n_obstruction_alerts >= 3

    def test_iso_history_grows(self, mon):
        img = healthy_image(std=4.5)
        ta = 28.0
        t_dry = _expected_dry_ref_temp(ta, 700.0)
        for _ in range(10):
            mon.evaluate(img, ta, t_dry + 0.5, 700.0)
        assert len(mon._state.iso_history) == 10


# ─────────────────────────────────────────────
# Tests — Persistencia
# ─────────────────────────────────────────────

class TestPersistence:

    def test_save_creates_file(self, tmp_dir):
        mon = OpticalHealthMonitor("N05", storage_dir=tmp_dir)
        img = healthy_image(std=4.0)
        ta = 28.0
        t_dry = _expected_dry_ref_temp(ta, 700.0)
        mon.evaluate(img, ta, t_dry + 0.5, 700.0)
        mon.save()
        path = os.path.join(tmp_dir, "optical_health_N05.json")
        assert os.path.exists(path)

    def test_roundtrip_preserves_n_evaluations(self, tmp_dir):
        mon = OpticalHealthMonitor("N06", storage_dir=tmp_dir)
        img = healthy_image(std=4.0)
        ta = 28.0
        t_dry = _expected_dry_ref_temp(ta, 700.0)
        for _ in range(7):
            mon.evaluate(img, ta, t_dry + 0.5, 700.0)
        mon.save()
        mon2 = OpticalHealthMonitor("N06", storage_dir=tmp_dir)
        assert mon2._state.n_evaluations == 7

    def test_corrupted_file_starts_fresh(self, tmp_dir):
        path = os.path.join(tmp_dir, "optical_health_N99.json")
        with open(path, "w") as f:
            f.write("{bad json")
        mon = OpticalHealthMonitor("N99", storage_dir=tmp_dir)
        assert mon._state.n_evaluations == 0


# ─────────────────────────────────────────────
# Tests — summary()
# ─────────────────────────────────────────────

class TestSummary:

    def test_summary_keys_present(self, mon):
        s = mon.summary()
        for key in ("node_id", "n_evaluations", "last_iso", "avg_iso",
                    "n_alerts", "n_emissivity_alerts", "n_obstruction_alerts",
                    "alert_rate_pct"):
            assert key in s

    def test_summary_alert_rate_zero_initially(self, tmp_dir):
        mon2 = OpticalHealthMonitor("FRESH", storage_dir=tmp_dir)
        s = mon2.summary()
        assert s["alert_rate_pct"] == pytest.approx(0.0, abs=0.01)
