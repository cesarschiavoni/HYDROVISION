"""
Condiciones meteorológicas para el simulador térmico.
Calibrado para Colonia Caroya (Córdoba, Argentina) — temporada nov-mar.
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class WeatherConditions:
    """
    Snapshot de condiciones atmosféricas en un momento dado.

    Parámetros calibrados para Colonia Caroya:
    - ETP Penman-Monteith promedio temporada: 6-8 mm/día
    - Temperatura media dic-feb: 24-28°C
    - VPD medio: 1.5-3.5 kPa en horas de máximo estrés (12-15hs)
    - Viento: 2-5 m/s, predominantemente del norte
    """

    # Temperatura del aire [°C]
    ta: float

    # Déficit de presión de vapor [kPa]
    # VPD = es(Ta) - ea, donde es = presión de saturación y ea = presión actual
    vpd: float

    # Radiación neta en la canopia [W/m²]
    # Rango típico: 200-600 W/m² durante el día en verano cordobés
    rn: float

    # Velocidad del viento a altura de canopia [m/s]
    wind_speed: float = 2.0

    # Hora del día [0-23.99]
    hour: float = 12.0

    # Precipitación acumulada últimas 48h [mm]
    rain_48h: float = 0.0

    def __post_init__(self):
        if self.vpd < 0:
            raise ValueError(f"VPD no puede ser negativo: {self.vpd}")
        if self.ta < -5 or self.ta > 50:
            raise ValueError(f"Temperatura fuera de rango plausible: {self.ta}°C")

    @property
    def vpd_pa(self) -> float:
        """VPD en Pascales (para cálculos de resistencia)."""
        return self.vpd * 1000

    @property
    def aerodynamic_resistance(self) -> float:
        """
        Resistencia aerodinámica [s/m] en función del viento.
        ra = 208 / u  (Allen et al. FAO-56, simplificado para canopia de vid)
        Límite mínimo 20 s/m para evitar singularidades con viento fuerte.
        """
        return max(208.0 / max(self.wind_speed, 0.5), 20.0)

    @property
    def delta(self) -> float:
        """
        Pendiente de la curva de presión de vapor de saturación [Pa/K].
        Válida para rango 5-40°C.
        """
        return (
            4098.0
            * 0.6108
            * np.exp(17.27 * self.ta / (self.ta + 237.3))
            * 1000.0
            / (self.ta + 237.3) ** 2
        )


def sample_colonia_caroya(
    hour: float,
    day_of_year: int = 15,
    rain_48h: float = 0.0,
    rng: Optional[np.random.Generator] = None,
) -> WeatherConditions:
    """
    Genera condiciones meteorológicas realistas para Colonia Caroya
    dadas la hora del día y el día del año (temporada nov-mar, DOY 305-90).

    Curvas diarias calibradas con datos históricos de la estación INTA Córdoba.
    """
    if rng is None:
        rng = np.random.default_rng()

    # --- Temperatura del aire (curva sinusoidal diaria) ---
    # Mínima a las 6am, máxima a las 14hs
    t_min = 18.0 + 4.0 * np.sin(2 * np.pi * (day_of_year - 355) / 365)
    t_max = 30.0 + 6.0 * np.sin(2 * np.pi * (day_of_year - 355) / 365)
    hour_norm = (hour - 6.0) / 8.0  # normalizado: 0 a las 6am, 1 a las 14hs
    ta_base = t_min + (t_max - t_min) * np.clip(np.sin(np.pi * hour_norm / 2), 0, 1)
    ta = ta_base + rng.normal(0, 0.5)

    # --- VPD [kPa] (máximo al mediodía, bajo de noche) ---
    vpd_max = 2.5 + 1.0 * np.sin(2 * np.pi * (day_of_year - 355) / 365)
    vpd_max *= max(0.3, 1.0 - rain_48h / 20.0)  # lluvia reciente reduce VPD
    vpd_curve = vpd_max * np.clip(np.sin(np.pi * max(hour - 6, 0) / 14), 0, 1)
    vpd = max(0.1, vpd_curve + rng.normal(0, 0.15))

    # --- Radiación neta [W/m²] ---
    if 6 <= hour <= 20:
        rn_max = 550.0
        rn = rn_max * np.sin(np.pi * (hour - 6) / 14) + rng.normal(0, 20)
        rn = max(0.0, rn)
    else:
        rn = rng.uniform(-30, -10)  # radiación neta negativa de noche

    # --- Viento [m/s] ---
    wind_speed = max(0.3, rng.lognormal(mean=0.7, sigma=0.4))

    return WeatherConditions(
        ta=round(ta, 2),
        vpd=round(vpd, 3),
        rn=round(rn, 1),
        wind_speed=round(wind_speed, 2),
        hour=hour,
        rain_48h=rain_48h,
    )
