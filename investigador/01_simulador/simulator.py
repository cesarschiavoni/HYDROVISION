"""
Simulador físico de imágenes térmicas — HydroVision AG
======================================================
Genera imágenes sintéticas de canopia de vid Malbec bajo diferentes
niveles de estrés hídrico, replicando las características del sensor
FLIR Lepton 3.5 (160×120 px, NETD ~50mK).

Física:
- Balance energético de hoja (Penman-Monteith simplificado)
- Resistencia estomática escalada por fracción ETc
- Baselines CWSI: lower = NWSB (Jackson 1981), upper = hoja no transpirante
- Ruido de sensor: distribución normal truncada con NETD 50mK

Regímenes hídricos del protocolo Scholander (viñedo Colonia Caroya):
  A: ETc 100%  — control bien regado
  B: ETc  65%  — estrés leve
  C: ETc  40%  — estrés moderado
  D: ETc  15%  — estrés severo
  E: ETc   0%  — sin riego (estrés máximo)

Uso:
    sim = ThermalSimulator()
    weather = sample_colonia_caroya(hour=13.0)
    img, meta = sim.generate(weather, etc_fraction=0.65)
    # img: ndarray (120, 160) float32 en °C
    # meta: dict con CWSI, Tc_mean, Tc_wet, Tc_dry, etc.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, Dict, Optional

from weather import WeatherConditions, sample_colonia_caroya


# ---------------------------------------------------------------------------
# Constantes físicas
# ---------------------------------------------------------------------------
RHO_AIR = 1.2       # kg/m³ — densidad del aire a 25°C
CP_AIR = 1005.0     # J/kg/K — calor específico del aire
GAMMA = 66.0        # Pa/K — constante psicrométrica a nivel del mar
LAMBDA = 2.45e6     # J/kg — calor latente de vaporización


# ---------------------------------------------------------------------------
# Parámetros fisiológicos de Malbec (Colonia Caroya)
# ---------------------------------------------------------------------------
@dataclass
class MalbecParams:
    """
    Parámetros fisiológicos de Vitis vinifera cv. Malbec.
    Calibrados para pie americano, conducción en espaldera, Colonia Caroya.
    """
    # Resistencia estomática mínima (planta bien regada) [s/m]
    # Equivale a gs_max ≈ 0.30 mol/m²/s
    rs_min: float = 100.0

    # Resistencia estomática máxima (estomas cerrados, sin riego) [s/m]
    rs_max: float = 8000.0

    # Emisividad de la hoja (para corrección radiométrica)
    emissivity: float = 0.98

    # Temperatura de suelo desnudo relativa al aire [°C delta]
    # El suelo bajo viñedo suele estar 5-12°C más caliente que el aire al mediodía
    soil_delta_t: float = 8.0

    # Temperatura de madera/sarmiento relativa al aire [°C delta]
    wood_delta_t: float = 3.0

    # Fracción de píxeles de canopia en la imagen (LAI, geometría del bracket)
    canopy_fraction: float = 0.65


# ---------------------------------------------------------------------------
# Sensor FLIR Lepton 3.5
# ---------------------------------------------------------------------------
@dataclass
class FLIRLepton35:
    """Especificaciones del sensor térmico embebido en el nodo HydroVision."""
    width: int = 160
    height: int = 120
    netd: float = 0.05        # °C — Noise Equivalent Temperature Difference
    fov_h: float = 57.0       # grados horizontal
    fov_v: float = 45.0       # grados vertical
    quantization: float = 0.01  # paso de cuantización [°C] (resolución radiométrica)

    def add_noise(self, image: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        """Agrega ruido gaussiano NETD y cuantiza al paso del sensor."""
        noisy = image + rng.normal(0, self.netd, image.shape)
        return (np.round(noisy / self.quantization) * self.quantization).astype(np.float32)


# ---------------------------------------------------------------------------
# Física del balance energético
# ---------------------------------------------------------------------------
def leaf_temperature(
    weather: WeatherConditions,
    rs: float,
    params: MalbecParams,
) -> float:
    """
    Temperatura de hoja [°C] por balance energético Penman-Monteith.

    Energía neta absorbida = H (sensible) + LE (latente)
    Tc - Ta = H * ra / (ρ_a * Cp)

    LE = (Δ * Rn + ρ_a * Cp * VPD / ra) / (Δ + γ * (1 + rs/ra))

    Args:
        weather: condiciones atmosféricas actuales
        rs: resistencia estomática [s/m] (función del nivel de estrés)
        params: parámetros fisiológicos del cultivo

    Returns:
        Tc: temperatura de canopia [°C]
    """
    ra = weather.aerodynamic_resistance
    delta = weather.delta

    le = (delta * weather.rn + RHO_AIR * CP_AIR * weather.vpd_pa / ra) / (
        delta + GAMMA * (1.0 + rs / ra)
    )
    h = weather.rn - le
    tc = weather.ta + h * ra / (RHO_AIR * CP_AIR)
    return float(tc)


def stomatal_resistance(etc_fraction: float, params: MalbecParams) -> float:
    """
    Resistencia estomática en función de la fracción de ETc aplicada.

    Modelo potencial: rs = rs_min / (etc_fraction ^ alpha)
    alpha ≈ 0.6 para Malbec (relación sublineal — la planta regula parcialmente)
    En ETc=0%: rs → rs_max (estomas completamente cerrados).

    Args:
        etc_fraction: fracción de ETc [0.0 – 1.0]
        params: parámetros de Malbec

    Returns:
        rs [s/m]
    """
    if etc_fraction <= 0.0:
        return params.rs_max
    alpha = 0.6
    rs = params.rs_min / (etc_fraction ** alpha)
    return float(np.clip(rs, params.rs_min, params.rs_max))


def cwsi_baselines(
    weather: WeatherConditions, params: MalbecParams
) -> Tuple[float, float]:
    """
    Calcula los baselines del CWSI para las condiciones actuales.

    Lower baseline (Tc_wet): planta sin estrés, rs = rs_min
    Upper baseline (Tc_dry): planta con estomas cerrados, rs = rs_max

    Returns:
        (tc_wet, tc_dry) — ambos en °C
    """
    tc_wet = leaf_temperature(weather, params.rs_min, params)
    tc_dry = leaf_temperature(weather, params.rs_max, params)
    return tc_wet, tc_dry


def compute_cwsi(tc: float, tc_wet: float, tc_dry: float) -> float:
    """
    CWSI = (Tc - Tc_wet) / (Tc_dry - Tc_wet)

    Clipeado a [0, 1]. Valores fuera de rango indican condiciones extremas
    (ej. medición nocturna o error de baseline).
    """
    denom = tc_dry - tc_wet
    if abs(denom) < 0.1:
        return 0.0
    return float(np.clip((tc - tc_wet) / denom, 0.0, 1.0))


# ---------------------------------------------------------------------------
# Generador de imágenes sintéticas
# ---------------------------------------------------------------------------
class ThermalSimulator:
    """
    Simulador de imágenes térmicas FLIR Lepton 3.5 para canopia de Malbec.

    Genera imágenes (120, 160) float32 en °C con:
    - Variabilidad espacial de temperatura en la canopia
    - Fondo de suelo y madera con temperaturas propias
    - Ruido de sensor realista
    - Metadatos físicos (CWSI, baselines, Tc_mean)
    """

    def __init__(
        self,
        params: Optional[MalbecParams] = None,
        sensor: Optional[FLIRLepton35] = None,
        seed: Optional[int] = None,
    ):
        self.params = params or MalbecParams()
        self.sensor = sensor or FLIRLepton35()
        self.rng = np.random.default_rng(seed)

    def _make_canopy_mask(self) -> np.ndarray:
        """
        Máscara binaria (H, W) indicando píxeles de canopia.
        Genera un patrón de follaje irregular usando ruido Perlin simplificado
        (suma de sinusoides con fases aleatorias).
        """
        H, W = self.sensor.height, self.sensor.width
        x = np.linspace(0, 4 * np.pi, W)
        y = np.linspace(0, 4 * np.pi, H)
        xx, yy = np.meshgrid(x, y)

        # Suma de 4 frecuencias con fases aleatorias → textura orgánica
        noise = sum(
            np.sin(xx * f + self.rng.uniform(0, 2 * np.pi))
            * np.cos(yy * f + self.rng.uniform(0, 2 * np.pi))
            for f in [1, 2, 3, 5]
        )
        noise = (noise - noise.min()) / (noise.max() - noise.min())
        return noise > (1.0 - self.params.canopy_fraction)

    def generate(
        self,
        weather: WeatherConditions,
        etc_fraction: float,
    ) -> Tuple[np.ndarray, Dict]:
        """
        Genera una imagen térmica sintética.

        Args:
            weather: condiciones atmosféricas en el momento de la captura
            etc_fraction: fracción de ETc aplicada [0.0–1.0]
                          0.0 = sin riego, 1.0 = bien regado

        Returns:
            image: ndarray (120, 160) float32 — temperatura en °C por píxel
            meta: dict con métricas físicas del frame:
                  cwsi, tc_mean, tc_std, tc_wet, tc_dry, rs, etc_fraction,
                  ta, vpd, rn, wind_speed
        """
        etc_fraction = float(np.clip(etc_fraction, 0.0, 1.0))

        # --- Resistencia estomática para este nivel de estrés ---
        rs = stomatal_resistance(etc_fraction, self.params)

        # --- Temperatura media de la canopia (física) ---
        tc_mean = leaf_temperature(weather, rs, self.params)

        # --- Baselines CWSI ---
        tc_wet, tc_dry = cwsi_baselines(weather, self.params)
        cwsi = compute_cwsi(tc_mean, tc_wet, tc_dry)

        # --- Máscara espacial canopia / fondo ---
        canopy_mask = self._make_canopy_mask()

        H, W = self.sensor.height, self.sensor.width
        image = np.zeros((H, W), dtype=np.float32)

        # Píxeles de canopia: tc_mean + variación espacial
        # La variación refleja heterogeneidad de conductancia estomática
        tc_std = 0.3 + 0.8 * (1.0 - etc_fraction)  # mayor estrés → más heterogeneidad
        canopy_temps = self.rng.normal(tc_mean, tc_std, (H, W)).astype(np.float32)
        image[canopy_mask] = canopy_temps[canopy_mask]

        # Píxeles de suelo (más caliente que el aire al mediodía)
        soil_temp = weather.ta + self.params.soil_delta_t * (weather.rn / 550.0)
        soil_temps = self.rng.normal(soil_temp, 1.5, (H, W)).astype(np.float32)
        image[~canopy_mask] = soil_temps[~canopy_mask]

        # --- Ruido de sensor FLIR ---
        image = self.sensor.add_noise(image, self.rng)

        meta = {
            "cwsi": round(cwsi, 4),
            "tc_mean": round(float(tc_mean), 3),
            "tc_std": round(float(tc_std), 3),
            "tc_wet": round(float(tc_wet), 3),
            "tc_dry": round(float(tc_dry), 3),
            "rs": round(float(rs), 1),
            "etc_fraction": etc_fraction,
            "ta": weather.ta,
            "vpd": weather.vpd,
            "rn": weather.rn,
            "wind_speed": weather.wind_speed,
            "hour": weather.hour,
            "rain_48h": weather.rain_48h,
        }
        return image, meta


# ---------------------------------------------------------------------------
# Generador de dataset
# ---------------------------------------------------------------------------
ETC_REGIMES = {
    "A": 1.00,  # 100% ETc — control
    "B": 0.65,  # 65%  — estrés leve
    "C": 0.40,  # 40%  — estrés moderado
    "D": 0.15,  # 15%  — estrés severo
    "E": 0.00,  # 0%   — sin riego
}


def generate_dataset(
    n_per_regime: int = 200,
    hours: Tuple[float, ...] = (8.5, 12.0, 16.0),
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, list]:
    """
    Genera un dataset sintético balanceado por régimen hídrico.

    Args:
        n_per_regime: imágenes por régimen × hora
        hours: horas del día a simular (D_max check, mediodía, D_min check)
        seed: semilla para reproducibilidad

    Returns:
        images: ndarray (N, 120, 160) float32
        labels: ndarray (N,) float32 — CWSI ground truth
        metadata: lista de dicts con contexto de cada frame
    """
    sim = ThermalSimulator(seed=seed)
    rng = np.random.default_rng(seed)

    images, labels, metadata = [], [], []

    for regime, etc in ETC_REGIMES.items():
        for hour in hours:
            for i in range(n_per_regime):
                # Día del año aleatorio en temporada (nov=305 a mar=90)
                doy = rng.integers(305, 365 + 90)
                rain = float(rng.choice([0, 0, 0, 3, 8, 15], p=[0.6, 0.1, 0.1, 0.1, 0.05, 0.05]))
                weather = sample_colonia_caroya(hour=hour, day_of_year=int(doy % 365), rain_48h=rain, rng=rng)
                img, meta = sim.generate(weather, etc_fraction=etc)
                meta["regime"] = regime
                meta["sample_id"] = f"{regime}_h{hour}_{i:04d}"
                images.append(img)
                labels.append(meta["cwsi"])
                metadata.append(meta)

    images_arr = np.stack(images, axis=0)
    labels_arr = np.array(labels, dtype=np.float32)
    return images_arr, labels_arr, metadata


# ---------------------------------------------------------------------------
# Ejecución directa: genera y visualiza un ejemplo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    sim = ThermalSimulator(seed=0)

    fig, axes = plt.subplots(1, 5, figsize=(16, 4))
    fig.suptitle("Imágenes térmicas sintéticas — Malbec Colonia Caroya (12hs, VPD alto)", fontsize=13)

    weather = sample_colonia_caroya(hour=12.0, rng=np.random.default_rng(0))

    for ax, (regime, etc) in zip(axes, ETC_REGIMES.items()):
        img, meta = sim.generate(weather, etc_fraction=etc)
        vmin = weather.ta - 2
        vmax = weather.ta + 15
        im = ax.imshow(img, cmap="inferno", vmin=vmin, vmax=vmax)
        ax.set_title(
            f"Régimen {regime} (ETc {int(etc*100)}%)\n"
            f"CWSI={meta['cwsi']:.2f}  Tc={meta['tc_mean']:.1f}°C",
            fontsize=9,
        )
        ax.axis("off")

    plt.colorbar(im, ax=axes, label="Temperatura [°C]", shrink=0.8)
    plt.tight_layout()
    plt.savefig("ejemplo_simulador.png", dpi=150)
    print("Guardado: ejemplo_simulador.png")

    # Generar dataset pequeño de prueba
    print("\nGenerando dataset de prueba (200 imgs/régimen × 3 horas)...")
    images, labels, meta = generate_dataset(n_per_regime=200)
    print(f"  Shape imágenes: {images.shape}")
    print(f"  Shape labels:   {labels.shape}")
    print(f"  CWSI por régimen:")
    for regime in ETC_REGIMES:
        idx = [i for i, m in enumerate(meta) if m["regime"] == regime]
        cwsi_vals = labels[idx]
        print(f"    {regime}: mean={cwsi_vals.mean():.3f}  std={cwsi_vals.std():.3f}  "
              f"[{cwsi_vals.min():.3f}-{cwsi_vals.max():.3f}]")
