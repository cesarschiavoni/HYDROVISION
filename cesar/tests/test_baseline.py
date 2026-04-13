"""
Tests — Módulo CWSIBaseline (baseline.py)
Validación de la calibración adaptativa EMA para offsets Wet/Dry Ref.
HydroVision AG — TRL 3, Colonia Caroya, Córdoba.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import json
import tempfile
from datetime import date
from baseline import (
    CWSIBaseline, BaselineState,
    LEARNING_RATE_RAIN, LEARNING_RATE_SCHOLANDER,
    RAIN_THRESHOLD_MM, MDS_HYDRATED_THRESHOLD_UM,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def bl(tmp_dir):
    return CWSIBaseline.load("N01", tmp_dir)


# ─────────────────────────────────────────────
# Tests — Instanciación y carga
# ─────────────────────────────────────────────

class TestLoad:

    def test_load_fresh(self, tmp_dir):
        bl = CWSIBaseline.load("N01", tmp_dir)
        assert bl.state.node_id == "N01"
        assert bl.state.tc_wet_offset == 0.0
        assert bl.state.tc_dry_offset == 0.0
        assert bl.state.calibration_quality == "factory"

    def test_load_persists(self, tmp_dir):
        bl = CWSIBaseline.load("N02", tmp_dir)
        bl.state.tc_wet_offset = 1.23
        bl.save(tmp_dir)
        bl2 = CWSIBaseline.load("N02", tmp_dir)
        assert bl2.state.tc_wet_offset == pytest.approx(1.23, abs=0.001)

    def test_load_different_nodes_independent(self, tmp_dir):
        bl1 = CWSIBaseline.load("N01", tmp_dir)
        bl2 = CWSIBaseline.load("N02", tmp_dir)
        bl1.state.tc_wet_offset = 2.5
        bl1.save(tmp_dir)
        bl2_reloaded = CWSIBaseline.load("N02", tmp_dir)
        assert bl2_reloaded.state.tc_wet_offset == pytest.approx(0.0, abs=0.001)


# ─────────────────────────────────────────────
# Tests — update_rain
# ─────────────────────────────────────────────

class TestUpdateRain:

    def _rain(self, bl, tc=24.5, ta=30.0, vpd=2.0, mds=50.0,
              rain=10.0, date_str="2025-11-15"):
        return bl.update_rain(tc_measured_c=tc, ta_c=ta, vpd_kpa=vpd,
                              mds_um=mds, rain_mm=rain, date=date_str)

    def test_rain_event_updates_offset(self, bl):
        result = self._rain(bl)
        assert result["updated"] is True
        assert bl.state.n_rain_events == 1
        assert bl.state.tc_wet_offset != 0.0

    def test_rain_below_threshold_ignored(self, bl):
        result = bl.update_rain(tc_measured_c=24.5, ta_c=30.0, vpd_kpa=2.0,
                                mds_um=50.0,
                                rain_mm=RAIN_THRESHOLD_MM - 0.1,
                                date="2025-11-15")
        assert result["updated"] is False
        assert bl.state.n_rain_events == 0
        assert bl.state.tc_wet_offset == pytest.approx(0.0, abs=1e-6)

    def test_mds_too_high_ignored(self, bl):
        """Si MDS > umbral de hidratación, la planta no está completamente hidratada."""
        result = bl.update_rain(tc_measured_c=24.5, ta_c=30.0, vpd_kpa=2.0,
                                mds_um=MDS_HYDRATED_THRESHOLD_UM + 10.0,
                                rain_mm=15.0, date="2025-11-15")
        assert result["updated"] is False
        assert bl.state.n_rain_events == 0

    def test_ema_convergence_multiple_events(self, bl):
        """Con suficientes eventos iguales, el offset converge al valor correcto."""
        for i in range(20):
            bl.update_rain(tc_measured_c=25.0, ta_c=30.0, vpd_kpa=2.0,
                           mds_um=40.0, rain_mm=8.0,
                           date=f"2025-11-{i+1:02d}")
        # NWSB = 30 - 0.45*2 = 29.1°C → offset = 25 - 29.1 = -4.1°C
        expected_nwsb = 30.0 - 0.45 * 2.0
        expected_offset = 25.0 - expected_nwsb
        assert bl.state.tc_wet_offset == pytest.approx(expected_offset, abs=0.5)

    def test_calibration_quality_progresses(self, bl):
        assert bl.state.calibration_quality == "factory"
        for i in range(5):
            bl.update_rain(tc_measured_c=24.5, ta_c=30.0, vpd_kpa=2.0,
                           mds_um=40.0, rain_mm=10.0,
                           date=f"2025-11-{i+1:02d}")
        assert bl.state.calibration_quality in ("field_good", "field_excellent")


# ─────────────────────────────────────────────
# Tests — update_scholander
# ─────────────────────────────────────────────

class TestUpdateScholander:

    def test_scholander_updates_offset(self, bl):
        result = bl.update_scholander(tc_measured_c=26.0, ta_c=32.0, vpd_kpa=2.5,
                                      psi_stem_mpa=-0.5, mds_um=60.0,
                                      date="2025-12-01")
        assert result["updated"] is True
        assert bl.state.n_scholander_updates == 1

    def test_scholander_stressed_plant_ignored(self, bl):
        """No actualizar con Scholander si la planta está estresada (psi < -1.0 MPa)."""
        result = bl.update_scholander(tc_measured_c=38.0, ta_c=34.0, vpd_kpa=3.0,
                                      psi_stem_mpa=-1.5, mds_um=300.0,
                                      date="2025-12-01")
        assert result["updated"] is False
        assert bl.state.n_scholander_updates == 0

    def test_scholander_learning_rate_scaled_by_confidence(self, tmp_dir):
        """Confianza baja (MDS alto) reduce el learning rate → menor actualización."""
        bl_low = CWSIBaseline.load("LOW", tmp_dir)
        bl_high = CWSIBaseline.load("HIGH", tmp_dir)
        kwargs = dict(tc_measured_c=26.0, ta_c=32.0, vpd_kpa=2.5,
                      psi_stem_mpa=-0.4, date="2025-12-01")
        bl_low.update_scholander(mds_um=30.0, **kwargs)
        bl_high.update_scholander(mds_um=400.0, **kwargs)
        # MDS bajo → confianza alta → mayor |offset|
        assert abs(bl_low.state.tc_wet_offset) >= abs(bl_high.state.tc_wet_offset)


# ─────────────────────────────────────────────
# Tests — tc_wet_effective / tc_dry_effective
# ─────────────────────────────────────────────

class TestEffectiveTemperatures:

    def test_without_offset_equals_nwsb(self, bl):
        """Sin offset, tc_wet_effective == NWSB."""
        ta, vpd = 30.0, 2.0
        tc_wet = bl.tc_wet_effective(ta, vpd)
        expected = ta - 0.45 * vpd
        assert tc_wet == pytest.approx(expected, abs=0.01)

    def test_offset_applied_wet(self, bl):
        bl.state.tc_wet_offset = 1.5
        tc_wet = bl.tc_wet_effective(30.0, 2.0)
        expected_nwsb = 30.0 - 0.45 * 2.0
        assert tc_wet == pytest.approx(expected_nwsb + 1.5, abs=0.01)

    def test_dry_ref_base_without_offset(self, bl):
        """Tc_dry sin offset = Ta + 3.5 (Bellvert 2016)."""
        tc_dry = bl.tc_dry_effective(30.0, 2.0)
        assert tc_dry == pytest.approx(33.5, abs=0.01)

    def test_dry_ref_offset_applied(self, bl):
        bl.state.tc_dry_offset = -0.8
        tc_dry = bl.tc_dry_effective(30.0, 2.0)
        assert tc_dry == pytest.approx(33.5 - 0.8, abs=0.01)


# ─────────────────────────────────────────────
# Tests — check_drift
# ─────────────────────────────────────────────

class TestDriftDetection:

    def test_no_drift_healthy_range(self, bl):
        for v in [0.3, 0.4, 0.5, 0.45, 0.35, 0.42, 0.38, 0.47, 0.33, 0.41]:
            bl.add_cwsi_sample(v)
        result = bl.check_drift()
        assert result["drift_detected"] is False
        assert not bl.state.drift_alert

    def test_low_drift_detection(self, bl):
        """CWSI permanentemente bajo → baseline alto / sensor cubierto."""
        # Usar valores con variación mínima pero media < DRIFT_LOW_THRESHOLD
        for i in range(15):
            bl.add_cwsi_sample(0.005 + (i % 3) * 0.003)  # media ≈ 0.011, std > 0.01
        result = bl.check_drift()
        assert result["drift_detected"] is True
        assert result["direction"] == "low"
        assert bl.state.drift_alert

    def test_high_drift_detection(self, bl):
        """CWSI permanentemente alto → baseline bajo / sensor desconectado."""
        # Usar valores con variación mínima pero media > DRIFT_HIGH_THRESHOLD
        for i in range(15):
            bl.add_cwsi_sample(0.985 + (i % 3) * 0.004)  # media ≈ 0.989, std > 0.01
        result = bl.check_drift()
        assert result["drift_detected"] is True
        assert result["direction"] == "high"
        assert bl.state.drift_alert

    def test_dead_drift_detection(self, bl):
        """CWSI constante → señal muerta (std ≈ 0)."""
        for _ in range(15):
            bl.add_cwsi_sample(0.4500)   # mismo valor → std = 0
        result = bl.check_drift()
        # Debe detectar señal muerta (std < DRIFT_STD_MIN)
        assert result["drift_detected"] is True
        assert result["direction"] == "dead"

    def test_insufficient_samples_no_drift(self, bl):
        """Con pocas muestras no se puede detectar drift."""
        bl.add_cwsi_sample(0.01)
        result = bl.check_drift()
        assert result["drift_detected"] is False


# ─────────────────────────────────────────────
# Tests — Constantes del módulo
# ─────────────────────────────────────────────

class TestConstants:

    def test_learning_rates_positive(self):
        assert 0.0 < LEARNING_RATE_RAIN <= 1.0
        assert 0.0 < LEARNING_RATE_SCHOLANDER <= 1.0

    def test_rain_lr_greater_than_scholander_lr(self):
        """Rain LR más agresivo (evento fisiológico fuerte)."""
        assert LEARNING_RATE_RAIN > LEARNING_RATE_SCHOLANDER

    def test_rain_threshold_positive(self):
        assert RAIN_THRESHOLD_MM > 0.0

    def test_mds_hydrated_threshold_positive(self):
        assert MDS_HYDRATED_THRESHOLD_UM > 0.0


# ─────────────────────────────────────────────
# Tests — Persistencia JSON
# ─────────────────────────────────────────────

class TestPersistence:

    def test_json_roundtrip(self, tmp_dir):
        bl = CWSIBaseline.load("N03", tmp_dir)
        bl.update_rain(tc_measured_c=24.0, ta_c=30.0, vpd_kpa=2.0,
                       mds_um=45.0, rain_mm=12.0, date="2025-11-01")
        bl.save(tmp_dir)

        path = os.path.join(tmp_dir, "baseline_N03.json")
        assert os.path.exists(path)

        with open(path, "r") as f:
            data = json.load(f)
        assert data["node_id"] == "N03"
        assert data["n_rain_events"] == 1

    def test_save_stores_offset(self, tmp_dir):
        bl = CWSIBaseline.load("N04", tmp_dir)
        bl.update_rain(tc_measured_c=25.0, ta_c=32.0, vpd_kpa=2.5,
                       mds_um=50.0, rain_mm=10.0, date="2025-11-10")
        offset_before = bl.state.tc_wet_offset
        bl.save(tmp_dir)
        bl2 = CWSIBaseline.load("N04", tmp_dir)
        assert bl2.state.tc_wet_offset == pytest.approx(offset_before, abs=0.001)
