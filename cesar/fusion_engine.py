"""
fusion_engine.py — Motor HSI con regresión lineal online adaptativa
HydroVision AG | ML Engineer / 03_fusion

Implementa:
- Regresión lineal online CWSI = α + β × MDS_norm (ventana deslizante 60 muestras)
- Pesos dinámicos por madurez del historial dendrométrico (mds_maturity = min(1, n/20))
- Imputación de CWSI desde MDS cuando cwsi_confidence < 0.4
- Alerta de divergencia automática (|CWSI − MDS_norm| > 0.35)
- Rampa gradual viento 4-18 m/s → reducción progresiva peso CWSI. ≥18 m/s → 100% MDS
- Persistencia JSON por nodo

Referencia: combined_stress_index.py (pesos estáticos base 35/65),
            baseline.py (EMA calibración), dendrometry.py (MDS engine)
"""

from __future__ import annotations

import json
import math
import os
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
WINDOW_SIZE = 60          # muestras en ventana deslizante para regresión
MDS_MATURITY_FULL = 20    # sesiones Scholander para mds_maturity = 1.0
CWSI_CONFIDENCE_THRESHOLD = 0.4   # umbral para imputación desde MDS
DIVERGENCE_THRESHOLD = 0.35       # |CWSI − MDS_norm| > 0.35 → alerta
WIND_RAMP_LO_MS = 4.0     # m/s — inicio reduccion peso CWSI
WIND_RAMP_HI_MS = 18.0    # m/s (65 km/h) — override completo → 100% MDS (v2 firmware: Kalman, Muller, Hampel)
WIND_OVERRIDE_MS = WIND_RAMP_HI_MS  # backward compat
DEFAULT_ALPHA = 0.0       # intercepto inicial (HSI ≈ MDS_norm si sin datos)
DEFAULT_BETA = 1.0        # pendiente inicial (correlación perfecta asumida)
STORAGE_DIR_DEFAULT = "/var/hydrovision/fusion"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class RegressionWindow:
    """Ventana deslizante para regresión lineal online CWSI = α + β × MDS_norm."""
    mds_norm_values: list[float] = field(default_factory=list)
    cwsi_values: list[float] = field(default_factory=list)

    def add(self, mds_norm: float, cwsi: float) -> None:
        self.mds_norm_values.append(mds_norm)
        self.cwsi_values.append(cwsi)
        if len(self.mds_norm_values) > WINDOW_SIZE:
            self.mds_norm_values.pop(0)
            self.cwsi_values.pop(0)

    @property
    def n(self) -> int:
        return len(self.mds_norm_values)

    def fit(self) -> tuple[float, float]:
        """
        OLS: β = Σ(xi-x̄)(yi-ȳ) / Σ(xi-x̄)²,  α = ȳ - β·x̄
        Returns (alpha, beta). Falls back to defaults if n < 5 or var(x) ≈ 0.
        """
        n = self.n
        if n < 5:
            return DEFAULT_ALPHA, DEFAULT_BETA

        xs = self.mds_norm_values
        ys = self.cwsi_values
        x_mean = sum(xs) / n
        y_mean = sum(ys) / n

        ss_xx = sum((x - x_mean) ** 2 for x in xs)
        ss_xy = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))

        if ss_xx < 1e-9:
            return DEFAULT_ALPHA, DEFAULT_BETA

        beta = ss_xy / ss_xx
        alpha = y_mean - beta * x_mean
        return alpha, beta

    def r_squared(self) -> float:
        """R² de la regresión actual. Retorna 0.0 si n < 5."""
        n = self.n
        if n < 5:
            return 0.0

        alpha, beta = self.fit()
        ys = self.cwsi_values
        xs = self.mds_norm_values
        y_mean = sum(ys) / n

        ss_tot = sum((y - y_mean) ** 2 for y in ys)
        if ss_tot < 1e-9:
            return 1.0

        ss_res = sum((y - (alpha + beta * x)) ** 2 for x, y in zip(xs, ys))
        return max(0.0, 1.0 - ss_res / ss_tot)


@dataclass
class FusionState:
    """Estado persistente del motor de fusión por nodo."""
    node_id: str
    crop: str = "Malbec"
    n_scholander_sessions: int = 0      # sesiones con Scholander (para mds_maturity)
    n_fusion_calls: int = 0             # total de fusiones realizadas
    last_alpha: float = DEFAULT_ALPHA
    last_beta: float = DEFAULT_BETA
    last_r2: float = 0.0
    divergence_count: int = 0           # alertas de divergencia acumuladas
    imputation_count: int = 0           # veces que se imputó CWSI desde MDS
    wind_override_count: int = 0        # veces que viento forzó 100% MDS
    last_update: str = ""
    # ventana de regresión serializada
    window_mds: list[float] = field(default_factory=list)
    window_cwsi: list[float] = field(default_factory=list)


@dataclass
class FusionResult:
    """Resultado de una llamada a FusionEngine.fuse()."""
    hsi: float                  # Hydration Stress Index 0-1 (o MPa si se mapea)
    cwsi_used: float            # CWSI efectivamente usado (medido o imputado)
    mds_norm: float             # MDS normalizado 0-1
    weight_cwsi: float          # peso asignado a CWSI (0.0–1.0)
    weight_mds: float           # peso asignado a MDS
    alpha: float                # intercepto de la regresión actual
    beta: float                 # pendiente de la regresión actual
    r2: float                   # R² de la regresión (confianza del modelo local)
    mds_maturity: float         # madurez 0-1 del historial dendrométrico
    imputed: bool               # True si CWSI fue imputado desde MDS
    wind_override: bool         # True si viento forzó 100% MDS
    divergence_alert: bool      # True si |CWSI − MDS_norm| > 0.35
    divergence_delta: float     # valor real de |CWSI − MDS_norm|
    timestamp: str


# ---------------------------------------------------------------------------
# Motor principal
# ---------------------------------------------------------------------------
class FusionEngine:
    """
    Motor de fusión HSI con regresión lineal online adaptativa.

    Flujo por llamada a fuse():
    1. Calcular mds_maturity = min(1, n_scholander / MDS_MATURITY_FULL)
    2. Rampa gradual 4-18 m/s: peso CWSI se reduce linealmente. ≥18 m/s → wind_override, weight_mds=1.0
    3. Si cwsi_confidence < CWSI_CONFIDENCE_THRESHOLD → imputar CWSI = α + β×MDS_norm
    4. Actualizar ventana de regresión (solo con datos no imputados)
    5. Calcular pesos dinámicos base: w_mds = 0.65 + 0.20×mds_maturity (cap 0.85)
    6. Modular por R²: a mayor R², más confianza en la señal térmico-dendrométrica
    7. Fusionar: HSI = w_cwsi×CWSI + w_mds×MDS_norm
    8. Alertar si divergencia > umbral
    """

    def __init__(self, node_id: str, crop: str = "Malbec",
                 storage_dir: str = STORAGE_DIR_DEFAULT):
        self.storage_dir = storage_dir
        self._state = FusionState(node_id=node_id, crop=crop)
        self._window = RegressionWindow()
        self._load()

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------
    def _state_path(self) -> str:
        return os.path.join(self.storage_dir, f"fusion_{self._state.node_id}.json")

    def _load(self) -> None:
        path = self._state_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # restaurar ventana
            window_mds = data.pop("window_mds", [])
            window_cwsi = data.pop("window_cwsi", [])
            self._state = FusionState(**data)
            self._window.mds_norm_values = window_mds
            self._window.cwsi_values = window_cwsi
        except (json.JSONDecodeError, TypeError, KeyError):
            pass  # estado corrupto → arrancar fresco

    def save(self) -> None:
        os.makedirs(self.storage_dir, exist_ok=True)
        payload = asdict(self._state)
        payload["window_mds"] = self._window.mds_norm_values.copy()
        payload["window_cwsi"] = self._window.cwsi_values.copy()
        with open(self._state_path(), "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def register_scholander_session(self) -> None:
        """Llamar cada vez que se realiza una sesión de presión de cámara."""
        self._state.n_scholander_sessions += 1

    @property
    def mds_maturity(self) -> float:
        return min(1.0, self._state.n_scholander_sessions / MDS_MATURITY_FULL)

    def fuse(
        self,
        cwsi: float,
        mds_norm: float,
        cwsi_confidence: float = 1.0,
        wind_speed_ms: float = 0.0,
        timestamp: Optional[datetime] = None,
    ) -> FusionResult:
        """
        Fusiona CWSI y MDS_norm en el HSI.

        Args:
            cwsi: Crop Water Stress Index medido (0-1).
            mds_norm: MDS normalizado por baseline (0-1).
            cwsi_confidence: Confianza en el CWSI (0-1). < 0.4 → imputación.
            wind_speed_ms: Velocidad del viento en m/s. Rampa 4-18 m/s. ≥18 → override 100% MDS.
            timestamp: Momento de la medición (default: ahora).
        """
        ts = (timestamp or datetime.now()).isoformat()
        self._state.n_fusion_calls += 1
        self._state.last_update = ts

        # --- 1. Regresión actual
        alpha, beta = self._window.fit()
        r2 = self._window.r_squared()
        self._state.last_alpha = alpha
        self._state.last_beta = beta
        self._state.last_r2 = r2

        # --- 2. Wind override con rampa gradual 4-18 m/s
        wind_override = wind_speed_ms >= WIND_RAMP_HI_MS
        if wind_speed_ms <= WIND_RAMP_LO_MS:
            wind_cwsi_factor = 1.0
        elif wind_speed_ms >= WIND_RAMP_HI_MS:
            wind_cwsi_factor = 0.0
        else:
            wind_cwsi_factor = (WIND_RAMP_HI_MS - wind_speed_ms) / (WIND_RAMP_HI_MS - WIND_RAMP_LO_MS)
        if wind_override:
            self._state.wind_override_count += 1

        # --- 3. Imputación CWSI
        imputed = False
        cwsi_used = cwsi
        if not wind_override and cwsi_confidence < CWSI_CONFIDENCE_THRESHOLD:
            # Imputar CWSI desde el modelo local de regresión
            cwsi_used = float(alpha + beta * mds_norm)
            cwsi_used = max(0.0, min(1.0, cwsi_used))
            imputed = True
            self._state.imputation_count += 1

        # --- 4. Actualizar ventana (solo con datos reales, no imputados)
        if not imputed and not wind_override:
            cwsi_clipped = max(0.0, min(1.0, cwsi))
            mds_clipped = max(0.0, min(1.0, mds_norm))
            self._window.add(mds_clipped, cwsi_clipped)
            # recalcular con el nuevo dato
            alpha, beta = self._window.fit()
            r2 = self._window.r_squared()
            self._state.last_alpha = alpha
            self._state.last_beta = beta
            self._state.last_r2 = r2

        # --- 5. Pesos dinámicos
        mat = self.mds_maturity
        if wind_override:
            w_mds = 1.0
            w_cwsi = 0.0
        else:
            # base: 65% MDS + hasta 20% extra por madurez → máx 85%
            w_mds_base = 0.65 + 0.20 * mat
            # R² modula cuánto confiar en la señal térmica observada
            # Si R² alto, el modelo local es bueno → mantener más CWSI
            r2_factor = 1.0 - 0.5 * r2   # r2=0 → full shift MDS; r2=1 → half shift
            w_mds = min(0.90, w_mds_base * r2_factor + w_mds_base * (1 - r2_factor))
            w_mds = min(0.85, w_mds_base)
            w_cwsi = (1.0 - w_mds) * wind_cwsi_factor  # rampa gradual 4-18 m/s
            w_mds = 1.0 - w_cwsi

        # --- 6. Fusión
        hsi = w_cwsi * cwsi_used + w_mds * mds_norm
        hsi = max(0.0, min(1.0, hsi))

        # --- 7. Divergencia
        divergence_delta = abs(cwsi_used - mds_norm)
        divergence_alert = (not wind_override) and (divergence_delta > DIVERGENCE_THRESHOLD)
        if divergence_alert:
            self._state.divergence_count += 1

        return FusionResult(
            hsi=round(hsi, 4),
            cwsi_used=round(cwsi_used, 4),
            mds_norm=round(mds_norm, 4),
            weight_cwsi=round(w_cwsi, 4),
            weight_mds=round(w_mds, 4),
            alpha=round(alpha, 4),
            beta=round(beta, 4),
            r2=round(r2, 4),
            mds_maturity=round(mat, 4),
            imputed=imputed,
            wind_override=wind_override,
            divergence_alert=divergence_alert,
            divergence_delta=round(divergence_delta, 4),
            timestamp=ts,
        )

    def summary(self) -> dict:
        s = self._state
        return {
            "node_id": s.node_id,
            "crop": s.crop,
            "n_scholander_sessions": s.n_scholander_sessions,
            "mds_maturity": round(self.mds_maturity, 3),
            "window_samples": self._window.n,
            "regression": {
                "alpha": round(s.last_alpha, 4),
                "beta": round(s.last_beta, 4),
                "r2": round(s.last_r2, 4),
            },
            "n_fusion_calls": s.n_fusion_calls,
            "imputation_count": s.imputation_count,
            "wind_override_count": s.wind_override_count,
            "divergence_count": s.divergence_count,
            "last_update": s.last_update,
        }


# ---------------------------------------------------------------------------
# Demo __main__: 10 nodos × 30 días × 3 sesiones diarias
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import random
    import tempfile

    random.seed(42)
    tmp = tempfile.mkdtemp()
    print("=" * 70)
    print("DEMO FusionEngine — 10 nodos × 30 días × 3 sesiones/día")
    print("=" * 70)

    nodes = [f"N{i+1:02d}" for i in range(10)]
    engines = {nid: FusionEngine(nid, storage_dir=tmp) for nid in nodes}

    # Simular 30 días con estrés creciente a partir del día 15
    for day in range(1, 31):
        stress_base = 0.2 + 0.02 * max(0, day - 14)   # sube a partir del día 15
        for session in range(3):
            hour = 7 + session * 5  # 07:00, 12:00, 17:00
            for nid, eng in engines.items():
                # Correlación real + ruido
                mds_true = min(0.95, stress_base + random.gauss(0, 0.05))
                cwsi_true = min(0.95, 0.85 * mds_true + 0.05 + random.gauss(0, 0.04))
                mds_true = max(0.0, mds_true)
                cwsi_true = max(0.0, cwsi_true)

                # Semana 4: simular día nublado (baja confianza CWSI)
                conf = 0.25 if (day >= 22 and session == 1) else 0.95

                # Día 10: simular viento fuerte
                wind = 5.5 if day == 10 else random.uniform(0.5, 2.5)

                ts = datetime(2025, 11, day, hour, 0, 0)
                result = eng.fuse(cwsi_true, mds_true,
                                  cwsi_confidence=conf,
                                  wind_speed_ms=wind,
                                  timestamp=ts)

                # Registrar sesión Scholander día 5, 10, 15, 20, 25 (sesión matutina)
                if day % 5 == 0 and session == 0:
                    eng.register_scholander_session()

    print()
    print(f"{'Nodo':<6} {'Sesiones':>8} {'Madurez':>8} {'Muestras':>9} "
          f"{'α':>7} {'β':>7} {'R²':>6} {'Div.':>5} {'Imp.':>5} {'Viento':>7}")
    print("-" * 70)
    for nid, eng in engines.items():
        s = eng.summary()
        r = s["regression"]
        print(f"{nid:<6} {s['n_scholander_sessions']:>8} {s['mds_maturity']:>8.3f} "
              f"{s['window_samples']:>9} {r['alpha']:>7.4f} {r['beta']:>7.4f} "
              f"{r['r2']:>6.4f} {s['divergence_count']:>5} "
              f"{s['imputation_count']:>5} {s['wind_override_count']:>7}")

    # Ejemplo de resultado individual
    print()
    eng_demo = engines["N01"]
    result_demo = eng_demo.fuse(cwsi=0.72, mds_norm=0.65, cwsi_confidence=0.9,
                                wind_speed_ms=1.2)
    print("Ejemplo fusión N01 (estrés moderado):")
    print(f"  HSI          = {result_demo.hsi:.4f}")
    print(f"  CWSI usado   = {result_demo.cwsi_used:.4f}  (imputado={result_demo.imputed})")
    print(f"  MDS_norm     = {result_demo.mds_norm:.4f}")
    print(f"  Pesos        = CWSI {result_demo.weight_cwsi:.2f} / MDS {result_demo.weight_mds:.2f}")
    print(f"  Regresión    = α={result_demo.alpha:.4f}, β={result_demo.beta:.4f}, R²={result_demo.r2:.4f}")
    print(f"  MDS maturity = {result_demo.mds_maturity:.3f}")
    print(f"  Divergencia  = {result_demo.divergence_delta:.4f}  "
          f"(alerta={result_demo.divergence_alert})")
    print(f"  Wind override= {result_demo.wind_override}")
    print(f"  Timestamp    = {result_demo.timestamp}")

    # Escenario viento fuerte
    result_wind = eng_demo.fuse(cwsi=0.80, mds_norm=0.65, wind_speed_ms=6.0)
    print()
    print("Escenario viento fuerte (6 m/s) → override 100% MDS:")
    print(f"  HSI={result_wind.hsi:.4f}  Pesos CWSI={result_wind.weight_cwsi:.2f}/"
          f"MDS={result_wind.weight_mds:.2f}  wind_override={result_wind.wind_override}")

    # Escenario día nublado (imputación)
    result_imp = eng_demo.fuse(cwsi=0.55, mds_norm=0.68, cwsi_confidence=0.2)
    print()
    print("Escenario día nublado (cwsi_confidence=0.2) → imputación CWSI:")
    print(f"  CWSI medido=0.55  CWSI imputado={result_imp.cwsi_used:.4f}  "
          f"imputed={result_imp.imputed}")
    print(f"  HSI={result_imp.hsi:.4f}")

    print()
    print("Demo completada exitosamente.")
