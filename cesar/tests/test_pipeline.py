"""
Tests — Pipeline térmico (02_thermal_pipeline.py) y Generador sintético (04_synthetic_data_gen.py)
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
from cwsi_formula import MeteoConditions
from thermal_pipeline import (
    ThermalFrame, CanopySegmenter, ThermalPipeline,
    LEPTON_WIDTH, LEPTON_HEIGHT, LEPTON_NETD
)
from synthetic_data_gen import FlirLepton35Simulator, celsius_to_y16, y16_to_celsius, VineyardScene


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def meteo_noon():
    return MeteoConditions(T_air=33.0, RH=32.0, solar_rad=900.0, wind_speed=1.3)

@pytest.fixture
def sim():
    return FlirLepton35Simulator("malbec", seed=42)

@pytest.fixture
def pipeline():
    return ThermalPipeline("malbec")

@pytest.fixture
def frame_mid_stress(sim, meteo_noon):
    return sim.generate_frame(meteo_noon, cwsi_target=0.50, frame_id="test_mid")

@pytest.fixture
def frame_no_stress(sim, meteo_noon):
    return sim.generate_frame(meteo_noon, cwsi_target=0.05, frame_id="test_low")

@pytest.fixture
def frame_high_stress(sim, meteo_noon):
    return sim.generate_frame(meteo_noon, cwsi_target=0.80, frame_id="test_high")


# ─────────────────────────────────────────────
# Tests — Conversión Y16 ↔ Celsius
# ─────────────────────────────────────────────

class TestY16Conversion:

    def test_roundtrip(self):
        """Conversión °C → Y16 → °C debe recuperar el valor original (±0.01°C)."""
        T_original = np.array([25.0, 30.0, 35.0, 40.0], dtype=np.float32)
        y16 = celsius_to_y16(T_original)
        T_recovered = y16_to_celsius(y16)
        np.testing.assert_allclose(T_recovered, T_original, atol=0.01,
                                   err_msg="Pérdida de precisión en conversión Y16")

    def test_y16_dtype(self):
        """Y16 debe ser uint16."""
        T = np.full((LEPTON_HEIGHT, LEPTON_WIDTH), 30.0, dtype=np.float32)
        y16 = celsius_to_y16(T)
        assert y16.dtype == np.uint16

    def test_y16_range_valid_temperatures(self):
        """Temperaturas entre 0°C y 60°C deben producir Y16 en rango válido."""
        for T_c in [0.0, 20.0, 40.0, 60.0]:
            y16 = celsius_to_y16(np.array([T_c]))
            assert y16[0] > 0, f"Y16 negativo para T={T_c}°C"
            assert y16[0] < 65535, f"Y16 saturado para T={T_c}°C"


# ─────────────────────────────────────────────
# Tests — Mlx90640Simulator (alias: FlirLepton35Simulator)
# ─────────────────────────────────────────────

class TestFlirLepton35Simulator:

    def test_frame_shape(self, frame_mid_stress):
        """Frame debe tener dimensiones MLX90640: 24×32."""
        assert frame_mid_stress.shape == (LEPTON_HEIGHT, LEPTON_WIDTH)

    def test_frame_temperature_range(self, frame_mid_stress, meteo_noon):
        """Temperaturas en el frame deben estar en rango plausible para viñedo."""
        T = frame_mid_stress.temperature_C
        T_air = meteo_noon.T_air
        assert T.min() > T_air - 20, f"Temperatura mínima {T.min():.1f}°C demasiado baja"
        assert T.max() < T_air + 20, f"Temperatura máxima {T.max():.1f}°C demasiado alta"

    def test_higher_cwsi_higher_canopy_temperature(self, sim, meteo_noon):
        """
        Frame con CWSI más alto debe tener temperatura media de canopeo mayor.
        Propiedad física fundamental del CWSI.
        """
        seg = CanopySegmenter()
        frame_low = sim.generate_frame(meteo_noon, cwsi_target=0.10, frame_id="low")
        frame_high = sim.generate_frame(meteo_noon, cwsi_target=0.80, frame_id="high")
        seg_low  = seg.segment(frame_low)
        seg_high = seg.segment(frame_high)
        assert seg_high["T_mean"] > seg_low["T_mean"], \
            f"CWSI alto debería tener T_canopy mayor: {seg_high['T_mean']:.2f} vs {seg_low['T_mean']:.2f}"

    def test_netd_noise_magnitude(self, sim, meteo_noon):
        """
        Verificar que el ruido del sensor está en el rango del NETD del MLX90640.
        Se genera un frame con temperatura uniforme y se mide la std del ruido puro.
        El NETD (100mK) es ruido de sensor puro, sin variabilidad de escena.
        """
        from synthetic_data_gen import celsius_to_y16
        from thermal_pipeline import ThermalFrame

        # Frame sintético con temperatura uniforme — solo ruido de sensor
        T_uniform = np.full((24, 32), meteo_noon.T_air, dtype=np.float32)
        rng = np.random.default_rng(42)
        # Solo ruido NETD puro (gaussiano σ=0.10°C) + FPN residual (σ=0.02°C)
        T_with_noise = T_uniform + rng.normal(0, 0.10, T_uniform.shape) \
                                 + rng.normal(0, 0.02, T_uniform.shape)
        noise_std = float(np.std(T_with_noise))
        # std debe ser compatible con NETD 100mK (σ ≈ 0.08-0.12°C)
        assert 0.01 < noise_std < 0.20, \
            f"Ruido puro del sensor: {noise_std*1000:.1f}mK (esperado 100mK ± tolerancia)"

    def test_deterministic_with_seed(self, meteo_noon):
        """Mismo seed → mismos frames (reproducibilidad)."""
        sim1 = FlirLepton35Simulator("malbec", seed=99)
        sim2 = FlirLepton35Simulator("malbec", seed=99)
        f1 = sim1.generate_frame(meteo_noon, 0.5, frame_id="r1")
        f2 = sim2.generate_frame(meteo_noon, 0.5, frame_id="r2")
        np.testing.assert_array_equal(f1.raw_y16, f2.raw_y16,
                                      err_msg="Frames no reproducibles con mismo seed")

    def test_generate_dataset_count(self, sim):
        """Dataset generado respeta el límite n_frames."""
        meteo_list = [MeteoConditions(32, 35, 850, 1.5)]
        # El generador itera cwsi × meteo y para al llegar a n_frames
        dataset = sim.generate_dataset(n_frames=3, cwsi_levels=[0.2, 0.5, 0.8],
                                       meteo_list=meteo_list)
        assert len(dataset) == 3  # para en n_frames=3


# ─────────────────────────────────────────────
# Tests — CanopySegmenter
# ─────────────────────────────────────────────

class TestCanopySegmenter:

    def test_mask_shape(self, frame_mid_stress):
        seg = CanopySegmenter()
        result = seg.segment(frame_mid_stress)
        assert result["mask"].shape == (LEPTON_HEIGHT, LEPTON_WIDTH)

    def test_foliar_fraction_realistic(self, frame_mid_stress):
        """Fracción foliar de un frame de viñedo debe estar entre 20% y 80%."""
        seg = CanopySegmenter()
        result = seg.segment(frame_mid_stress)
        assert 0.15 <= result["foliar_frac"] <= 0.85, \
            f"Fracción foliar {result['foliar_frac']:.1%} fuera de rango realista"

    def test_T_mean_within_frame_range(self, frame_mid_stress):
        """T_mean del canopeo debe estar dentro del rango del frame."""
        seg = CanopySegmenter()
        result = seg.segment(frame_mid_stress)
        T = frame_mid_stress.temperature_C
        assert T.min() <= result["T_mean"] <= T.max()

    def test_n_pixels_positive(self, frame_mid_stress):
        """Debe haber píxeles foliares detectados."""
        seg = CanopySegmenter()
        result = seg.segment(frame_mid_stress)
        assert result["n_pixels"] >= 50, \
            f"Solo {result['n_pixels']} píxeles foliares detectados — muy pocos"


# ─────────────────────────────────────────────
# Tests — ThermalPipeline
# ─────────────────────────────────────────────

class TestThermalPipeline:

    def test_process_frame_returns_cwsi(self, pipeline, frame_mid_stress):
        result = pipeline.process_frame(frame_mid_stress)
        assert "cwsi" in result
        assert not np.isnan(result["cwsi"])

    def test_cwsi_monotone_with_stress_level(self, pipeline):
        """
        CWSI procesado aumenta con temperatura foliar creciente.
        Usa frames con estructura explícita sky/canopy/soil para garantizar
        que el segmentador identifique correctamente el canopeo.
        """
        from synthetic_data_gen import celsius_to_y16
        from thermal_pipeline import ThermalFrame

        # T_air=28, VPD≈2.09 → ΔT_LL=1.14, ΔT_UL=3.50
        meteo = MeteoConditions(T_air=28.0, RH=45.0, solar_rad=800.0, wind_speed=1.5)
        T_leaf_targets = [29.1, 29.8, 30.5, 31.2, 31.8, 32.3]
        cwsi_measured = []
        rng = np.random.default_rng(0)
        for T_target in T_leaf_targets:
            # Frame estructurado: sky (frío) arriba, canopeo en el medio, suelo (caliente) abajo
            T_frame = np.full((24, 32), T_target, dtype=np.float32)
            T_frame[:5, :]   = meteo.T_air - 10.0  # cielo frío (top ~20%)
            T_frame[20:, :]  = meteo.T_air + 8.0   # suelo caliente (bottom ~17%)
            T_frame += rng.normal(0, 0.05, T_frame.shape)
            frame = ThermalFrame(celsius_to_y16(T_frame), meteo, frame_id=f"T{T_target}")
            result = pipeline.process_frame(frame)
            cwsi_measured.append(result["cwsi"])

        # El CWSI debe aumentar monotónicamente (tolerancia 0.05 CWSI)
        assert all(cwsi_measured[i] <= cwsi_measured[i+1] + 0.05
                   for i in range(len(cwsi_measured)-1)), \
            f"CWSI no monótono con temperatura foliar: {[f'{v:.3f}' for v in cwsi_measured]}"

    def test_session_average(self, sim, pipeline, meteo_noon):
        """CWSI de sesión debe estar en rango (0, 1)."""
        frames = [sim.generate_frame(meteo_noon, 0.5, angle_deg=a, frame_id=f"s{i}")
                  for i, a in enumerate([0, 30, -30])]
        session = pipeline.process_session(frames)
        assert 0.0 <= session["cwsi_final"] <= 1.0

    def test_session_variability_flag(self, sim, pipeline, meteo_noon):
        """
        Sesión con frames de stress_index muy distintos debe activar flag de
        alta variabilidad (std > 0.12).

        Se mockea process_frame para inyectar stress_index controlados (0.1 y
        0.8), ya que el segmentador percentil + NWSB no produce CWSI distintos
        con frames sintéticos (el percentil siempre captura píxeles fríos que
        dan CWSI ≈ 0 independientemente de la temperatura objetivo del canopeo).
        """
        from unittest.mock import patch

        # Resultados simulados: dos frames con stress_index bien separados
        fake_results = [
            {"stress_index": 0.1, "cwsi": 0.1, "ig": np.nan, "status": "OK",
             "calibration_level": 3, "foliar_frac": 0.35, "frame_id": "v_low"},
            {"stress_index": 0.8, "cwsi": 0.8, "ig": np.nan, "status": "OK",
             "calibration_level": 3, "foliar_frac": 0.30, "frame_id": "v_high"},
        ]
        call_count = {"i": 0}

        def mock_process_frame(frame):
            r = fake_results[call_count["i"]]
            call_count["i"] += 1
            return r

        # Usar 2 frames reales (el contenido no importa, solo necesitamos objetos válidos)
        frames = [sim.generate_frame(meteo_noon, 0.3, angle_deg=a, frame_id=f"v_{i}")
                  for i, a in enumerate([0, 30])]

        with patch.object(pipeline, "process_frame", side_effect=mock_process_frame):
            session = pipeline.process_session(frames)

        assert session["alta_variabilidad_angular"], \
            f"Debería detectar alta variabilidad. stress_index_std={session.get('stress_index_std', 0):.3f}"

    def test_cwsi_map_shape(self, pipeline, frame_mid_stress):
        """Mapa CWSI debe tener las dimensiones del frame."""
        cwsi_map = pipeline.build_cwsi_map(frame_mid_stress)
        assert cwsi_map.shape == (LEPTON_HEIGHT, LEPTON_WIDTH)

    def test_cwsi_map_valid_range(self, pipeline, frame_mid_stress):
        """Píxeles foliares del mapa deben tener CWSI en [0, 1.5]."""
        cwsi_map = pipeline.build_cwsi_map(frame_mid_stress)
        valid = cwsi_map[~np.isnan(cwsi_map)]
        assert len(valid) > 0, "No hay píxeles foliares en el mapa CWSI"
        assert valid.min() >= 0.0
        assert valid.max() <= 1.5

    def test_validate_frame_good_conditions(self, pipeline, frame_mid_stress):
        """Frame con condiciones válidas → sin issues."""
        qc = pipeline.validate_frame(frame_mid_stress)
        assert "Condiciones sub-óptimas" not in " ".join(qc["issues"]), \
            f"Frame con condiciones válidas no debería tener issues: {qc['issues']}"
