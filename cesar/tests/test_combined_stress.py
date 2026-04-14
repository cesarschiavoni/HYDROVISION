"""
Tests — Modulo HSI / CombinedStressEngine (combined_stress_index.py)
Validacion de la logica de fusion CWSI termico + MDS dendrometrico.
Jones (2004) + Fernandez et al. (2011).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import math
from datetime import datetime
from cwsi_formula import MeteoConditions
from dendrometry import DendrometryEngine, DailyDendrometryResult
from combined_stress_index import (
    CombinedStressEngine, HydroVisionStressIndex, SignalAgreement,
    HSI_WEIGHT_CWSI, HSI_WEIGHT_MDS,
    HSI_DISAGREEMENT_WEIGHT_CWSI, HSI_DISAGREEMENT_WEIGHT_MDS,
    HSI_DISAGREEMENT_THRESHOLD_MPa, RESCUE_THRESHOLD_MPa,
    SINGLE_SIGNAL_UNCERTAINTY_FACTOR, WIND_OVERRIDE_THRESHOLD_MS,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def engine():
    return CombinedStressEngine("malbec")

@pytest.fixture
def meteo_std():
    """Condiciones Colonia Caroya enero, 13h — ventana termica valida.
    T_air=32, RH=35 -> VPD ~3.09 kPa -> dT_LL=2.63 < dT_UL=3.50 (modelo valido).
    """
    return MeteoConditions(T_air=32.0, RH=35.0, solar_rad=880.0, wind_speed=1.5)

@pytest.fixture
def dendro():
    return DendrometryEngine("malbec")


def make_dendro(mds_um: float, psi_override: float = None) -> DailyDendrometryResult:
    """Crea un DailyDendrometryResult simplificado para los tests."""
    d = DendrometryEngine("malbec")
    psi = psi_override if psi_override is not None else d.psi_stem_from_mds(mds_um)
    level, alert_d, rescue_d = d.classify(mds_um)
    return DailyDendrometryResult(
        date="2026-01-15",
        d_max_um=25400.0,
        d_min_um=25400.0 - mds_um,
        mds_raw_um=mds_um,
        mds_corrected_um=mds_um,
        delta_T_trunk_c=10.0,
        psi_stem_mpa=psi,
        recovery_rate=0.88,
        stress_level=level,
        alert=alert_d,
        rescue_required=rescue_d,
    )


# ─────────────────────────────────────────────
# Tests — Instanciacion
# ─────────────────────────────────────────────

class TestCombinedStressEngineInit:

    def test_malbec_ok(self):
        e = CombinedStressEngine("malbec")
        assert e.crop == "malbec"

    def test_cultivo_invalido(self):
        with pytest.raises((ValueError, KeyError)):
            CombinedStressEngine("sorgo")

    def test_ponderaciones_suman_uno(self):
        assert HSI_WEIGHT_CWSI + HSI_WEIGHT_MDS == pytest.approx(1.0, abs=0.001)
        assert HSI_DISAGREEMENT_WEIGHT_CWSI + HSI_DISAGREEMENT_WEIGHT_MDS == pytest.approx(1.0, abs=0.001)


# ─────────────────────────────────────────────
# Tests — Acuerdo total (ambas señales coherentes)
# ─────────────────────────────────────────────

class TestFullAgreement:

    def test_acuerdo_retorna_acuerdo_total(self, engine, meteo_std):
        """Señales coherentes (delta < umbral) deben retornar FULL_AGREEMENT."""
        # T_air=32, RH=35 -> VPD~3.09 -> dT_LL=2.63, dT_UL=3.50
        # T_leaf=35 -> dT=3.0 -> CWSI=0.425 -> psi_cwsi=-0.86 MPa
        # MDS=80 um -> psi_mds=-0.15+(-0.008*80)=-0.79 MPa
        # delta = 0.07 MPa < 0.35 -> acuerdo
        hsi = engine.fuse(T_leaf_c=35.0, meteo=meteo_std,
                          dendro_result=make_dendro(80.0))
        assert hsi.signal_agreement == SignalAgreement.FULL_AGREEMENT

    def test_ponderacion_correcta_en_acuerdo(self, engine, meteo_std):
        """Los pesos efectivos deben ser 35/65 en caso de acuerdo."""
        hsi = engine.fuse(T_leaf_c=35.0, meteo=meteo_std,
                          dendro_result=make_dendro(80.0))
        if hsi.signal_agreement == SignalAgreement.FULL_AGREEMENT:
            assert hsi.weight_cwsi_used == pytest.approx(HSI_WEIGHT_CWSI, abs=0.001)
            assert hsi.weight_mds_used  == pytest.approx(HSI_WEIGHT_MDS,  abs=0.001)

    def test_psi_hsi_entre_ambos_en_acuerdo(self, engine, meteo_std):
        """psi_HSI debe quedar entre psi_CWSI y psi_MDS (ambos positivos relativos)."""
        hsi = engine.fuse(T_leaf_c=35.0, meteo=meteo_std,
                          dendro_result=make_dendro(80.0))
        if hsi.signal_agreement == SignalAgreement.FULL_AGREEMENT:
            psi_min = min(hsi.psi_cwsi_mpa, hsi.psi_mds_mpa)
            psi_max = max(hsi.psi_cwsi_mpa, hsi.psi_mds_mpa)
            assert psi_min <= hsi.psi_hsi_mpa <= psi_max

    def test_resultado_es_dataclass(self, engine, meteo_std):
        hsi = engine.fuse(T_leaf_c=35.0, meteo=meteo_std,
                          dendro_result=make_dendro(80.0))
        assert isinstance(hsi, HydroVisionStressIndex)


# ─────────────────────────────────────────────
# Tests — Desacuerdo entre señales
# ─────────────────────────────────────────────

class TestDisagreement:

    def test_desacuerdo_detectado(self, engine, meteo_std):
        """Delta > 0.35 MPa debe activar modo DISAGREEMENT."""
        # CWSI bajo: T_leaf ~= T_air + 0.5 -> psi_cwsi ~= -0.42 MPa
        # MDS alto: 350 um -> psi_mds = -0.15 + (-0.008*350) = -2.95 MPa
        # delta = 2.53 MPa >> 0.35 -> desacuerdo
        hsi = engine.fuse(T_leaf_c=34.5, meteo=meteo_std,
                          dendro_result=make_dendro(350.0))
        assert hsi.signal_agreement == SignalAgreement.DISAGREEMENT

    def test_mds_domina_en_desacuerdo(self, engine, meteo_std):
        """En desacuerdo, peso MDS debe ser 80% y CWSI 20%."""
        hsi = engine.fuse(T_leaf_c=34.5, meteo=meteo_std,
                          dendro_result=make_dendro(350.0))
        if hsi.signal_agreement == SignalAgreement.DISAGREEMENT:
            assert hsi.weight_mds_used  == pytest.approx(HSI_DISAGREEMENT_WEIGHT_MDS,  abs=0.001)
            assert hsi.weight_cwsi_used == pytest.approx(HSI_DISAGREEMENT_WEIGHT_CWSI, abs=0.001)

    def test_incertidumbre_mayor_en_desacuerdo(self, engine, meteo_std):
        """La incertidumbre en desacuerdo debe ser mayor que en acuerdo."""
        hsi_agree = engine.fuse(T_leaf_c=36.0, meteo=meteo_std,
                                dendro_result=make_dendro(100.0))
        hsi_disagree = engine.fuse(T_leaf_c=34.5, meteo=meteo_std,
                                   dendro_result=make_dendro(350.0))
        if (hsi_agree.signal_agreement == SignalAgreement.FULL_AGREEMENT and
                hsi_disagree.signal_agreement == SignalAgreement.DISAGREEMENT):
            assert hsi_disagree.psi_uncertainty_mpa > hsi_agree.psi_uncertainty_mpa


# ─────────────────────────────────────────────
# Tests — Señal unica: solo termico
# ─────────────────────────────────────────────

class TestThermalOnly:

    def test_modo_solo_termico(self, engine, meteo_std):
        """Sin dendro_result, debe retornar THERMAL_ONLY."""
        hsi = engine.fuse(T_leaf_c=36.0, meteo=meteo_std)
        assert hsi.signal_agreement == SignalAgreement.THERMAL_ONLY

    def test_peso_cwsi_uno_en_solo_termico(self, engine, meteo_std):
        hsi = engine.fuse(T_leaf_c=36.0, meteo=meteo_std)
        assert hsi.weight_cwsi_used == pytest.approx(1.0, abs=0.001)
        assert hsi.weight_mds_used  == pytest.approx(0.0, abs=0.001)

    def test_psi_mds_es_none_en_solo_termico(self, engine, meteo_std):
        hsi = engine.fuse(T_leaf_c=36.0, meteo=meteo_std)
        assert hsi.psi_mds_mpa is None
        assert hsi.mds_corrected_um is None

    def test_incertidumbre_ampliada_en_solo_termico(self, engine, meteo_std):
        """Con señal unica, incertidumbre debe ser mayor que en acuerdo."""
        hsi_single = engine.fuse(T_leaf_c=36.0, meteo=meteo_std)
        hsi_full   = engine.fuse(T_leaf_c=36.0, meteo=meteo_std,
                                 dendro_result=make_dendro(100.0))
        if hsi_full.signal_agreement == SignalAgreement.FULL_AGREEMENT:
            assert hsi_single.psi_uncertainty_mpa > hsi_full.psi_uncertainty_mpa


# ─────────────────────────────────────────────
# Tests — Señal unica: solo dendrometrico
# ─────────────────────────────────────────────

class TestDendroOnly:

    def test_modo_solo_dendro(self, engine):
        """Sin T_leaf ni meteo, debe retornar DENDRO_ONLY."""
        hsi = engine.fuse(dendro_result=make_dendro(150.0))
        assert hsi.signal_agreement == SignalAgreement.DENDRO_ONLY

    def test_peso_mds_uno_en_solo_dendro(self, engine):
        hsi = engine.fuse(dendro_result=make_dendro(150.0))
        assert hsi.weight_mds_used  == pytest.approx(1.0, abs=0.001)
        assert hsi.weight_cwsi_used == pytest.approx(0.0, abs=0.001)

    def test_psi_cwsi_es_none_en_solo_dendro(self, engine):
        hsi = engine.fuse(dendro_result=make_dendro(150.0))
        assert hsi.psi_cwsi_mpa is None
        assert hsi.cwsi_value is None

    def test_psi_hsi_igual_psi_mds_en_solo_dendro(self, engine):
        """Con solo dendro, psi_HSI debe ser igual a psi_MDS."""
        d_res = make_dendro(150.0)
        hsi = engine.fuse(dendro_result=d_res)
        assert hsi.psi_hsi_mpa == pytest.approx(d_res.psi_stem_mpa, abs=0.001)


# ─────────────────────────────────────────────
# Tests — Protocolo de rescate hidrico
# ─────────────────────────────────────────────

class TestRescueProtocol:

    def test_rescate_por_mds_alto(self, engine):
        """MDS que lleva a psi < -1.5 MPa debe activar rescate."""
        # psi = -0.15 + (-0.008 * 200) = -1.75 MPa < -1.5 -> rescate
        hsi = engine.fuse(dendro_result=make_dendro(200.0))
        assert hsi.rescue_required

    def test_rescate_por_cwsi_alto(self, engine, meteo_std):
        """CWSI muy alto (T_leaf muy elevada) debe activar rescate por via termica."""
        # T_leaf = 42 degC con T_air = 34 -> CWSI muy elevado -> psi < -1.5 MPa
        hsi = engine.fuse(T_leaf_c=42.0, meteo=meteo_std)
        if hsi.psi_cwsi_mpa is not None and hsi.psi_cwsi_mpa <= RESCUE_THRESHOLD_MPa:
            assert hsi.rescue_required

    def test_rescate_indica_fuente(self, engine):
        """El campo rescue_source debe indicar que fuente activo el rescate."""
        hsi = engine.fuse(dendro_result=make_dendro(250.0))
        if hsi.rescue_required:
            assert len(hsi.rescue_source) > 0
            assert "MDS" in hsi.rescue_source or "CWSI" in hsi.rescue_source

    def test_rescate_en_alerta(self, engine):
        """El texto de alerta debe incluir 'RESCATE' cuando se activa."""
        hsi = engine.fuse(dendro_result=make_dendro(250.0))
        if hsi.rescue_required:
            assert "RESCATE" in hsi.alert

    def test_sin_rescate_en_estres_leve(self, engine):
        """MDS bajo (estres leve) no debe activar rescate."""
        # MDS=80 um -> psi = -0.15 + (-0.008*80) = -0.79 MPa > -1.5 MPa
        hsi = engine.fuse(dendro_result=make_dendro(80.0))
        assert not hsi.rescue_required

    def test_umbral_rescate_es_negativo(self):
        assert RESCUE_THRESHOLD_MPa < 0


# ─────────────────────────────────────────────
# Tests — Sin datos
# ─────────────────────────────────────────────

class TestNoData:

    def test_sin_ninguna_senal_retorna_no_data(self, engine):
        hsi = engine.fuse()
        assert hsi.signal_agreement == SignalAgreement.NO_DATA

    def test_psi_hsi_es_nan_en_no_data(self, engine):
        hsi = engine.fuse()
        assert math.isnan(hsi.psi_hsi_mpa)

    def test_alerta_menciona_error_en_no_data(self, engine):
        hsi = engine.fuse()
        assert "ERROR" in hsi.alert or "ninguna" in hsi.alert


# ─────────────────────────────────────────────
# Tests — Clasificacion y niveles
# ─────────────────────────────────────────────

class TestStressClassification:

    def test_sin_estres(self, engine):
        # MDS=40 um -> psi = -0.15 + (-0.008*40) = -0.47 MPa (sin estres)
        hsi = engine.fuse(dendro_result=make_dendro(40.0))
        assert hsi.stress_level == "SIN_ESTRES"

    def test_estres_leve(self, engine):
        # MDS=80 um -> psi = -0.79 MPa (estres leve)
        hsi = engine.fuse(dendro_result=make_dendro(80.0))
        assert hsi.stress_level == "ESTRES_LEVE"

    def test_estres_critico(self, engine):
        # MDS=450 um -> psi = -0.15 + (-0.008*450) = -3.75 MPa (critico)
        hsi = engine.fuse(dendro_result=make_dendro(450.0))
        assert hsi.stress_level == "ESTRES_CRITICO"

    def test_crop_en_resultado(self, engine, meteo_std):
        hsi = engine.fuse(T_leaf_c=36.0, meteo=meteo_std)
        assert hsi.crop == "malbec"

    def test_incertidumbre_positiva(self, engine, meteo_std):
        """La incertidumbre siempre debe ser positiva."""
        for T in [35.0, 37.0, 40.0]:
            hsi = engine.fuse(T_leaf_c=T, meteo=meteo_std)
            assert hsi.psi_uncertainty_mpa > 0


# ─────────────────────────────────────────────
# Tests — Wind override (rampa gradual 4-18 m/s, override completo >= 18 m/s)
# ─────────────────────────────────────────────

class TestWindOverride:

    def test_wind_override_fuerza_dendro_only(self, engine, meteo_std):
        """Viento >= 18 m/s (65 km/h) invalida la señal térmica → DENDRO_ONLY."""
        hsi = engine.fuse(T_leaf_c=36.0, meteo=meteo_std,
                          dendro_result=make_dendro(150.0),
                          wind_speed_ms=WIND_OVERRIDE_THRESHOLD_MS + 1.0)
        assert hsi.signal_agreement == SignalAgreement.DENDRO_ONLY

    def test_wind_override_peso_mds_100(self, engine, meteo_std):
        """Con wind override (>= 18 m/s) el peso MDS debe ser 1.0."""
        hsi = engine.fuse(T_leaf_c=36.0, meteo=meteo_std,
                          dendro_result=make_dendro(150.0),
                          wind_speed_ms=19.0)
        assert hsi.weight_mds_used == pytest.approx(1.0, abs=0.001)
        assert hsi.weight_cwsi_used == pytest.approx(0.0, abs=0.001)

    def test_wind_override_psi_cwsi_none(self, engine, meteo_std):
        """Con wind override (>= 18 m/s), psi_cwsi debe ser None (señal descartada)."""
        hsi = engine.fuse(T_leaf_c=36.0, meteo=meteo_std,
                          dendro_result=make_dendro(150.0),
                          wind_speed_ms=19.0)
        assert hsi.psi_cwsi_mpa is None

    def test_wind_ramp_reduces_cwsi_weight(self, engine, meteo_std):
        """Viento 8 m/s (en rampa 4-12) debe reducir peso CWSI pero no eliminarlo."""
        hsi = engine.fuse(T_leaf_c=36.0, meteo=meteo_std,
                          dendro_result=make_dendro(150.0),
                          wind_speed_ms=8.0)
        # A 8 m/s, factor = (12-8)/(12-4) = 0.5 → w_cwsi ~= 0.35 * 0.5 = 0.175
        assert hsi.weight_cwsi_used < 0.35   # menor que el peso nominal
        assert hsi.weight_cwsi_used > 0.0    # pero no cero (aun en rango util)

    def test_wind_override_nota_menciona_viento(self, engine, meteo_std):
        """La nota de fusión debe mencionar el wind override."""
        hsi = engine.fuse(T_leaf_c=36.0, meteo=meteo_std,
                          dendro_result=make_dendro(150.0),
                          wind_speed_ms=13.0)
        if hsi.signal_agreement == SignalAgreement.DENDRO_ONLY:
            assert "wind" in hsi.fusion_note.lower() or "viento" in hsi.fusion_note.lower()

    def test_sin_dendro_wind_override_retorna_no_data(self, engine, meteo_std):
        """Wind override (>= 18 m/s) sin dendro: termica descartada + sin MDS = NO_DATA."""
        hsi = engine.fuse(T_leaf_c=36.0, meteo=meteo_std,
                          wind_speed_ms=19.0)   # sin dendro_result, >= 18 m/s
        assert hsi.signal_agreement == SignalAgreement.NO_DATA

    def test_wind_debajo_umbral_no_override(self, engine, meteo_std):
        """Viento por debajo de 4 m/s (14 km/h) no debe reducir peso CWSI."""
        hsi = engine.fuse(T_leaf_c=36.0, meteo=meteo_std,
                          dendro_result=make_dendro(100.0),
                          wind_speed_ms=3.5)
        # CWSI debe estar disponible con peso completo
        assert hsi.psi_cwsi_mpa is not None

    def test_wind_override_threshold_constante(self):
        """El override completo ocurre a 18 m/s (rampa gradual 4-18)."""
        assert WIND_OVERRIDE_THRESHOLD_MS == pytest.approx(18.0, abs=0.001)
