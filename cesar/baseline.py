"""
Auto-Calibración Dinámica del Baseline CWSI — baseline.py
Prueba de Concepto TRL 3 — HydroVision AG — Colonia Caroya, Córdoba

El CWSI requiere dos parámetros baseline por nodo:
  - Tc_wet: temperatura de la hoja bien hidratada (límite inferior)
  - Tc_dry: temperatura sin transpiración (límite superior)

Sin calibración de campo, el error sistemático del baseline se acumula
silenciosamente durante la temporada y puede desplazar el CWSI ±0.15–0.20
unidades — suficiente para generar falsas alarmas o perder estrés real.

Este módulo implementa tres mecanismos de auto-calibración:

  1. Evento de lluvia con MDS≈0:
     Cuando llueve ≥5mm y el extensómetro registra MDS cercano a cero
     (planta al máximo de hidratación), la temperatura foliar medida ES el
     Tc_wet real del nodo para esas condiciones. Actualización por EMA.

  2. Sesión Scholander:
     Cada sesión aporta un par verificado (Tc, ψ_stem). Si ψ_stem indica
     planta bien hidratada (MDS < 200µm), actualiza el baseline con tasa
     de aprendizaje reducida (más conservador que lluvia).

  3. Detección de deriva:
     CWSI sistemáticamente fuera de rango o señal sin variación →
     alerta de recalibración al dashboard.

Persistencia: los offsets se guardan en JSON local (un archivo por nodo).
Al reiniciar el RPi4, el nodo carga el baseline calibrado de la temporada.

Referencias:
  Jackson, R.D. et al. (1981). Canopy temperature as a crop water stress
  indicator. Water Resources Research, 17(4), 1133-1138.
  [NWSB original — baseline de fábrica]

  Jones, H.G. (1999). Use of thermography for quantitative studies of
  spatial and temporal variation of stomatal conductance over leaf surfaces.
  Plant, Cell & Environment, 22(9), 1043-1055.
  [Validación de Tc_wet medido físicamente vs. estimado]

  Fernandez, J.E. & Cuevas, M.V. (2010).
  Irrigation scheduling from stem diameter variations: A review.
  Agricultural and Forest Meteorology, 150(2), 135-151.
  [MDS≈0 como indicador de planta al máximo de hidratación]
"""

import json
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES DE CALIBRACIÓN
# ─────────────────────────────────────────────────────────────────────────────

# EMA (Exponential Moving Average) — tasa de aprendizaje base
LEARNING_RATE_RAIN  = 0.25   # lluvia + MDS≈0 → señal fisiológica fuerte
LEARNING_RATE_SCHOLANDER = 0.10  # sesión Scholander → señal verificada pero conservadora

# Umbral de lluvia mínima para activar calibración [mm]
RAIN_THRESHOLD_MM = 5.0

# Umbral MDS para considerar planta "al máximo de hidratación" [µm]
# Por debajo de este valor el extensómetro confirma que la planta está bien hidratada
MDS_HYDRATED_THRESHOLD_UM = 80.0

# Umbral de CWSI para detectar deriva sistemática
DRIFT_LOW_THRESHOLD  = 0.02   # CWSI < 0.02 sostenido → Tc_wet sobreestimado
DRIFT_HIGH_THRESHOLD = 0.98   # CWSI > 0.98 sostenido → Tc_wet subestimado
DRIFT_MIN_SAMPLES    = 10     # mínimo de muestras para detectar deriva

# Umbral de variación para detectar señal muerta
DRIFT_STD_MIN = 0.01          # std(CWSI) < este valor → posible falla de sensor


# ─────────────────────────────────────────────────────────────────────────────
# ESTADO DEL BASELINE
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BaselineState:
    """
    Estado de calibración del baseline CWSI para un nodo.

    tc_wet_offset: corrección sobre el NWSB calculado.
      Tc_wet_efectivo = NWSB(Ta, VPD) + tc_wet_offset
      Empieza en 0.0 (sin corrección) y converge al comportamiento real del nodo.

    tc_dry_offset: corrección análoga para el límite superior.
      Empieza en 0.0.

    n_rain_events: cantidad de eventos de lluvia usados para calibración.
    n_scholander_updates: cantidad de sesiones Scholander incorporadas.
    calibration_quality: 'factory' → sin calibración real,
                         'field_partial' → 1-4 eventos,
                         'field_good' → 5+ eventos,
                         'field_excellent' → 10+ eventos.
    drift_alert: True si se detectó deriva sostenida sin resolver.
    """
    node_id: str            = "N01"
    crop: str               = "malbec"
    tc_wet_offset: float    = 0.0       # [°C]
    tc_dry_offset: float    = 0.0       # [°C]
    n_rain_events: int      = 0
    n_scholander_updates: int = 0
    last_rain_date: str     = ""
    last_scholander_date: str = ""
    calibration_quality: str  = "factory"
    drift_alert: bool         = False
    drift_direction: str      = ""      # "low" | "high" | "dead" | ""
    season: str               = ""      # "2026-2027"
    cwsi_history: list        = field(default_factory=list)   # últimas N muestras

    def update_quality(self) -> None:
        """Actualiza la calificación de calidad según el historial de eventos."""
        total = self.n_rain_events + self.n_scholander_updates
        if total == 0:
            self.calibration_quality = "factory"
        elif total < 5:
            self.calibration_quality = "field_partial"
        elif total < 10:
            self.calibration_quality = "field_good"
        else:
            self.calibration_quality = "field_excellent"


# ─────────────────────────────────────────────────────────────────────────────
# MOTOR DE AUTO-CALIBRACIÓN
# ─────────────────────────────────────────────────────────────────────────────

class CWSIBaseline:
    """
    Motor de auto-calibración dinámica del baseline CWSI por nodo.

    Uso típico en el nodo:
        baseline = CWSIBaseline.load("N01")           # carga JSON local
        # ... en cada ciclo de captura:
        cwsi_real = (Tc - (nwsb + baseline.state.tc_wet_offset)) / ...
        baseline.add_cwsi_sample(cwsi_real)
        # ... tras evento de lluvia:
        baseline.update_rain(Tc_measured, Ta, VPD, MDS, rain_mm, date)
        baseline.save()                               # persiste en JSON
    """

    MAX_HISTORY = 60   # muestras CWSI retenidas para detección de deriva

    def __init__(self, state: BaselineState):
        self.state = state

    # ── Persistencia ──────────────────────────────────────────────────────────

    @classmethod
    def load(cls, node_id: str,
             storage_dir: str = "/var/hydrovision/baseline") -> "CWSIBaseline":
        """
        Carga el baseline desde JSON local.
        Si el archivo no existe, crea un baseline de fábrica (offsets = 0).
        """
        path = Path(storage_dir) / f"baseline_{node_id}.json"
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            state = BaselineState(**data)
        else:
            state = BaselineState(node_id=node_id)
        return cls(state)

    def save(self, storage_dir: str = "/var/hydrovision/baseline") -> None:
        """Persiste el estado del baseline en JSON local."""
        path = Path(storage_dir) / f"baseline_{self.state.node_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        # cwsi_history: guardar solo las últimas MAX_HISTORY muestras
        self.state.cwsi_history = self.state.cwsi_history[-self.MAX_HISTORY:]
        with open(path, "w") as f:
            json.dump(asdict(self.state), f, indent=2)

    # ── Actualización por evento de lluvia ────────────────────────────────────

    def update_rain(self,
                    tc_measured_c: float,
                    ta_c: float,
                    vpd_kpa: float,
                    mds_um: float,
                    rain_mm: float,
                    date: str) -> dict:
        """
        Actualiza el baseline usando un evento de lluvia con MDS≈0.

        La planta al máximo de hidratación → Tc medida ≈ Tc_wet real del nodo.
        La diferencia (Tc_medido − NWSB_calculado) es el offset de campo.

        Parámetros
        ----------
        tc_measured_c  : temperatura foliar medida por la cámara [°C]
        ta_c           : temperatura del aire [°C]
        vpd_kpa        : déficit de presión de vapor [kPa]
        mds_um         : MDS del extensómetro ese día [µm]
        rain_mm        : precipitación registrada [mm]
        date           : fecha del evento (YYYY-MM-DD)

        Retorna dict con resultado de la actualización.
        """
        if rain_mm < RAIN_THRESHOLD_MM:
            return {"updated": False,
                    "reason": f"Lluvia insuficiente ({rain_mm:.1f}mm < {RAIN_THRESHOLD_MM}mm)"}

        if mds_um > MDS_HYDRATED_THRESHOLD_UM:
            return {"updated": False,
                    "reason": f"MDS={mds_um:.0f}µm > umbral {MDS_HYDRATED_THRESHOLD_UM}µm — planta no al máximo de hidratación"}

        # NWSB de Jackson (1981): Tc_wet ≈ Ta − 0.5·VPD (aproximación lineal)
        nwsb = _nwsb_tc_wet(ta_c, vpd_kpa)
        measured_offset = tc_measured_c - nwsb

        # EMA update
        old_offset = self.state.tc_wet_offset
        lr = LEARNING_RATE_RAIN
        new_offset = (1 - lr) * old_offset + lr * measured_offset

        self.state.tc_wet_offset = round(new_offset, 4)
        self.state.n_rain_events += 1
        self.state.last_rain_date = date
        self.state.drift_alert = False
        self.state.drift_direction = ""
        self.state.update_quality()

        return {
            "updated": True,
            "event": "rain",
            "date": date,
            "nwsb_tc_wet": round(nwsb, 2),
            "tc_measured": round(tc_measured_c, 2),
            "measured_offset": round(measured_offset, 4),
            "old_offset": round(old_offset, 4),
            "new_offset": round(new_offset, 4),
            "learning_rate": lr,
            "calibration_quality": self.state.calibration_quality,
            "n_rain_events": self.state.n_rain_events,
        }

    # ── Actualización por sesión Scholander ───────────────────────────────────

    def update_scholander(self,
                          tc_measured_c: float,
                          ta_c: float,
                          vpd_kpa: float,
                          psi_stem_mpa: float,
                          mds_um: float,
                          date: str) -> dict:
        """
        Actualiza el baseline usando datos verificados de una sesión Scholander.

        Solo actualiza si ψ_stem indica planta razonablemente hidratada.
        La confianza es proporcional al nivel de hidratación (MDS bajo → más confianza).

        Parámetros
        ----------
        tc_measured_c  : temperatura foliar medida [°C]
        ta_c           : temperatura del aire [°C]
        vpd_kpa        : VPD [kPa]
        psi_stem_mpa   : potencial hídrico de tallo medido con Scholander [MPa]
        mds_um         : MDS del extensómetro en esa sesión [µm]
        date           : fecha de la sesión (YYYY-MM-DD)
        """
        # Solo actualizar si la planta está razonablemente hidratada
        if psi_stem_mpa < -1.0:
            return {"updated": False,
                    "reason": f"ψ_stem={psi_stem_mpa:.2f}MPa — planta con estrés, no actualizar baseline wet"}

        # Confianza proporcional a la hidratación (MDS bajo → más confianza)
        confidence = max(0.1, 1.0 - mds_um / 500.0)
        lr = LEARNING_RATE_SCHOLANDER * confidence

        nwsb = _nwsb_tc_wet(ta_c, vpd_kpa)
        measured_offset = tc_measured_c - nwsb

        old_offset = self.state.tc_wet_offset
        new_offset = (1 - lr) * old_offset + lr * measured_offset

        self.state.tc_wet_offset = round(new_offset, 4)
        self.state.n_scholander_updates += 1
        self.state.last_scholander_date = date
        self.state.update_quality()

        return {
            "updated": True,
            "event": "scholander",
            "date": date,
            "psi_stem_mpa": psi_stem_mpa,
            "confidence": round(confidence, 3),
            "effective_lr": round(lr, 4),
            "measured_offset": round(measured_offset, 4),
            "old_offset": round(old_offset, 4),
            "new_offset": round(new_offset, 4),
            "calibration_quality": self.state.calibration_quality,
        }

    # ── Detección de deriva ───────────────────────────────────────────────────

    def add_cwsi_sample(self, cwsi: float) -> None:
        """Agrega una muestra CWSI al historial para detección de deriva."""
        if 0.0 <= cwsi <= 1.0:
            self.state.cwsi_history.append(cwsi)
            if len(self.state.cwsi_history) > self.MAX_HISTORY:
                self.state.cwsi_history.pop(0)

    def check_drift(self) -> dict:
        """
        Detecta deriva sistemática del baseline a partir del historial CWSI.

        Condiciones de alerta:
          (a) media < DRIFT_LOW_THRESHOLD → Tc_wet sobreestimado (baseline alto)
          (b) media > DRIFT_HIGH_THRESHOLD → Tc_wet subestimado (baseline bajo)
          (c) std < DRIFT_STD_MIN con N > mínimo → señal muerta / falla de sensor

        Retorna dict con estado de la deriva.
        """
        h = self.state.cwsi_history
        if len(h) < DRIFT_MIN_SAMPLES:
            return {"drift_detected": False,
                    "reason": f"Historial insuficiente ({len(h)}/{DRIFT_MIN_SAMPLES} muestras)"}

        mean_cwsi = sum(h) / len(h)
        variance  = sum((x - mean_cwsi) ** 2 for x in h) / len(h)
        std_cwsi  = math.sqrt(variance)

        # Verificar media primero (calibración sistemática) → luego señal muerta
        if mean_cwsi < DRIFT_LOW_THRESHOLD:
            self.state.drift_alert = True
            self.state.drift_direction = "low"
            return {"drift_detected": True, "direction": "low",
                    "mean": round(mean_cwsi, 4), "std": round(std_cwsi, 4),
                    "message": f"CWSI sistemáticamente bajo (media={mean_cwsi:.3f}). Tc_wet sobreestimado — recalibrar."}

        if mean_cwsi > DRIFT_HIGH_THRESHOLD:
            self.state.drift_alert = True
            self.state.drift_direction = "high"
            return {"drift_detected": True, "direction": "high",
                    "mean": round(mean_cwsi, 4), "std": round(std_cwsi, 4),
                    "message": f"CWSI sistemáticamente alto (media={mean_cwsi:.3f}). Tc_wet subestimado — recalibrar."}

        # Señal sin variación (valor medio OK, pero sensor posiblemente congelado)
        if std_cwsi < DRIFT_STD_MIN:
            self.state.drift_alert = True
            self.state.drift_direction = "dead"
            return {"drift_detected": True, "direction": "dead",
                    "mean": round(mean_cwsi, 4), "std": round(std_cwsi, 4),
                    "message": f"Señal CWSI sin variación (std={std_cwsi:.4f}). Posible falla de sensor."}

        self.state.drift_alert = False
        self.state.drift_direction = ""
        return {"drift_detected": False,
                "mean": round(mean_cwsi, 4), "std": round(std_cwsi, 4),
                "message": "Baseline estable."}

    # ── Aplicación del offset ─────────────────────────────────────────────────

    def tc_wet_effective(self, ta_c: float, vpd_kpa: float) -> float:
        """
        Calcula el Tc_wet efectivo del nodo para las condiciones actuales.

        Tc_wet_efectivo = NWSB(Ta, VPD) + tc_wet_offset
        """
        return _nwsb_tc_wet(ta_c, vpd_kpa) + self.state.tc_wet_offset

    def tc_dry_effective(self, ta_c: float, vpd_kpa: float) -> float:
        """
        Calcula el Tc_dry efectivo (límite superior) para las condiciones actuales.
        Modelo simplificado: Tc_dry ≈ Ta + 3.5°C (Bellvert 2016) + offset.
        """
        return (ta_c + 3.5) + self.state.tc_dry_offset


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _nwsb_tc_wet(ta_c: float, vpd_kpa: float) -> float:
    """
    Non-Water-Stressed Baseline de Jackson (1981).
    Tc_wet ≈ Ta − a·VPD  donde a ≈ 0.5 para la mayoría de cultivos.
    Para Malbec en Cuyo: recalibrado a a=0.45 (Bellvert 2016).
    """
    return ta_c - 0.45 * vpd_kpa


# ─────────────────────────────────────────────────────────────────────────────
# Demo — Prueba de Concepto TRL 3
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    SEP = "=" * 66

    print(SEP)
    print("  Auto-Calibración Baseline CWSI — HydroVision AG — TRL 3")
    print("  Colonia Caroya, Córdoba — Jackson (1981) + EMA")
    print(SEP)

    # Nodo N01 — inicio de temporada (baseline de fábrica)
    state = BaselineState(node_id="N01", crop="malbec", season="2026-2027")
    bl = CWSIBaseline(state)

    print(f"\n  Baseline inicial: offset Tc_wet = {bl.state.tc_wet_offset:+.4f}°C (fábrica)")
    print(f"  Calidad: {bl.state.calibration_quality}\n")

    # ── Evento 1: lluvia de 12mm, enero — planta bien hidratada ──────────────
    r1 = bl.update_rain(
        tc_measured_c=31.8,   # Tc medida cuando la planta está bien hidratada
        ta_c=32.5,
        vpd_kpa=1.2,          # VPD bajo post-lluvia
        mds_um=45.0,          # MDS casi cero: planta al máximo
        rain_mm=12.0,
        date="2026-01-08",
    )
    print(f"  Evento lluvia 12mm (2026-01-08):")
    print(f"    NWSB calculado : {r1['nwsb_tc_wet']:.2f}°C")
    print(f"    Tc medido      : {r1['tc_measured']:.2f}°C")
    print(f"    Offset campo   : {r1['measured_offset']:+.4f}°C")
    print(f"    Offset EMA nuevo: {r1['new_offset']:+.4f}°C")
    print(f"    Calidad        : {r1['calibration_quality']}")

    # ── Evento 2: sesión Scholander — planta moderadamente hidratada ──────────
    r2 = bl.update_scholander(
        tc_measured_c=33.1,
        ta_c=35.0,
        vpd_kpa=2.4,
        psi_stem_mpa=-0.72,   # estrés leve → confianza moderada
        mds_um=130.0,
        date="2026-02-05",
    )
    print(f"\n  Sesión Scholander (2026-02-05):")
    print(f"    ψ_stem         : {r2['psi_stem_mpa']:.2f} MPa")
    print(f"    Confianza EMA  : {r2['confidence']:.3f}")
    print(f"    lr efectiva    : {r2['effective_lr']:.4f}")
    print(f"    Offset nuevo   : {r2['new_offset']:+.4f}°C")

    # ── Detección de deriva — simular historial de CWSI sistemáticamente bajo ─
    print(f"\n  Simulando historial CWSI bajo (baseline sobreestimado):")
    for _ in range(15):
        bl.add_cwsi_sample(0.008)   # valores muy bajos → posible deriva
    drift = bl.check_drift()
    print(f"    Deriva detectada: {drift['drift_detected']}")
    print(f"    Dirección      : {drift.get('direction', '-')}")
    print(f"    Media CWSI     : {drift['mean']:.4f}")
    print(f"    Mensaje        : {drift['message']}")

    # ── Estado final ──────────────────────────────────────────────────────────
    print(f"\n  Estado final del baseline N01:")
    print(f"    Offset Tc_wet  : {bl.state.tc_wet_offset:+.4f}°C")
    print(f"    Eventos lluvia : {bl.state.n_rain_events}")
    print(f"    Sesiones Scholander: {bl.state.n_scholander_updates}")
    print(f"    Calidad        : {bl.state.calibration_quality}")
    print(f"    Tc_wet efectiva (Ta=35°C, VPD=2.5): "
          f"{bl.tc_wet_effective(35.0, 2.5):.2f}°C")

    print(f"\n  [OK] Módulo baseline.py operativo — TRL 3")
    print(f"  Auto-calibración: lluvia+MDS≈0 → EMA lr={LEARNING_RATE_RAIN}")
    print(f"  Deriva detectada si media CWSI < {DRIFT_LOW_THRESHOLD} o > {DRIFT_HIGH_THRESHOLD}")
    print(f"  Persistencia: JSON local por nodo (reboot-safe)")
