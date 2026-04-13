"""
Tests — Modulo Dendrometria (dendrometry.py)
Validacion de la implementacion MDS + psi_stem para Malbec.
Fernandez & Cuevas (2010) + Naor (2000) + Perez-Lopez (2008).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
from datetime import datetime
from dendrometry import (
    DendrometryEngine, TrunkDiameterReading, DailyDendrometryResult,
    DENDRO_COEFFICIENTS,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def engine():
    return DendrometryEngine("malbec")

@pytest.fixture
def coef():
    return DENDRO_COEFFICIENTS["malbec"]


def make_readings(d_values, t_values=None, sensor_id="D01"):
    """Genera lista de TrunkDiameterReading con diametros y temperaturas dados."""
    if t_values is None:
        t_values = [25.0] * len(d_values)
    return [
        TrunkDiameterReading(
            timestamp=datetime(2026, 1, 15, h, 0),
            diameter_um=float(d),
            temperature_c=float(t),
            sensor_id=sensor_id,
        )
        for h, (d, t) in enumerate(zip(d_values, t_values), start=6)
    ]


# ─────────────────────────────────────────────
# Tests — Instanciacion
# ─────────────────────────────────────────────

class TestDendrometryEngineInit:

    def test_malbec_instancia_ok(self):
        e = DendrometryEngine("malbec")
        assert e.crop == "malbec"

    def test_cultivo_invalido_error(self):
        with pytest.raises(ValueError, match="no reconocido"):
            DendrometryEngine("frutilla")

    def test_coeficientes_cargados(self, engine, coef):
        assert engine.coef["psi_a"] == coef["psi_a"]
        assert engine.coef["psi_b"] == coef["psi_b"]
        assert engine.coef["mds_critical"] > engine.coef["mds_severe"]


# ─────────────────────────────────────────────
# Tests — Calculo MDS
# ─────────────────────────────────────────────

class TestMDSCalculation:

    def test_mds_basico(self, engine):
        """MDS = D_max - D_min antes de correccion termica."""
        readings = make_readings(
            [25400, 25410, 25395, 25380, 25350, 25360, 25370, 25380],
            t_values=[22, 25, 28, 30, 32, 31, 28, 25],
        )
        result = engine.mds(readings)
        assert result["d_max_um"] == pytest.approx(25410.0)
        assert result["d_min_um"] == pytest.approx(25350.0)
        assert result["mds_raw_um"] == pytest.approx(60.0)

    def test_correccion_termica_reduce_mds(self, engine):
        """La correccion termica debe reducir el MDS raw."""
        readings = make_readings(
            [25400, 25400, 25320, 25300, 25280, 25300, 25320, 25340],
            t_values=[20, 22, 28, 34, 38, 36, 30, 24],  # delta_T = 18 degC
        )
        result = engine.mds(readings)
        alpha = engine.coef["thermal_alpha_um_per_C"]
        expected_correction = alpha * result["delta_T_trunk_c"]
        assert result["mds_corrected_um"] < result["mds_raw_um"]
        assert result["mds_corrected_um"] == pytest.approx(
            result["mds_raw_um"] - expected_correction, abs=0.1
        )

    def test_correccion_termica_no_negativa(self, engine):
        """MDS corregido nunca debe ser negativo."""
        # Lecturas con delta_T enorme — la correccion no debe hacer MDS negativo
        readings = make_readings(
            [25400, 25402, 25401, 25400],
            t_values=[15, 50, 50, 15],  # delta_T = 35 degC, MDS_raw muy pequeno
        )
        result = engine.mds(readings)
        assert result["mds_corrected_um"] >= 0.0

    def test_pocas_lecturas_error(self, engine):
        """Menos de 4 lecturas debe lanzar ValueError."""
        readings = make_readings([25400, 25380, 25370])
        with pytest.raises(ValueError, match="al menos 4 lecturas"):
            engine.mds(readings)

    def test_n_readings_correcto(self, engine):
        readings = make_readings([25400, 25390, 25380, 25370, 25360, 25370])
        result = engine.mds(readings)
        assert result["n_readings"] == 6


# ─────────────────────────────────────────────
# Tests — psi_stem desde MDS
# ─────────────────────────────────────────────

class TestPsiStemFromMDS:

    def test_mds_cero_es_psi_a(self, engine, coef):
        """Con MDS=0, psi_stem debe ser psi_a (intercept)."""
        psi = engine.psi_stem_from_mds(0.0)
        assert psi == pytest.approx(coef["psi_a"], abs=0.001)

    def test_pendiente_negativa(self, engine):
        """A mayor MDS, psi_stem mas negativo."""
        psi_low = engine.psi_stem_from_mds(50.0)
        psi_high = engine.psi_stem_from_mds(300.0)
        assert psi_high < psi_low

    def test_mds_150_moderado(self, engine):
        """MDS=150 um debe dar psi_stem cerca de -1.35 MPa (Naor 2000)."""
        psi = engine.psi_stem_from_mds(150.0)
        # psi = -0.15 + (-0.008 * 150) = -0.15 - 1.20 = -1.35
        assert psi == pytest.approx(-1.35, abs=0.01)

    def test_mds_60_sin_estres(self, engine):
        """MDS=60 um (referencia sin estres) debe dar psi >= -0.63 MPa."""
        psi = engine.psi_stem_from_mds(60.0)
        # psi = -0.15 + (-0.008 * 60) = -0.15 - 0.48 = -0.63
        assert psi == pytest.approx(-0.63, abs=0.01)

    def test_umbral_rescate_alcanzado(self, engine):
        """El umbral de rescate (-1.5 MPa) debe alcanzarse antes del mds_critical."""
        psi_rescue = -1.5
        # Despejar MDS: MDS = (psi - psi_a) / psi_b
        coef = engine.coef
        mds_rescue = (psi_rescue - coef["psi_a"]) / coef["psi_b"]
        # mds_rescue debe ser menor que mds_critical (400 um)
        assert mds_rescue < coef["mds_critical"]
        # Y mayor que mds_ref_unstressed (60 um)
        assert mds_rescue > coef["mds_ref_unstressed"]


# ─────────────────────────────────────────────
# Tests — Clasificacion y alertas
# ─────────────────────────────────────────────

class TestClassification:

    def test_sin_estres(self, engine, coef):
        level, _, rescue = engine.classify(coef["mds_ref_unstressed"] - 10)
        assert level == "SIN_ESTRES"
        assert not rescue

    def test_estres_leve(self, engine, coef):
        mds = (coef["mds_ref_unstressed"] + coef["mds_trigger"]) / 2
        level, _, _ = engine.classify(mds)
        assert level == "ESTRES_LEVE"

    def test_estres_moderado(self, engine, coef):
        mds = (coef["mds_trigger"] + coef["mds_severe"]) / 2
        level, _, _ = engine.classify(mds)
        assert level == "ESTRES_MODERADO"

    def test_estres_severo(self, engine, coef):
        mds = (coef["mds_severe"] + coef["mds_critical"]) / 2
        level, _, _ = engine.classify(mds)
        assert level == "ESTRES_SEVERO"

    def test_estres_critico(self, engine, coef):
        level, _, _ = engine.classify(coef["mds_critical"] + 50)
        assert level == "ESTRES_CRITICO"

    def test_rescate_activado_psi(self, engine):
        """MDS que lleva a psi_stem < -1.5 MPa debe activar rescate."""
        # psi = -0.15 + (-0.008 * MDS) < -1.5  => MDS > 168.75
        _, _, rescue = engine.classify(200.0)
        assert rescue  # psi = -0.15 - 1.60 = -1.75 MPa

    def test_rescate_no_activado(self, engine):
        """MDS pequeno no debe activar rescate."""
        _, _, rescue = engine.classify(60.0)
        assert not rescue  # psi = -0.63 MPa > -1.5

    def test_alerta_rescate_menciona_mpa(self, engine):
        """El mensaje de rescate debe incluir el valor de psi_stem."""
        _, alert, _ = engine.classify(420.0)
        assert "RESCATE" in alert
        assert "MPa" in alert


# ─────────────────────────────────────────────
# Tests — Recuperacion nocturna
# ─────────────────────────────────────────────

class TestRecoveryRate:

    def test_recuperacion_completa(self, engine):
        """Si el diametro nocturno vuelve a D_max, recovery = 1.0."""
        d_min = 25300.0
        d_max = 25400.0
        night = make_readings([d_max, d_max, d_max, d_max])
        rec = engine.recovery_rate(night, d_min, d_max)
        assert rec == pytest.approx(1.0, abs=0.01)

    def test_recuperacion_parcial(self, engine):
        """Recuperacion de 80% del MDS debe retornar ~0.80."""
        d_min = 25300.0
        d_max = 25400.0
        mds = d_max - d_min   # 100 um
        d_dawn = d_min + 0.80 * mds   # 25380
        night = make_readings([d_dawn] * 4)
        rec = engine.recovery_rate(night, d_min, d_max)
        assert rec == pytest.approx(0.80, abs=0.02)

    def test_sin_lecturas_nocturnas_retorna_nan(self, engine):
        """Sin lecturas nocturnas, recovery_rate debe retornar nan."""
        rec = engine.recovery_rate([], 25300.0, 25400.0)
        assert np.isnan(rec)

    def test_mds_cero_retorna_uno(self, engine):
        """Con MDS=0 (sin contraccion), recovery_rate = 1.0."""
        d_ref = 25400.0
        rec = engine.recovery_rate(make_readings([d_ref] * 4), d_ref, d_ref)
        assert rec == pytest.approx(1.0, abs=0.01)


# ─────────────────────────────────────────────
# Tests — Analisis diario completo
# ─────────────────────────────────────────────

class TestAnalyzeDay:

    def test_result_es_dataclass(self, engine):
        readings = make_readings([25400, 25410, 25350, 25340, 25320, 25340, 25360, 25380])
        result = engine.analyze_day("2026-01-15", readings)
        assert isinstance(result, DailyDendrometryResult)

    def test_fecha_correcta(self, engine):
        readings = make_readings([25400, 25410, 25380, 25350, 25330, 25350, 25370, 25390])
        result = engine.analyze_day("2026-01-15", readings)
        assert result.date == "2026-01-15"

    def test_rescue_required_propagado(self, engine):
        """Lecturas con MDS muy alto deben activar rescue_required."""
        # MDS raw ~450 um -> psi < -1.5 MPa
        d_min = 25000.0
        d_max = 25450.0
        readings = make_readings(
            [d_max, d_max, d_max * 0.999, d_max * 0.998,
             d_min, d_min * 1.001, d_min * 1.003, d_min * 1.006],
            t_values=[20.0] * 8,   # temperatura constante -> delta_T = 0 -> no hay correccion
        )
        result = engine.analyze_day("2026-01-15", readings)
        assert result.rescue_required

    def test_recuperacion_baja_en_alerta(self, engine):
        """Baja recuperacion nocturna debe aparecer en el texto de alerta."""
        readings = make_readings([25400, 25410, 25380, 25350, 25330, 25350, 25370, 25390])
        # Simulamos recuperacion parcial del 50%
        d_min = 25330.0
        d_max = 25410.0
        d_dawn = d_min + 0.50 * (d_max - d_min)   # 50% de recuperacion
        night = make_readings([d_dawn] * 4)
        result = engine.analyze_day("2026-01-15", readings,
                                    readings_night=night,
                                    d_min_prev=d_min, d_max_prev=d_max)
        # Con recuperacion baja y sin rescate, la alerta debe mencionarlo
        if not result.rescue_required:
            assert "Recuperacion" in result.alert or "recuperacion" in result.alert.lower()

    def test_n_readings_en_resultado(self, engine):
        readings = make_readings([25400, 25390, 25370, 25350, 25340, 25350, 25365, 25380])
        result = engine.analyze_day("2026-01-15", readings)
        assert result.n_readings == len(readings)

    def test_crop_en_resultado(self, engine):
        readings = make_readings([25400, 25390, 25380, 25360, 25350, 25360, 25370, 25390])
        result = engine.analyze_day("2026-01-15", readings)
        assert result.crop == "malbec"
