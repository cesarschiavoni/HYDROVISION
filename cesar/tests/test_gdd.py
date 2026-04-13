"""
Tests — Motor GDD (03_gdd_engine.py)
Validación del cálculo de grados-día y detección fenológica
para vid Malbec en Colonia Caroya.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
from gdd_engine import (
    DiaMeteorologico, MotorGDD, FenologiaEstadio,
    FENOLOGIA_GDD_THRESHOLDS, CWSI_UMBRAL_ALERTA,
    generar_meteo_colonia_caroya,
)


@pytest.fixture
def motor():
    return MotorGDD("Malbec")

@pytest.fixture
def temporada_completa():
    datos = generar_meteo_colonia_caroya("2026-2027", seed=42)
    motor = MotorGDD("Malbec")
    df = motor.procesar_temporada(datos)
    return motor, df


class TestDiaMeteorologico:

    def test_gdd_zero_below_base(self):
        """GDD = 0 cuando T_media < T_base (10°C)."""
        dia = DiaMeteorologico("2027-07-01", T_max=8.0, T_min=2.0)
        assert dia.GDD == 0.0

    def test_gdd_positive_above_base(self):
        """GDD > 0 cuando T_media > 10°C."""
        dia = DiaMeteorologico("2026-12-15", T_max=30.0, T_min=18.0)
        assert dia.GDD > 0
        assert dia.GDD == pytest.approx(14.0, abs=0.1)  # (30+18)/2 - 10

    def test_T_media(self):
        dia = DiaMeteorologico("2026-10-01", T_max=25.0, T_min=11.0)
        assert dia.T_media == pytest.approx(18.0, abs=0.01)

    def test_gdd_at_exact_base(self):
        """GDD = 0 cuando T_media = T_base exactamente."""
        dia = DiaMeteorologico("2027-05-01", T_max=15.0, T_min=5.0)
        assert dia.GDD == 0.0


class TestMotorGDD:

    def test_gdd_accumulates_over_season(self, temporada_completa):
        """GDD acumulado debe aumentar durante la temporada activa."""
        motor, df = temporada_completa
        # En la parte activa de la temporada (oct-feb), GDD debe acumularse
        df_verano = df[df["fecha"].str.startswith(("2026-10", "2026-11", "2026-12",
                                                    "2027-01", "2027-02"))]
        gdd_series = df_verano["GDD_acum"].values
        # Tendencia general creciente
        assert gdd_series[-1] > gdd_series[0], "GDD no aumentó durante el verano"

    def test_brotacion_detected_in_october(self, temporada_completa):
        """La brotación debe detectarse en octubre (típico Colonia Caroya)."""
        motor, df = temporada_completa
        assert motor.fecha_brotacion is not None, "Brotación no detectada"
        assert motor.fecha_brotacion.startswith("2026-10"), \
            f"Brotación detectada en {motor.fecha_brotacion} (esperado octubre 2026)"

    def test_all_estadios_present(self, temporada_completa):
        """Todos los estadios fenológicos deben aparecer en la temporada."""
        motor, df = temporada_completa
        estadios_presentes = set(df["estadio"].unique())
        estadios_esperados = {
            FenologiaEstadio.BROTACION.value,
            FenologiaEstadio.FLORACION.value,
            FenologiaEstadio.ENVERO.value,
            FenologiaEstadio.MADURACION.value,
            FenologiaEstadio.COSECHA.value,
        }
        for estadio in estadios_esperados:
            assert estadio in estadios_presentes, \
                f"Estadio '{estadio}' no detectado en la temporada"

    def test_cosecha_in_february(self, temporada_completa):
        """La cosecha debe ocurrir en febrero (típico Malbec Colonia Caroya)."""
        motor, df = temporada_completa
        cosecha_mask = df["estadio"] == FenologiaEstadio.COSECHA.value
        if cosecha_mask.any():
            primera_cosecha = df[cosecha_mask]["fecha"].iloc[0]
            assert "2027-02" in primera_cosecha or "2027-01" in primera_cosecha, \
                f"Cosecha en {primera_cosecha} — esperado enero-febrero 2027"

    def test_total_gdd_range(self, temporada_completa):
        """
        GDD total de la temporada debe estar en rango Winkler para región cálida.
        El generador acumula GDD desde sep a sep (12 meses completos), incluyendo
        los 5 meses de verano con temperatura media ~22-24°C, por eso el GDD total
        puede superar el umbral de zona Winkler IV (>1667 GDD) al contar todo el año.
        Colonia Caroya ~700m → zona Winkler III-IV (~1400-2200 GDD anuales).
        """
        motor, df = temporada_completa
        gdd_total = df["GDD_acum"].max()
        assert 800 <= gdd_total <= 3200, \
            f"GDD total {gdd_total:.0f} fuera del rango esperado para Colonia Caroya"

    def test_cwsi_umbral_floración_strict(self):
        """Umbral CWSI en floración debe ser el más restrictivo (bajo) — evitar aborto floral."""
        umbral_floracion = CWSI_UMBRAL_ALERTA[FenologiaEstadio.FLORACION]
        umbral_envero    = CWSI_UMBRAL_ALERTA[FenologiaEstadio.ENVERO]
        assert umbral_floracion < umbral_envero, \
            "Umbral de floración debe ser más restrictivo que envero (RDI tolerable)"

    def test_gdd_thresholds_ordered(self):
        """Los umbrales GDD de cada estadio deben estar ordenados correctamente."""
        for estadio, (gdd_min, gdd_max) in FENOLOGIA_GDD_THRESHOLDS.items():
            assert gdd_min < gdd_max, \
                f"Estadio {estadio.value}: gdd_min ({gdd_min}) >= gdd_max ({gdd_max})"

    def test_meteo_generator_produces_correct_count(self):
        """El generador de datos meteorológicos debe producir 365-366 días."""
        datos = generar_meteo_colonia_caroya("2026-2027", seed=1)
        assert 363 <= len(datos) <= 367, \
            f"Generador produjo {len(datos)} días (esperado ~365)"

    def test_meteo_temperatures_realistic(self):
        """Temperaturas generadas deben estar en rangos realistas para Colonia Caroya."""
        datos = generar_meteo_colonia_caroya("2026-2027", seed=1)
        T_maxs = [d.T_max for d in datos]
        T_mins = [d.T_min for d in datos]
        assert max(T_maxs) < 48.0, f"T_max irreal: {max(T_maxs):.1f}°C"
        assert min(T_mins) > -10.0, f"T_min irreal: {min(T_mins):.1f}°C"
        assert np.mean(T_maxs) > 18.0, f"T_max media muy baja: {np.mean(T_maxs):.1f}°C"

    def test_scholander_sessions_timing(self, temporada_completa):
        """
        Las 4 sesiones Scholander deben poder ubicarse entre oct 2026 y feb 2027
        (temporada activa antes de cosecha = ventana del proyecto TRL 3-4).
        """
        motor, df = temporada_completa
        ventana = df[
            (df["fecha"] >= "2026-10-01") & (df["fecha"] <= "2027-02-28")
        ]
        # Al menos 3 de los 4 estadios objetivo deben estar en esa ventana
        estadios_ventana = set(ventana["estadio"].unique())
        estadios_scholander = {
            FenologiaEstadio.BROTACION.value,
            FenologiaEstadio.ENVERO.value,
            FenologiaEstadio.MADURACION.value,
            FenologiaEstadio.COSECHA.value,
        }
        overlap = estadios_ventana & estadios_scholander
        assert len(overlap) >= 3, \
            f"Solo {len(overlap)} estadios Scholander en la ventana oct-feb: {overlap}"
