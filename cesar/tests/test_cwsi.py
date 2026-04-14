"""
Tests — Módulo CWSI (01_cwsi_formula.py)
Validación de la implementación de Jackson et al. (1981)
con coeficientes Bellvert 2016 (Malbec) y García-Tejero 2018 (Olivo).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
from cwsi_formula import CWSICalculator, MeteoConditions, CROP_COEFFICIENTS


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def calc_malbec():
    return CWSICalculator("malbec")

@pytest.fixture
def meteo_std():
    """Condiciones estándar de Colonia Caroya en enero (mediodía)."""
    return MeteoConditions(T_air=32.0, RH=35.0, solar_rad=880.0, wind_speed=1.5)

@pytest.fixture
def meteo_low_vpd():
    """Mañana fresca — VPD bajo."""
    return MeteoConditions(T_air=20.0, RH=70.0, solar_rad=450.0, wind_speed=0.8)


# ─────────────────────────────────────────────
# Tests — MeteoConditions
# ─────────────────────────────────────────────

class TestMeteoConditions:

    def test_vpd_positive(self, meteo_std):
        """VPD siempre debe ser positivo."""
        assert meteo_std.VPD > 0

    def test_vpd_range_verano(self, meteo_std):
        """En verano con RH=35% → VPD esperado ≈ 2.5-3.5 kPa."""
        assert 2.0 <= meteo_std.VPD <= 4.0, f"VPD={meteo_std.VPD:.3f} fuera de rango verano"

    def test_vpd_range_maniana(self, meteo_low_vpd):
        """Mañana fresca con RH=70% → VPD esperado ≈ 0.4-1.0 kPa."""
        assert 0.3 <= meteo_low_vpd.VPD <= 1.2, f"VPD={meteo_low_vpd.VPD:.3f} fuera de rango mañana"

    def test_vpd_formula_100rh(self):
        """Con HR=100%, VPD debe ser ≈ 0."""
        m = MeteoConditions(T_air=25, RH=100, solar_rad=500, wind_speed=1)
        assert abs(m.VPD) < 0.01

    def test_vpd_formula_0rh(self):
        """Con HR→0%, VPD ≈ es (presión de saturación)."""
        m = MeteoConditions(T_air=25, RH=0.1, solar_rad=500, wind_speed=1)
        es = 0.6108 * np.exp(17.27 * 25 / (25 + 237.3))
        assert abs(m.VPD - es) < 0.05

    def test_valid_capture_window(self, meteo_std):
        """Condiciones de mediodía verano → ventana válida."""
        assert meteo_std.is_valid_capture_window

    def test_invalid_low_radiation(self):
        """Radiación baja → no válido para captura."""
        m = MeteoConditions(T_air=25, RH=60, solar_rad=200, wind_speed=1)
        assert not m.is_valid_capture_window

    def test_invalid_high_wind(self):
        """Viento >= 18 m/s (65 km/h) → no válido para captura (override completo)."""
        m = MeteoConditions(T_air=32, RH=35, solar_rad=900, wind_speed=19.0)
        assert not m.is_valid_capture_window

    def test_wind_in_ramp_still_valid(self):
        """Viento 8 m/s (en rampa 4-18) → sigue válido para captura con peso reducido."""
        m = MeteoConditions(T_air=32, RH=35, solar_rad=900, wind_speed=8.0)
        assert m.is_valid_capture_window


# ─────────────────────────────────────────────
# Tests — CWSICalculator límites biofísicos
# ─────────────────────────────────────────────

class TestCWSILimits:

    def test_delta_T_LL_negative_low_vpd(self, calc_malbec):
        """ΔT_LL debe ser negativo con VPD bajo (hoja más fría que el aire)."""
        vpd_bajo = 0.5  # kPa
        assert calc_malbec.delta_T_LL(vpd_bajo) < 0, \
            "Planta bien hidratada con VPD bajo: T_hoja < T_aire esperado"

    def test_delta_T_LL_increases_with_vpd(self, calc_malbec):
        """ΔT_LL aumenta con VPD (relación lineal Bellvert 2016)."""
        dT_ll_low  = calc_malbec.delta_T_LL(0.5)
        dT_ll_high = calc_malbec.delta_T_LL(3.0)
        assert dT_ll_high > dT_ll_low

    def test_delta_T_UL_positive(self, calc_malbec):
        """ΔT_UL siempre positivo (hoja sin transpiración > T_aire)."""
        for vpd in [0.5, 1.0, 2.0, 3.5]:
            assert calc_malbec.delta_T_UL(vpd) > 0

    def test_delta_T_UL_greater_than_LL(self, calc_malbec):
        """
        ΔT_UL > ΔT_LL para VPD en rango válido del modelo Bellvert 2016 (0.3-3.5 kPa).
        El modelo lineal Bellvert no es válido para VPD > 3.5 kPa (condiciones extremas
        fuera del rango de calibración de la publicación).
        """
        # Límite biofísico: ΔT_LL = ΔT_UL cuando VPD = (c-a)/b = (3.50+1.97)/1.49 ≈ 3.67 kPa
        # El protocolo de captura requiere VPD > 0.5 y < 3.5 kPa (ventana válida del modelo)
        for vpd in np.arange(0.3, 3.5, 0.2):
            assert calc_malbec.delta_T_UL(vpd) > calc_malbec.delta_T_LL(vpd), \
                f"ΔT_UL ≤ ΔT_LL para VPD={vpd:.1f} kPa"

    def test_malbec_coefficients_from_bellvert(self, calc_malbec):
        """Verificar coeficientes Bellvert 2016 cargados correctamente."""
        coef = calc_malbec.coef
        assert coef["a"] == pytest.approx(-1.97, abs=0.01)
        assert coef["b"] == pytest.approx(1.49, abs=0.01)
        assert coef["c"] == pytest.approx(3.50, abs=0.01)


# ─────────────────────────────────────────────
# Tests — CWSI valores esperados
# ─────────────────────────────────────────────

class TestCWSIValues:

    def test_cwsi_zero_for_well_watered(self, calc_malbec, meteo_std):
        """Planta en ΔT_LL → CWSI ≈ 0."""
        T_leaf = meteo_std.T_air + calc_malbec.delta_T_LL(meteo_std.VPD)
        result = calc_malbec.cwsi(T_leaf, meteo_std)
        assert abs(result["cwsi"]) < 0.02, f"CWSI esperado ≈0, obtenido={result['cwsi']:.4f}"

    def test_cwsi_one_for_max_stress(self, calc_malbec, meteo_std):
        """Planta en ΔT_UL → CWSI ≈ 1."""
        T_leaf = meteo_std.T_air + calc_malbec.delta_T_UL(meteo_std.VPD)
        result = calc_malbec.cwsi(T_leaf, meteo_std)
        assert abs(result["cwsi"] - 1.0) < 0.02, f"CWSI esperado ≈1, obtenido={result['cwsi']:.4f}"

    def test_cwsi_mid_stress(self, calc_malbec, meteo_std):
        """Temperatura entre LL y UL → CWSI entre 0 y 1."""
        dT_ll = calc_malbec.delta_T_LL(meteo_std.VPD)
        dT_ul = calc_malbec.delta_T_UL(meteo_std.VPD)
        T_leaf = meteo_std.T_air + (dT_ll + dT_ul) / 2
        result = calc_malbec.cwsi(T_leaf, meteo_std)
        assert 0.45 <= result["cwsi"] <= 0.55, f"CWSI esperado ≈0.5, obtenido={result['cwsi']:.4f}"

    def test_cwsi_increases_with_leaf_temperature(self, calc_malbec, meteo_std):
        """CWSI debe aumentar monotónicamente con temperatura foliar."""
        T_leaves = np.linspace(28, 38, 20)
        cwsi_prev = -1.0
        for T in T_leaves:
            result = calc_malbec.cwsi(T, meteo_std)
            assert result["cwsi"] >= cwsi_prev - 1e-9, \
                f"CWSI no monótono: T={T:.1f}°C → CWSI={result['cwsi']:.4f} < {cwsi_prev:.4f}"
            cwsi_prev = result["cwsi"]

    def test_cwsi_range_colonia_caroya_verano(self, calc_malbec):
        """
        Para condiciones típicas de Colonia Caroya en verano (VPD ≤ 3.0 kPa),
        los CWSI deben estar en rangos coherentes con literatura.
        Referencia: Bellvert 2016 reporta CWSI 0.0-0.85 para vid Malbec.
        Nota: VPD debe estar en el rango de calibración del modelo (<3.5 kPa).
        T_air=32°C, RH=40% → VPD ≈ 2.73 kPa (dentro del rango Bellvert 2016).
        """
        meteo = MeteoConditions(T_air=32.0, RH=40.0, solar_rad=880.0, wind_speed=1.8)
        # Escenario bien regado: T_leaf ≈ T_air - 2°C (hoja más fría que el aire)
        r1 = calc_malbec.cwsi(30.0, meteo)
        assert r1["cwsi"] < 0.25, f"Vid bien regada: CWSI debería ser bajo, obtenido={r1['cwsi']:.3f}"

        # Escenario estrés severo: T_leaf ≈ T_air + 3.5°C
        r2 = calc_malbec.cwsi(35.5, meteo)
        assert r2["cwsi"] > 0.55, f"Vid bajo estrés severo: CWSI debería ser alto, obtenido={r2['cwsi']:.3f}"

    def test_cwsi_all_crops_valid(self, meteo_std):
        """Todos los cultivos configurados producen CWSI válido."""
        for crop in CROP_COEFFICIENTS:
            calc = CWSICalculator(crop)
            dT_ll = calc.delta_T_LL(meteo_std.VPD)
            dT_ul = calc.delta_T_UL(meteo_std.VPD)
            T_leaf = meteo_std.T_air + (dT_ll + dT_ul) / 2
            result = calc.cwsi(T_leaf, meteo_std)
            assert 0.0 <= result["cwsi"] <= 1.0, \
                f"CWSI fuera de rango para cultivo {crop}: {result['cwsi']}"

    def test_cwsi_classification_levels(self, calc_malbec, meteo_std):
        """Verificar clasificaciones agronomicas en el rango correcto."""
        test_cases = [
            (0.05, "SIN_ESTRES"),
            (0.20, "ESTRES_LEVE"),
            (0.45, "ESTRES_MODERADO"),
            (0.70, "ESTRES_SEVERO"),
            (0.90, "ESTRES_CRITICO"),
        ]
        for cwsi_val, expected_class in test_cases:
            classified = calc_malbec._classify(cwsi_val)
            assert classified == expected_class, \
                f"CWSI={cwsi_val} -> '{classified}', esperado '{expected_class}'"

    def test_cwsi_invalid_crop(self):
        """Cultivo no registrado debe lanzar ValueError."""
        with pytest.raises(ValueError, match="no reconocido"):
            CWSICalculator("limon_eureka_no_existe")


# ─────────────────────────────────────────────
# Tests — Batch processing y NETD
# ─────────────────────────────────────────────

class TestCWSIBatchAndSensitivity:

    def test_batch_same_as_scalar(self, calc_malbec, meteo_std):
        """CWSI batch debe dar mismo resultado que cálculo escalar."""
        T_array = np.array([28.0, 30.0, 32.0, 34.0, 36.0])
        cwsi_batch = calc_malbec.cwsi_batch(T_array, meteo_std)
        for i, T in enumerate(T_array):
            cwsi_scalar = calc_malbec.cwsi(T, meteo_std)["cwsi"]
            assert abs(cwsi_batch[i] - cwsi_scalar) < 1e-6, \
                f"Discrepancia batch vs escalar en T={T}°C: {cwsi_batch[i]:.6f} vs {cwsi_scalar:.6f}"

    def test_netd_50mk_error_below_005(self, calc_malbec, meteo_std):
        """
        NETD 50mK (FLIR Lepton 3.5, datos sintéticos pre-training): error CWSI < ±0.05.
        Referencia: Araújo-Paredes et al. (2022) — error < ±0.07 aceptable.
        """
        sens = calc_malbec.sensitivity_analysis(meteo_std)
        netd_error = sens["NETD_50mK_cwsi_error"]
        assert netd_error < 0.05, \
            f"Error CWSI por NETD 50mK = {netd_error:.4f} — excede ±0.05 umbral"

    def test_netd_100mk_mlx90640_pixel_unico(self, calc_malbec, meteo_std):
        """
        NETD 100mK (MLX90640, sensor de campo): error CWSI por píxel < ±0.07.
        Umbral Araújo-Paredes et al. (2022). Pixel único — sin promediar.
        """
        sens = calc_malbec.sensitivity_analysis(meteo_std)
        netd_error = sens["NETD_100mK_cwsi_error"]
        assert netd_error < 0.07, \
            f"Error CWSI por NETD 100mK (MLX90640 pixel único) = {netd_error:.4f} — excede ±0.07"

    def test_netd_efectivo_28px_below_001(self, calc_malbec, meteo_std):
        """
        NETD efectivo con 28 píxeles foliares promediados (MLX90640 campo):
        error CWSI < ±0.01. Es el error real del sistema completo.
        100mK / sqrt(28) ≈ 19mK → error CWSI ~±0.008.
        """
        sens = calc_malbec.sensitivity_analysis(meteo_std)
        netd_error = sens["NETD_efectivo_cwsi_error"]
        assert netd_error < 0.01, \
            f"Error CWSI efectivo (28 px promediados) = {netd_error:.4f} — excede ±0.01"

    def test_sensitivity_monotone(self, calc_malbec, meteo_std):
        """Sensibilidad (dCWSI/dT) debe ser positiva y acotada."""
        sens = calc_malbec.sensitivity_analysis(meteo_std)
        dCWSI_dT = sens["dCWSI_dT"]
        # La derivada debe ser positiva (CWSI aumenta con T_leaf)
        assert np.mean(dCWSI_dT[5:-5]) > 0  # ignorar bordes del gradiente numérico
        # Y acotada (no mayor a 1.0 CWSI/°C para condiciones normales)
        assert sens["cwsi_per_degree"] < 1.0
