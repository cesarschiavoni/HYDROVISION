"""
Motor de fusión HSI — HydroVision AG
=====================================
HydroVision Stress Index (HSI) = fusión de CWSI térmico + MDS dendrométrico.

Arquitectura de fusión:
    HSI = w_cwsi(t) × CWSI_calibrado + w_mds(t) × MDS_normalizado

Los pesos son DINÁMICOS: se ajustan en cada sesión según:
- Calidad de señal del extensómetro (temperatura compensada, sin ruido)
- Cantidad de datos de calibración local disponibles
- Condiciones meteorológicas (nublado → cámara menos confiable)
- Etapa de la temporada (Mes 1–3: pocos datos MDS → más peso CWSI)

Cross-calibración MDS↔CWSI:
- El nodo aprende la regresión local CWSI = f(MDS) para ESE viñedo
- Permite detectar derivas de sensor: si CWSI y MDS divergen → alerta
- Después de N sesiones, usa la regresión local para imputar CWSI
  cuando la cámara tiene baja confianza (nubes, sol muy bajo)

Conversión MDS → ψ_stem:
    ψ_stem = -0.15 + (-0.0080) × MDS  [MPa]
    (Fernández & Cuevas 2010, R²=0.80–0.92 para vid)

MDS normalizado a [0,1]:
    MDS_norm = MDS / MDS_max
    donde MDS_max ≈ 350 µm (estrés severo Malbec, Colonia Caroya)

Uso típico (por sesión en campo, ~3 veces/día):
    engine = HSIFusionEngine(node_id="nodo_A")
    engine.ingest_mds(mds_um=180.0, timestamp=..., temp_celsius=25.1)
    hsi, report = engine.compute(cwsi=0.55, ta=28.0, vpd=2.1, weather_quality=0.9)
    print(report)
"""

from __future__ import annotations

import json
import logging
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from baseline import CWSIBaseline

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constantes de normalización y umbrales
# ---------------------------------------------------------------------------

# MDS de referencia para normalización [µm]
# Basado en datos de Malbec bajo estrés severo (ETc 0-15%)
MDS_MAX_REFERENCE = 350.0   # µm → HSI_mds = 1.0 (estrés máximo)
MDS_MIN_WELLWATERED = 30.0  # µm → HSI_mds ≈ 0.0 (sin estrés)

# Conversión MDS → ψ_stem (Fernández & Cuevas 2010)
PSI_INTERCEPT = -0.15   # MPa
PSI_SLOPE = -0.0080     # MPa/µm

# Pesos base (sin ajuste dinámico)
W_CWSI_DEFAULT = 0.35
W_MDS_DEFAULT = 0.65


# ---------------------------------------------------------------------------
# Regresión online CWSI↔MDS (mínimos cuadrados incrementales)
# ---------------------------------------------------------------------------
class OnlineLinearRegression:
    """
    Regresión lineal CWSI = α + β × MDS_norm actualizada online
    con cada nuevo par de observaciones.

    Usa el algoritmo de actualización de mínimos cuadrados recursivo
    (RLS simplificado con ventana deslizante).
    """

    MIN_SAMPLES = 10  # mínimo para confiar en la regresión

    def __init__(self, window: int = 60):
        self.window = window
        self._x: deque[float] = deque(maxlen=window)
        self._y: deque[float] = deque(maxlen=window)
        self.alpha: float = 0.0    # intercepto
        self.beta: float = 1.0     # pendiente (CWSI ≈ MDS inicialmente)
        self.r2: float = float("nan")
        self.n_samples: int = 0

    def update(self, mds_norm: float, cwsi: float) -> None:
        self._x.append(mds_norm)
        self._y.append(cwsi)
        self.n_samples += 1
        if len(self._x) >= self.MIN_SAMPLES:
            self._fit()

    def _fit(self) -> None:
        x = np.array(self._x)
        y = np.array(self._y)
        xm, ym = x.mean(), y.mean()
        denom = ((x - xm) ** 2).sum()
        if denom < 1e-9:
            return
        self.beta = float(((x - xm) * (y - ym)).sum() / denom)
        self.alpha = float(ym - self.beta * xm)
        y_pred = self.alpha + self.beta * x
        ss_res = ((y - y_pred) ** 2).sum()
        ss_tot = ((y - ym) ** 2).sum()
        self.r2 = float(1 - ss_res / ss_tot) if ss_tot > 1e-9 else float("nan")

    def predict_cwsi(self, mds_norm: float) -> Optional[float]:
        """Predice CWSI a partir de MDS si hay suficientes datos."""
        if self.n_samples < self.MIN_SAMPLES:
            return None
        return float(np.clip(self.alpha + self.beta * mds_norm, 0.0, 1.0))

    @property
    def is_fitted(self) -> bool:
        return self.n_samples >= self.MIN_SAMPLES

    def summary(self) -> dict:
        return {
            "n_samples": self.n_samples,
            "alpha": round(self.alpha, 4),
            "beta": round(self.beta, 4),
            "r2": round(self.r2, 4) if not np.isnan(self.r2) else None,
            "is_fitted": self.is_fitted,
        }


# ---------------------------------------------------------------------------
# Lectura del extensómetro
# ---------------------------------------------------------------------------
@dataclass
class MDSReading:
    """
    Lectura del extensómetro de tronco en un instante dado.

    El extensómetro mide diámetro de tronco [µm] continuamente.
    MDS = D_max - D_min dentro del mismo día.
    """
    timestamp_iso: str
    diameter_um: float          # diámetro absoluto actual [µm]
    temperature_c: float        # temperatura del tronco para compensación
    quality: float              # 0-1 (1 = señal limpia, sin ruido ni drift térmico)
    is_dmax: bool = False       # True si es lectura de D_max (≈ 5-6am)
    is_dmin: bool = False       # True si es lectura de D_min (≈ 13-15hs)


# ---------------------------------------------------------------------------
# Reporte de sesión
# ---------------------------------------------------------------------------
@dataclass
class FusionReport:
    """Resultado completo de una sesión de fusión HSI."""
    timestamp_iso: str
    node_id: str

    # Índices finales
    hsi: float                  # HydroVision Stress Index [0-1]
    cwsi: float                 # CWSI térmico (input)
    mds_um: float               # MDS dendrométrico [µm]
    mds_norm: float             # MDS normalizado [0-1]
    psi_stem_mpa: float         # ψ_stem estimado [MPa]

    # Pesos dinámicos usados
    w_cwsi: float
    w_mds: float

    # Calidad y alertas
    cwsi_confidence: float      # 0-1
    mds_quality: float          # 0-1
    divergence_alert: bool      # True si CWSI y MDS divergen significativamente
    divergence_delta: float     # diferencia absoluta CWSI - MDS_norm

    # Regresión local
    regression_r2: Optional[float]
    cwsi_predicted_from_mds: Optional[float]

    # Calibración de baseline
    baseline_offset: float      # tc_wet_offset actual

    def stress_level(self) -> str:
        """Clasificación semáforo del nivel de estrés."""
        if self.hsi < 0.25:
            return "SIN_ESTRÉS"
        elif self.hsi < 0.50:
            return "LEVE"
        elif self.hsi < 0.75:
            return "MODERADO"
        else:
            return "SEVERO"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["stress_level"] = self.stress_level()
        return d


# ---------------------------------------------------------------------------
# Motor principal de fusión
# ---------------------------------------------------------------------------
class HSIFusionEngine:
    """
    Motor de fusión HSI para un nodo HydroVision.

    Combina CWSI térmico + MDS dendrométrico con:
    - Pesos dinámicos por calidad de señal
    - Cross-calibración CWSI↔MDS online
    - Detección de divergencia entre sensores
    - Impugnación de CWSI desde MDS cuando la cámara falla
    """

    def __init__(
        self,
        node_id: str,
        zone: str = "A",
        mds_max: float = MDS_MAX_REFERENCE,
    ):
        self.node_id = node_id
        self.zone = zone
        self.mds_max = mds_max

        self.baseline = CWSIBaseline(node_id)
        self.regression = OnlineLinearRegression(window=60)

        # Buffer de lecturas del extensómetro del día actual
        self._today_readings: list[MDSReading] = []
        self._dmax: Optional[float] = None
        self._dmin: Optional[float] = None
        self._current_mds: float = 0.0
        self._mds_quality: float = 1.0

        # Historial de HSI (para detectar deriva)
        self._hsi_history: deque[float] = deque(maxlen=90)
        self._cwsi_history: deque[float] = deque(maxlen=90)
        self._session_count: int = 0

    # --- Ingesta de datos del extensómetro ---

    def ingest_mds_reading(self, reading: MDSReading) -> None:
        """
        Recibe una lectura del extensómetro y actualiza D_max / D_min del día.
        El firmware envía lecturas continuas; este método actualiza el MDS
        rolling a medida que llegan datos.
        """
        self._today_readings.append(reading)
        self._mds_quality = reading.quality

        diameters = [r.diameter_um for r in self._today_readings]
        d_max = max(diameters)
        d_min = min(diameters)
        self._current_mds = d_max - d_min

        if reading.is_dmax:
            self._dmax = reading.diameter_um
        if reading.is_dmin:
            self._dmin = reading.diameter_um
            if self._dmax is not None:
                self._current_mds = self._dmax - reading.diameter_um

    def reset_daily(self) -> None:
        """Llama al inicio de cada día (medianoche) para limpiar el buffer."""
        self._today_readings.clear()
        self._dmax = None
        self._dmin = None

    # --- Normalización y conversión ---

    def normalize_mds(self, mds_um: float) -> float:
        """MDS [µm] → [0, 1] usando la referencia de estrés máximo."""
        return float(np.clip(mds_um / self.mds_max, 0.0, 1.0))

    @staticmethod
    def mds_to_psi(mds_um: float) -> float:
        """
        ψ_stem [MPa] = -0.15 + (-0.0080) × MDS [µm]
        (Fernández & Cuevas 2010, R²=0.80–0.92)
        """
        return PSI_INTERCEPT + PSI_SLOPE * mds_um

    # --- Pesos dinámicos ---

    def _compute_weights(
        self,
        cwsi_confidence: float,
        mds_quality: float,
        n_sessions: int,
    ) -> Tuple[float, float]:
        """
        Calcula pesos dinámicos w_cwsi y w_mds que suman 1.0.

        Lógica:
        - Al inicio de la temporada (pocos datos), CWSI pesa más porque
          el extensómetro aún no tiene calibración local suficiente.
        - Con alta calidad de MDS y muchas sesiones, MDS pesa más.
        - Si la cámara está degradada (nublado, sol oblicuo), CWSI baja.

        Args:
            cwsi_confidence: calidad de la imagen térmica [0-1]
            mds_quality: calidad de señal del extensómetro [0-1]
            n_sessions: sesiones acumuladas en el nodo

        Returns:
            (w_cwsi, w_mds) normalizados a suma 1.0
        """
        # Confianza de datos MDS crece con sesiones acumuladas
        mds_maturity = min(1.0, n_sessions / 20.0)

        raw_cwsi = W_CWSI_DEFAULT * cwsi_confidence
        raw_mds = W_MDS_DEFAULT * mds_quality * mds_maturity

        # Si MDS no tiene madurez suficiente, trasladar su peso a CWSI
        if mds_maturity < 0.5:
            raw_cwsi += W_MDS_DEFAULT * (1 - mds_maturity) * 0.5

        total = raw_cwsi + raw_mds
        if total < 1e-6:
            return 0.5, 0.5
        return round(raw_cwsi / total, 4), round(raw_mds / total, 4)

    # --- Detección de divergencia ---

    def _check_divergence(self, cwsi: float, mds_norm: float) -> Tuple[bool, float]:
        """
        Detecta divergencia entre CWSI y MDS.
        Umbral: > 0.35 de diferencia absoluta sostenida → alerta.
        """
        delta = abs(cwsi - mds_norm)
        alert = delta > 0.35
        if alert:
            logger.warning(
                f"[{self.node_id}] Divergencia CWSI↔MDS: "
                f"CWSI={cwsi:.3f}, MDS_norm={mds_norm:.3f}, Δ={delta:.3f}"
            )
        return alert, delta

    # --- Compute principal ---

    def compute(
        self,
        cwsi: float,
        ta: float,
        vpd_kpa: float,
        cwsi_confidence: float = 1.0,
        mds_override: Optional[float] = None,
        timestamp_iso: Optional[str] = None,
    ) -> Tuple[float, FusionReport]:
        """
        Calcula el HSI para la sesión actual.

        Args:
            cwsi: CWSI térmico de la cámara [0-1]
            ta: temperatura del aire [°C]
            vpd_kpa: VPD [kPa]
            cwsi_confidence: calidad de la imagen térmica [0-1]
                             (1.0 = cielo despejado, sol en ángulo óptimo)
            mds_override: forzar un valor de MDS [µm] (para testing)
            timestamp_iso: timestamp de la sesión (default: ahora UTC)

        Returns:
            hsi: HydroVision Stress Index [0-1]
            report: FusionReport con todos los detalles
        """
        if timestamp_iso is None:
            timestamp_iso = datetime.now(timezone.utc).isoformat()

        mds_um = mds_override if mds_override is not None else self._current_mds
        mds_norm = self.normalize_mds(mds_um)
        psi_stem = self.mds_to_psi(mds_um)

        # --- Actualizar regresión local CWSI↔MDS ---
        self.regression.update(mds_norm, cwsi)

        # --- Pesos dinámicos ---
        w_cwsi, w_mds = self._compute_weights(
            cwsi_confidence=cwsi_confidence,
            mds_quality=self._mds_quality,
            n_sessions=self._session_count,
        )

        # --- Si la cámara tiene baja confianza, imputar CWSI desde MDS ---
        cwsi_used = cwsi
        if cwsi_confidence < 0.4 and self.regression.is_fitted:
            cwsi_pred = self.regression.predict_cwsi(mds_norm)
            if cwsi_pred is not None:
                blend = cwsi_confidence  # más confianza térmica → más peso al valor real
                cwsi_used = blend * cwsi + (1 - blend) * cwsi_pred
                logger.info(
                    f"[{self.node_id}] CWSI imputado desde MDS: "
                    f"raw={cwsi:.3f}, pred={cwsi_pred:.3f}, blended={cwsi_used:.3f}"
                )

        # --- Fusión ---
        hsi = float(np.clip(w_cwsi * cwsi_used + w_mds * mds_norm, 0.0, 1.0))

        # --- Divergencia ---
        divergence_alert, divergence_delta = self._check_divergence(cwsi, mds_norm)

        # --- Historial ---
        self._hsi_history.append(hsi)
        self._cwsi_history.append(cwsi)
        self._session_count += 1

        report = FusionReport(
            timestamp_iso=timestamp_iso,
            node_id=self.node_id,
            hsi=round(hsi, 4),
            cwsi=round(cwsi, 4),
            mds_um=round(mds_um, 2),
            mds_norm=round(mds_norm, 4),
            psi_stem_mpa=round(psi_stem, 3),
            w_cwsi=w_cwsi,
            w_mds=w_mds,
            cwsi_confidence=round(cwsi_confidence, 3),
            mds_quality=round(self._mds_quality, 3),
            divergence_alert=divergence_alert,
            divergence_delta=round(divergence_delta, 4),
            regression_r2=self.regression.summary()["r2"],
            cwsi_predicted_from_mds=self.regression.predict_cwsi(mds_norm),
            baseline_offset=round(self.baseline.tc_wet_offset, 4),
        )

        logger.info(
            f"[{self.node_id}] HSI={hsi:.3f} ({report.stress_level()}) | "
            f"CWSI={cwsi:.3f}×{w_cwsi:.2f} + MDS_norm={mds_norm:.3f}×{w_mds:.2f} | "
            f"ψ_stem={psi_stem:.2f}MPa"
        )

        return hsi, report

    # --- Integración con calibración por lluvia ---

    def on_rain_event(
        self,
        tc_canopy: float,
        ta: float,
        vpd_kpa: float,
        timestamp_iso: str,
    ) -> bool:
        """
        Notifica un evento de lluvia al motor.
        Si el MDS actual es bajo → dispara recalibración del baseline CWSI.
        """
        return self.baseline.update_rain(
            tc_measured=tc_canopy,
            ta=ta,
            vpd_kpa=vpd_kpa,
            mds_um=self._current_mds,
            timestamp_iso=timestamp_iso,
        )

    # --- Estado y persistencia ---

    def summary(self) -> dict:
        hsi_arr = np.array(list(self._hsi_history))
        return {
            "node_id": self.node_id,
            "zone": self.zone,
            "session_count": self._session_count,
            "current_mds_um": round(self._current_mds, 2),
            "current_mds_norm": round(self.normalize_mds(self._current_mds), 4),
            "psi_stem_mpa": round(self.mds_to_psi(self._current_mds), 3),
            "hsi_mean_last10": round(float(hsi_arr[-10:].mean()), 4) if len(hsi_arr) >= 10 else None,
            "regression": self.regression.summary(),
            "baseline": self.baseline.summary(),
        }

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        state = {
            "node_id": self.node_id,
            "zone": self.zone,
            "mds_max": self.mds_max,
            "current_mds": self._current_mds,
            "mds_quality": self._mds_quality,
            "session_count": self._session_count,
            "hsi_history": list(self._hsi_history),
            "cwsi_history": list(self._cwsi_history),
            "regression": {
                "x": list(self.regression._x),
                "y": list(self.regression._y),
                "alpha": self.regression.alpha,
                "beta": self.regression.beta,
                "r2": self.regression.r2,
                "n_samples": self.regression.n_samples,
            },
        }
        (directory / f"fusion_{self.node_id}.json").write_text(
            json.dumps(state, indent=2, ensure_ascii=False)
        )
        self.baseline.save(directory / f"baseline_{self.node_id}.json")
        logger.info(f"[{self.node_id}] Estado guardado en {directory}")


# ---------------------------------------------------------------------------
# Demo: 10 nodos × temporada completa simulada
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "01_simulador"))
    from simulator import ThermalSimulator, ETC_REGIMES
    from weather import sample_colonia_caroya

    print("=== Demo HSI Fusion Engine — 10 nodos, temporada simulada ===\n")

    rng = np.random.default_rng(42)
    sim = ThermalSimulator(seed=42)

    # Crear un motor por zona hídrica
    engines = {
        zone: HSIFusionEngine(node_id=f"nodo_{zone}", zone=zone)
        for zone in ETC_REGIMES
    }
    etc_values = list(ETC_REGIMES.values())

    # Simular 30 días × 3 sesiones/día
    for day in range(1, 31):
        doy = 330 + day
        rain = float(rng.choice([0, 0, 0, 8, 20], p=[0.7, 0.1, 0.1, 0.06, 0.04]))

        for hour in [8.5, 12.0, 16.0]:
            weather = sample_colonia_caroya(hour=hour, day_of_year=doy, rain_48h=rain, rng=rng)

            for zone, engine in engines.items():
                etc = ETC_REGIMES[zone]
                _, meta = sim.generate(weather, etc_fraction=etc)

                # MDS simulado: crece con estrés, ciclo diario
                mds_base = (1 - etc) * 280 + rng.normal(0, 15)
                mds_um = max(0, mds_base * (0.6 if hour < 10 else 1.0))

                hsi, report = engine.compute(
                    cwsi=meta["cwsi"],
                    ta=weather.ta,
                    vpd_kpa=weather.vpd,
                    cwsi_confidence=min(1.0, weather.rn / 500),
                    mds_override=mds_um,
                )

                if rain > 5 and hour == 8.5:
                    engine.on_rain_event(
                        tc_canopy=meta["tc_mean"],
                        ta=weather.ta,
                        vpd_kpa=weather.vpd,
                        timestamp_iso=f"2025-{11+day//30:02d}-{(day%30)+1:02d}T{int(hour):02d}:00:00Z",
                    )

    print("Resumen por nodo al final de 30 días:\n")
    for zone, engine in engines.items():
        s = engine.summary()
        etc_pct = int(ETC_REGIMES[zone] * 100)
        print(
            f"  Zona {zone} (ETc {etc_pct:3d}%): "
            f"HSI_mean={s['hsi_mean_last10']:.3f}  "
            f"MDS={s['current_mds_um']:.1f}µm  "
            f"ψ={s['psi_stem_mpa']:.2f}MPa  "
            f"Reg_R²={s['regression']['r2']}  "
            f"Baseline_offset={s['baseline']['tc_wet_offset']:+.3f}°C"
        )
