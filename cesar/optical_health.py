"""
optical_health.py — Índice de Salud Óptica ISO_nodo
HydroVision AG | ML Engineer / 04_diagnostico

Implementa:
- Detección de obstrucción por desviación estándar del histograma térmico
- Validación de emisividad del panel Dry Ref (>1.5°C desviación → alerta)
- ISO_nodo: índice compuesto 0-100% de calidad óptica del nodo
- Alerta automática cuando ISO_nodo < 80% (Javier interviene)
- Persistencia JSON por nodo

Referencia:
  - Dry Ref: aluminio anodizado negro, ε ≈ 0.98, T_dry_expected = f(Ta, irradiación)
  - Histograma: imagen MLX90640 (32×24 px), rango 8-14 µm
  - ISO_nodo = 0.5 × score_histograma + 0.5 × score_emisividad
  - Thresholds calibrados para campo Malbec Colonia Caroya (noviembre-marzo)
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
ALERT_THRESHOLD_ISO = 80.0        # ISO_nodo < 80 → Javier interviene
STD_DEV_MIN_HEALTHY = 1.5         # °C; por debajo sugiere lente sucia/nublado
STD_DEV_MAX_HEALTHY = 12.0        # °C; por encima sugiere artefactos/saturación
DRY_REF_EMISSIVITY_DEVIATION = 1.5  # °C; desviación máxima aceptable
DRY_REF_EMISSIVITY = 0.98         # emisividad nominal del panel Dry Ref
STEFAN_BOLTZMANN = 5.670374419e-8  # W m⁻² K⁻⁴
PIXEL_SAMPLE_MIN = 50             # píxeles mínimos sobre el panel para validar
ISO_WEIGHT_HISTOGRAM = 0.50       # peso del score de histograma en ISO_nodo
ISO_WEIGHT_EMISSIVITY = 0.50      # peso del score de emisividad en ISO_nodo
HISTORY_MAX = 200                 # máximo de registros históricos en memoria
STORAGE_DIR_DEFAULT = "/var/hydrovision/optical_health"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class OpticalHealthState:
    """Estado persistente del módulo de salud óptica por nodo."""
    node_id: str
    crop: str = "Malbec"
    n_evaluations: int = 0
    n_alerts: int = 0                      # veces ISO_nodo < ALERT_THRESHOLD_ISO
    n_emissivity_alerts: int = 0           # veces desviación Dry Ref > umbral
    n_obstruction_alerts: int = 0          # veces std_dev fuera de rango
    last_iso: float = 100.0
    last_update: str = ""
    iso_history: list[float] = field(default_factory=list)  # rolling últimos N


@dataclass
class OpticalHealthResult:
    """Resultado de una evaluación ISO_nodo."""
    iso_nodo: float                 # 0-100, índice compuesto
    score_histogram: float          # 0-100, score de std dev histograma
    score_emissivity: float         # 0-100, score de validación Dry Ref
    std_dev_measured: float         # °C, desviación estándar del histograma
    dry_ref_deviation: float        # °C, desviación T_dry medido vs esperado
    obstruction_alert: bool         # std_dev fuera de rango saludable
    emissivity_alert: bool          # Dry Ref desviación > DRY_REF_EMISSIVITY_DEVIATION
    iso_alert: bool                 # ISO_nodo < ALERT_THRESHOLD_ISO
    alert_message: str              # descripción legible del problema
    timestamp: str


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
def _compute_std_dev(pixel_temps: list[float]) -> float:
    """Desviación estándar de la distribución de temperaturas (°C)."""
    n = len(pixel_temps)
    if n < 2:
        return 0.0
    mean = sum(pixel_temps) / n
    variance = sum((t - mean) ** 2 for t in pixel_temps) / (n - 1)
    return math.sqrt(variance)


def _histogram_score(std_dev: float) -> float:
    """
    Score 0-100 basado en std_dev del histograma.
    - std_dev en [STD_DEV_MIN_HEALTHY, STD_DEV_MAX_HEALTHY] → score 100
    - Por debajo del mínimo → posible lente sucia o escena homogénea anormal
    - Por encima del máximo → artefactos o saturación
    Transición suave (rampa lineal de ±1.5°C en los extremos).
    """
    lo = STD_DEV_MIN_HEALTHY
    hi = STD_DEV_MAX_HEALTHY
    ramp = 1.5  # °C de transición

    if std_dev < lo - ramp:
        return 0.0
    elif std_dev < lo:
        return 100.0 * (std_dev - (lo - ramp)) / ramp
    elif std_dev <= hi:
        return 100.0
    elif std_dev <= hi + ramp:
        return 100.0 * (1.0 - (std_dev - hi) / ramp)
    else:
        return 0.0


def _expected_dry_ref_temp(ta_celsius: float, solar_irradiance_wm2: float) -> float:
    """
    Temperatura esperada del panel Dry Ref (aluminio negro ε=0.98).
    Modelo simplificado de equilibrio energético:
        T_dry ≈ Ta + (α_solar × G) / (ε × σ × 4 × Ta³)
    donde α_solar ≈ 0.95 (aluminio anodizado negro absorbe ~95% solar).
    En sombra total o de noche: T_dry ≈ Ta + 0.5°C (self-heating electrónico).
    """
    if solar_irradiance_wm2 < 10.0:
        return ta_celsius + 0.5  # noche/nublado denso

    ta_k = ta_celsius + 273.15
    alpha_solar = 0.95
    # Linearización de la radiación: dT ≈ α·G / (4·ε·σ·Ta³)
    denominator = 4.0 * DRY_REF_EMISSIVITY * STEFAN_BOLTZMANN * (ta_k ** 3)
    delta_t = alpha_solar * solar_irradiance_wm2 / denominator
    return ta_celsius + delta_t


def _emissivity_score(deviation: float) -> float:
    """
    Score 0-100 basado en desviación del panel Dry Ref.
    - deviation < DRY_REF_EMISSIVITY_DEVIATION → score 100
    - Lineal hasta deviation = 2 × umbral → score 0
    """
    threshold = DRY_REF_EMISSIVITY_DEVIATION
    if deviation <= threshold:
        return 100.0
    elif deviation <= 2.0 * threshold:
        return 100.0 * (1.0 - (deviation - threshold) / threshold)
    else:
        return 0.0


# ---------------------------------------------------------------------------
# Motor principal
# ---------------------------------------------------------------------------
class OpticalHealthMonitor:
    """
    Monitor de salud óptica para nodos HydroVision AG.

    Evalúa la calidad de la imagen térmica mediante:
    1. Análisis de histograma: std_dev de la temperatura de la escena
    2. Validación del panel Dry Ref: temperatura medida vs modelo energético
    3. ISO_nodo = media ponderada de ambos scores (50/50)
    4. Alerta automática cuando ISO_nodo < 80%
    """

    def __init__(self, node_id: str, crop: str = "Malbec",
                 storage_dir: str = STORAGE_DIR_DEFAULT):
        self.storage_dir = storage_dir
        self._state = OpticalHealthState(node_id=node_id, crop=crop)
        self._load()

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------
    def _state_path(self) -> str:
        return os.path.join(self.storage_dir,
                            f"optical_health_{self._state.node_id}.json")

    def _load(self) -> None:
        path = self._state_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._state = OpticalHealthState(**data)
        except (json.JSONDecodeError, TypeError, KeyError):
            pass

    def save(self) -> None:
        os.makedirs(self.storage_dir, exist_ok=True)
        with open(self._state_path(), "w", encoding="utf-8") as f:
            json.dump(asdict(self._state), f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Evaluación
    # ------------------------------------------------------------------
    def evaluate(
        self,
        pixel_temps: list[float],
        ta_celsius: float,
        dry_ref_temp_measured: float,
        solar_irradiance_wm2: float = 600.0,
        timestamp: Optional[datetime] = None,
    ) -> OpticalHealthResult:
        """
        Evalúa la salud óptica del nodo.

        Args:
            pixel_temps: Lista de temperaturas (°C) de todos los píxeles de la imagen.
            ta_celsius: Temperatura del aire (°C) del sensor local.
            dry_ref_temp_measured: Temperatura media medida sobre el panel Dry Ref (°C).
            solar_irradiance_wm2: Irradiancia solar global (W/m²), default 600.
            timestamp: Momento de la evaluación.
        """
        ts = (timestamp or datetime.now()).isoformat()

        # --- 1. Score histograma
        std_dev = _compute_std_dev(pixel_temps)
        score_hist = _histogram_score(std_dev)
        obstruction_alert = not (STD_DEV_MIN_HEALTHY <= std_dev <= STD_DEV_MAX_HEALTHY)

        # --- 2. Score emisividad Dry Ref
        t_dry_expected = _expected_dry_ref_temp(ta_celsius, solar_irradiance_wm2)
        deviation = abs(dry_ref_temp_measured - t_dry_expected)
        score_emis = _emissivity_score(deviation)
        emissivity_alert = deviation > DRY_REF_EMISSIVITY_DEVIATION

        # --- 3. ISO_nodo compuesto
        iso = (ISO_WEIGHT_HISTOGRAM * score_hist +
               ISO_WEIGHT_EMISSIVITY * score_emis)
        iso = max(0.0, min(100.0, iso))
        iso_alert = iso < ALERT_THRESHOLD_ISO

        # --- 4. Mensaje de alerta
        messages = []
        if obstruction_alert:
            if std_dev < STD_DEV_MIN_HEALTHY:
                messages.append(
                    f"std_dev={std_dev:.2f}°C < {STD_DEV_MIN_HEALTHY}°C: "
                    "posible lente sucia o obstrucción parcial"
                )
            else:
                messages.append(
                    f"std_dev={std_dev:.2f}°C > {STD_DEV_MAX_HEALTHY}°C: "
                    "artefactos térmicos o saturación de sensor"
                )
        if emissivity_alert:
            messages.append(
                f"Dry Ref desviación={deviation:.2f}°C > {DRY_REF_EMISSIVITY_DEVIATION}°C "
                f"(medido={dry_ref_temp_measured:.1f}°C, esperado={t_dry_expected:.1f}°C): "
                "panel sucio o emisividad alterada"
            )
        if iso_alert and not messages:
            messages.append(
                f"ISO_nodo={iso:.1f}% < {ALERT_THRESHOLD_ISO}%: "
                "intervención de Javier requerida"
            )
        alert_message = " | ".join(messages) if messages else "OK"

        # --- 5. Actualizar estado
        self._state.n_evaluations += 1
        self._state.last_iso = round(iso, 2)
        self._state.last_update = ts
        if iso_alert:
            self._state.n_alerts += 1
        if emissivity_alert:
            self._state.n_emissivity_alerts += 1
        if obstruction_alert:
            self._state.n_obstruction_alerts += 1
        self._state.iso_history.append(round(iso, 2))
        if len(self._state.iso_history) > HISTORY_MAX:
            self._state.iso_history.pop(0)

        return OpticalHealthResult(
            iso_nodo=round(iso, 2),
            score_histogram=round(score_hist, 2),
            score_emissivity=round(score_emis, 2),
            std_dev_measured=round(std_dev, 4),
            dry_ref_deviation=round(deviation, 4),
            obstruction_alert=obstruction_alert,
            emissivity_alert=emissivity_alert,
            iso_alert=iso_alert,
            alert_message=alert_message,
            timestamp=ts,
        )

    def summary(self) -> dict:
        s = self._state
        iso_hist = s.iso_history
        avg_iso = sum(iso_hist) / len(iso_hist) if iso_hist else 100.0
        return {
            "node_id": s.node_id,
            "crop": s.crop,
            "n_evaluations": s.n_evaluations,
            "last_iso": s.last_iso,
            "avg_iso": round(avg_iso, 2),
            "n_alerts": s.n_alerts,
            "n_emissivity_alerts": s.n_emissivity_alerts,
            "n_obstruction_alerts": s.n_obstruction_alerts,
            "alert_rate_pct": round(
                100.0 * s.n_alerts / max(1, s.n_evaluations), 2
            ),
            "last_update": s.last_update,
        }


# ---------------------------------------------------------------------------
# Demo __main__
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import random
    import tempfile

    random.seed(7)
    tmp = tempfile.mkdtemp()
    print("=" * 70)
    print("DEMO OpticalHealthMonitor — 3 escenarios por nodo")
    print("=" * 70)

    def _fake_image(n_pixels: int = 160 * 120, mean: float = 28.0,
                    std: float = 4.5) -> list[float]:
        return [random.gauss(mean, std) for _ in range(n_pixels)]

    nodes = ["N01", "N02", "N03", "N04", "N05"]
    monitors = {nid: OpticalHealthMonitor(nid, storage_dir=tmp) for nid in nodes}

    # Escenario A: nodo saludable, mediodía verano
    print("\n--- Escenario A: Nodo saludable (verano, mediodía) ---")
    for nid in nodes:
        img = _fake_image(std=4.5)  # std_dev ≈ 4.5°C — rango saludable
        r = monitors[nid].evaluate(
            pixel_temps=img,
            ta_celsius=30.0,
            dry_ref_temp_measured=44.2,   # esperado ≈ 44.5°C → desviación <1.5
            solar_irradiance_wm2=850.0,
            timestamp=datetime(2025, 12, 15, 13, 0, 0),
        )
        print(f"  {nid}: ISO={r.iso_nodo:.1f}%  hist={r.score_histogram:.0f}  "
              f"emis={r.score_emissivity:.0f}  alerta={r.iso_alert}  {r.alert_message}")

    # Escenario B: lente sucia (std_dev muy baja)
    print("\n--- Escenario B: Lente sucia (std_dev baja) ---")
    r_dirty = monitors["N01"].evaluate(
        pixel_temps=_fake_image(std=0.6),   # std baja → obstrucción
        ta_celsius=28.0,
        dry_ref_temp_measured=41.0,
        solar_irradiance_wm2=750.0,
    )
    print(f"  N01: ISO={r_dirty.iso_nodo:.1f}%  std={r_dirty.std_dev_measured:.3f}°C  "
          f"alerta={r_dirty.iso_alert}")
    print(f"       Mensaje: {r_dirty.alert_message}")

    # Escenario C: panel Dry Ref sucio (desviación de emisividad)
    print("\n--- Escenario C: Panel Dry Ref sucio (desviación > 1.5°C) ---")
    r_panel = monitors["N02"].evaluate(
        pixel_temps=_fake_image(std=3.8),   # histograma OK
        ta_celsius=28.0,
        dry_ref_temp_measured=36.0,    # esperado ~44°C → desviación ~8°C
        solar_irradiance_wm2=750.0,
    )
    print(f"  N02: ISO={r_panel.iso_nodo:.1f}%  "
          f"dry_ref_dev={r_panel.dry_ref_deviation:.2f}°C  "
          f"emis_alerta={r_panel.emissivity_alert}")
    print(f"       Mensaje: {r_panel.alert_message}")

    # Escenario D: doble problema (lente sucia + panel)
    print("\n--- Escenario D: Doble falla (lente + panel) ---")
    r_double = monitors["N03"].evaluate(
        pixel_temps=_fake_image(std=0.4),
        ta_celsius=25.0,
        dry_ref_temp_measured=33.0,
        solar_irradiance_wm2=600.0,
    )
    print(f"  N03: ISO={r_double.iso_nodo:.1f}%  alerta={r_double.iso_alert}")
    print(f"       Mensaje: {r_double.alert_message}")

    # Resumen final
    print("\n--- Resumen por nodo ---")
    print(f"{'Nodo':<6} {'Eval':>5} {'ISO_last':>9} {'ISO_avg':>8} "
          f"{'Alertas':>8} {'Emis':>6} {'Obstr':>6}")
    print("-" * 55)
    for nid, mon in monitors.items():
        s = mon.summary()
        print(f"{nid:<6} {s['n_evaluations']:>5} {s['last_iso']:>9.1f} "
              f"{s['avg_iso']:>8.1f} {s['n_alerts']:>8} "
              f"{s['n_emissivity_alerts']:>6} {s['n_obstruction_alerts']:>6}")

    print("\nDemo completada exitosamente.")
